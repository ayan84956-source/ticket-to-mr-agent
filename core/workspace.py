import os
import shutil
import stat
import subprocess
from pathlib import Path
from core.config import Settings
from core.gitlab_client import GitLabClient

class WorkspaceError(Exception):
    """Raised when git fails while preparing the workspace."""

def _run_git(args: list, cwd: Path = None, secret: str = "") -> str:
    """Run one git command and return its output."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=120
        )
    except FileNotFoundError as e:
        raise WorkspaceError("Git was not found. Is it installed and on PATH?") from e
    except subprocess.TimeoutExpired as e:
        raise WorkspaceError(f"git {args[0]} took too long.") from e

    if result.returncode != 0:
        message = result.stderr.strip()
        if secret:
            message = message.replace(secret, "***")
        raise WorkspaceError(f"git {args[0]} failed: {message}")
    return result.stdout.strip()


def _on_remove_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def create_workspace(project_id: int, issue_iid: int,
                     settings: Settings, gitlab: GitLabClient) -> Path:
    project = gitlab.get_project(project_id)
    repo_url = project["http_url_to_repo"]
    token = settings.gitlab_token
    clone_url = repo_url.replace("https://", f"https://oauth2:{token}@", 1)

    folder = settings.work_dir / f"issue-{issue_iid}"
    if folder.exists():
        shutil.rmtree(folder, onerror=_on_remove_error)
    folder.parent.mkdir(parents=True, exist_ok=True)

    _run_git(["clone", clone_url, str(folder)], secret=token)
    _run_git(["checkout", "-b", f"ai/issue-{issue_iid}"], cwd=folder)
    _run_git(["config", "user.name", "Ticket-to-MR Agent"], cwd=folder)
    _run_git(["config", "user.email", "agent@example.com"], cwd=folder)
    return folder

if __name__ == "__main__":
    import sys

    from core.config import load_settings

    settings = load_settings()
    settings.check_secrets()
    gitlab = GitLabClient(settings)
    path = create_workspace(int(sys.argv[1]), int(sys.argv[2]), settings, gitlab)
    print("Workspace:", path)
    print("Branch   :", _run_git(["branch", "--show-current"], cwd=path))
    print("Files    :", sorted(p.name for p in path.iterdir() if p.name != ".git"))