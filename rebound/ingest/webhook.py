from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, Request, Response
from rebound.ingest.store import EventStore


def _verify(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def create_app(db_path: Path, ctx: Optional[Any] = None) -> FastAPI:
    app = FastAPI()
    store = EventStore(db_path)

    @app.post("/webhook")
    async def webhook(request: Request):
        body = await request.body()
        signature = request.headers.get("x-razorpay-signature", "")
        secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        if not secret or not _verify(body, signature, secret):
            return Response(status_code=400, content="invalid signature")

        event_id = request.headers.get("x-razorpay-event-id", "")
        payload = json.loads(body)
        is_new = store.insert_if_new(event_id, payload.get("event", "unknown"), payload)

        if is_new and ctx is not None:
            _dispatch(ctx, event_id, payload)

        return Response(status_code=200, content="ok" if is_new else "duplicate")

    return app


def _dispatch(ctx: Any, event_id: str, payload: dict) -> None:
    from rebound.ingest.adapter import event_to_pipeline_inputs
    from rebound.pipeline import Pipeline

    parsed = event_to_pipeline_inputs(payload, client=getattr(ctx, "executor_client", None))
    if parsed is None:
        return
    failure, state, invoice_id = parsed
    Pipeline(ctx).process_failure(event_id=event_id, failure=failure, state=state, invoice_id=invoice_id)
