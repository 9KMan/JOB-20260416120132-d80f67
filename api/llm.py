"""LLM integration routers for AI Platform."""
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

router = APIRouter(prefix="/api/llm", tags=["LLM Integration"])

class ChatRequest(BaseModel):
    provider: str
    model: str
    message: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class ChatResponse(BaseModel):
    response: str
    model: str
    usage: dict

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    if request.provider == "openai":
        llm = ChatOpenAI(model=request.model, temperature=request.temperature, max_tokens=request.max_tokens)
        messages = []
        if request.system_prompt:
            messages.append(("system", request.system_prompt))
        messages.append(("human", request.message))
        response = llm.invoke(messages)
        return ChatResponse(
            response=response.content,
            model=request.model,
            usage={"input_tokens": 0, "output_tokens": 0}
        )
    elif request.provider == "anthropic":
        llm = ChatAnthropic(model=request.model, temperature=request.temperature, max_tokens=request.max_tokens)
        messages = []
        if request.system_prompt:
            messages.append(("system", request.system_prompt))
        messages.append(("human", request.message))
        response = llm.invoke(messages)
        return ChatResponse(
            response=response.content,
            model=request.model,
            usage={"input_tokens": 0, "output_tokens": 0}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Provider {request.provider} not supported")

@router.get("/models")
async def list_models():
    return {
        "openai": ["gpt-4-turbo-preview", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
    }