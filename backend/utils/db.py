import os
from motor.motor_asyncio import AsyncIOMotorClient

_mongo_client = None
_db = None

def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        mongo_url = os.environ.get("MONGO_URL")
        if not mongo_url:
            raise ValueError("MONGO_URL environment variable is not set")
        _mongo_client = AsyncIOMotorClient(mongo_url)
    return _mongo_client

def get_database():
    global _db
    if _db is None:
        db_name = os.environ.get("DB_NAME", "bayqadam")
        client = get_mongo_client()
        _db = client[db_name]
    return _db

async def init_indexes():
    """Initialize database indexes"""
    db = get_database()
    
    # Users collection indexes
    await db.users.create_index("email", unique=True)
    
    # Login attempts index
    await db.login_attempts.create_index("identifier")
    
    # Password reset tokens TTL index
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    
    # Transactions indexes
    await db.transactions.create_index([("user_id", 1), ("date", -1)])
    
    # Goals indexes
    await db.goals.create_index("user_id")
    
    # Debts indexes
    await db.debts.create_index("user_id")
    
    print("✅ Database indexes initialized")