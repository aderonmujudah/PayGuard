from abc import ABC, abstractmethod
from typing import Any


class AccountVerificationProvider(ABC):
    """Resolve and verify a bank account (name enquiry)."""

    name: str = "base"

    @abstractmethod
    def verify_account(
        self, account_number: str, bank_code: str
    ) -> dict[str, Any]:
        """Return normalized result: {resolved, account_name, bank_code, raw}."""


class BusinessVerificationProvider(ABC):
    """Verify a business registration (RC number / TIN)."""

    name: str = "base"

    @abstractmethod
    def verify_business(
        self, rc_number: str | None, tin: str | None, legal_name: str
    ) -> dict[str, Any]:
        """Return normalized result: {verified, registered_name, status, raw}."""


class PaymentProvider(ABC):
    """Payment rail abstraction. Swap MockSquad for real Squad later."""

    name: str = "base"

    @abstractmethod
    def verify_transaction(self, reference: str) -> dict[str, Any]: ...

    @abstractmethod
    def hold_payment(self, invoice_id: str, amount: float) -> dict[str, Any]: ...

    @abstractmethod
    def release_payment(self, invoice_id: str, amount: float) -> dict[str, Any]: ...

    @abstractmethod
    def block_payment(self, invoice_id: str) -> dict[str, Any]: ...
