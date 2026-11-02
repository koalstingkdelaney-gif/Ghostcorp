"""Spend governor: hard cap on paid spend. Default cap is $0 before revenue.

Any attempted charge above the remaining cap is refused loudly — the cap is
never raised silently (brief section 1).
"""


class SpendCapExceeded(Exception):
    pass


class SpendGovernor:
    def __init__(self, cap_usd: float):
        self.cap_usd = float(cap_usd)
        self.spent_usd = 0.0
        self.ledger = []

    def check(self, amount_usd: float, purpose: str) -> None:
        amount = float(amount_usd)
        if amount < 0:
            raise ValueError("spend amount cannot be negative")
        if self.spent_usd + amount > self.cap_usd:
            raise SpendCapExceeded(
                f"spend of ${amount:.2f} for '{purpose}' would exceed cap "
                f"${self.cap_usd:.2f} (already spent ${self.spent_usd:.2f})"
            )

    def record(self, amount_usd: float, purpose: str) -> None:
        self.check(amount_usd, purpose)
        self.spent_usd += float(amount_usd)
        self.ledger.append({"amount_usd": float(amount_usd), "purpose": purpose})
