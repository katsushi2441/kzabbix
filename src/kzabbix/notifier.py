from __future__ import annotations

import smtplib
from email.message import EmailMessage

import requests


class EmailNotifier:
    def __init__(self, host: str, port: int, username: str, password: str, sender: str, recipient: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipient = recipient

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.username and self.password and self.sender and self.recipient)

    def send(self, subject: str, report: str) -> None:
        if not self.enabled:
            raise RuntimeError("SMTP settings are incomplete")
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = self.recipient
        message.set_content(report)
        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(message)


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
