from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from .notifier import BluditPublisher, EmailNotifier
from .ollama import OllamaClient
from .storage import IncidentStore
from .zabbix import ZabbixClient

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|authorization|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+"),
]


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    text = value
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def build_prompt(payload: dict[str, Any], evidence: dict[str, Any]) -> str:
    safe = redact(evidence)
    interesting = re.compile(
        r"(?i)(kzabbix|evidence|log|journal|kernel|smart|nvme|disk|vfs\.dev|pressure|iostat|proc\."
        r"|cpu|load|memory|swap|filesystem|vfs\.fs|agent\.ping|system\.uptime|net\."
        r"|icmpping|web\.|resolv\.conf|/proc/net/route|error|drop|timeout|oom)"
    )
    safe["items"] = [
        item
        for item in safe.get("items", [])
        if item.get("error") or interesting.search(f"{item.get('name', '')} {item.get('key_', '')}")
    ][:80]
    history = [
        row
        for row in safe.get("history", [])
        if interesting.search(f"{row.get('name', '')} {row.get('key', '')} {row.get('value', '')[:200]}")
    ]
    safe["history"] = history[-300:]
    compact = json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
    while len(compact) > 50_000 and len(safe["history"]) > 60:
        safe["history"] = safe["history"][len(safe["history"]) // 3 :]
        compact = json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
    if len(compact) > 50_000 and len(safe.get("evidence_snapshots", [])) > 1:
        safe["evidence_snapshots"] = safe["evidence_snapshots"][-1:]
        compact = json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
    if len(compact) > 50_000:
        compact = json.dumps(
            {"truncated": True, "evidence_prefix": compact[:46_000]},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return f"""あなたはKurage Zabbixの障害調査担当です。以下のZabbixイベントと実測データだけを根拠に、日本語Markdownレポートを作成してください。

必須ルール:
- 観測事実、推定、未確認事項を明確に分ける。
- 原因を断定できない場合は断定しない。
- 時刻、ホスト、障害時間、復旧状況、ログ行、メトリクスを具体的に示す。
- 障害時間はactual_duration_secondsがある場合だけ実測として記載する。トリガー評価期間を障害時間とみなさない。
- evidence_snapshots内のjournal、kernel、iostat、top_process_io、containersを優先して原因を切り分ける。
- system.loadavgのload_1m/load_5m/load_15mは、それぞれ1分・5分・15分平均として記載する。
- PCスリープ、OS再起動、LAN、DNS、ルーターWAN、ISP、監視サーバー障害を可能な範囲で切り分ける。
- 秘密情報らしき値は再掲しない。
- 最後に「原因候補と確度」「推奨対応」「追加で必要な証拠」を記載する。

章構成:
# 障害調査レポート
## 概要
## 影響範囲
## 時系列
## 観測事実
## ログ解析
## 原因候補と確度
## 推奨対応
## 追加で必要な証拠

Webhook payload:
{json.dumps(redact(payload), ensure_ascii=False)}

Zabbix evidence:
{compact}
"""


def is_problem_event(payload: dict[str, Any]) -> bool:
    return str(payload.get("event_status") or "").strip().upper() == "PROBLEM"


def build_problem_notification(payload: dict[str, Any]) -> tuple[str, str]:
    host = str(payload.get("host_name") or "unknown-host")
    event_name = str(payload.get("event_name") or "Zabbix incident")
    event_date = str(payload.get("event_date") or "")
    event_time = str(payload.get("event_time") or "")
    detected_at = " ".join(part for part in (event_date, event_time) if part) or "不明"
    subject = f"[障害発生] {host}: {event_name}"
    body = "\n".join(
        [
            "Zabbixが障害を検知しました。",
            "",
            f"ホスト: {host}",
            f"障害: {event_name}",
            f"重要度: {payload.get('event_severity') or '不明'}",
            f"検知日時: {detected_at}",
            f"イベントID: {payload.get('event_id') or '不明'}",
            f"トリガーID: {payload.get('trigger_id') or '不明'}",
            "",
            "AI調査レポートはKurage Zabbixブログへ保存されます。",
            "https://kurage.exbridge.jp/zabbix/",
        ]
    )
    return subject, body


class IncidentProcessor:
    def __init__(
        self,
        store: IncidentStore,
        zabbix: ZabbixClient,
        ollama: OllamaClient,
        email: EmailNotifier,
        bludit: BluditPublisher,
    ):
        self.store = store
        self.zabbix = zabbix
        self.ollama = ollama
        self.email = email
        self.bludit = bludit

    def process(self, incident_id: str, payload: dict[str, Any]) -> None:
        email_sent = 0
        notification_errors: list[str] = []
        try:
            if is_problem_event(payload):
                try:
                    subject, body = build_problem_notification(payload)
                    self.email.send(subject, body)
                    email_sent = 1
                    self.store.update(incident_id, email_sent=email_sent)
                except Exception as exc:  # noqa: BLE001 - notification failure must remain visible
                    notification_errors.append(f"email: {exc}")
            self.store.update(incident_id, status="collecting", error="")
            evidence = self.zabbix.collect_incident(
                str(payload.get("event_id") or ""), str(payload.get("host_id") or "")
            )
            self.store.update(
                incident_id,
                evidence_json=json.dumps(redact(evidence), ensure_ascii=False),
                status="analyzing",
            )
            report = self.ollama.analyze(build_prompt(payload, evidence))
            self.store.update(incident_id, report=report, status="notifying")
            host = str(payload.get("host_name") or "unknown-host")
            event_name = str(payload.get("event_name") or "Zabbix incident")
            title = f"[{host}] {event_name} ({incident_id})"
            errors = notification_errors
            blog_posted = 0
            try:
                self.bludit.publish(title, report, incident_id)
                blog_posted = 1
            except Exception as exc:  # noqa: BLE001 - preserve the report if one destination fails
                errors.append(f"blog: {exc}")
            status = "complete" if not errors else "partial"
            self.store.update(
                incident_id,
                status=status,
                email_sent=email_sent,
                blog_posted=blog_posted,
                error="; ".join(errors),
            )
        except Exception as exc:  # noqa: BLE001 - background jobs must persist failure details
            self.store.update(incident_id, status="failed", error=str(exc))


def incident_id_for(payload: dict[str, Any]) -> str:
    event_id = str(payload.get("event_id") or "unknown")
    status = re.sub(r"[^a-z0-9_-]+", "-", str(payload.get("event_status") or "problem").lower())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"zbx-{event_id}-{status}-{stamp}"
