from fastapi import APIRouter, HTTPException
from transformer.api.v1.schema.auth import LoginRequest 
from transformer.api.v1.service.auth_service import AuthTransformerService

router = APIRouter()
auth_service = AuthTransformerService()

@router.post("/auth/login")
async def login(payload: LoginRequest):
    try:
        return await auth_service.login(payload)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))