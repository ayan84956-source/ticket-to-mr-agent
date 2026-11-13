from dataclasses import dataclass
from pathlib import Path
from core.config import Settings
from core.model_client import ModelClient
from core.test_runner import run_test
from ai_steps.write_code import write_code
from ai_steps.fix_code import fix_code

@dataclass
class DevResult:
    passed : bool
    fix_attemps : int
    output : str

def fix_loop(spec: str, fields: dict, workspace: Path,
               settings: Settings, model: ModelClient) -> DevResult:
    result = run_test(workspace)
    attemps = 0
    while not result.passed and attemps < settings.max_attempts:
        attemps += 1
        print(f"Failed . Fix attemps {attemps} of {settings.max_attempts}")
        fix_code(spec, fields, workspace, result.output, model)
        result = run_test(workspace)
    return DevResult(result.passed, attemps, result.output)

def develop(spec: str, fields: dict, workspace: Path,
            settings: Settings, model: ModelClient) -> DevResult:
    written = write_code(spec, fields, workspace, model)
    print("Filea Written:", written)
    return fix_loop(spec, fields, workspace, settings, model)

if __name__ == "__main__":
    from core.config import load_settings
    from ai_steps.write_code import find_paths

    settings = load_settings()
    fields = {
        "What to change": "Add a function slugify(text) that makes a URL-friendly slug.",
        "Where": "app/utils.py\ntests/test_utils.py",
        "Done when": "slugify('Hello World') returns 'hello-world'\nslugify('') returns ''",
    }
    spec = (
        "## Files\n- app/utils.py\n- tests/test_utils.py\n\n"
        "## Behavior\n"
        "- A function slugify(text) takes a string and returns a string.\n"
        "- 'Hello World' becomes 'hello-world' (lowercase, spaces become hyphens).\n"
        "- An empty string returns an empty string.\n\n"
        "## Tests\n"
        "- slugify('Hello World') returns 'hello-world'\n"
        "- slugify('') returns ''"
    )
    folder = settings.work_dir / "selftest"
    code_path, _ = find_paths(fields["Where"])

    (folder / code_path).write_text("def slugify(text):\n    return text\n", encoding="utf-8")

    result = fix_loop(spec, fields, folder, settings, ModelClient(settings))
    print("Passed       :", result.passed)
    print("Fix attempts :", result.fix_attemps)
    print("Final code   :\n" + (folder / code_path).read_text(encoding="utf-8"))