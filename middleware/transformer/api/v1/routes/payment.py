import logging
from fastapi import APIRouter, Depends, HTTPException
from transformer.api.v1.schema.payment import PaymentTransferRequest
from transformer.api.v1.service.transaction_service import TransactionService
from backend.core.security import get_current_fsp
from backend.core.security import verify_admin_access
from backend.core.security import get_actor_id

logger = logging.getLogger(__name__)


payment_service = TransactionService()

router = APIRouter()


# Payment transfer
@router.post("/payment/transfer")
async def transfer(
    payload: PaymentTransferRequest,
    actor_id: str = Depends(get_actor_id),
):
    """
    Initiates a transfer.
    - If caller is ADMIN: Skip ownership check (Admin can act for any sender).
    - If caller is a fsp: Ensure sender_id matches their own ID.
    """

    if actor_id != "ADMIN":
        if str(payload.sender_id) != actor_id:
            raise HTTPException(
                status_code=403,
                detail="Security Violation: You can only initiate transfers from your own account.",
            )
        logger.info(f"fsp {actor_id} initiating transfer.")
    else:
        logger.info(
            f"Admin-initiated transfer on behalf of Coop ID: {payload.sender_id}"
        )

    service = TransactionService()
    return await service.payment_transfer(payload)


# Payment Status
@router.get("/payment/status/{payment_id}", dependencies=[Depends(verify_admin_access)])
async def payment_status(payment_id: str):

    return await payment_service.payment_status(payment_id)


@router.get("/payment/history/{fsp_id}")
async def get_transaction_history(
    fsp_id: str,
    actor_id: str = Depends(get_actor_id),
):
    """
    Logic:
    - If Admin: Allow access to any fsp_id.
    - If fsp: Only allow access if the requested ID matches their own ID.
    """
    if actor_id != "ADMIN" and actor_id != str(fsp_id):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You can only view your own transaction history.",
        )

    service = TransactionService()
    return await service.get_history(fsp_id)
