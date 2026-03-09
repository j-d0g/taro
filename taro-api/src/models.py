"""Pydantic request/response models for the Taro.ai API."""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # e.g. "diego_carvalho" for personalized context
    channel: str = "lookfantastic"
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    tool_calls: list[dict] = []
    products: list[dict] = []


class DistillRequest(BaseModel):
    thread_id: str
    user_id: str  # e.g. "diego_carvalho"


class DistillResponse(BaseModel):
    user_id: str
    context: str
    updated: bool


class PreferenceRequest(BaseModel):
    user_id: str
    product_id: str
    action: str  # "cart", "keep", "remove"
    reason: Optional[str] = None


AVAILABLE_MODELS = {
    "openai": {"default_model": "gpt-5.4", "models": ["gpt-5.4", "gpt-5.2", "gpt-4.1", "gpt-4.1-mini"]},
    "anthropic": {"default_model": "claude-sonnet-4-20250514", "models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]},
    "google": {"default_model": "gemini-2.0-flash", "models": ["gemini-2.0-flash", "gemini-2.5-pro-preview-06-05"]},
}
