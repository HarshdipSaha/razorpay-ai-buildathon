from rebound.actions.executor import Executor
from rebound.models import Action, ActionRequest, Cause
from rebound.sim.fake_razorpay import SimulatedRazorpayClient


def test_charge_invoice_rejects_amount_mismatch():
    ex = Executor(client=SimulatedRazorpayClient())
    req = ActionRequest(subscription_id="s1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=999, attempt_no=1, sim_time=0.0)
    outcome = ex.execute(req, invoice_id="inv_1", invoice_amount=50000)
    assert outcome.executed is False
    assert "amount" in (outcome.error or "")


def test_payment_link_creates_with_correct_amount():
    fake = SimulatedRazorpayClient()
    ex = Executor(client=fake)
    req = ActionRequest(subscription_id="s1", cause=Cause.MANDATE_NOT_ACTIVE,
                         action=Action.PAYMENT_LINK, amount=50000, attempt_no=1, sim_time=0.0)
    outcome = ex.execute(req, invoice_id="inv_1", invoice_amount=50000)
    assert outcome.executed is True
    assert fake.calls[0]["args"]["amount"] == 50000


def test_charge_invoice_succeeds():
    fake = SimulatedRazorpayClient()
    ex = Executor(client=fake)
    req = ActionRequest(subscription_id="s1", cause=Cause.INSUFFICIENT_FUNDS,
                         action=Action.CHARGE_INVOICE, amount=50000, attempt_no=1, sim_time=0.0)
    outcome = ex.execute(req, invoice_id="inv_1", invoice_amount=50000)
    assert outcome.executed is True
    assert outcome.api_ref == "inv_1"
