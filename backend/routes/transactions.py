from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

from backend.models.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from backend.utils.auth_utils import get_current_user
from backend.utils.db import get_database

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("", response_model=TransactionResponse)
async def create_transaction(transaction_data: TransactionCreate, request: Request):
    """Create a new transaction"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Validate type
    if transaction_data.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
    
    # Generate unique ID
    transaction_id = str(ObjectId())
    
    # Create transaction document
    transaction_doc = {
        "id": transaction_id,
        "user_id": user["id"],
        "type": transaction_data.type,
        "amount": transaction_data.amount,
        "category": transaction_data.category,
        "description": transaction_data.description,
        "date": transaction_data.date,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.transactions.insert_one(transaction_doc)
    
    return TransactionResponse(
        id=transaction_id,
        **transaction_doc
    )

@router.get("", response_model=List[TransactionResponse])
async def get_transactions(
    request: Request,
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
):
    """Get user transactions with filters"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Build query
    query = {"user_id": user["id"]}
    
    if type:
        query["type"] = type
    
    if category:
        query["category"] = category
    
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    # Fetch transactions
    transactions = await db.transactions.find(query, {"_id": 0}).sort("date", -1).limit(limit).to_list(limit)
    
    return [TransactionResponse(**t) for t in transactions]

@router.get("/stats")
async def get_transaction_stats(
    request: Request,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """Get transaction statistics"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Default to current year/month
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month
    
    # Build date range
    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    
    # Aggregate statistics
    pipeline = [
        {
            "$match": {
                "user_id": user["id"],
                "date": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        }
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(10)
    
    # Format results
    stats = {
        "year": year,
        "month": month,
        "income": 0,
        "expense": 0,
        "balance": 0,
        "transactions_count": 0
    }
    
    for r in results:
        if r["_id"] == "income":
            stats["income"] = r["total"]
            stats["transactions_count"] += r["count"]
        elif r["_id"] == "expense":
            stats["expense"] = r["total"]
            stats["transactions_count"] += r["count"]
    
    stats["balance"] = stats["income"] - stats["expense"]
    
    # Get category breakdown
    category_pipeline = [
        {
            "$match": {
                "user_id": user["id"],
                "type": "expense",
                "date": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"total": -1}
        }
    ]
    
    categories = await db.transactions.aggregate(category_pipeline).to_list(20)
    
    stats["categories"] = [
        {"category": c["_id"], "total": c["total"], "count": c["count"]}
        for c in categories
    ]
    
    return stats

@router.get("/yearly-stats")
async def get_yearly_stats(request: Request, year: Optional[int] = None):
    """Get yearly statistics (month by month)"""
    db = get_database()
    user = await get_current_user(request, db)
    
    year = year or datetime.now(timezone.utc).year
    
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    
    pipeline = [
        {
            "$match": {
                "user_id": user["id"],
                "date": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "month": {"$month": "$date"},
                    "type": "$type"
                },
                "total": {"$sum": "$amount"}
            }
        },
        {
            "$sort": {"_id.month": 1}
        }
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(100)
    
    # Format by month
    monthly_data = {}
    for i in range(1, 13):
        monthly_data[i] = {"month": i, "income": 0, "expense": 0, "balance": 0}
    
    for r in results:
        month = r["_id"]["month"]
        type_ = r["_id"]["type"]
        
        if type_ == "income":
            monthly_data[month]["income"] = r["total"]
        elif type_ == "expense":
            monthly_data[month]["expense"] = r["total"]
    
    for month_data in monthly_data.values():
        month_data["balance"] = month_data["income"] - month_data["expense"]
    
    return {
        "year": year,
        "months": list(monthly_data.values())
    }

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, update_data: TransactionUpdate, request: Request):
    """Update a transaction"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Check transaction exists and belongs to user
    transaction = await db.transactions.find_one({"id": transaction_id, "user_id": user["id"]})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Build update dict
    update_fields = {}
    if update_data.type is not None:
        if update_data.type not in ["income", "expense"]:
            raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
        update_fields["type"] = update_data.type
    
    if update_data.amount is not None:
        update_fields["amount"] = update_data.amount
    
    if update_data.category is not None:
        update_fields["category"] = update_data.category
    
    if update_data.description is not None:
        update_fields["description"] = update_data.description
    
    if update_data.date is not None:
        update_fields["date"] = update_data.date
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update transaction
    await db.transactions.update_one(
        {"id": transaction_id, "user_id": user["id"]},
        {"$set": update_fields}
    )
    
    # Get updated transaction
    updated = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    
    return TransactionResponse(**updated)

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str, request: Request):
    """Delete a transaction"""
    db = get_database()
    user = await get_current_user(request, db)
    
    result = await db.transactions.delete_one({"id": transaction_id, "user_id": user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted successfully"}