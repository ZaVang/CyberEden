import logging
import os
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from src.schemas.eden import PrayerRequest, RevelationResponse, ActionPlan
from src.infra.llm_bridge import LLMBridge

logger = logging.getLogger("oracle")
logging.basicConfig(level=logging.INFO)

bridge: LLMBridge = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bridge
    bridge = LLMBridge.from_env()
    yield

app = FastAPI(title="Oracle Gateway", lifespan=lifespan)

@app.post("/ask_god", response_model=RevelationResponse)
async def ask_god(prayer: PrayerRequest) -> RevelationResponse:
    try:
        logger.info("Oracle received prayer, invoking LLMBridge...")
        
        response = await bridge.chat(
            messages=[{"role": "user", "content": prayer.prompt}],
            response_model=ActionPlan
        )
        
        if response.parsed:
            return RevelationResponse(revelation=response.parsed)
        else:
            raise HTTPException(status_code=500, detail="LLM failed to generate a valid JSON actionable plan.")
    except Exception as e:
        logger.error(f"Oracle failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
