import os
from dataclasses import dataclass
from pathlib import Path
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

@dataclass

class Settings:

    gitlab_url: str
    gitlab_token: str
    webhook_secret: str
    ollama_url: str
    cloud_api_key: str
    trigger_label: str
    in_progress_label: str
    failed_label: str
    review_label: str
    max_attempts: int
    work_dir: Path
    models: dict

    def model_for(self, job: str) -> dict:
        merged = dict(self.models["default"])
        merged.update(self.models.get(job) or {})
        return merged

    def check_secrets(self) -> None:
        missing = []
        for Name, value in [
            ("GITLAB_TOKEN", self.gitlab_token),
            ("WEBHOOK_SECRET", self.webhook_secret)
        ]:
            if not value or  value.startswith("put-"):
                missing.append(Name)
            if missing:
                raise ValueError("Add this in your .env"+",". join(missing))

def load_settings() -> Settings:
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.full_load(f)
        return Settings(
                gitlab_url=os.getenv("GITLAB_URL", "https://gitlab.com").rstrip("/"),
                gitlab_token=os.getenv("GITLAB_TOKEN", ""),
                webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
                ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
                cloud_api_key=os.getenv("CLOUD_API_KEY", ""),
                trigger_label=cfg["labels"]["trigger"],
                in_progress_label=cfg["labels"]["in_progress"],
                failed_label=cfg["labels"]["failed"],
                review_label=cfg["labels"]["review"],
                max_attempts=cfg["agent"]["max_attempts"],
                work_dir=Path(cfg["agent"]["work_dir"]),
                models=cfg["models"],
            )

if __name__=="__main__":
    s = load_settings()
    print("GITLAB ADDRESS :", s.gitlab_url)
    print("Token          :", "set" if s.gitlab_token and not s.gitlab_token.startswith("put-") else "NOT SET")
    print("Trigger label  :", s.trigger_label)
    print("Max attempts   :", s.max_attempts)
    print("Work folder    :", s.work_dir)
    print("Model (default):", s.model_for("write_code"))