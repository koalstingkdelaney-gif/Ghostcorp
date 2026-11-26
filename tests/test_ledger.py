import pytest

from app.ledger import SimulationLedger


def test_ledger_is_simulated_and_idempotent(tmp_path):
    ledger = SimulationLedger(str(tmp_path / "ledger.db"))
    args = ("evt-001", "payment-001", "storefront", "payment_settled", 1299, "USD", {})
    assert ledger.record(*args) == "recorded"
    assert ledger.record(*args) == "duplicate"
    status = ledger.summary()
    assert status["mode"] == "SIMULATED_ONLY"
    assert status["live_money_enabled"] is False
    assert status["event_count"] == 1


def test_ledger_rejects_unapproved_currency_and_invalid_amount(tmp_path):
    ledger = SimulationLedger(str(tmp_path / "ledger.db"))
    with pytest.raises(ValueError, match="currency"):
        ledger.record("evt-002", "payment-002", "storefront", "payment_pending", 100, "EUR", {})
    with pytest.raises(ValueError, match="positive integer"):
        ledger.record("evt-003", "payment-003", "storefront", "payment_pending", 0, "USD", {})
