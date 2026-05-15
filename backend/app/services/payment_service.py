import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Invoice, Payment
from app.providers.registry import get_payment_provider
from app.services import audit_service

_ACTION_STATUS = {"release": "cleared", "hold": "hold", "block": "blocked"}


def execute_payment_action(
    db: Session,
    invoice_id: uuid.UUID,
    action: str,
    actor_user_id: uuid.UUID | None = None,
) -> Payment:
    if action not in _ACTION_STATUS:
        raise ValueError(f"Unsupported action: {action}")

    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")

    provider = get_payment_provider()
    amount = float(invoice.total_amount or 0)
    iid = str(invoice.id)

    if action == "release":
        resp = provider.release_payment(iid, amount)
    elif action == "hold":
        resp = provider.hold_payment(iid, amount)
    else:
        resp = provider.block_payment(iid)

    payment = Payment(
        invoice_id=invoice.id,
        initiated_by=actor_user_id,
        payment_action=action,
        payment_status="success" if resp.get("success") else "failed",
        amount=Decimal(str(amount)),
        currency_code=invoice.currency_code,
        provider_name=provider.name,
        squad_transaction_ref=resp.get("reference"),
        provider_response=resp,
    )
    db.add(payment)

    old_status = invoice.status
    invoice.status = _ACTION_STATUS[action]

    audit_service.record(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action=f"payment_{action}",
        actor_user_id=actor_user_id,
        old_values={"status": old_status},
        new_values={"status": invoice.status},
        metadata={"provider_reference": resp.get("reference")},
    )
    db.commit()
    db.refresh(payment)
    return payment
