from dataclasses import dataclass
from core.config import PROJECT_ROOT
from core.model_client import ModelClient

FIELDS = {
    "what to change": "What to change",
    "where": "Where",
    "done when": "Done when",
}

@dataclass
class CheckResult:
    ok: bool
    message: str
    fields: dict

def parse_issue(description: str) -> dict[str, str]:
    fields = {name: "" for name in FIELDS.values()}
    current = None
    for line in (description or "").splitlines():
        clean = line.replace("*", "").replace("#", "").strip()
        lowered = clean.lower()
        matched = False
        for key, name in FIELDS.items():
            if lowered.startswith(f"{key}:"):
                current = name
                fields[name] = clean.split(":", 1)[1].strip()
                matched = True
                break
        if not matched and current:
            fields[current] = f"{fields[current]}\n{clean}".strip()
    return fields

def find_missing(fields: dict[str, str]) -> list[str]:
    return [name for name, value in fields.items() if len(value.strip()) < 3]

def missing_message(missing: list) -> str:
    lines = "\n".join(f"-**{name}**" for name in missing)
    return (
        "Thanks! Before I can start, I need a bit more information. "
        "Please add:\n\n" + lines + "\n\n"
        "Use this format in the issue description:\n\n"
        "**What to change:** ...\n\n**Where:** ...\n\n**Done when:** ...\n\n"
        "Then add the `ai-ready` label again."
    )

def check_issue(issue: dict, model: ModelClient) -> CheckResult:
    fields = parse_issue(issue.get("description") or issue.get("Description") or "")
    missing = find_missing(fields)
    if missing:
        return CheckResult(False, missing_message(missing), fields)
    system_prompt = (PROJECT_ROOT / "prompts" / "check_issue.txt").read_text(encoding="utf-8")
    user_prompt = (
        f"Title: {issue['title']}\n"
        f"What to change: {fields['What to change']}\n"
        f"Where: {fields['Where']}\n"
        f"Done when: {fields['Done when']}"
    )
    answer = model.ask("check_issue", system_prompt, user_prompt)
    first_line = next((l.strip() for l in answer.splitlines() if l.strip()),"")
    if first_line.upper().startswith("UNCLEAR"):
        question = first_line.strip(":", 1)[1].strip() if ":" in first_line else ""
        message = (
            "I have a question before i start:\n\n",
            f">{question or 'could you descride the current behavior more clearly?'}\n\n"
            "Plase update the issue and add the 'AI-ready' label again."
        )
        return CheckResult(False, message, fields)
    return CheckResult(True, "", fields)

if __name__ == "__main__":
    import sys
    from core.config import load_settings
    from core.gitlab_client import GitLabClient

    settings = load_settings()
    settings.check_secrets()
    gitlab = GitLabClient(settings)
    model = ModelClient(settings)
    issue = gitlab.get_issue(int(sys.argv[1]), int(sys.argv[2]))
    result = check_issue(issue, model)
    print ("parse fields:", result.fields)
    print ("ok to contineu:", result.ok)
    if not result.ok:
        print("Would post this command:\n", result.message)