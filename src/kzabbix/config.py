from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    api_token: str
    db_path: str
    zabbix_api_url: str
    zabbix_username: str
    zabbix_password: str
    ollama_url: str
    ollama_model: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from: str
    report_email_to: str
    mail_relay_url: str
    mail_relay_token: str
    bludit_api_url: str
    bludit_api_token: str
    bludit_auth_token: str
    bludit_gate_token: str

    @classmethod
    def from_env(cls) -> Settings:
        smtp_username = os.getenv("SMTP_USERNAME", "").strip()
        return cls(
            api_token=_required("KZABBIX_API_TOKEN"),
            db_path=os.getenv("KZABBIX_DB_PATH", "data/incidents.sqlite3"),
            zabbix_api_url=os.getenv("ZABBIX_API_URL", "http://127.0.0.1:18202/api_jsonrpc.php"),
            zabbix_username=os.getenv("ZABBIX_USERNAME", "Admin"),
            zabbix_password=_required("ZABBIX_PASSWORD"),
            ollama_url=os.getenv("OLLAMA_URL", "http://192.168.0.3:11434/api/generate"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:12b-it-qat"),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=smtp_username,
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", smtp_username),
            report_email_to=os.getenv("REPORT_EMAIL_TO", "katsushi2441@gmail.com"),
            mail_relay_url=os.getenv("MAIL_RELAY_URL", "https://kurage.exbridge.jp/zabbix/notify.php"),
            mail_relay_token=os.getenv("MAIL_RELAY_TOKEN", ""),
            bludit_api_url=os.getenv("BLUDIT_API_URL", "https://kurage.exbridge.jp/zabbix/api/pages"),
            bludit_api_token=os.getenv("BLUDIT_API_TOKEN", ""),
            bludit_auth_token=os.getenv("BLUDIT_AUTH_TOKEN", ""),
            bludit_gate_token=os.getenv("BLUDIT_GATE_TOKEN", ""),
        )
