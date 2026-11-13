from pathlib import Path
from core.config import PROJECT_ROOT
from core.model_client import ModelClient
from ai_steps.write_code import find_paths, _ask_for_code

def fix_code(spec: str, fields: dict, workspace: Path,
             test_output: str, model: ModelClient) -> None:
    code_path, test_path = find_paths(fields["Where"])
    current_code = (workspace / code_path).read_text(encoding="utf-8")
    test_code = (workspace / test_path).read_text(encoding="utf-8")
    system_prompt = (PROJECT_ROOT / "prompts" / "fix_code.txt").read_text(encoding="utf-8")
    user_prompt = (
        f"File to rewrite: {code_path}\n\n"
        f"Plan:\n{spec}\n\n"
        f"Current Code:\n'''Python{test_code}'''\n\n"
        f"Pytest Output:\n{test_output}"
    )
    print(type(user_prompt))
    fixed = _ask_for_code(model, system_prompt, user_prompt, code_path, job="fixed_code")
    (workspace / code_path).write_text(fixed, encoding="utf-8")
