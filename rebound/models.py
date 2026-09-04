from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel


class Cause(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INSTRUMENT_EXPIRED_OR_BLOCKED = "instrument_expired_or_blocked"
    AUTHENTICATION_FAILED = "authentication_failed"
    BANK_OR_GATEWAY_ERROR = "bank_or_gateway_error"
    MANDATE_NOT_ACTIVE = "mandate_not_active"
    LIMIT_EXCEEDED = "limit_exceeded"
    UNKNOWN = "unknown"


class Action(str, Enum):
    CHARGE_INVOICE = "charge_invoice"
    PAYMENT_LINK = "payment_link"
    NUDGE = "nudge"
    ESCALATE = "escalate"
    NOOP_WAIT = "noop_wait"


Provenance = Literal["rule", "llm", "abstain"]
Decision = Literal["allow", "block", "escalate"]


class Event(BaseModel):
    event_id: str
    event_type: str
    received_at: datetime
    payload: dict


class PaymentFailure(BaseModel):
    payment_id: str
    subscription_id: str
    amount: int  # paise
    method: str
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None
    token_status: Optional[str] = None


class Classification(BaseModel):
    cause: Cause
    provenance: Provenance
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    mapped_from: Optional[str] = None


class SubscriptionState(BaseModel):
    subscription_id: str
    status: str
    attempt_no: int = 0
    consent: bool = True
    dispute_open: bool = False
    token_status: Optional[str] = None
    last_action_at: Optional[float] = None


class ActionRequest(BaseModel):
    subscription_id: str
    cause: Cause
    action: Action
    amount: int
    attempt_no: int
    sim_time: float


class Verdict(BaseModel):
    decision: Decision
    rule_id: str
    reason: str


class Outcome(BaseModel):
    action: Action
    executed: bool
    api_ref: Optional[str] = None
    error: Optional[str] = None


class ProcessResult(BaseModel):
    classification: Classification
    outcome: Outcome


class AuditRecord(BaseModel):
    seq: int
    ts: datetime
    sim_time: float
    event_id: Optional[str] = None
    subscription_id: Optional[str] = None
    stage: str
    payload: dict
    prev_hash: str
    hash: str


class Scenario(BaseModel):
    id: str
    tags: list[str]
    failure: PaymentFailure
    state: SubscriptionState
    truth_cause: Cause
    truth_action: Optional[Action] = None
