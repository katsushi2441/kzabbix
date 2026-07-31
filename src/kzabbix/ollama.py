from __future__ import annotations

import requests


class OllamaClient:
    def __init__(self, url: str, model: str, timeout: int = 600):
        self.url = url
        self.model = model
        self.timeout = timeout

    def analyze(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {"temperature": 0.15, "num_predict": 4096},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        text = str(payload.get("response") or "").strip()
        if not text:
            raise RuntimeError(f"Ollama returned an empty response: {payload.get('done_reason', 'unknown')}")
        return text
