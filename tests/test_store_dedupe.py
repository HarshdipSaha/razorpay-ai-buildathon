from rebound.ingest.store import EventStore


def test_first_insert_is_new(tmp_path):
    store = EventStore(tmp_path / "events.db")
    assert store.insert_if_new("evt_1", "payment.failed", {"x": 1}) is True


def test_duplicate_insert_is_rejected(tmp_path):
    store = EventStore(tmp_path / "events.db")
    store.insert_if_new("evt_1", "payment.failed", {"x": 1})
    assert store.insert_if_new("evt_1", "payment.failed", {"x": 1}) is False
