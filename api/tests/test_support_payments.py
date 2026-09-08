from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import SupportPayment


async def _resolve_user(client: AsyncClient, telegram_user_id: int) -> None:
    response = await client.post(
        "/users/resolve",
        json={
            "provider": "telegram",
            "external_id": str(telegram_user_id),
            "default_timezone": "Europe/Moscow",
            "default_language": "en",
        },
    )
    assert response.status_code in {200, 201}


@pytest.mark.asyncio
async def test_support_invoice_accepts_bot_amount_and_is_bound_to_user(client: AsyncClient) -> None:
    await _resolve_user(client, 101)
    invalid = await client.post(
        "/support-payments/invoices",
        json={"provider": "telegram", "external_id": "101", "amount": 0},
    )
    assert invalid.status_code == 422

    invoice = await client.post(
        "/support-payments/invoices",
        json={"provider": "telegram", "external_id": "101", "amount": 10_001},
    )
    assert invoice.status_code == 201
    payload = invoice.json()["payload"]
    assert payload.startswith("support:")

    await _resolve_user(client, 202)
    substituted = await client.post(
        "/support-payments/check",
        json={
            "provider": "telegram",
            "external_id": "202",
            "payload": payload,
            "amount": 10_001,
            "currency": "XTR",
        },
    )
    assert substituted.status_code == 200
    assert substituted.json() == {"valid": False}


@pytest.mark.asyncio
async def test_precheckout_success_and_duplicate_payment_are_idempotent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _resolve_user(client, 303)
    invoice = await client.post(
        "/support-payments/invoices",
        json={"provider": "telegram", "external_id": "303", "amount": 10},
    )
    payload = invoice.json()["payload"]
    request = {
        "provider": "telegram",
        "external_id": "303",
        "payload": payload,
        "amount": 10,
        "currency": "XTR",
    }
    checked = await client.post("/support-payments/check", json=request)
    assert checked.json() == {"valid": True}

    completed = await client.post(
        "/support-payments/complete",
        json={**request, "telegram_payment_charge_id": "charge-303"},
    )
    assert completed.status_code == 200
    assert completed.json() == {"newly_completed": True}

    duplicate = await client.post(
        "/support-payments/complete",
        json={**request, "telegram_payment_charge_id": "charge-303"},
    )
    assert duplicate.status_code == 200
    assert duplicate.json() == {"newly_completed": False}

    payment = await db_session.scalar(
        select(SupportPayment).where(SupportPayment.invoice_payload == payload)
    )
    assert payment is not None
    assert payment.status == "succeeded"
    assert payment.telegram_user_id == 303
    assert payment.amount == 10
    assert payment.telegram_payment_charge_id == "charge-303"
    assert payment.paid_at is not None


@pytest.mark.asyncio
async def test_expired_support_invoice_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _resolve_user(client, 404)
    invoice = await client.post(
        "/support-payments/invoices",
        json={"provider": "telegram", "external_id": "404", "amount": 10},
    )
    payload = invoice.json()["payload"]
    payment = await db_session.scalar(
        select(SupportPayment).where(SupportPayment.invoice_payload == payload)
    )
    assert payment is not None
    payment.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()

    request = {
        "provider": "telegram",
        "external_id": "404",
        "payload": payload,
        "amount": 10,
        "currency": "XTR",
    }
    rejected = await client.post("/support-payments/check", json=request)
    assert rejected.status_code == 200
    assert rejected.json() == {"valid": False}
    await db_session.refresh(payment)
    assert payment.status == "expired"
