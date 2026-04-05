from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GoalCreate(BaseModel):
    title: str = Field(min_length=1)
    target_amount: float = Field(gt=0)
    current_amount: float = Field(default=0, ge=0)
    deadline: Optional[datetime] = None
    description: Optional[str] = None

class GoalResponse(BaseModel):
    id: str
    user_id: str
    title: str
    target_amount: float
    current_amount: float
    deadline: Optional[datetime] = None
    description: Optional[str] = None
    progress: float  # percentage
    created_at: datetime

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    current_amount: Optional[float] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    description: Optional[str] = None