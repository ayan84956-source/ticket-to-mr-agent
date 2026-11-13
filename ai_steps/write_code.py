import re
from pathlib import Path
from core.config import PROJECT_ROOT
from core.model_client import ModelClient

class CodeError(Exception):
    """Raised when the files cannot be planned or the model's code is unusable."""

def is_test_file(path: str) -> bool:
    name = path.split("/")[-1]
    return name.startswith("test_") or name.endswith("_test.py")

def find_paths(where: str) -> tuple:
    """Return (code_path, test_path) taken from the issue's Where field."""
    paths = []
    for found in re.findall(r"[\w./\\-]+\.py", where):
        path = found.replace("\\", "/")
        if path.startswith("./"):
            path = path[2:]
        if path not in paths:
            paths.append(path)

    code_files = [p for p in paths if not is_test_file(p)]
    test_files = [p for p in paths if is_test_file(p)]
    if len(code_files) != 1 or len(test_files) > 1:
        raise CodeError(
            "for it only handles one code file and at most one test file. "
            f"Found in Where: {paths}"
        )

    code_path = code_files[0]
    if test_files:
        return code_path, test_files[0]
    folder, _, name = code_path.rpartition("/")
    test_name = f"test_{name}"
    return code_path, f"{folder}/{test_name}" if folder else test_name

def extract_code(answer: str) -> str:
    """Take the code out of a fenced block; use the whole answer if there is none."""
    match = re.search(r"```(?:python)?\s*\n(.*?)```", answer, re.DOTALL)
    code = match.group(1) if match else answer
    return code.strip() + "\n"

def _ask_for_code(model: ModelClient, system_prompt: str, user_prompt: str, path: str,
                  job: str = "write_code") -> str:
    """Ask the model for code; accept it only if Python can parse it."""
    for _ in range(2):
        code = extract_code(model.ask(job, system_prompt, user_prompt))
        try:
            compile(code, path, "exec")
            return code
        except SyntaxError:
            continue
    raise CodeError(f"The model did not produce valid Python for {path}.")

def write_code(spec: str, fields: dict, workspace: Path, model: ModelClient) -> list:
    code_path, test_path = find_paths(fields["Where"])
    module = code_path[:-3].replace("/", ".")

    code_prompt = (PROJECT_ROOT / "prompts" / "write_code.txt").read_text(encoding="utf-8")
    test_prompt = (PROJECT_ROOT / "prompts" / "write_test.txt").read_text(encoding="utf-8")

    code = _ask_for_code(
        model, code_prompt,
        f"File to write: {code_path}\n\nPlan:\n{spec}", code_path,
    )
    tests = _ask_for_code(
        model, test_prompt,
        f"Test file to write: {test_path}\nModule under test: {module}\n\nPlan:\n{spec}",
        test_path,
    )

    for rel_path, text in ((code_path, code), (test_path, tests)):
        target = workspace / rel_path
        if not target.resolve().is_relative_to(workspace.resolve()):
            raise CodeError(f"Path {rel_path} is outside the workspace.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return [code_path, test_path]

if __name__ == "__main__":
    from core.config import load_settings

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
    folder.mkdir(parents=True, exist_ok=True)
    written = write_code(spec, fields, folder, ModelClient(settings))
    for rel_path in written:
        print(f"===== {rel_path} =====")
        print((folder / rel_path).read_text(encoding="utf-8"))