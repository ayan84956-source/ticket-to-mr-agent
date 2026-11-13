import requests
from core.config import Settings

class ModelError(Exception):
    """Raised when the model cannot be reached or answers badly."""

class ModelClient():

    def __init__(self, settings: Settings):
        self.settings= settings

    def ask(self, job: str, system_prompt: str, user_prompts: str) -> str:
        model_cfg= self.settings.model_for(job)
        provider = model_cfg["provider"]
        if provider == "ollama":
            return self._ask_ollama(model_cfg, system_prompt, user_prompts)
        if provider == "cloud":
            raise ModelError("The cloud provider is not build yet.")
        raise ModelError(f"Unknown Provider '{provider}' for job '{job}'.")

    def _ask_ollama(self, cfg: dict, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.settings.ollama_url}/api/chat"
        body = {
            "model": cfg["name"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": cfg.get("temperature", 0.2),
                "num_ctx": cfg.get("num_ctx", 8192),
            },
        }
        try:
           response = requests.post(url, json=body, timeout=cfg.get("timeout", 300))
           response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise ModelError(
                f"Can't Reach at Ollama {self.settings.ollama_url}. Is it running?"
            ) from e
        except requests.exceptions.HTTPError as e:
            raise ModelError(
                f"Ollama returned an error ({response.status_code}). "
                f"Is the model installed? Run: ollama pull {cfg['name']}"
            ) from e
        return response.json()["message"]["content"]

if __name__=="__main__":
    from core.config import load_settings
    client = ModelClient(load_settings())
    answer = client.ask(
        "Check Issue",
        "You are an assistant, Keep answer short",
        "Write a Python Code which add two numbers"
    )
    print(answer)