"""
Core module - Configuration and shared utilities
"""

from app.core.config import settings

from app.core.config import settings
from app.core.ai import GeminiClient

__all__ = ["settings", "GeminiClient"]
