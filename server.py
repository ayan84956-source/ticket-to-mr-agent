import hmac
import threading
import traceback
from flask import Flask, request
from agent import run_agent
from core.config import load_settings
from core.gitlab_client import GitLabClient
from core.model_client import ModelClient

settings = load_settings()
settings.check_secrets()
gitlab = GitLabClient(settings)
model = ModelClient(settings)
app = Flask(__name__)
running = set()
lock = threading.Lock()

def label_was_added(payload: dict, label: str) -> bool:
    if payload.get("object_kind") != "issue":
        return False
    now = [item["title"] for item in payload.get("labels", [])]
    if label not in now:
        return False
    changes = payload.get("changes", {}).get("labels")
    if changes:
        before = [item["title"] for item in changes.get("previous", [])]
        return label not in before
    return payload.get("object_attributes", {}).get("action") == "open"

def _work(key: tuple) -> None:
    project_id, issue_iid = key
    try:
        run_agent(project_id, issue_iid, settings, gitlab, model)
    except Exception:
        traceback.print_exc()
    finally:
        with lock:
            running.discard(key)

@app.post("/")
@app.post("/webhook")

def webhook():
    token = request.headers.get("X-Gitlab-Token", "")
    if not hmac.compare_digest(token, settings.webhook_secret):
        return "forbidden", 403

    payload = request.get_json(silent=True) or {}
    if not label_was_added(payload, settings.trigger_label):
        return "ignored", 200

    key = (payload["project"]["id"], payload["object_attributes"]["iid"])
    with lock:
        if key in running:
            return "already running", 200
        running.add(key)

    threading.Thread(target=_work, args=(key,), daemon=True).start()
    return "started", 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)