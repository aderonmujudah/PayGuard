from typing import Any

from app.providers.base import AccountVerificationProvider

# Deterministic mock directory. Real provider (e.g. Squad name enquiry)
# would replace this class entirely without touching callers.
_KNOWN_ACCOUNTS: dict[str, dict[str, str]] = {
    "0123456789": {"account_name": "ACME SUPPLIES LIMITED", "bank_code": "058"},
    "9988776655": {"account_name": "BRIGHT LOGISTICS NIG LTD", "bank_code": "044"},
    "5544332211": {"account_name": "GLOBAL TECH SERVICES", "bank_code": "011"},
    "1112223334": {"account_name": "QUICK MART STORES", "bank_code": "057"},
}


class MockAccountVerificationProvider(AccountVerificationProvider):
    name = "mock_account_verification"

    def verify_account(self, account_number: str, bank_code: str) -> dict[str, Any]:
        record = _KNOWN_ACCOUNTS.get(account_number)
        if not record:
            return {
                "resolved": False,
                "account_name": None,
                "bank_code": bank_code,
                "raw": {"status": "not_found", "account_number": account_number},
            }
        return {
            "resolved": True,
            "account_name": record["account_name"],
            "bank_code": record["bank_code"],
            "raw": {"status": "success", **record, "account_number": account_number},
        }
