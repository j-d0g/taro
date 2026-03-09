"""Config endpoints: GET /models, /prompts, /health."""

from fastapi import APIRouter

from graph import DEFAULT_MODEL, DEFAULT_PROVIDER
from models import AVAILABLE_MODELS
from prompts.system import list_prompts


router = APIRouter()


@router.get("/models")
async def models():
    """Return available model providers and their models."""
    return {
        "default_provider": DEFAULT_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "providers": AVAILABLE_MODELS,
    }


@router.get("/prompts")
async def prompts():
    """Return available prompt template IDs."""
    return {"prompts": list_prompts(), "default": "default"}


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "taro-ai"}
