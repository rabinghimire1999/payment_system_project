from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date
from typing import Dict, Any, Optional


class MemberKYC(BaseModel):
    dob: date = Field(..., examples=["1990-01-01"])
    citizenship_number: str = Field(..., examples=["1234-5678"])
    issued_date: date = Field(..., examples=["2010-05-15"])
    issued_district: str = Field(..., examples=["Kathmandu"])


class MemberEnrollRequest(BaseModel):
    fsp_name: str = Field(..., examples=["Adele fsp Ltd"])
    name: str = Field(..., examples=["Pankaj Kumar"])
    email: EmailStr
    account_number: str = Field(
        ..., pattern=r"^[A-Z0-9]+$", examples=["MEM12345"]
    )  # NEW
    kyc_details: MemberKYC

    @field_validator("account_number", mode="before")
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper().strip()
        return v


class MemberActivateRequest(BaseModel):
    member_id: str = Field(
        ..., description="The internal Database ID returned during enrollment"
    )



