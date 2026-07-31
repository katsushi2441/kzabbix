from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

import requests


class EmailNotifier:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        recipient: str,
        relay_url: str = "",
        relay_token: str = "",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipient = recipient
        self.relay_url = relay_url
        self.relay_token = relay_token

    @property
    def enabled(self) -> bool:
        relay = bool(self.relay_url and self.relay_token and self.recipient)
        smtp = bool(self.host and self.username and self.password and self.sender and self.recipient)
        return relay or smtp

    def send(self, subject: str, report: str) -> None:
        if not self.enabled:
            raise RuntimeError("email settings are incomplete")
        smtp_enabled = bool(
            self.host and self.username and self.password and self.sender and self.recipient
        )
        smtp_error: Exception | None = None
        if smtp_enabled:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = self.sender
            message["To"] = self.recipient
            message.set_content(report)
            try:
                context = ssl.create_default_context()
                if self.port == 465:
                    with smtplib.SMTP_SSL(
                        self.host, self.port, timeout=30, context=context
                    ) as smtp:
                        smtp.login(self.username, self.password)
                        smtp.send_message(message)
                else:
                    with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
                        smtp.starttls(context=context)
                        smtp.login(self.username, self.password)
                        smtp.send_message(message)
                return
            except Exception as exc:  # noqa: BLE001 - relay is the delivery fallback
                smtp_error = exc
        if self.relay_url and self.relay_token and self.recipient:
            response = requests.post(
                self.relay_url,
                headers={"X-KZabbix-Gate-Token": self.relay_token},
                json={"subject": subject, "body": report},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise RuntimeError(f"mail relay rejected message: {payload}")
            return
        if smtp_error is not None:
            raise RuntimeError(f"authenticated SMTP failed: {smtp_error}") from smtp_error
        raise RuntimeError("email settings are incomplete")


class BluditPublisher:
    def __init__(self, url: str, api_token: str, auth_token: str, gate_token: str):
        self.url = url
        self.api_token = api_token
        self.auth_token = auth_token
        self.gate_token = gate_token

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.api_token and self.auth_token and self.gate_token)

    def publish(self, title: str, report: str, incident_id: str) -> dict:
        if not self.enabled:
            raise RuntimeError("Bludit API settings are incomplete")
        response = requests.post(
            self.url,
            headers={"X-KZabbix-Gate-Token": self.gate_token, "Content-Type": "application/json"},
            json={
                "token": self.api_token,
                "authentication": self.auth_token,
                "title": title,
                "content": report,
                "type": "published",
                "category": "incidents",
                "tags": "zabbix,incident," + incident_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if str(payload.get("status")) not in {"0", "201", "200"} and not payload.get("data"):
            raise RuntimeError(f"Bludit API rejected post: {payload}")
        return payload
