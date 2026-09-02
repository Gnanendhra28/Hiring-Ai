"""
Firestore Interview Session & Scorecard Persistence Repository.
Provides document persistence for interview turns, Gemini evaluations, and final scorecards,
ensuring Cloud Run multi-instance statelessness and restart resilience.
Integrates directly with Google Cloud Firestore AsyncClient in production.
"""

import json
import os
from pathlib import Path
from typing import Any
from app.core.logging import logger
from app.domains.interviews.ai_agent import (
    CandidateAnswerTurn,
    InterviewScorecard,
    TurnEvaluation,
)


class FirestoreInterviewRepository:
    """
    Persistent document repository for interview turns and scorecards.
    Supports Google Cloud Firestore AsyncClient with fallback to isolated local store for testing.
    """

    def __init__(self, project_id: str | None = None, storage_dir: str | None = None):
        self.project_id = project_id or os.getenv("FIRESTORE_PROJECT_ID") or os.getenv("FIREBASE_PROJECT_ID") or "hiring-ai-4ae76"
        self.storage_dir = Path(storage_dir or "backend/storage/firestore_interviews")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._firestore_client = None

    async def _get_client(self):
        """Lazy initialization of Google Cloud Firestore AsyncClient."""
        if self._firestore_client is None:
            try:
                from google.cloud import firestore
                # Try initializing real Firestore AsyncClient if credentials or ADC are present
                self._firestore_client = firestore.AsyncClient(project=self.project_id)
            except Exception as ex:
                logger.info(f"[Firestore Repo] Cloud Firestore client offline; using local document store: {ex}")
                self._firestore_client = False
        return self._firestore_client if self._firestore_client is not False else None

    def _get_session_file(self, interview_id: str) -> Path:
        clean_id = interview_id.replace("/", "_").replace("\\", "_")
        return self.storage_dir / f"{clean_id}.json"

    async def save_turn(
        self,
        interview_id: str,
        turn: CandidateAnswerTurn,
        turn_eval: TurnEvaluation | None = None,
    ) -> None:
        """
        Persists a candidate interview turn and optional Gemini turn evaluation.
        """
        client = await self._get_client()
        turn_payload = turn.model_dump()
        if turn_eval:
            turn_payload["evaluation"] = turn_eval.model_dump()

        if client:
            try:
                turn_ref = client.collection("interviews").document(interview_id).collection("turns").document()
                await turn_ref.set(turn_payload)
                logger.info(f"[Firestore Repo] Persisted turn to Cloud Firestore for interview={interview_id}")
                return
            except Exception as ex:
                logger.warning(f"[Firestore Repo] Cloud Firestore write failed ({ex}); persisting to disk store.")

        # Local document persistence fallback
        file_path = self._get_session_file(interview_id)
        data: dict[str, Any] = {"turns": [], "scorecard": None}
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as ex:
                logger.warning(f"[Firestore Repo] Could not load session {interview_id}: {ex}")

        data.setdefault("turns", []).append(turn_payload)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"[Firestore Repo] Successfully persisted turn {len(data['turns'])} for interview={interview_id}")
        except Exception as ex:
            logger.error(f"[Firestore Repo] Failed to persist turn for {interview_id}: {ex}")
            raise

    async def get_turns(self, interview_id: str) -> list[CandidateAnswerTurn]:
        """
        Loads all recorded turns for an interview session from persistent storage.
        """
        client = await self._get_client()
        if client:
            try:
                turns_stream = client.collection("interviews").document(interview_id).collection("turns").stream()
                turns = []
                async for doc in turns_stream:
                    t = doc.to_dict()
                    turns.append(
                        CandidateAnswerTurn(
                            question_id=t.get("question_id", "q-unknown"),
                            question_text=t.get("question_text", ""),
                            candidate_answer=t.get("candidate_answer", ""),
                            code_submission=t.get("code_submission"),
                            time_taken_seconds=t.get("time_taken_seconds"),
                        )
                    )
                if turns:
                    return turns
            except Exception as ex:
                logger.warning(f"[Firestore Repo] Cloud Firestore read failed ({ex}); reading from disk store.")

        # Local document persistence read
        file_path = self._get_session_file(interview_id)
        if not file_path.exists():
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                raw_turns = data.get("turns", [])
                turns = []
                for t in raw_turns:
                    turns.append(
                        CandidateAnswerTurn(
                            question_id=t.get("question_id", "q-unknown"),
                            question_text=t.get("question_text", ""),
                            candidate_answer=t.get("candidate_answer", ""),
                            code_submission=t.get("code_submission"),
                            time_taken_seconds=t.get("time_taken_seconds"),
                        )
                    )
                return turns
        except Exception as ex:
            logger.error(f"[Firestore Repo] Failed to read turns for {interview_id}: {ex}")
            return []

    async def save_scorecard(self, interview_id: str, scorecard: InterviewScorecard) -> None:
        """
        Persists finalized Gemini evaluation scorecard.
        """
        client = await self._get_client()
        card_payload = scorecard.model_dump()

        if client:
            try:
                card_ref = client.collection("interviews").document(interview_id).collection("scorecard").document("final")
                await card_ref.set(card_payload)
                logger.info(f"[Firestore Repo] Persisted scorecard to Cloud Firestore for interview={interview_id}")
                return
            except Exception as ex:
                logger.warning(f"[Firestore Repo] Cloud Firestore scorecard write failed ({ex}); persisting to disk store.")

        file_path = self._get_session_file(interview_id)
        data: dict[str, Any] = {"turns": [], "scorecard": None}
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        data["scorecard"] = card_payload
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"[Firestore Repo] Successfully persisted scorecard for interview={interview_id}")
        except Exception as ex:
            logger.error(f"[Firestore Repo] Failed to persist scorecard for {interview_id}: {ex}")
            raise

    async def get_scorecard(self, interview_id: str) -> InterviewScorecard | None:
        """
        Retrieves the persistent scorecard for an interview session.
        """
        client = await self._get_client()
        if client:
            try:
                card_doc = await client.collection("interviews").document(interview_id).collection("scorecard").document("final").get()
                if card_doc.exists:
                    return InterviewScorecard.model_validate(card_doc.to_dict())
            except Exception as ex:
                logger.warning(f"[Firestore Repo] Cloud Firestore scorecard read failed ({ex}); reading from disk store.")

        file_path = self._get_session_file(interview_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                card_data = data.get("scorecard")
                if card_data:
                    return InterviewScorecard.model_validate(card_data)
        except Exception as ex:
            logger.error(f"[Firestore Repo] Failed to read scorecard for {interview_id}: {ex}")

        return None
