import hashlib
import hmac
import json
from fastapi.testclient import TestClient
from rebound.ingest.webhook import create_app


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "testsecret")
    app = create_app(db_path=tmp_path / "events.db")
    client = TestClient(app)
    body = json.dumps({"event": "payment.failed", "payload": {}}).encode()
    sig = sign(body, "testsecret")
    resp = client.post("/webhook", content=body,
                        headers={"X-Razorpay-Signature": sig, "x-razorpay-event-id": "evt_1"})
    assert resp.status_code == 200


def test_invalid_signature_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "testsecret")
    app = create_app(db_path=tmp_path / "events.db")
    client = TestClient(app)
    body = json.dumps({"event": "payment.failed", "payload": {}}).encode()
    resp = client.post("/webhook", content=body,
                        headers={"X-Razorpay-Signature": "wrong", "x-razorpay-event-id": "evt_2"})
    assert resp.status_code == 400
