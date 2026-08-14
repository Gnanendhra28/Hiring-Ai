import uuid
from typing import Dict, Any, List
from sqlalchemy import select, text

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.rls import set_tenant_context

class SemanticMatcher:
    """
    Context-Aware pgvector Semantic Matching Engine.
    Queries PostgreSQL pgvector embeddings across distinct semantic contexts:
      - Job REQUIRED_SKILLS <-> Candidate SKILL_CONTEXT
      - Job RESPONSIBILITIES <-> Candidate EXPERIENCE_CONTEXT
      - Job JOB_INTENT <-> Candidate SUMMARY / EXPERIENCE / PROJECT_CONTEXT
    Uses HNSW vector cosine similarity while enforcing PostgreSQL RLS tenant context.
    """

    @staticmethod
    async def match_semantic_contexts(
        session: AsyncSession,
        organization_id: uuid.UUID,
        job_id: uuid.UUID,
        job_intelligence_version_id: uuid.UUID,
        candidate_id: uuid.UUID,
        candidate_document_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        Calculates context-aware vector similarities between Job embeddings and Candidate embeddings.
        Returns a list of semantic match records with query_context, candidate_context, and similarity_score.
        """
        await set_tenant_context(session, organization_id)

        from app.domains.candidates.models import CandidateProfile
        stmt_p = select(CandidateProfile).where(CandidateProfile.id == candidate_id)
        cand_p = (await session.execute(stmt_p)).scalar_one_or_none()
        cand_user_id = cand_p.user_id if cand_p else candidate_id

        # Context pairings to evaluate
        context_pairs = [
            ("REQUIRED_SKILLS", "SKILL_CONTEXT"),
            ("RESPONSIBILITIES", "EXPERIENCE_CONTEXT"),
            ("JOB_INTENT", "SUMMARY"),
        ]

        results = []

        query = text("""
            SELECT 
                j.context_type AS job_context,
                c.context_type AS cand_context,
                (1 - (j.embedding <=> c.embedding)) AS similarity
            FROM job_embeddings j
            JOIN candidate_embeddings c 
              ON j.organization_id = c.organization_id
             AND c.candidate_id = :candidate_id
             AND c.document_id = :candidate_document_id
            WHERE j.organization_id = :org_id
              AND j.job_id = :job_id
              AND j.intelligence_version_id = :job_intel_v_id
              AND j.context_type = :job_context
              AND c.context_type = :cand_context
            LIMIT 1;
        """)

        for job_ctx, cand_ctx in context_pairs:
            res = (
                await session.execute(
                    query,
                    {
                        "org_id": str(organization_id),
                        "job_id": str(job_id),
                        "job_intel_v_id": str(job_intelligence_version_id),
                        "candidate_id": str(cand_user_id),
                        "candidate_document_id": str(candidate_document_id),
                        "job_context": job_ctx,
                        "cand_context": cand_ctx,
                    },
                )
            ).fetchone()


            sim_score = float(res.similarity) if res and res.similarity is not None else 0.50

            results.append({
                "query_context": job_ctx,
                "candidate_context": cand_ctx,
                "similarity_score": round(sim_score, 4),
                "embedding_model": settings.EMBEDDING_MODEL,
                "dimension": settings.EMBEDDING_DIMENSION,
            })

        return results
