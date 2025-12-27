"""Brain Control API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from api.v1.brain_schemas import (
    DreamTriggerRequest,
    TrainTriggerRequest,
    BrainStatusResponse
)
from services.brain_service import get_brain_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/brain", tags=["Brain Control"])


@router.post("/dream")
async def trigger_dream_cycle(request: DreamTriggerRequest):
    """Manually trigger brain dream cycle.

    Args:
        request: Dream trigger configuration

    Returns:
        Task ID and status
    """
    try:
        service = get_brain_service()
        result = await service.trigger_dream(request.force, request.min_conversations)
        return result
    except Exception as e:
        logger.error(f"Dream trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def trigger_training(request: TrainTriggerRequest):
    """Trigger GEPA optimization.

    Args:
        request: Training configuration

    Returns:
        Task ID and status
    """
    try:
        service = get_brain_service()
        result = await service.trigger_training(request.optimizer, request.num_iterations)
        return result
    except Exception as e:
        logger.error(f"Training trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=BrainStatusResponse)
async def get_brain_status():
    """Get brain system status and metrics."""
    try:
        service = get_brain_service()
        return await service.get_brain_status()
    except Exception as e:
        logger.error(f"Status fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features")
async def get_feature_toggles():
    """Get all feature toggle states."""
    try:
        service = get_brain_service()
        return service.get_feature_toggles()
    except Exception as e:
        logger.error(f"Feature fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions")
async def get_recent_decisions(limit: int = 100):
    """Get recent brain decisions from RL Gym."""
    try:
        service = get_brain_service()
        decisions = await service.get_recent_decisions(limit)
        return {"decisions": decisions, "total": len(decisions)}
    except Exception as e:
        logger.error(f"Decisions fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
