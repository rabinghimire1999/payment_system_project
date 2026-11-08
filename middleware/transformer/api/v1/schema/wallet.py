from pydantic import BaseModel, EmailStr, Field

#Wallet Creation Validation
class WalletCreateRequest(BaseModel):
    fsp_id: str = Field(
        ..., 
        examples=["12"], 
        description="The internal ID returned after enrollment"
    )
    account_number: str = Field(
        ..., 
        pattern=r"^[A-Z0-9]+$", 
        examples=["REG12345ABC"],
        description="Must match the registration number used in enrollment"
    )
    email: EmailStr = Field(..., examples=["user@example.com"])

#Wallet Load Valiation
class WalletLoadRequest(BaseModel):
    fsp_id: str = Field(
        ..., 
        examples=["12"], 
        description="The internal ID returned after enrollment"
    )
    account_number: str = Field(
        ..., 
        pattern=r"^[A-Z0-9]+$", 
        examples=["REG12345ABC"],
        description="Must match the registration number used in enrollment"
    )
    amount: float = Field(..., gt=0, description="Amount in NPR")
    description: str = Field(..., min_length=3)
    