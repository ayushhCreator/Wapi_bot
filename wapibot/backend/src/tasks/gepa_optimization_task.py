"""Celery task for GEPA optimizer - reflective prompt evolution."""

import logging
from tasks import celery_app
from repositories.brain_decision_repo import BrainDecisionRepository
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


@celery_app.task(name="brain.gepa_optimize")
def run_gepa_optimization(num_iterations: int = 100) -> dict:
    """Execute GEPA optimization on brain decisions.

    Applies reflective prompt evolution to improve brain modules.

    Args:
        num_iterations: Number of optimization iterations

    Returns:
        Dict with optimization results
    """
    try:
        settings = get_brain_settings()

        if not settings.rl_gym_enabled:
            logger.info("⏭️ RL Gym disabled in config")
            return {"status": "skipped", "reason": "disabled"}

        # Get recent decisions
        decision_repo = BrainDecisionRepository()
        decisions = decision_repo.get_recent(num_iterations)

        if len(decisions) < num_iterations:
            logger.info(f"⏳ Not enough decisions: {len(decisions)}/{num_iterations}")
            return {"status": "skipped", "reason": "insufficient_data"}

        # TODO: Implement GEPA optimization
        # For now, just log
        logger.info(f"🧠 GEPA optimization: {len(decisions)} decisions")

        return {
            "status": "success",
            "decisions_processed": len(decisions),
            "iterations": num_iterations
        }

    except Exception as e:
        logger.error(f"❌ GEPA optimization failed: {e}")
        return {"status": "error", "error": str(e)}
