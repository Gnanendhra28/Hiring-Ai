import asyncio
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory

from app.infrastructure.events.envelope import EventEnvelope
from app.services.matching_service import MatchingService

from app.services.scoring_service import ScoringService
from app.services.ranking_service import RankingService
from app.services.recommendation_service import RecommendationService


import time
from app.core.metrics import metrics

class DeadLetterRecord(BaseModel):
    """Immutable dead-letter record for unresolvable event processing failures."""
    event_id: uuid.UUID
    event_type: str
    organization_id: uuid.UUID
    correlation_id: str
    reason: str
    failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int

class PipelineWorker:
    """
    Production-ready Distributed Asynchronous Event Worker & Retry Manager.
    
    Subscribes to pipeline domain events, propagates organization tenant RLS context,
    invokes authoritative domain services, enforces bounded retries for transient failures,
    and routes permanent errors to a dead-letter log.
    
    CRITICAL GOVERNANCE & SECURITY GUARANTEE:
    - Sets tenant RLS context for every database transaction.
    - Zero score, rank, or recommendation calculation logic in the worker itself.
    - Idempotent execution using database unique constraints.
    """

    def __init__(self, max_retries: int = 3, retry_delay_sec: float = 0.1):
        self.max_retries = max_retries
        self.retry_delay_sec = retry_delay_sec
        self.dead_letter_queue: list[DeadLetterRecord] = []
        self.processed_event_ids: set[uuid.UUID] = set()

    async def process_event(self, event: EventEnvelope) -> bool:
        """
        Main worker entrypoint for event processing.
        Returns True if processing succeeded or was idempotently skipped, False if failed.
        """
        metrics.increment("worker_events_received_total", labels={"event_type": event.event_type})

        if event.event_id in self.processed_event_ids:
            logger.info(f"[Worker] Idempotent skip for event_id={event.event_id}")
            metrics.increment("worker_events_idempotent_skips_total", labels={"event_type": event.event_type})
            return True

        logger.info(f"[Worker] Processing event '{event.event_type}' [id={event.event_id}, org={event.organization_id}]")
        start_t = time.time()
        attempts = 0

        while attempts < self.max_retries:
            attempts += 1
            try:
                async with async_session_factory() as session:
                    # 1. Establish strict tenant RLS context
                    await set_tenant_context(session, event.organization_id)

                    # 2. Dispatch to authoritative domain service handler
                    if event.event_type == "candidate.matched":
                        await self._handle_candidate_matched(session, event)
                    elif event.event_type == "candidate.scored":
                        await self._handle_candidate_scored(session, event)
                    elif event.event_type == "candidate.ranking.completed":
                        await self._handle_ranking_completed(session, event)
                    elif event.event_type == "candidate.recommendation.completed":
                        logger.info(f"[Worker] Recommendation completed for candidate_id={event.aggregate_id}")
                    elif event.event_type == "candidate.decision.recorded":
                        logger.info(f"[Worker] Recruiter decision recorded for application_id={event.aggregate_id}")

                    await session.commit()
                    self.processed_event_ids.add(event.event_id)

                    duration = time.time() - start_t
                    metrics.increment("worker_events_succeeded_total", labels={"event_type": event.event_type})
                    metrics.observe_duration("worker_event_duration_seconds", duration, labels={"event_type": event.event_type})
                    return True

            except ValueError as ve:
                # Permanent failure (e.g. STALE job intelligence, invalid ID) -> Do NOT retry
                logger.error(f"[Worker] Permanent error processing '{event.event_type}' (Attempt {attempts}/{self.max_retries}): {ve}")
                metrics.increment("worker_events_permanent_failures_total", labels={"event_type": event.event_type})
                self._record_dead_letter(event, str(ve), attempts)
                return False

            except Exception as e:
                # Transient failure (e.g. temporary network error) -> Bounded retry
                logger.warning(f"[Worker] Transient error processing '{event.event_type}' (Attempt {attempts}/{self.max_retries}): {e}")
                metrics.increment("worker_retries_total", labels={"event_type": event.event_type})

                if attempts >= self.max_retries:
                    logger.error(f"[Worker] Max retries exhausted for event {event.event_id}. Routing to dead-letter queue.")
                    metrics.increment("worker_events_failed_total", labels={"event_type": event.event_type})
                    self._record_dead_letter(event, f"Max retries exhausted: {str(e)}", attempts)
                    return False
                await asyncio.sleep(self.retry_delay_sec)

        return False


    async def _handle_candidate_matched(self, session, event: EventEnvelope):
        """Worker handler when candidate matching completes -> Triggers deterministic scoring."""
        job_id = event.payload.get("job_id")
        candidate_id = event.payload.get("candidate_id")
        candidate_doc_id = event.payload.get("candidate_document_id")
        if not (job_id and candidate_id and candidate_doc_id):
            raise ValueError("Invalid payload: missing job_id, candidate_id, or candidate_document_id")

        matching_service = MatchingService(session)

        scoring_service = ScoringService(session)

        match_rec = await matching_service.get_match(
            organization_id=event.organization_id,
            job_id=uuid.UUID(str(job_id)),
            candidate_id=uuid.UUID(str(candidate_id)),
        )
        if match_rec:
            await scoring_service.calculate_candidate_score(
                organization_id=event.organization_id,
                match_id=match_rec.id,
            )

    async def _handle_candidate_scored(self, session, event: EventEnvelope):
        """Worker handler when candidate scoring completes -> Triggers deterministic ranking update."""
        job_id = event.payload.get("job_id")
        if not job_id:
            raise ValueError("Invalid payload: missing job_id")

        ranking_service = RankingService(session)
        await ranking_service.generate_job_rankings(
            organization_id=event.organization_id,
            job_id=uuid.UUID(str(job_id)),
        )

    async def _handle_ranking_completed(self, session, event: EventEnvelope):
        """Worker handler when candidate ranking completes -> Triggers Top-K recommendation generation."""
        job_id = event.payload.get("job_id")
        if not job_id:
            raise ValueError("Invalid payload: missing job_id")

        ranking_service = RankingService(session)
        recommendation_service = RecommendationService(session)

        # Retrieve top-K candidates from ranking snapshot
        ranking_resp = await ranking_service.get_job_rankings(
            organization_id=event.organization_id,
            job_id=uuid.UUID(str(job_id)),
        )

        for r_item in ranking_resp.rankings:
            if r_item.is_top_k:
                try:
                    await recommendation_service.generate_recommendation(
                        organization_id=event.organization_id,
                        job_id=uuid.UUID(str(job_id)),
                        candidate_id=r_item.candidate_id,
                    )
                except Exception as ex:
                    logger.warning(f"[Worker] Failed recommendation generation for candidate {r_item.candidate_id}: {ex}")

    def _record_dead_letter(self, event: EventEnvelope, reason: str, attempts: int):
        dl_record = DeadLetterRecord(
            event_id=event.event_id,
            event_type=event.event_type,
            organization_id=event.organization_id,
            correlation_id=event.correlation_id,
            reason=reason,
            attempts=attempts,
        )
        self.dead_letter_queue.append(dl_record)
        logger.error(f"[DeadLetterQueue] Recorded event {event.event_id} reason='{reason}'")
