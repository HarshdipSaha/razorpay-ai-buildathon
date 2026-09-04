from rebound.models import Classification, PaymentFailure
from rebound.classify.taxonomy import REASON_TO_CAUSE, TOKEN_STATUS_TO_CAUSE


def classify_by_rules(pf: PaymentFailure) -> Classification | None:
    """Pure lookup against documented fields. Returns None if the fields are
    generic/null and the case must fall through to the LLM residue path."""
    if pf.error_reason and pf.error_reason in REASON_TO_CAUSE:
        return Classification(
            cause=REASON_TO_CAUSE[pf.error_reason],
            provenance="rule",
            mapped_from=f"error_reason={pf.error_reason}",
        )
    if pf.token_status and pf.token_status in TOKEN_STATUS_TO_CAUSE:
        return Classification(
            cause=TOKEN_STATUS_TO_CAUSE[pf.token_status],
            provenance="rule",
            mapped_from=f"token_status={pf.token_status}",
        )
    return None
