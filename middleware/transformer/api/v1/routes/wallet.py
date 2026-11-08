from fastapi import APIRouter, Depends
from transformer.api.v1.schema.wallet import WalletCreateRequest, WalletLoadRequest
from transformer.api.v1.service.wallet_service import WalletService
from backend.core.security import verify_admin_access

wallet_service = WalletService()

router = APIRouter()


# Wallet creation
@router.post("/wallet/create", dependencies=[Depends(verify_admin_access)])
async def wallet_create(payload: WalletCreateRequest):

    return await wallet_service.wallet_create(payload)


# Load Wallet
@router.post("/wallet/load", dependencies=[Depends(verify_admin_access)])
async def wallet_load(payload: WalletLoadRequest):

    return await wallet_service.wallet_load(payload)
