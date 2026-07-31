from __future__ import annotations

import time
from typing import Any

import requests


class ZabbixClient:
    def __init__(self, url: str, username: str, password: str, timeout: int = 20):
        self.url = url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.auth: str | None = None
        self.session = requests.Session()
        self._request_id = 0

    def rpc(self, method: str, params: dict[str, Any], auth: bool = True) -> Any:
        self._request_id += 1
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params, "id": self._request_id}
        if auth:
            if not self.auth:
                self.login()
            body["auth"] = self.auth
        response = self.session.post(self.url, json=body, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(f"Zabbix API {method}: {payload['error'].get('data', payload['error'])}")
        return payload["result"]

    def login(self) -> None:
        self.auth = self.rpc("user.login", {"username": self.username, "password": self.password}, auth=False)

    def collect_incident(self, event_id: str, host_id: str = "") -> dict[str, Any]:
        event_rows = self.rpc(
            "event.get",
            {
                "output": "extend",
                "eventids": [event_id],
                "selectHosts": ["hostid", "host", "name"],
                "selectRelatedObject": "extend",
                "selectAcknowledges": "extend",
            },
        )
        event = event_rows[0] if event_rows else {"eventid": event_id}
        hosts = event.get("hosts") or []
        resolved_host_id = host_id or (hosts[0].get("hostid") if hosts else "")
        clock = int(event.get("clock") or time.time())
        time_from = clock - 900
        time_till = max(int(time.time()), clock + 60)
        if not resolved_host_id:
            return {"event": event, "hosts": hosts, "items": [], "history": []}

        items = self.rpc(
            "item.get",
            {
                "output": [
                    "itemid",
                    "name",
                    "key_",
                    "value_type",
                    "lastclock",
                    "lastvalue",
                    "state",
                    "error",
                ],
                "hostids": [resolved_host_id],
                "filter": {"status": 0},
            },
        )
        selected = sorted(items, key=lambda row: int(row.get("lastclock") or 0), reverse=True)[:160]
        histories: list[dict[str, Any]] = []
        by_type: dict[int, list[str]] = {}
        for item in selected:
            by_type.setdefault(int(item["value_type"]), []).append(item["itemid"])
        item_map = {item["itemid"]: item for item in selected}
        for value_type, item_ids in by_type.items():
            rows = self.rpc(
                "history.get",
                {
                    "output": "extend",
                    "history": value_type,
                    "itemids": item_ids,
                    "time_from": time_from,
                    "time_till": time_till,
                    "sortfield": "clock",
                    "sortorder": "DESC",
                    "limit": 600,
                },
            )
            for row in rows:
                item = item_map.get(row["itemid"], {})
                histories.append(
                    {
                        "clock": row.get("clock"),
                        "itemid": row.get("itemid"),
                        "name": item.get("name"),
                        "key": item.get("key_"),
                        "value": row.get("value"),
                        "source": row.get("source", ""),
                        "severity": row.get("severity", "0"),
                    }
                )
        problems = self.rpc(
            "problem.get",
            {
                "output": ["eventid", "name", "severity", "clock", "r_eventid"],
                "hostids": [resolved_host_id],
                "recent": True,
                "sortfield": ["eventid"],
                "sortorder": "DESC",
                "limit": 50,
            },
        )
        return {
            "event": event,
            "hosts": hosts,
            "host_id": resolved_host_id,
            "window": {"time_from": time_from, "time_till": time_till},
            "items": selected,
            "history": sorted(histories, key=lambda row: int(row.get("clock") or 0)),
            "problems": problems,
        }
