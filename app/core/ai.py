"""
Gemini AI Client Wrapper
Handles all interactions with Google's Gemini Models.
Updated for google-genai
"""

from google import genai
from google.genai.errors import APIError
from app.core.config import settings
from typing import Optional, Any
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Wrapper for Google's Gemini AI.
    Features:
    - Singleton configuration
    - Safe API key handling
    - Error wrapping
    """
    
    challenge_id: Optional[str] = None
    challenge_index: int = 0
    _client: Optional[genai.Client] = None

    @classmethod
    def configure(cls):
        """Initialize the Gemini SDK with API key from settings."""
        if cls._client is not None:
            return
            
        if not settings.GEMINI_API_KEY or "your-gemini-api-key" in settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
            logger.warning("GEMINI_API_KEY is not set or is using default value. AI features may fail.")
            # Even if API Key is not set, we create a client so it can bubble errors cleanly.
            try:
                cls._client = genai.Client()
            except Exception as e:
                logger.error(f"Failed to auto-configure Gemini Client: {e}")
        else:
            try:
                cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Gemini AI successfully configured.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini Client: {e}")
                raise

    @classmethod
    def get_client(cls) -> Optional[genai.Client]:
        """Get the configured client instance."""
        cls.configure()
        return cls._client

    @staticmethod
    async def generate_content(prompt: str, model_name: str = "gemini-2.0-flash", timeout_seconds: int = 60) -> Optional[str]:
        """
        Generate content with fast failover.
        Optimized for speed: 2 models, 2 attempts each, minimal backoff.
        """
        import random
        from google.genai import types
        
        client = GeminiClient.get_client()
        if not client:
            return "Error: Gemini API Client not initialized."

        # Only try 2 models max — fast failover, not infinite retries
        models_to_try = [model_name, "gemini-1.5-flash"]
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for m in models_to_try:
            key = m if m.startswith("models/") else f"models/{m}"
            if key not in seen:
                seen.add(key)
                unique_models.append(key)
        models_to_try = unique_models

        for model_id in models_to_try:
            for attempt in range(2):  # Max 2 attempts per model = 4 total
                try:
                    logger.info(f"AI Generation ({model_id}) - Attempt {attempt+1}")
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model_id,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.7,
                                top_p=0.9,
                                max_output_tokens=8192,  # Large enough for 25 questions
                            )
                        ),
                        timeout=timeout_seconds
                    )
                    if response and response.text:
                        logger.info(f"AI Generation SUCCESS ({model_id})")
                        return response.text
                except asyncio.TimeoutError:
                    logger.warning(f"AI timeout ({timeout_seconds}s) on {model_id}, attempt {attempt+1}")
                    if attempt == 0:
                        await asyncio.sleep(2)  # Short wait then retry
                    else:
                        break  # Move to next model
                except Exception as e:
                    err_text = str(e).lower()
                    if "429" in err_text or "quota" in err_text:
                        sleep_time = 5 + random.uniform(1, 3)  # Fixed short backoff
                        logger.warning(f"AI Quota (429) on {model_id} - waiting {sleep_time:.1f}s")
                        await asyncio.sleep(sleep_time)
                    elif "404" in err_text or "not_found" in err_text:
                        logger.warning(f"AI Model {model_id} not found. Trying next...")
                        break  # Skip to next model immediately
                    else:
                        logger.error(f"AI Error ({model_id}): {str(e)}")
                        break  # Skip to next model
            
        return "AI Warning: All models unavailable. Using fallback mode."

# Default global accessor
ai_client = GeminiClient()
