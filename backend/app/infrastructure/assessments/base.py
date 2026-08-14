from abc import ABC, abstractmethod
from typing import Any, Dict
from app.core.logging import logger

class AssessmentProvider(ABC):
    """Abstract Base Class for External Assessment Providers."""

    @abstractmethod
    async def create_session(self, assessment_id: str, candidate_email: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_result(self, session_id: str) -> Dict[str, Any]:
        pass

class TestAssessmentAdapter(AssessmentProvider):
    """Development / Testing Assessment Provider Adapter."""

    async def create_session(self, assessment_id: str, candidate_email: str) -> Dict[str, Any]:
        logger.info(f"Generated test assessment session for assessment={assessment_id}, email={candidate_email}")
        return {
            "session_id": f"session-{assessment_id[:8]}",
            "test_url": f"https://assessment.internal/session/{assessment_id[:8]}",
            "provider": "TEST",
        }

    async def get_result(self, session_id: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "score": 85,
            "passed": True,
            "provider": "TEST",
        }
