"""Every GitLab API call lives in this file."""
import requests

from core.config import Settings

class GitLabError(Exception):
    """Raised when GitLab cannot be reached or refuses a request."""

class GitLabClient:
    def __init__(self, settings: Settings):
        self.base_url = f"{settings.gitlab_url}/api/v4"
        self.headers = {"PRIVATE-TOKEN": settings.gitlab_token}

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Send one request to GitLab and return the answer as a dictionary."""
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method, url, headers=self.headers, timeout=30, **kwargs
            )
        except requests.exceptions.RequestException as e:
            raise GitLabError(f"Cannot reach GitLab at {url}: {e}") from e

        if response.status_code == 401:
            raise GitLabError("GitLab rejected the token (401). Check GITLAB_TOKEN in .env.")
        if response.status_code == 404:
            raise GitLabError(
                "Not found (404). Check the project ID and issue number, "
                "and that the token can access this project."
            )
        if not response.ok:
            raise GitLabError(f"GitLab error {response.status_code}: {response.text[:200]}")
        return response.json()

    def get_issue(self, project_id: int, issue_iid: int) -> dict:
        return self._request("GET", f"/projects/{project_id}/issues/{issue_iid}")
    
    def get_project(self, project_id: int) -> dict:
        return self._request("GET", f"/projects/{project_id}")

    def add_comment(self, project_id: int, issue_iid: int, text: str) -> dict:
        return self._request(
            "POST",
            f"/projects/{project_id}/issues/{issue_iid}/notes",
            json={"body": text},
        )

    def change_labels(self, project_id: int, issue_iid: int,
                      add: list = None, remove: list = None) -> dict:
        data = {}
        if add:
            data["add_labels"] = ",".join(add)
        if remove:
            data["remove_labels"] = ",".join(remove)
        return self._request(
            "PUT", f"/projects/{project_id}/issues/{issue_iid}", json=data
        )

    def create_merge_request(self, project_id: int, source_branch: str,
                             title: str, description: str) -> dict:
        project = self.get_project(project_id)
        target_branch = project.get("default_branch")
        if not target_branch:
            raise GitLabError("The project has no default branch")
        if target_branch == source_branch:
            raise GitLabError(
                f"The default branch is '{target_branch}' the same as agent's"
                "branch, so merge request is not poassible, Create a 'Main' branch"            
                "with a first commit and make it default."
                )
        return self._request(
            "POST",
            f"/projects/{project_id}/merge_requests",
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": f"Draft: {title}",
                "description": description,
                "remove_source_branch": True,
            },
        )
    
if __name__ == "__main__":
    import sys

    from core.config import load_settings

    settings = load_settings()
    settings.check_secrets()
    client = GitLabClient(settings)

    project_id, issue_iid = int(sys.argv[1]), int(sys.argv[2])

    issue = client.get_issue(project_id, issue_iid)
    print("Title  :", issue["title"])
    print("Labels :", issue["labels"])

    client.add_comment(project_id, issue_iid, "Test comment from the Ticket-to-MR agent.")
    print("Comment posted.")

    client.change_labels(
        project_id, issue_iid,
        add=[settings.in_progress_label], remove=[settings.trigger_label],
    )
    print("Labels swapped.")