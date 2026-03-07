"""File-based prompt registry backed by markdown templates."""

from functools import lru_cache
from pathlib import Path

from loguru import logger

TEMPLATES_DIR = Path(__file__).parent / "templates"


@lru_cache(maxsize=32)
def load_prompt(prompt_id: str = "default") -> str:
    """Load a prompt template by ID from templates/{prompt_id}.md.

    Falls back to 'default' if the requested prompt_id is not found.
    """
    path = TEMPLATES_DIR / f"{prompt_id}.md"
    if not path.exists():
        logger.warning(f"Prompt '{prompt_id}' not found, falling back to 'default'")
        path = TEMPLATES_DIR / "default.md"
    return path.read_text()


def list_prompts() -> list[str]:
    """Return available prompt IDs (stem names of .md files in templates/)."""
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.md"))
