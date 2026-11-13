import sys
from core.config import load_settings
from core.gitlab_client import GitLabClient

settings = load_settings()
settings.check_secrets()
client = GitLabClient(settings)
project_id = int(sys.argv[1])
branch = sys.argv[2]
mr = client.create_merge_request(
    project_id, branch,"Agent MR Test", "Test description from the agent."
)
print("MR_Created:", mr["web_url"])