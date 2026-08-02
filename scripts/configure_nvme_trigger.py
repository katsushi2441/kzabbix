#!/usr/bin/env python3
from __future__ import annotations

import json
import os

import requests

HOST = "xb-rtx3090-1"
DEVICE = "nvme0n1"
LEGACY_DESCRIPTION = f"Linux: {DEVICE}: Disk read/write request responses are too high"
DESCRIPTION = f"Linux: {DEVICE}: Disk latency is high under sustained utilization"
EXPRESSION = (
    f"(min(/{HOST}/vfs.dev.read.await[{DEVICE}],15m)>20 or "
    f"min(/{HOST}/vfs.dev.write.await[{DEVICE}],15m)>20) and "
    f"avg(/{HOST}/vfs.dev.util[{DEVICE}],5m)>70"
)


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
    hosts = api.call("host.get", {"output": ["hostid", "host"], "filter": {"host": [HOST]}})
    if not hosts:
        raise RuntimeError(f"Zabbix host not found: {HOST}")
    host_id = hosts[0]["hostid"]

    legacy = api.call(
        "trigger.get",
        {
            "output": ["triggerid", "description", "status", "flags"],
            "hostids": [host_id],
            "filter": {"description": [LEGACY_DESCRIPTION]},
        },
    )
    disabled = []
    for trigger in legacy:
        if trigger["status"] != "1":
            api.call("trigger.update", {"triggerid": trigger["triggerid"], "status": 1})
        disabled.append(trigger["triggerid"])

    custom = api.call(
        "trigger.get",
        {
            "output": ["triggerid", "description", "status"],
            "hostids": [host_id],
            "filter": {"description": [DESCRIPTION]},
        },
    )
    definition = {
        "description": DESCRIPTION,
        "expression": EXPRESSION,
        "priority": 2,
        "status": 0,
        "manual_close": 1,
        "comments": (
            "Host-specific replacement for the latency-only discovery trigger. "
            "Alert only when read/write latency is over 20 ms and disk utilization "
            "averages over 70%, avoiding low-throughput synchronous-write noise."
        ),
        "event_name": (
            f"Linux: {DEVICE}: Disk latency is high under sustained utilization "
            "(await > 20 ms and utilization > 70%)"
        ),
    }
    if custom:
        trigger_id = custom[0]["triggerid"]
        api.call("trigger.update", {"triggerid": trigger_id, **definition})
        action = "updated"
    else:
        created = api.call("trigger.create", definition)
        trigger_id = created["triggerids"][0]
        action = "created"

    verified = api.call(
        "trigger.get",
        {
            "output": ["triggerid", "description", "expression", "status", "value"],
            "triggerids": [trigger_id, *disabled],
            "expandExpression": True,
        },
    )
    print(
        json.dumps(
            {
                "host": HOST,
                "disabled_latency_only_triggerids": disabled,
                "composite_trigger": {"action": action, "triggerid": trigger_id},
                "verified": verified,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
