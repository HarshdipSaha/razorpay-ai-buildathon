from rebound.models import Cause

# error_reason (primary key) -> Cause, per documented values.
# Source: https://razorpay.com/docs/errors/payments/list/
#         https://razorpay.com/docs/payments/recurring-payments/emandate/errors/
REASON_TO_CAUSE: dict[str, Cause] = {
    "insufficient_funds": Cause.INSUFFICIENT_FUNDS,
    "card_expired": Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
    "debit_instrument_blocked": Cause.INSTRUMENT_EXPIRED_OR_BLOCKED,
    "authentication_failed": Cause.AUTHENTICATION_FAILED,
    "incorrect_otp": Cause.AUTHENTICATION_FAILED,
    "bank_technical_error": Cause.BANK_OR_GATEWAY_ERROR,
    "gateway_technical_error": Cause.BANK_OR_GATEWAY_ERROR,
    "payment_timed_out": Cause.BANK_OR_GATEWAY_ERROR,
    "mandate_not_active": Cause.MANDATE_NOT_ACTIVE,
    "payment_mandate_not_active": Cause.MANDATE_NOT_ACTIVE,
    "funds_blocked_by_mandate": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_declined": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_expired": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_failed": Cause.MANDATE_NOT_ACTIVE,
    "mandate_creation_timeout": Cause.MANDATE_NOT_ACTIVE,
    "transaction_limit_exceeded": Cause.LIMIT_EXCEEDED,
}

TOKEN_STATUS_TO_CAUSE: dict[str, Cause] = {
    "paused": Cause.MANDATE_NOT_ACTIVE,
    "cancelled": Cause.MANDATE_NOT_ACTIVE,
    "rejected": Cause.MANDATE_NOT_ACTIVE,
}

DOC_URLS: dict[Cause, str] = {
    Cause.INSUFFICIENT_FUNDS: "https://razorpay.com/docs/errors/payments/list/",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "https://razorpay.com/docs/errors/payments/list/",
    Cause.AUTHENTICATION_FAILED: "https://razorpay.com/docs/errors/payments/payment-methods-error-parameters/",
    Cause.BANK_OR_GATEWAY_ERROR: "https://razorpay.com/docs/errors/payments/list/",
    Cause.MANDATE_NOT_ACTIVE: "https://razorpay.com/docs/payments/recurring-payments/emandate/errors/",
    Cause.LIMIT_EXCEEDED: "https://razorpay.com/docs/errors/payments/list/",
    Cause.UNKNOWN: "https://razorpay.com/docs/api/payments/entity/",
}

TEST_MODE_REPRODUCIBLE: dict[Cause, str] = {
    Cause.INSUFFICIENT_FUNDS: "yes_card",
    Cause.INSTRUMENT_EXPIRED_OR_BLOCKED: "partial_card",
    Cause.AUTHENTICATION_FAILED: "yes_card",
    Cause.BANK_OR_GATEWAY_ERROR: "yes_card",
    Cause.MANDATE_NOT_ACTIVE: "documented_not_manufacturable",
    Cause.LIMIT_EXCEEDED: "synthetic_only",
    Cause.UNKNOWN: "yes_upi_and_dashboard",
}
