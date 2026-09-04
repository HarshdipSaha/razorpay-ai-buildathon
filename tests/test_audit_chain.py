import json
from rebound.audit.log import AuditLog


def test_append_builds_valid_chain(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append(stage="event_received", payload={"a": 1}, sim_time=0.0)
    log.append(stage="classified", payload={"cause": "insufficient_funds"}, sim_time=1.0)
    assert log.verify() is True


def test_tampering_breaks_the_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.append(stage="event_received", payload={"a": 1}, sim_time=0.0)
    log.append(stage="classified", payload={"cause": "insufficient_funds"}, sim_time=1.0)

    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["payload"]["a"] = 999
    lines[0] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")

    log2 = AuditLog(path)
    assert log2.verify() is False


def test_first_break_reports_correct_seq(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.append("event_received", {"a": 1}, 0.0)
    log.append("classified", {"a": 2}, 1.0)
    log.append("action_executed", {"a": 3}, 2.0)

    lines = path.read_text().splitlines()
    rec = json.loads(lines[1])
    rec["payload"]["a"] = 999
    lines[1] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")

    log2 = AuditLog(path)
    assert log2.first_break() == 1
