#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import secrets
from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".runtime.env")
    parser.add_argument("--mail-env", default="/home/kojima/work/aixec/.env")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing secret file: {output}")
    mail = load_env(Path(args.mail_env))
    zabbix_password = os.getenv("ZABBIX_PASSWORD", "")
    if not zabbix_password:
        raise SystemExit("ZABBIX_PASSWORD must be supplied in the process environment")
    smtp_from = mail.get("SMTP_FROM", "")
    gate_token = secrets.token_hex(32)
    values = {
        "KZABBIX_API_TOKEN": secrets.token_hex(32),
        "KZABBIX_DB_PATH": "/home/kojima/work/kzabbix/data/incidents.sqlite3",
        "ZABBIX_API_URL": "http://127.0.0.1:18202/api_jsonrpc.php",
        "ZABBIX_USERNAME": "Admin",
        "ZABBIX_PASSWORD": zabbix_password,
        "OLLAMA_URL": "http://192.168.0.3:11434/api/generate",
        "OLLAMA_MODEL": "gemma4:12b-it-qat",
        "SMTP_HOST": mail.get("SMTP_HOST", "smtp.gmail.com"),
        "SMTP_PORT": mail.get("SMTP_PORT", "587"),
        "SMTP_USERNAME": smtp_from,
        "SMTP_PASSWORD": mail.get("SMTP_PASSWORD", ""),
        "SMTP_FROM": smtp_from,
        "REPORT_EMAIL_TO": "katsushi2441@gmail.com",
        "MAIL_RELAY_URL": "https://kurage.exbridge.jp/zabbix/notify.php",
        "MAIL_RELAY_TOKEN": gate_token,
        "BLUDIT_API_URL": "https://kurage.exbridge.jp/zabbix/api/pages",
        "BLUDIT_API_TOKEN": secrets.token_hex(32),
        "BLUDIT_AUTH_TOKEN": secrets.token_hex(24),
        "BLUDIT_GATE_TOKEN": gate_token,
        "BLUDIT_ADMIN_PASSWORD": secrets.token_urlsafe(36),
    }
    missing = [name for name in ("SMTP_USERNAME", "SMTP_PASSWORD") if not values[name]]
    if missing:
        raise SystemExit("mail environment is missing: " + ", ".join(missing))
    output.write_text(
        "\n".join(f"{key}={quote(value)}" for key, value in values.items()) + "\n", encoding="utf-8"
    )
    output.chmod(0o600)
    print(f"runtime secrets created: {output} (mode 600)")


if __name__ == "__main__":
    main()
