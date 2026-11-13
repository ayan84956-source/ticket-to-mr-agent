import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_OUTPUT_CHARS = 300

@dataclass
class RunResult:
    passed: bool
    output: str

def run_test(workspacce: Path, timeout: int = 60) -> RunResult:
    command = [
        sys.executable, "-m", "pytest",
        "-q", "--tb=short", "-p", "no:chacheprovider",
    ]
    env = {**os.environ, "PYTHONUTF8": "1"}
    try:
        result = subprocess.run(
            command, cwd = workspacce, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout, env=env
        )
    except subprocess.TimeoutExpired:
        return RunResult(
        False,
        f"The process didn't finish within {timeout} seconds"
        )
    output = (result.stdout + "\n" + result.stderr).strip()
    if len(output) > MAX_OUTPUT_CHARS:
        output = "...\n" + output[-MAX_OUTPUT_CHARS:]
    return RunResult(result.returncode == 0, output)
if __name__=="__main__":
    from core.config import load_settings
    settings = load_settings()
    result = run_test(settings.work_dir /"selftest")
    print("passed:", result.passed)
    print(result.output)