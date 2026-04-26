"""FastAPI application for AI Platform."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from api.llm import router as llm_router
from api.agents import router as agents_router
from api.supabase_integration import router as supabase_router
from api.sms import router as sms_router

Base = declarative_base()

class Settings(BaseSettings):
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql+asyncpg://erp_user:erp_password@localhost:5432/erp_database")
    CORS_ORIGINS: list[str] = ["*"]
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    TWILIO_ACCOUNT_SID: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.environ.get("TWILIO_PHONE_NUMBER", "")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(
    title="Boston AI Life Sciences - AI Platform API",
    description="Senior Python/FastAPI Engineer position - AI Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llm_router)
app.include_router(agents_router)
app.include_router(supabase_router)
app.include_router(sms_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Platform API", "version": "1.0.0"}

@app.get("/")
async def root():
    return {
        "message": "Boston AI Life Sciences - AI Platform API",
        "docs": "/docs",
        "health": "/health"
    }