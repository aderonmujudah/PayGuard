from typing import Any

from app.providers.base import BusinessVerificationProvider

_KNOWN_BUSINESSES: dict[str, dict[str, str]] = {
    "RC123456": {"registered_name": "ACME SUPPLIES LIMITED", "status": "active"},
    "RC777888": {"registered_name": "BRIGHT LOGISTICS NIG LTD", "status": "active"},
    "RC555000": {"registered_name": "GLOBAL TECH SERVICES", "status": "active"},
}


class MockBusinessVerificationProvider(BusinessVerificationProvider):
    name = "mock_business_verification"

    def verify_business(
        self, rc_number: str | None, tin: str | None, legal_name: str
    ) -> dict[str, Any]:
        if not rc_number:
            return {
                "verified": False,
                "registered_name": None,
                "status": "missing_rc_number",
                "raw": {"tin": tin, "legal_name": legal_name},
            }
        record = _KNOWN_BUSINESSES.get(rc_number.upper())
        if not record:
            return {
                "verified": False,
                "registered_name": None,
                "status": "not_found",
                "raw": {"rc_number": rc_number, "tin": tin},
            }
        return {
            "verified": True,
            "registered_name": record["registered_name"],
            "status": record["status"],
            "raw": {"rc_number": rc_number, "tin": tin, **record},
        }
