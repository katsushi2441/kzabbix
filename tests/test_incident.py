from kzabbix.incident import build_prompt, incident_id_for, redact


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
