from kzabbix.incident import (
    IncidentProcessor,
    build_problem_notification,
    build_prompt,
    incident_id_for,
    is_problem_event,
    redact,
)
from kzabbix.storage import IncidentStore


class FakeZabbix:
    def collect_incident(self, event_id, host_id):
        return {"event": {"eventid": event_id}, "host_id": host_id}


class FakeOllama:
    def analyze(self, prompt):
        return "# 障害調査レポート\n\n調査結果"


class FakeEmail:
    def __init__(self):
        self.messages = []

    def send(self, subject, body):
        self.messages.append((subject, body))


class FakeBludit:
    def publish(self, title, report, incident_id):
        return {"title": title, "incident_id": incident_id}


def test_redact_secrets():
    text = redact("token=abc123 password:secret")
    assert "abc123" not in text
    assert "secret" not in text
    assert "[REDACTED]" in text


def test_prompt_requires_evidence_boundaries():
    prompt = build_prompt({"event_id": "10"}, {"event": {"name": "DNS failed"}})
    assert "観測事実" in prompt
    assert "推定" in prompt
    assert "gemma" not in prompt.lower()


def test_prompt_compacts_unrelated_history():
    evidence = {
        "items": [],
        "history": [{"name": "FS metric", "key": "vfs.fs.size", "value": "x" * 1000}] * 500,
    }
    prompt = build_prompt({"event_id": "10"}, evidence)
    assert len(prompt) < 50_000


def test_incident_id_is_deterministic_for_event_and_status():
    value = incident_id_for({"event_id": "42", "event_status": "PROBLEM"})
    assert value.startswith("zbx-42-problem-")


def test_only_problem_events_are_email_notifications():
    assert is_problem_event({"event_status": "PROBLEM"})
    assert not is_problem_event({"event_status": "RESOLVED"})


def test_problem_notification_is_short_and_contains_event_facts():
    subject, body = build_problem_notification(
        {
            "event_id": "5856",
            "event_name": "Disk response is too high",
            "event_status": "PROBLEM",
            "event_severity": "Warning",
            "host_name": "xb-rtx3090-1",
            "trigger_id": "123",
            "event_date": "2026.08.02",
            "event_time": "12:32:22",
        }
    )
    assert subject == "[障害発生] xb-rtx3090-1: Disk response is too high"
    assert "2026.08.02 12:32:22" in body
    assert "イベントID: 5856" in body
    assert "# 障害調査レポート" not in body


def test_processor_emails_problem_only_and_keeps_reports_in_blog(tmp_path):
    store = IncidentStore(str(tmp_path / "incidents.sqlite3"))
    email = FakeEmail()
    bludit = FakeBludit()
    processor = IncidentProcessor(store, FakeZabbix(), FakeOllama(), email, bludit)

    problem = {"event_id": "1", "event_status": "PROBLEM", "host_name": "host-1"}
    store.enqueue("problem", "1", problem)
    processor.process("problem", problem)

    resolved = {"event_id": "1", "event_status": "RESOLVED", "host_name": "host-1"}
    store.enqueue("resolved", "1", resolved)
    processor.process("resolved", resolved)

    assert len(email.messages) == 1
    assert email.messages[0][0].startswith("[障害発生]")
    assert store.get("problem")["blog_posted"] == 1
    assert store.get("resolved")["blog_posted"] == 1
    assert store.get("resolved")["email_sent"] == 0
