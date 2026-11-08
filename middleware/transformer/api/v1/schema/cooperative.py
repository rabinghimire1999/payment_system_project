from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date
from enum import Enum

# 1. Define Enums in ALL CAPS (The "Target" state)
class fspTypeEnum(str, Enum):
    SAVING = "SAVING"
    CURRENT = "CURRENT"
    SAVING_AND_CREDIT = "SAVING_AND_CREDIT"
    MULTIPURPOSE = "MULTIPURPOSE"
    AGRICULTURE = "AGRICULTURE"
    HOUSING = "HOUSING"
    TRADE = "TRADE"
    FISHERIES = "FISHERIES"
    TRANSPORT = "TRANSPORT"
    EDUCATION = "EDUCATION"
    OTHER = "OTHER"

class CurrencyEnum(str, Enum):
    NPR = "NPR"

class fspEnrollRequest(BaseModel):
    fsp_name: str = Field(..., min_length=3, 
        examples=["Eagles fsp Ltd"],
        description="The full legal name of the fsp")
    account_number: str = Field(..., pattern=r"^[A-Z0-9]+$", 
        examples=["REG12345ABC"],
        description="Uppercase alphanumeric registration ID")
    pan_number: str = Field(..., pattern=r"^[0-9]{9}$", 
        examples=["123456789"],
        description="Exactly 9 numeric digits")
    registration_authority: str = Field(..., examples=["Department of fsps"],
        description="The governing body where the coop is registered")
    registration_date: date = Field(..., description="Date of registration in YYYY-MM-DD format")
    fsp_type: fspTypeEnum = Field(
        ..., 
        description="Choose from: SAVING, CREDIT, MULTIPURPOSE, CURRENT"
    )
    fsp_code: str = Field(
        ..., 
        min_length=3, 
        pattern=r"^[A-Z0-9]+$",
        examples=["EAG01"],
        description="Unique short code for the fsp"
    )
    fsp_email: EmailStr
    # email: EmailStr
    password: str

    # --- Case Normalization Logic ---
    @field_validator('fsp_type', mode='before')
    @classmethod
    def __normalize_coop_type(cls, v: str) -> str:
        """Converts input like 'saving' to 'SAVING' before validation"""
        if isinstance(v, str):
            return v.upper()
        return v

class CreateAssetRequest(BaseModel):
    fsp_id: int
    asset_name: str = "Nepalese Rupee"
    currency: CurrencyEnum

    @field_validator('currency', mode='before')
    @classmethod
    def __normalize_currency(cls, v: str) -> str:
        """Converts input like 'npr' to 'NPR' before validation"""
        if isinstance(v, str):
            return v.upper()
        return v

class fspCreditRequest(BaseModel):
    fsp_id: int
    fsp_code: str = Field(..., min_length=3)
    fsp_email: EmailStr
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=5)