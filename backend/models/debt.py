from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DebtCreate(BaseModel):
    type: str  # "credit" (bank loan with monthly payment) or "personal" (debt to person)
    title: str = Field(min_length=1)
    total_amount: float = Field(gt=0)
    remaining_amount: float = Field(gt=0)
    monthly_payment: Optional[float] = Field(None, ge=0)  # For credits
    creditor: Optional[str] = None  # Bank name or person name
    interest_rate: Optional[float] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    description: Optional[str] = None

class DebtResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    total_amount: float
    remaining_amount: float
    monthly_payment: Optional[float] = None
    creditor: Optional[str] = None
    interest_rate: Optional[float] = None
    deadline: Optional[datetime] = None
    description: Optional[str] = None
    progress: float  # percentage paid
    created_at: datetime

class DebtUpdate(BaseModel):
    title: Optional[str] = None
    remaining_amount: Optional[float] = Field(None, gt=0)
    monthly_payment: Optional[float] = Field(None, ge=0)
    creditor: Optional[str] = None
    interest_rate: Optional[float] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    description: Optional[str] = None