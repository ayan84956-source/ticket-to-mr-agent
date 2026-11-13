def _to_bullets(text: str) -> str:
    """Turn a field's text into markdown bullets, keeping the words unchanged."""
    lines = [ln.strip().lstrip("-*• ").strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(f"- {ln}" for ln in lines)

def build_files_section(where: str) -> str:
    return "## Files\n" + _to_bullets(where)

def build_tests_section(done_when: str) -> str:
    return "## Tests\n" + _to_bullets(done_when)

if __name__ == "__main__":
    where = "app/utils.py\n- tests/test_utils.py"
    done_when = "slugify('Hello World') returns 'hello-world'\nEmpty string returns empty string"
    print(build_files_section(where))
    print()
    print(build_tests_section(done_when))