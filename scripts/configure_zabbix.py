#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

import requests


class API:
    def __init__(self) -> None:
        self.url = os.environ["ZABBIX_API_URL"]
        self.auth: str | None = None
        self.request_id = 0

    def call(self, method: str, params: dict, auth: bool = True):
        self.request_id += 1
        body = {"jsonrpc": "2.0", "method": method, "params": params, "id": self.request_id}
        if auth:
            body["auth"] = self.auth
        response = requests.post(self.url, json=body, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(f"{method}: {payload['error']['data']}")
        return payload["result"]

    def login(self) -> None:
        self.auth = self.call(
            "user.login",
            {
                "username": os.environ.get("ZABBIX_USERNAME", "Admin"),
                "password": os.environ["ZABBIX_PASSWORD"],
            },
            auth=False,
        )


def main() -> None:
    api = API()
    api.login()
    name = "Kurage Zabbix AI Investigation"
    params = [
        {"name": "url", "value": "http://127.0.0.1:18300/webhook/zabbix"},
        {"name": "token", "value": os.environ["KZABBIX_API_TOKEN"]},
        {"name": "event_id", "value": "{EVENT.ID}"},
        {"name": "event_name", "value": "{EVENT.NAME}"},
        {"name": "event_status", "value": "{EVENT.STATUS}"},
        {"name": "event_severity", "value": "{EVENT.SEVERITY}"},
        {"name": "host_id", "value": "{HOST.ID}"},
        {"name": "host_name", "value": "{HOST.HOST}"},
        {"name": "trigger_id", "value": "{TRIGGER.ID}"},
        {"name": "trigger_expression", "value": "{TRIGGER.EXPRESSION}"},
        {"name": "event_date", "value": "{EVENT.DATE}"},
        {"name": "event_time", "value": "{EVENT.TIME}"},
    ]
    message_templates = [
        {
            "eventsource": 0,
            "recovery": 0,
            "subject": "Problem: {EVENT.NAME}",
            "message": "Kurage Zabbix AI investigation for problem event {EVENT.ID}",
        },
        {
            "eventsource": 0,
            "recovery": 1,
            "subject": "Resolved: {EVENT.NAME}",
            "message": "Kurage Zabbix AI investigation for recovered event {EVENT.ID}",
        },
    ]
    script = Path("zabbix/webhook.js").read_text(encoding="utf-8")
    found = api.call("mediatype.get", {"output": "extend", "filter": {"name": [name]}})
    if found:
        media_id = found[0]["mediatypeid"]
        api.call(
            "mediatype.update",
            {
                "mediatypeid": media_id,
                "type": 4,
                "status": 0,
                "parameters": params,
                "script": script,
                "message_templates": message_templates,
            },
        )
        media_action = "updated"
    else:
        made = api.call(
            "mediatype.create",
            {
                "name": name,
                "type": 4,
                "status": 0,
                "parameters": params,
                "script": script,
                "timeout": "30s",
                "message_templates": message_templates,
            },
        )
        media_id = made["mediatypeids"][0]
        media_action = "created"

    users = api.call(
        "user.get",
        {
            "output": ["userid", "username"],
            "selectMedias": "extend",
            "filter": {"username": ["Admin"]},
        },
    )
    if not users:
        raise RuntimeError("Zabbix Admin user not found")
    user_id = users[0]["userid"]
    medias = users[0].get("medias") or []
    if not any(str(media.get("mediatypeid")) == str(media_id) for media in medias):
        normalized = []
        for media in medias:
            normalized.append(
                {
                    "mediatypeid": media["mediatypeid"],
                    "sendto": media.get("sendto") or [],
                    "active": int(media.get("active", 0)),
                    "severity": int(media.get("severity", 63)),
                    "period": media.get("period", "1-7,00:00-24:00"),
                }
            )
        normalized.append(
            {
                "mediatypeid": media_id,
                "sendto": ["kzabbix"],
                "active": 0,
                "severity": 63,
                "period": "1-7,00:00-24:00",
            }
        )
        api.call("user.update", {"userid": user_id, "medias": normalized})
    action_name = "Kurage Zabbix AI investigation (Warning+)"
    actions = api.call(
        "action.get", {"output": ["actionid", "name", "status"], "filter": {"name": [action_name]}}
    )
    action = {
        "name": action_name,
        "eventsource": 0,
        "status": 0,
        "esc_period": "1m",
        "filter": {"evaltype": 0, "conditions": [{"conditiontype": 4, "operator": 5, "value": "2"}]},
        "operations": [
            {
                "operationtype": 0,
                "opmessage": {"default_msg": 1, "mediatypeid": media_id},
                "opmessage_usr": [{"userid": user_id}],
            }
        ],
        "recovery_operations": [
            {
                "operationtype": 0,
                "opmessage": {"default_msg": 1, "mediatypeid": media_id},
                "opmessage_usr": [{"userid": user_id}],
            }
        ],
    }
    if actions:
        action["actionid"] = actions[0]["actionid"]
        api.call("action.update", action)
        action_result = {"action": "updated", "actionid": actions[0]["actionid"]}
    else:
        made = api.call("action.create", action)
        action_result = {"action": "created", "actionid": made["actionids"][0]}
    print(
        json.dumps({"media_type": media_action, "mediatypeid": media_id, **action_result}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
