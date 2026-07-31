from __future__ import annotations

import requests


class OllamaClient:
    def __init__(self, url: str, model: str, timeout: int = 600):
        self.url = url
        self.model = model
        self.timeout = timeout

    def analyze(self, prompt: str) -> str:
        current_prompt = prompt
        last_payload: dict = {}
        for attempt in range(2):
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": current_prompt,
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0.15, "num_predict": 4096, "num_ctx": 32768},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            last_payload = response.json()
            text = str(last_payload.get("response") or "").strip()
            if len(text) >= 400 and "障害" in text:
                return text
            current_prompt = (
                current_prompt[:30_000]
                + "\n\n前回の出力が不完全でした。必須の章をすべて含む400文字以上の日本語Markdownレポートを返してください。"
            )
        raise RuntimeError(
            "Ollama returned an incomplete report: "
            f"chars={len(str(last_payload.get('response') or ''))}, "
            f"done_reason={last_payload.get('done_reason', 'unknown')}"
        )
