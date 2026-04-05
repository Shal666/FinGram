import os
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import secrets

from backend.models.user import UserRegister, UserLogin, UserResponse, UserUpdate
from backend.utils.auth_utils import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    get_current_user
)
from backend.utils.db import get_database

router = APIRouter(prefix="/api/auth", tags=["auth"])

async def seed_admin():
    """Create admin user if doesn't exist"""
    db = get_database()
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@bayqadam.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    existing = await db.users.find_one({"email": admin_email})
    
    if existing is None:
        hashed = hash_password(admin_password)
        user_doc = {
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "surname": "User",
            "age": 30,
            "currency": "KZT",
            "role": "admin",
            "created_at": datetime.now(timezone.utc)
        }
        result = await db.users.insert_one(user_doc)
        print(f"✅ Admin user created: {admin_email}")
        
        # Write to test_credentials.md
        with open("/app/memory/test_credentials.md", "w") as f:
            f.write("# Test Credentials for BayQadam\n\n")
            f.write("## Admin Account\n")
            f.write(f"- Email: {admin_email}\n")
            f.write(f"- Password: {admin_password}\n")
            f.write(f"- Role: admin\n\n")
            f.write("## Auth Endpoints\n")
            f.write("- POST /api/auth/register\n")
            f.write("- POST /api/auth/login\n")
            f.write("- GET /api/auth/me\n")
            f.write("- PUT /api/auth/profile\n")
            f.write("- POST /api/auth/logout\n")
    
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        print(f"✅ Admin password updated: {admin_email}")

async def check_brute_force(identifier: str, db) -> bool:
    """Check if user is locked out due to failed login attempts"""
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    
    if not attempt:
        return False
    
    if attempt["count"] >= 5:
        lockout_until = attempt["last_attempt"] + timedelta(minutes=15)
        if datetime.now(timezone.utc) < lockout_until:
            return True
        else:
            # Lockout expired, reset
            await db.login_attempts.delete_one({"identifier": identifier})
            return False
    
    return False

async def record_failed_login(identifier: str, db):
    """Record a failed login attempt"""
    await db.login_attempts.update_one(
        {"identifier": identifier},
        {
            "$inc": {"count": 1},
            "$set": {"last_attempt": datetime.now(timezone.utc)}
        },
        upsert=True
    )

async def clear_failed_logins(identifier: str, db):
    """Clear failed login attempts"""
    await db.login_attempts.delete_one({"identifier": identifier})

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, request: Request, response: Response):
    """Register a new user"""
    db = get_database()
    
    # Normalize email
    email = user_data.email.lower()
    
    # Check if user exists
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user document
    user_doc = {
        "email": email,
        "password_hash": password_hash,
        "name": user_data.name,
        "surname": user_data.surname,
        "age": user_data.age,
        "currency": user_data.currency,
        "role": "user",
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create tokens
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=900,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=604800,
        path="/"
    )
    
    return UserResponse(
        id=user_id,
        email=email,
        name=user_data.name,
        surname=user_data.surname,
        age=user_data.age,
        currency=user_data.currency,
        role="user",
        created_at=user_doc["created_at"]
    )

@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin, request: Request, response: Response):
    """Login user"""
    db = get_database()
    
    # Normalize email
    email = credentials.email.lower()
    
    # Check brute force
    client_ip = request.client.host
    identifier = f"{client_ip}:{email}"
    
    if await check_brute_force(identifier, db):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Try again in 15 minutes.")
    
    # Find user
    user = await db.users.find_one({"email": email})
    if not user:
        await record_failed_login(identifier, db)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        await record_failed_login(identifier, db)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Clear failed attempts
    await clear_failed_logins(identifier, db)
    
    # Create tokens
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=900,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=604800,
        path="/"
    )
    
    return UserResponse(
        id=user_id,
        email=user["email"],
        name=user["name"],
        surname=user["surname"],
        age=user["age"],
        currency=user["currency"],
        role=user.get("role", "user"),
        created_at=user["created_at"]
    )

@router.get("/me", response_model=UserResponse)
async def get_me(request: Request):
    """Get current user"""
    db = get_database()
    user = await get_current_user(request, db)
    return UserResponse(**user)

@router.put("/profile", response_model=UserResponse)
async def update_profile(update_data: UserUpdate, request: Request):
    """Update user profile"""
    db = get_database()
    user = await get_current_user(request, db)
    
    # Build update dict
    update_fields = {}
    if update_data.name is not None:
        update_fields["name"] = update_data.name
    if update_data.surname is not None:
        update_fields["surname"] = update_data.surname
    if update_data.age is not None:
        update_fields["age"] = update_data.age
    if update_data.currency is not None:
        if update_data.currency not in ["KZT", "RUB", "USD"]:
            raise HTTPException(status_code=400, detail="Invalid currency")
        update_fields["currency"] = update_data.currency
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update user
    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": update_fields}
    )
    
    # Get updated user
    updated_user = await db.users.find_one({"_id": ObjectId(user["id"])}, {"_id": 0})
    updated_user["id"] = user["id"]
    
    return UserResponse(**updated_user)

@router.post("/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}