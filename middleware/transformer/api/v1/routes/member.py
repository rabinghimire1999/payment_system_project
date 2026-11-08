from fastapi import APIRouter, Depends, HTTPException
from transformer.api.v1.schema.member import MemberEnrollRequest, MemberActivateRequest
from transformer.api.v1.schema.payment import MemberTransferRequest
from backend.core.security import get_actor_id  # Import the Guard
from transformer.api.v1.service.member_service import MemberTransformerService

router = APIRouter(tags=["Member Management"])
member_service = MemberTransformerService()


@router.post("/member/enroll")
async def enroll_member(payload: MemberEnrollRequest):
    """
    Step 1: Register a member's legal identity and link to a fsp.
    """
    return await member_service.enroll_member(payload)


@router.post("/member/activate")
async def activate_member_wallet(payload: MemberActivateRequest):
    """
    Step 2: Create the Rafiki Wallet Address using the parent coop's tenant.
    """
    return await member_service.activate_member(payload)


@router.post("/member/transfer")
async def member_transfer(
    payload: MemberTransferRequest, actor_id: str = Depends(get_actor_id)
):
    """
    Triggers a cross-fsp member transfer.
    Security:
    - If ADMIN: Can send from any member ID.
    - If MEMBER: Can ONLY send from their own member ID.
    """
    # --- OWNERSHIP CHECK ---
    # Note: Assuming the JWT 'sub' contains the Member ID for member logins
    if actor_id != "ADMIN" and actor_id != str(payload.sender_member_id):
        raise HTTPException(
            status_code=403,
            detail="Security Violation: You can only send money from your own account.",
        )

    return await member_service.transfer_funds(payload)

@router.get("/member/all")
async def get_all_members(actor_id: str = Depends(get_actor_id)):
    """
    Returns all members in the system.
    Security: Admin or Authorized fsp.
    """
    return await member_service.get_all()

@router.get("/member/{member_id}")
async def get_member_details(
    member_id: str, 
    actor_id: str = Depends(get_actor_id)
):
    """
    Returns full details for a specific member.
    Security: Admin can see anyone; fsps can only see their own members.
    """
    service = MemberTransformerService()
    result = await service.get_by_id(member_id)
    
    if actor_id != "ADMIN":
        if str(result["data"]["fsp_id"]) != actor_id:
            raise HTTPException(
                status_code=403, 
                detail="Access Denied: This member does not belong to your fsp."
            )

    return result


