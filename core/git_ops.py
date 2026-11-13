import re
import subprocess
import sys

def _clean(text):
    return re.sub(r"://[^@/\s]+@", "://***@", text)

def _git(workspace, *args):
    return subprocess.run(
        ["git", *args],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )

def commit_and_push(workspace, branch, message):
    add = _git(workspace, "add", "-A")
    if add.returncode != 0:
        return False, "git add failed: " + _clean(add.stderr)
    status = _git(workspace, "status", "--porcelain")
    if not status.stdout.strip():
        return False, "nothing to commit: no files were changed"
    commit = _git(workspace, "commit", "-m", message)
    if commit.returncode != 0:
        return False, "git commit failed: " + _clean(commit.stderr or commit.stdout)
    push = _git(workspace, "push", "-u", "origin", branch)
    if push.returncode != 0:
        return False, "git push failed: " + _clean(push.stderr)

    return True, "pushed " + branch
if __name__ == "__main__":
    ws, br = sys.argv[1], sys.argv[2]
    with open(ws + "\\agent_push_test.txt", "w") as f:
        f.write("push test from the agent\n")
    print(commit_and_push(ws, br, "Agent: push test"))