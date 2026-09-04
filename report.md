# Rebound batch report

- Duplicates rejected: **5**
- Double charges: **0** (must be 0)
- Policy violations: **0** (must be 0)
- False escalations: **0**

## Per-cause outcomes (policy outcome, not money recovered)
| Cause | Allowed | Blocked | Escalated |
|---|---|---|---|
| bank_or_gateway_error | 12 | 0 | 0 |
| insufficient_funds | 21 | 0 | 0 |
| instrument_expired_or_blocked | 6 | 0 | 0 |
| mandate_not_active | 5 | 0 | 0 |
| unknown | 0 | 0 | 4 |
| authentication_failed | 9 | 0 | 0 |
| limit_exceeded | 3 | 0 | 0 |

## Classifier (held-out set, n=20)
- Overall accuracy: 1.0 · Abstain rate: 0.05

| Cause | Precision | Recall |
|---|---|---|
| authentication_failed | 1.0 | 1.0 |
| bank_or_gateway_error | 1.0 | 1.0 |
| instrument_expired_or_blocked | 1.0 | 1.0 |
| insufficient_funds | 1.0 | 1.0 |
| limit_exceeded | 1.0 | 1.0 |
| unknown | 1.0 | 1.0 |

### Confusion matrix (truth → predicted : count)
- authentication_failed → authentication_failed: 2
- bank_or_gateway_error → bank_or_gateway_error: 5
- instrument_expired_or_blocked → instrument_expired_or_blocked: 2
- insufficient_funds → insufficient_funds: 8
- limit_exceeded → limit_exceeded: 2
- unknown → unknown: 1

## Exceptions
- `scn_9` (unknown): attempt 1 exceeds max 0 for unknown
- `scn_34` (unknown): attempt 1 exceeds max 0 for unknown
- `scn_45` (unknown): attempt 1 exceeds max 0 for unknown
- `scn_48` (unknown): attempt 1 exceeds max 0 for unknown

## Classification citations (every non-unknown cause traced to its source field)
- `scn_0` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_1` → insufficient_funds: error_reason=insufficient_funds
- `scn_2` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_3` → insufficient_funds: error_reason=insufficient_funds
- `scn_4` → insufficient_funds: error_reason=insufficient_funds
- `scn_5` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_6` → instrument_expired_or_blocked: error_reason=card_expired
- `scn_7` → mandate_not_active: token_status=paused
- `scn_8` → instrument_expired_or_blocked: error_reason=card_expired
- `scn_10` → insufficient_funds: error_reason=insufficient_funds
- `scn_11` → mandate_not_active: token_status=paused
- `scn_12` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_13` → insufficient_funds: error_reason=insufficient_funds
- `scn_14` → authentication_failed: error_reason=authentication_failed
- `scn_15` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_16` → limit_exceeded: error_reason=transaction_limit_exceeded
- `scn_17` → insufficient_funds: error_reason=insufficient_funds
- `scn_18` → instrument_expired_or_blocked: error_reason=card_expired
- `scn_19` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_20` → authentication_failed: error_reason=authentication_failed
- `scn_21` → authentication_failed: error_reason=authentication_failed
- `scn_22` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_23` → mandate_not_active: token_status=paused
- `scn_24` → insufficient_funds: error_reason=insufficient_funds
- `scn_25` → insufficient_funds: error_reason=insufficient_funds
- `scn_26` → limit_exceeded: error_reason=transaction_limit_exceeded
- `scn_27` → insufficient_funds: error_reason=insufficient_funds
- `scn_28` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_29` → instrument_expired_or_blocked: error_reason=card_expired
- `scn_30` → insufficient_funds: error_reason=insufficient_funds
- `scn_31` → insufficient_funds: error_reason=insufficient_funds
- `scn_32` → authentication_failed: error_reason=authentication_failed
- `scn_33` → authentication_failed: error_reason=authentication_failed
- `scn_35` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_36` → insufficient_funds: error_reason=insufficient_funds
- `scn_37` → authentication_failed: error_reason=authentication_failed
- `scn_38` → authentication_failed: error_reason=authentication_failed
- `scn_39` → mandate_not_active: token_status=paused
- `scn_40` → instrument_expired_or_blocked: error_reason=card_expired
- `scn_41` → authentication_failed: error_reason=authentication_failed
- `scn_42` → insufficient_funds: error_reason=insufficient_funds
- `scn_43` → insufficient_funds: error_reason=insufficient_funds
- `scn_44` → insufficient_funds: error_reason=insufficient_funds
- `scn_46` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_47` → authentication_failed: error_reason=authentication_failed
- `scn_49` → instrument_expired_or_blocked: error_reason=card_expired
- `scn_50` → limit_exceeded: error_reason=transaction_limit_exceeded
- `scn_51` → insufficient_funds: error_reason=insufficient_funds
- `scn_52` → insufficient_funds: error_reason=insufficient_funds
- `scn_53` → insufficient_funds: error_reason=insufficient_funds
- `scn_54` → insufficient_funds: error_reason=insufficient_funds
- `scn_55` → insufficient_funds: error_reason=insufficient_funds
- `scn_56` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_57` → bank_or_gateway_error: error_reason=bank_technical_error
- `scn_58` → mandate_not_active: token_status=paused
- `scn_59` → insufficient_funds: error_reason=insufficient_funds