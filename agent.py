from core.config import Settings, load_settings
from core.gitlab_client import GitLabClient
from core.model_client import ModelClient
from ai_steps.check_issue import check_issue
from ai_steps.write_spec import write_spec, SpecError
from core.gitlab_client import GitLabError
from core.workspace import create_workspace, WorkspaceError
from core.git_ops import commit_and_push
from ai_steps.write_code import CodeError
from ai_steps.develop import develop

def _fail(gitlab, settings, project_id, issue_iid, message):
    gitlab.add_comment(project_id, issue_iid, message)
    gitlab.change_labels(
        project_id, issue_iid,
        add=[settings.failed_label], remove=[settings.in_progress_label],
    )

def run_agent(project_id: str, issue_iid: str, settings: Settings, gitlab: GitLabClient, model: ModelClient) -> None:
    issue = gitlab.get_issue(project_id, issue_iid)
    check = check_issue(issue, model)
    if not check.ok:
        gitlab.add_comment(project_id, issue_iid, check.message)
        gitlab.change_labels(project_id, issue_iid, remove=[settings.trigger_label])
        print("Stop the Issue needs more information")
        return
    gitlab.change_labels(
        project_id, issue_iid,
        add=[settings.in_progress_label], remove=[settings.trigger_label],
    )
    try:
        spec = write_spec(issue["title"], check.fields, model)
    except SpecError as e:
        gitlab.add_comment(
            project_id, issue_iid,
            f"I could not write plan for this issue. \n\nReason:{e}"
        )
        gitlab.change_labels(
            project_id, issue_iid,
            add=[settings.failed_label], remove=[settings.in_progress_label],
        )
        print("Stopped: Spec Failed:")
        return
    gitlab.add_comment(project_id, issue_iid,"### plan for thsi issue \n\n"+ spec)
    print("Spec posted.")
    branch = f"ai/issue-{issue_iid}"
    try:
        workspace = create_workspace(project_id, issue_iid, settings, gitlab)
        result = develop(spec, check.fields, workspace, settings, model)
    except (WorkspaceError, CodeError, GitLabError) as e:
        _fail(gitlab, settings, project_id, issue_iid,
              f"I could not write the code for this issue.\n\nReason: {e}")
        print("Stopped: development failed")
        return

    if not result.passed:
        _fail(gitlab, settings, project_id, issue_iid,
              f"I tried {result.fix_attemps} fix attempts and the tests still fail. "
              f"No merge request was created.\n\nLast error:\n```\n{result.output}\n```")
        print("Stopped: tests failed")
        return

    ok, detail = commit_and_push(workspace, branch, f"Issue #{issue_iid}: {issue['title']}")
    if not ok:
        _fail(gitlab, settings, project_id, issue_iid,
              f"The tests passed, but I could not push the code.\n\nReason: {detail}")
        print("Stopped: push failed")
        return

    description = (
        f"Closes #{issue_iid}\n\n"
        f"Automatic test result: passed after {result.fix_attemps} fix attempt(s).\n\n"
        f"```\n{result.output}\n```"
    )
    try:
        mr = gitlab.create_merge_request(project_id, branch, issue["title"], description)
    except GitLabError as e:
        _fail(gitlab, settings, project_id, issue_iid,
              f"The code is pushed to branch {branch}, but I could not open the merge request.\n\nReason: {e}")
        print("Stopped: merge request failed")
        return

    gitlab.add_comment(project_id, issue_iid, f"Draft merge request created: {mr['web_url']}")
    gitlab.change_labels(
        project_id, issue_iid,
        add=[settings.review_label], remove=[settings.in_progress_label],
    )
    print("Draft MR created:", mr["web_url"])

if __name__=="__main__":
    import sys
    Settings = load_settings()
    Settings.check_secrets()
    run_agent(
        int(sys.argv[1]), int(sys.argv[2]),
        Settings, GitLabClient(Settings), ModelClient(Settings),
    )