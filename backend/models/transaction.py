from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TransactionCreate(BaseModel):
    type: str  # "income" or "expense"
    amount: float = Field(gt=0)
    category: str
    description: Optional[str] = None
    date: datetime

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    category: str
    description: Optional[str] = None
    date: datetime
    created_at: datetime

class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None