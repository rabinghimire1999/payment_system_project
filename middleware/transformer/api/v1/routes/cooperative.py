from fastapi import APIRouter, Depends
from transformer.api.v1.schema.fsp import (
    fspEnrollRequest,
    CreateAssetRequest,
    fspCreditRequest,
)
from transformer.api.v1.service.fsp_service import fspService
from backend.core.security import verify_admin_access

router = APIRouter()
fsp_service = fspService()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "middleware", "message": "Server is running"}


# fsp enrollment
@router.post("/fsp/enroll", dependencies=[Depends(verify_admin_access)])
async def enroll_fsp(payload: fspEnrollRequest):

    return await fsp_service.enroll_fsp(payload)


# Balance Inquiry
@router.get(
    "/fsp/balance_inquiry/{fsp_id}",
    dependencies=[Depends(verify_admin_access)],
)
async def balance_inquiry(fsp_id: str):

    return await fsp_service.balance_inquiry(fsp_id)


# Create asset  by fsp
# @router.post("/asset/create")
# async def create_asset(payload: CreateAssetRequest):

#     return await fsp_service.create_asset(payload)


# #Load balance by fsp
# @router.post("/fsp/{fsp_id}/credit")
# async def credit_fsp(payload: fspCreditRequest):

#     return await fsp_service.credit_fsp(payload)


@router.get("/fsp/lookup", dependencies=[Depends(verify_admin_access)])
async def lookup_fsp(name: str, account_number: str):
    return await fsp_service.get_by_details(name, account_number)


@router.get("/fsp/all", dependencies=[Depends(verify_admin_access)])
async def get_all_fsps():
    """
    Returns all fsps in the system.
    """
    return await fsp_service.get_all()


@router.get(
    "/fsp/{fsp_id}", dependencies=[Depends(verify_admin_access)]
)
async def get_fsp_details(fsp_id: str):
    """
    Returns full details for a specific fsp by its ID.
    """
    return await fsp_service.get_by_id(fsp_id)
