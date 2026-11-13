import sys

from core.config import load_settings
from core.gitlab_client import GitLabClient

settings = load_settings()
client = GitLabClient(settings)

project_id, issue_iid = int(sys.argv[1]), int(sys.argv[2])

print("Project:", client.get_project(project_id)["path_with_namespace"])
print("Issue  :", client.get_issue(project_id, issue_iid)["title"])