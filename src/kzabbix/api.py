from __future__ import annotations

import json
from functools import lru_cache

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict

from .config import Settings
from .incident import IncidentProcessor, incident_id_for
from .notifier import BluditPublisher, EmailNotifier
from .ollama import OllamaClient
from .storage import IncidentStore
from .zabbix import ZabbixClient

app = FastAPI(title="Kurage Zabbix", version="0.1.0")


class WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_id: str
    event_name: str = "Zabbix incident"
    event_status: str = "PROBLEM"
    event_severity: str = ""
    host_id: str = ""
    host_name: str = ""
    trigger_id: str = ""
    trigger_expression: str = ""
    event_date: str = ""
    event_time: str = ""


@lru_cache
def settings() -> Settings:
    return Settings.from_env()


@lru_cache
def store() -> IncidentStore:
    return IncidentStore(settings().db_path)


def processor() -> IncidentProcessor:
    cfg = settings()
    return IncidentProcessor(
        store(),
        ZabbixClient(cfg.zabbix_api_url, cfg.zabbix_username, cfg.zabbix_password),
        OllamaClient(cfg.ollama_url, cfg.ollama_model),
        EmailNotifier(
            cfg.smtp_host,
            cfg.smtp_port,
            cfg.smtp_username,
            cfg.smtp_password,
            cfg.smtp_from,
            cfg.report_email_to,
            cfg.mail_relay_url,
            cfg.mail_relay_token,
        ),
        BluditPublisher(
            cfg.bludit_api_url, cfg.bludit_api_token, cfg.bludit_auth_token, cfg.bludit_gate_token
        ),
    )


def authorize(x_kzabbix_token: str = Header(default="")) -> None:
    if not x_kzabbix_token or x_kzabbix_token != settings().api_token:
        raise HTTPException(status_code=403, detail="invalid webhook token")


@app.get("/health")
def health() -> dict:
    cfg = settings()
    return {"ok": True, "service": "kzabbix", "model": cfg.ollama_model}


@app.post("/webhook/zabbix", dependencies=[Depends(authorize)], status_code=202)
def zabbix_webhook(payload: WebhookPayload, tasks: BackgroundTasks) -> dict:
    data = json.loads(payload.model_dump_json())
    incident_id = incident_id_for(data)
    created = store().enqueue(incident_id, payload.event_id, data)
    if created:
        tasks.add_task(processor().process, incident_id, data)
    return {"accepted": True, "created": created, "incident_id": incident_id}


@app.get("/v1/incidents", dependencies=[Depends(authorize)])
def incidents(limit: int = 50) -> dict:
    return {"items": store().list(limit)}


@app.get("/v1/incidents/{incident_id}", dependencies=[Depends(authorize)])
def incident(incident_id: str) -> dict:
    row = store().get(incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="incident not found")
    return row
