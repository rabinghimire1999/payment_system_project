from pydantic import BaseModel, EmailStr, Field

class PaymentTransferRequest(BaseModel):
    sender_id: str = Field(..., description="Internal DB ID of Sender")
    receiver_id: str = Field(..., description="Internal DB ID of Receiver")
    amount: float = Field(..., gt=0, description="Amount in NPR")
    description: str = Field("fsp Transfer", min_length=3)

#Payment Status Validation
class PaymentStatusRequest(BaseModel):
    fsp_id: str = Field(..., min_length=1)
    payment_id: str
    wallet: str

class MemberTransferRequest(BaseModel):
    sender_member_id: str = Field(
        ..., description="Internal DB ID of the sending member"
    )
    receiver_member_id: str = Field(
        ..., description="Internal DB ID of the receiving member"
    )
    amount: float = Field(..., gt=0, description="Amount in NPR (e.g., 50.00)")
    description: str = Field("Member to Member Transfer", min_length=3)
