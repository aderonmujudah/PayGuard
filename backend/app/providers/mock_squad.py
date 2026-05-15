import uuid
from datetime import datetime, timezone
from typing import Any

from app.providers.base import PaymentProvider


class MockSquadPaymentProvider(PaymentProvider):
    """Mock implementation of the Squad payment rail.

    The real Squad integration should implement the same PaymentProvider
    interface and be registered in app.providers.registry. No caller code
    needs to change when swapping this out.
    """

    name = "mock_squad"

    def _ref(self) -> str:
        return f"MOCK-SQD-{uuid.uuid4().hex[:12].upper()}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def verify_transaction(self, reference: str) -> dict[str, Any]:
        return {
            "success": True,
            "reference": reference,
            "transaction_status": "successful",
            "verified_at": self._now(),
            "provider": self.name,
        }

    def hold_payment(self, invoice_id: str, amount: float) -> dict[str, Any]:
        return {
            "success": True,
            "action": "hold",
            "invoice_id": invoice_id,
            "amount": amount,
            "reference": self._ref(),
            "status": "held",
            "timestamp": self._now(),
            "provider": self.name,
        }

    def release_payment(self, invoice_id: str, amount: float) -> dict[str, Any]:
        return {
            "success": True,
            "action": "release",
            "invoice_id": invoice_id,
            "amount": amount,
            "reference": self._ref(),
            "status": "disbursed",
            "timestamp": self._now(),
            "provider": self.name,
        }

    def block_payment(self, invoice_id: str) -> dict[str, Any]:
        return {
            "success": True,
            "action": "block",
            "invoice_id": invoice_id,
            "reference": self._ref(),
            "status": "blocked",
            "timestamp": self._now(),
            "provider": self.name,
        }
