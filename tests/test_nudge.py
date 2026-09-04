from rebound.actions.nudge import draft_nudge
from rebound.models import Cause


class FakeAnthropicClient:
    class _Messages:
        def create(self, **kwargs):
            class R:
                content = [type("Block", (), {"text": "Your card has expired — please update it to keep your subscription active."})()]
            return R()
    @property
    def messages(self):
        return self._Messages()


def test_draft_nudge_returns_text_only_no_send():
    fake = FakeAnthropicClient()
    text = draft_nudge(fake, Cause.INSTRUMENT_EXPIRED_OR_BLOCKED)
    assert "expired" in text.lower()
    assert len(text) < 400


def test_draft_nudge_works_without_llm_client():
    text = draft_nudge(None, Cause.INSUFFICIENT_FUNDS)
    assert isinstance(text, str) and len(text) > 0
