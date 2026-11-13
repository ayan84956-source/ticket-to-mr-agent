from core.config import load_settings
from core.model_client import ModelClient
from ai_steps.develop import develop

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

result = develop(spec, fields, folder, settings, ModelClient(settings))
print("Passed       :", result.passed)
print("Fix attempts :", result.fix_attemps)
print("Output       :", result.output)