"""Supabase integration router for AI Platform."""
import os
from typing import Optional, Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

router = APIRouter(prefix="/api/supabase", tags=["Supabase Integration"])

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

class QueryRequest(BaseModel):
    table: str
    query: Dict[str, Any] = {}
    limit: Optional[int] = 100

class QueryResponse(BaseModel):
    data: list
    count: int

@router.get("/tables")
async def list_tables():
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    try:
        tables = ["users", "suppliers", "customers", "materials", "products",
                  "warehouses", "stocks", "purchase_orders", "goods_receipts",
                  "production_orders", "sales_orders", "invoices", "ai_agents"]
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def query_table(request: QueryRequest):
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    try:
        response = supabase_client.table(request.table).select("*").execute()
        return QueryResponse(data=response.data, count=len(response.data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def supabase_health():
    if not supabase_client:
        return {"status": "not_configured", "supabase_url": SUPABASE_URL or "not set"}
    try:
        supabase_client.table("users").select("id").limit(1).execute()
        return {"status": "connected", "supabase_url": SUPABASE_URL}
    except Exception as e:
        return {"status": "error", "error": str(e)}