import json
from rebound.classify.llm import LLMClassifier
from rebound.models import PaymentFailure


class FakeAnthropicClient:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = 0

    class _Messages:
        def __init__(self, outer):
            self.outer = outer

        def create(self, **kwargs):
            self.outer.calls += 1
            class R:
                content = [type("Block", (), {"text": self.outer.response_text})()]
            return R()

    @property
    def messages(self):
        return self._Messages(self)


def test_confident_classification_is_used(tmp_path):
    fake = FakeAnthropicClient(json.dumps(
        {"cause": "authentication_failed", "confidence": 0.9, "rationale": "OTP mismatch mentioned"}
    ))
    clf = LLMClassifier(client=fake, cache_dir=tmp_path)
    pf = PaymentFailure(
        payment_id="p1", subscription_id="s1", amount=1000, method="card",
        error_reason="payment_failed", error_description="customer entered wrong OTP twice",
    )
    result = clf.classify(pf)
    assert result.cause.value == "authentication_failed"
    assert result.provenance == "llm"
    assert fake.calls == 1


def test_low_confidence_abstains(tmp_path):
    fake = FakeAnthropicClient(json.dumps(
        {"cause": "insufficient_funds", "confidence": 0.3, "rationale": "unclear"}
    ))
    clf = LLMClassifier(client=fake, cache_dir=tmp_path, confidence_threshold=0.75)
    pf = PaymentFailure(
        payment_id="p2", subscription_id="s2", amount=1000, method="upi",
        error_reason="payment_failed", error_description="vague failure",
    )
    result = clf.classify(pf)
    assert result.cause.value == "unknown"
    assert result.provenance == "abstain"


def test_second_call_hits_cache_not_the_client(tmp_path):
    fake = FakeAnthropicClient(json.dumps(
        {"cause": "bank_or_gateway_error", "confidence": 0.8, "rationale": "timeout mentioned"}
    ))
    clf = LLMClassifier(client=fake, cache_dir=tmp_path)
    pf = PaymentFailure(
        payment_id="p3", subscription_id="s3", amount=1000, method="card",
        error_reason="payment_failed", error_description="gateway took too long",
    )
    clf.classify(pf)
    clf.classify(pf)
    assert fake.calls == 1
