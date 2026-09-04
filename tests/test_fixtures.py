import json
from rebound.ingest.fixtures import load_fixture, iter_fixtures


def test_load_single_fixture(tmp_path):
    f = tmp_path / "sample.json"
    f.write_text(json.dumps({"event_id": "evt_x", "event": "payment.failed", "payload": {"a": 1}}))
    envelope = load_fixture(f)
    assert envelope["event_id"] == "evt_x"


def test_iter_fixtures_yields_all_json_files(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"event_id": "e1", "event": "x", "payload": {}}))
    (tmp_path / "b.json").write_text(json.dumps({"event_id": "e2", "event": "x", "payload": {}}))
    ids = sorted(e["event_id"] for e in iter_fixtures(tmp_path))
    assert ids == ["e1", "e2"]
