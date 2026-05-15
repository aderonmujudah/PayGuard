"""Single place to swap mock providers for real ones.

To plug in the real Squad API later, implement a SquadPaymentProvider that
subclasses PaymentProvider and return it from get_payment_provider() based
on settings (e.g. settings.ENV == "prod"). Nothing else needs to change.
"""

from app.providers.base import (
    AccountVerificationProvider,
    BusinessVerificationProvider,
    PaymentProvider,
)
from app.providers.mock_account import MockAccountVerificationProvider
from app.providers.mock_business import MockBusinessVerificationProvider
from app.providers.mock_squad import MockSquadPaymentProvider


def get_account_verification_provider() -> AccountVerificationProvider:
    return MockAccountVerificationProvider()


def get_business_verification_provider() -> BusinessVerificationProvider:
    return MockBusinessVerificationProvider()


def get_payment_provider() -> PaymentProvider:
    # When ready: if settings.ENV == "prod": return SquadPaymentProvider(...)
    return MockSquadPaymentProvider()
