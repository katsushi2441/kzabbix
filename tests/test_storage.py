from kzabbix.storage import IncidentStore


def test_store_deduplicates_event(tmp_path):
    store = IncidentStore(str(tmp_path / "incidents.sqlite3"))
    assert store.enqueue("one", "1", {"event_id": "1"}) is True
    assert store.enqueue("one", "1", {"event_id": "1"}) is False
    store.update("one", status="complete", email_sent=1)
    row = store.get("one")
    assert row["status"] == "complete"
    assert row["email_sent"] == 1
