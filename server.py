from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from backend.utils.db import init_indexes
from backend.routes.auth import router as auth_router, seed_admin
from backend.routes.transactions import router as transactions_router
from backend.routes.goals import router as goals_router
from backend.routes.debts import router as debts_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting BayQadam Backend API...")
    
    # Initialize database indexes
    await init_indexes()
    
    # Seed admin user
    await seed_admin()
    
    print("✅ BayQadam Backend API ready!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down BayQadam Backend API...")

app = FastAPI(
    title="BayQadam Finance API",
    description="Financial literacy and personal finance management API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - разрешаем все нужные домены
allowed_origins = [
    "https://fin-gram.vercel.app",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

# Добавляем FRONTEND_URL из переменных окружения если есть
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "bayqadam-backend-api",
        "port": 8001
    }

# Register routers
app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(goals_router)
app.include_router(debts_router)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)