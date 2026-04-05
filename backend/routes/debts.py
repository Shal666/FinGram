from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from bson import ObjectId
from typing import List

from backend.models.debt import DebtCreate, DebtResponse, DebtUpdate
from backend.utils.auth_utils import get_current_user
from backend.utils.db import get_database

router = APIRouter(prefix="/api/debts", tags=["debts"])

def calculate_debt_progress(remaining: float, total: float) -> float:
    """Calculate debt payment progress percentage"""
    if total <= 0:
        return 0
    paid = total - remaining
    progress = (paid / total) * 100
    return min(max(progress, 0), 100)

@router.post("", response_model=DebtResponse)
async def create_debt(debt_data: DebtCreate, request: Request):
    """Create a new debt/credit"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Validate type
    if debt_data.type not in ["credit", "personal"]:
        raise HTTPException(status_code=400, detail="Type must be 'credit' or 'personal'")
    
    # Generate unique ID
    debt_id = str(ObjectId())
    
    # Create debt document
    debt_doc = {
        "id": debt_id,
        "user_id": user["id"],
        "type": debt_data.type,
        "title": debt_data.title,
        "total_amount": debt_data.total_amount,
        "remaining_amount": debt_data.remaining_amount,
        "monthly_payment": debt_data.monthly_payment,
        "creditor": debt_data.creditor,
        "interest_rate": debt_data.interest_rate,
        "deadline": debt_data.deadline,
        "description": debt_data.description,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.debts.insert_one(debt_doc)
    
    return DebtResponse(
        id=debt_id,
        user_id=user["id"],
        type=debt_data.type,
        title=debt_data.title,
        total_amount=debt_data.total_amount,
        remaining_amount=debt_data.remaining_amount,
        monthly_payment=debt_data.monthly_payment,
        creditor=debt_data.creditor,
        interest_rate=debt_data.interest_rate,
        deadline=debt_data.deadline,
        description=debt_data.description,
        progress=calculate_debt_progress(debt_data.remaining_amount, debt_data.total_amount),
        created_at=debt_doc["created_at"]
    )

@router.get("", response_model=List[DebtResponse])
async def get_debts(request: Request, type: str = None):
    """Get all user debts/credits"""
    db = get_database()
    user = await get_current_user(request, db)
    
    query = {"user_id": user["id"]}
    if type:
        if type not in ["credit", "personal"]:
            raise HTTPException(status_code=400, detail="Type must be 'credit' or 'personal'")
        query["type"] = type
    
    debts = await db.debts.find(query, {"_id": 0}).to_list(100)
    
    # Calculate progress for each debt
    for debt in debts:
        debt["progress"] = calculate_debt_progress(debt["remaining_amount"], debt["total_amount"])
    
    return [DebtResponse(**d) for d in debts]

@router.get("/{debt_id}", response_model=DebtResponse)
async def get_debt(debt_id: str, request: Request):
    """Get a specific debt"""
    db = get_database()
    user = await get_current_user(request, db)
    
    debt = await db.debts.find_one({"id": debt_id, "user_id": user["id"]}, {"_id": 0})
    
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    
    debt["progress"] = calculate_debt_progress(debt["remaining_amount"], debt["total_amount"])
    
    return DebtResponse(**debt)

@router.put("/{debt_id}", response_model=DebtResponse)
async def update_debt(debt_id: str, update_data: DebtUpdate, request: Request):
    """Update a debt"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Check debt exists
    debt = await db.debts.find_one({"id": debt_id, "user_id": user["id"]})
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    
    # Build update dict
    update_fields = {}
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    
    if update_data.remaining_amount is not None:
        update_fields["remaining_amount"] = update_data.remaining_amount
    
    if update_data.monthly_payment is not None:
        update_fields["monthly_payment"] = update_data.monthly_payment
    
    if update_data.creditor is not None:
        update_fields["creditor"] = update_data.creditor
    
    if update_data.interest_rate is not None:
        update_fields["interest_rate"] = update_data.interest_rate
    
    if update_data.deadline is not None:
        update_fields["deadline"] = update_data.deadline
    
    if update_data.description is not None:
        update_fields["description"] = update_data.description
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update debt
    await db.debts.update_one(
        {"id": debt_id, "user_id": user["id"]},
        {"$set": update_fields}
    )
    
    # Get updated debt
    updated = await db.debts.find_one({"id": debt_id}, {"_id": 0})
    updated["progress"] = calculate_debt_progress(updated["remaining_amount"], updated["total_amount"])
    
    return DebtResponse(**updated)

@router.delete("/{debt_id}")
async def delete_debt(debt_id: str, request: Request):
    """Delete a debt"""
    db = get_database()
    user = await get_current_user(request, db)
    
    result = await db.debts.delete_one({"id": debt_id, "user_id": user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Debt not found")
    
    return {"message": "Debt deleted successfully"}

@router.get("/stats/summary")
async def get_debt_summary(request: Request):
    """Get debt summary statistics"""
    db = get_database()
    user = await get_current_user(request, db)
    
    debts = await db.debts.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    total_debt = sum(d["remaining_amount"] for d in debts)
    total_monthly_payments = sum(d.get("monthly_payment", 0) or 0 for d in debts if d["type"] == "credit")
    
    credits = [d for d in debts if d["type"] == "credit"]
    personal_debts = [d for d in debts if d["type"] == "personal"]
    
    # Calculate progress for each debt
    for debt in credits + personal_debts:
        debt["progress"] = calculate_debt_progress(debt["remaining_amount"], debt["total_amount"])
    
    return {
        "total_debt": total_debt,
        "total_monthly_payments": total_monthly_payments,
        "credits_count": len(credits),
        "personal_debts_count": len(personal_debts),
        "credits": credits,
        "personal_debts": personal_debts
    }