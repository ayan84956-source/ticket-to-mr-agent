import requests
import sys
from core.config import load_settings

settings = load_settings()
settings.check_secrets()
url = "http://127.0.0.1:8000/webhook"
good = {"X-Gitlab-Token": settings.webhook_secret}

def event(labels_now, labels_before):
    return {
        "object_kind": "issue",
        "project": {"id": int(sys.argv[1])},
        "object_attributes": {"iid": int(sys.argv[2]), "action": "update"},
        "labels": [{"title": t} for t in labels_now],
        "changes": {"labels": {
            "previous": [{"title": t} for t in labels_before],
            "current": [{"title": t} for t in labels_now],
        }},
    }

r = requests.post(url, json= event([settings.trigger_label], []), headers={"X-Gitlab-Token": "wrong"})
print("Wrong secret :", r.status_code, r.text)

r = requests.post(url, json= event(["bug"], []), headers= good)
print("Other label  :", r.status_code, r.text)

if "run" in sys.argv:
    r = requests.post(url, json=event([settings.trigger_label], []), headers=good)
    print("Trigger label:", r.status_code, r.text)