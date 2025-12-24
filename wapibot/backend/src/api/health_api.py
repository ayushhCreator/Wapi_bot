"""Health check API endpoints.

Provides honest system health monitoring by running the test suite.
The /health endpoint executes all tests and reports real status.
"""

import logging
import subprocess
from datetime import datetime
from fastapi import APIRouter

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Basic health check endpoint - quick status."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/health")
async def health_check():
    """REAL health check - runs test suite and reports results.

    Executes the test suite in tests/ and returns a concise health report.
    This is the honest health check that actually validates the system.

    Returns:
        Concise test results with pass/fail status
    """
    start_time = datetime.now()

    # Run test suite
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="."
        )

        # Parse pytest output for summary
        output_lines = result.stdout.strip().split('\n')
        summary_line = next((line for line in reversed(output_lines) if 'passed' in line or 'failed' in line), "")

        test_passed = result.returncode == 0
        elapsed = (datetime.now() - start_time).total_seconds()

        return {
            "status": "healthy" if test_passed else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "check_duration_seconds": round(elapsed, 3),
            "test_summary": summary_line.strip(),
            "exit_code": result.returncode,
            "service": settings.app_name,
            "version": settings.app_version
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": "Test suite timed out after 60 seconds",
            "service": settings.app_name,
            "version": settings.app_version
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "service": settings.app_name,
            "version": settings.app_version
        }
