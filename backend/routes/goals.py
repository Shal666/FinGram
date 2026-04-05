from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from bson import ObjectId
from typing import List

from backend.models.goal import GoalCreate, GoalResponse, GoalUpdate
from backend.utils.auth_utils import get_current_user
from backend.utils.db import get_database

router = APIRouter(prefix="/api/goals", tags=["goals"])

def calculate_progress(current: float, target: float) -> float:
    """Calculate goal progress percentage"""
    if target <= 0:
        return 0
    progress = (current / target) * 100
    return min(progress, 100)

@router.post("", response_model=GoalResponse)
async def create_goal(goal_data: GoalCreate, request: Request):
    """Create a new financial goal"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Generate unique ID
    goal_id = str(ObjectId())
    
    # Create goal document
    goal_doc = {
        "id": goal_id,
        "user_id": user["id"],
        "title": goal_data.title,
        "target_amount": goal_data.target_amount,
        "current_amount": goal_data.current_amount,
        "deadline": goal_data.deadline,
        "description": goal_data.description,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.goals.insert_one(goal_doc)
    
    return GoalResponse(
        id=goal_id,
        user_id=user["id"],
        title=goal_data.title,
        target_amount=goal_data.target_amount,
        current_amount=goal_data.current_amount,
        deadline=goal_data.deadline,
        description=goal_data.description,
        progress=calculate_progress(goal_data.current_amount, goal_data.target_amount),
        created_at=goal_doc["created_at"]
    )

@router.get("", response_model=List[GoalResponse])
async def get_goals(request: Request):
    """Get all user goals"""
    db = get_database()
    user = await get_current_user(request, db)
    
    goals = await db.goals.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Calculate progress for each goal
    for goal in goals:
        goal["progress"] = calculate_progress(goal["current_amount"], goal["target_amount"])
    
    return [GoalResponse(**g) for g in goals]

@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str, request: Request):
    """Get a specific goal"""
    db = get_database()
    user = await get_current_user(request, db)
    
    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal["progress"] = calculate_progress(goal["current_amount"], goal["target_amount"])
    
    return GoalResponse(**goal)

@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: str, update_data: GoalUpdate, request: Request):
    """Update a goal"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Check goal exists
    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Build update dict
    update_fields = {}
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    
    if update_data.target_amount is not None:
        update_fields["target_amount"] = update_data.target_amount
    
    if update_data.current_amount is not None:
        update_fields["current_amount"] = update_data.current_amount
    
    if update_data.deadline is not None:
        update_fields["deadline"] = update_data.deadline
    
    if update_data.description is not None:
        update_fields["description"] = update_data.description
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update goal
    await db.goals.update_one(
        {"id": goal_id, "user_id": user["id"]},
        {"$set": update_fields}
    )
    
    # Get updated goal
    updated = await db.goals.find_one({"id": goal_id}, {"_id": 0})
    updated["progress"] = calculate_progress(updated["current_amount"], updated["target_amount"])
    
    return GoalResponse(**updated)

@router.delete("/{goal_id}")
async def delete_goal(goal_id: str, request: Request):
    """Delete a goal"""
    db = get_database()
    user = await get_current_user(request, db)
    
    result = await db.goals.delete_one({"id": goal_id, "user_id": user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return {"message": "Goal deleted successfully"}