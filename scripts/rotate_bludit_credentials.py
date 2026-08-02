#!/usr/bin/env python3
from __future__ import annotations

import ftplib
import hashlib
import io
import json
import secrets
from pathlib import Path


def load_env(path: Path) -> dict[str, str]:
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"").strip("'")
    return values


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def decode_db(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    _, payload = text.split("\n", 1)
    return json.loads(payload)


def encode_db(data: dict) -> bytes:
    prefix = "<?php defined('BLUDIT') or die('Bludit CMS.'); ?>\n"
    return (prefix + json.dumps(data, ensure_ascii=False, indent=4) + "\n").encode("utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime_path = root / ".runtime.env"
    runtime = load_env(runtime_path)
    mail = load_env(Path("/home/kojima/work/aixec/.env"))
    new_api = secrets.token_hex(32)
    new_auth = secrets.token_hex(24)
    new_password = secrets.token_urlsafe(36)
    new_salt = secrets.token_hex(8)

    ftp = ftplib.FTP(mail["FTP_HOST"], timeout=30)
    ftp.login(mail["FTP_USER"], mail["FTP_PASS"])
    base = "/web/kurage_exbridge_jp/zabbix"

    def download(path: str) -> bytes:
        output = io.BytesIO()
        ftp.retrbinary(f"RETR {base}/{path}", output.write)
        return output.getvalue()

    def upload(path: str, content: bytes) -> None:
        ftp.storbinary(f"STOR {base}/{path}", io.BytesIO(content))

    api_path = "bl-content/databases/plugins/api/db.php"
    api = decode_db(download(api_path))
    api["token"] = new_api
    upload(api_path, encode_db(api))

    users_path = "bl-content/databases/users.php"
    users = decode_db(download(users_path))
    users["admin"]["salt"] = new_salt
    users["admin"]["password"] = hashlib.sha1((new_password + new_salt).encode()).hexdigest()
    users["admin"]["tokenAuth"] = new_auth
    users["admin"]["tokenAuthTTL"] = "2099-12-31 23:59"
    upload(users_path, encode_db(users))
    ftp.quit()

    runtime.update(
        {
            "BLUDIT_API_TOKEN": new_api,
            "BLUDIT_AUTH_TOKEN": new_auth,
            "BLUDIT_ADMIN_PASSWORD": new_password,
        }
    )
    temporary = runtime_path.with_suffix(".tmp")
    temporary.write_text(
        "\n".join(f"{key}={quote(value)}" for key, value in runtime.items()) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(runtime_path)
    print("Bludit API, authentication, and admin credentials rotated")


if __name__ == "__main__":
    main()
