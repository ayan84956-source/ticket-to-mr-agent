from core.config import PROJECT_ROOT
from core.model_client import ModelClient
from ai_steps.spec_parts import build_files_section, build_tests_section

MAX_BEHAVIOR_BULLETS = 6

class SpecError(Exception):
    """Raised when the model gives no usable Behavior list."""

def extract_bullets(answer: str, fields: dict) -> list[str]:
    """Keep clean bullet lines, dropping ones that repeat file names or tests."""
    file_names = [
        ln.strip().lstrip("-*• ").strip().lower()
        for ln in fields["Where"].splitlines()
    ]
    file_names = [name for name in file_names if name]

    bullets = []
    for line in answer.splitlines():
        line = line.strip()
        if not line.startswith(("- ", "* ")):
            continue
        text = line[2:].strip()
        lowered = text.lower()
        if "test" in lowered:
            continue
        if any(name in lowered for name in file_names):
            continue
        bullets.append("- " + text)
    return bullets[:MAX_BEHAVIOR_BULLETS]

def write_spec(title: str, fields: dict, model: ModelClient) -> str:
    system_prompt = (PROJECT_ROOT / "prompts" / "write_behaviour.txt").read_text(encoding="utf-8")
    user_prompt = (
        f"Title: {title}\n"
        f"What to change: {fields['What to change']}\n"
        f"Where: {fields['Where']}\n"
        f"Done when: {fields['Done when']}"
    )

    bullets = []
    for _ in range(2):
        answer = model.ask("write_spec", system_prompt, user_prompt)
        bullets = extract_bullets(answer, fields)
        if bullets:
            break
    if not bullets:
        raise SpecError("The model did not return a usable Behavior list.")

    files = build_files_section(fields["Where"])
    behavior = "## Behavior\n" + "\n".join(bullets)
    tests = build_tests_section(fields["Done when"])
    return "\n\n".join([files, behavior, tests])

if __name__ == "__main__":
    from core.config import load_settings

    fields = {
        "What to change": "Add a function slugify(text) that makes a URL-friendly slug.",
        "Where": "app/utils.py\ntests/test_utils.py",
        "Done when": "slugify('Hello World') returns 'hello-world'\nslugify('') returns ''",
    }
    model = ModelClient(load_settings())
    print(write_spec("Add slugify helper", fields, model))