"""
AI Recruitment Matching Engine - Main Pipeline Orchestrator
Executes the 3-tier matching pipeline:
  Tier 1: Dense Vector Cosine Similarity (ChromaDB + all-MiniLM-L6-v2) [Weight: 30%]
  Tier 2: Cross-Encoder Re-ranking (ms-marco-MiniLM-L-6-v2)           [Weight: 40%]
  Tier 3: LLM Structured Reasoning Evaluator (Gemini/OpenAI)          [Weight: 30%]
Synthesizes the final weighted score: (T1 * 0.3) + (T2 * 0.4) + (T3 * 0.3)
"""

import time
from typing import List

from .models import (
    CandidateProfile,
    EducationItem,
    JobDescription,
    ProjectItem,
    TierScoreResult,
    WorkExperienceItem,
)
from .tier1_vector import VectorSearchEngine
from .tier2_rerank import CrossEncoderReranker
from .tier3_llm import LLMEvaluator


class RecruitmentMatchingEngine:
    """
    Orchestrates the 3-Tier AI Recruitment Matching Pipeline.
    """

    def __init__(
        self,
        tier1_engine: VectorSearchEngine = None,
        tier2_engine: CrossEncoderReranker = None,
        tier3_engine: LLMEvaluator = None,
    ):
        print("⚡ Initializing 3-Tier AI Recruitment Matching Engine...")
        t0 = time.time()
        self.tier1 = tier1_engine or VectorSearchEngine()
        self.tier2 = tier2_engine or CrossEncoderReranker()
        self.tier3 = tier3_engine or LLMEvaluator()
        print(f"✓ Matching Engine ready in {time.time() - t0:.2f}s.\n")

    def match(
        self,
        candidate: CandidateProfile,
        jd: JobDescription,
    ) -> TierScoreResult:
        """
        Runs a candidate and Job Description through all 3 tiers and calculates the weighted final score.
        Formula: (Tier 1 * 0.3) + (Tier 2 * 0.4) + (Tier 3 * 0.3)
        """
        # Tier 1: Dense Vector Cosine Similarity (0 - 100)
        t1_score = self.tier1.score_single_candidate(candidate, jd)

        # Tier 2: Cross-Encoder Deep Semantic Relevance (0 - 100)
        t2_score = self.tier2.score_pair(candidate, jd)

        # Tier 3: LLM Structured Recruiter Evaluation (0 - 100)
        t3_output = self.tier3.evaluate(candidate, jd)
        t3_score = float(t3_output.total_score)

        # Weighted Final Score Synthesis
        final_score = round((t1_score * 0.30) + (t2_score * 0.40) + (t3_score * 0.30), 2)

        return TierScoreResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            job_id=jd.id,
            job_title=jd.title,
            tier1_vector_score=t1_score,
            tier2_rerank_score=t2_score,
            tier3_llm_score=t3_score,
            tier3_skills_score=t3_output.skills_score,
            tier3_experience_score=t3_output.experience_score,
            tier3_justification=t3_output.justification,
            final_weighted_score=final_score,
        )

    def rank_candidates(
        self,
        candidates: List[CandidateProfile],
        jd: JobDescription,
    ) -> List[TierScoreResult]:
        """Evaluates and ranks multiple candidate profiles against a Job Description."""
        results = [self.match(c, jd) for c in candidates]
        results.sort(key=lambda r: r.final_weighted_score, reverse=True)
        return results


def print_scorecard(result: TierScoreResult) -> None:
    """Renders a structured terminal scorecard."""
    print("=" * 70)
    print(f"📊 RECRUITMENT MATCH SCORECARD: {result.candidate_name.upper()}")
    print(f"🎯 Target Job: {result.job_title} (ID: {result.job_id})")
    print("=" * 70)
    print(f"• Tier 1 (Vector Dense Cosine Similarity - 30% weight): {result.tier1_vector_score:>6.1f} / 100")
    print(f"• Tier 2 (Cross-Encoder Re-ranking       - 40% weight): {result.tier2_rerank_score:>6.1f} / 100")
    print(f"• Tier 3 (LLM Recruiter Evaluator        - 30% weight): {result.tier3_llm_score:>6.1f} / 100")
    print(f"    ├─ Skills Alignment Sub-score:                      {result.tier3_skills_score:>6} / 100")
    print(f"    └─ Experience & Seniority Sub-score:                {result.tier3_experience_score:>6} / 100")
    print("-" * 70)
    print(f"🏆 FINAL WEIGHTED CANDIDATE SCORE:                      {result.final_weighted_score:>6.1f} / 100")
    print("-" * 70)
    print(f"📝 Recruiter Justification:\n   \"{result.tier3_justification}\"")
    print("=" * 70 + "\n")


def run_demo():
    """Sample pipeline demonstration."""
    # 1. Sample Job Description
    sample_jd = JobDescription(
        id="job-ai-001",
        title="Senior AI/ML Backend Engineer",
        department="AI Core Platform",
        required_skills=["Python", "FastAPI", "PyTorch", "Vector Databases", "ChromaDB", "LLMs", "RAG"],
        preferred_skills=["Docker", "Kubernetes", "PostgreSQL", "LangChain"],
        experience_required_years=4.0,
        responsibilities=[
            "Design and build scalable RAG and semantic search pipelines",
            "Deploy LLM agent frameworks and embedding indexing services",
            "Optimize backend APIs using FastAPI and asynchronous databases",
        ],
        description="We are seeking a Senior AI/ML Backend Engineer to lead the development of our next-generation retrieval-augmented AI recruitment platform.",
    )

    # 2. Sample Strong Match Candidate
    candidate_strong = CandidateProfile(
        id="cand-001",
        name="Alex Chen",
        headline="Senior AI Systems Engineer",
        summary="5+ years designing production AI systems, LLM embeddings, RAG architectures with FastAPI and ChromaDB.",
        skills=["Python", "PyTorch", "FastAPI", "ChromaDB", "RAG", "LLMs", "PostgreSQL", "Docker"],
        experience_years=5.5,
        work_history=[
            WorkExperienceItem(
                title="Lead AI Engineer",
                company="VectorAI Labs",
                duration_years=3.5,
                description="Built high-throughput RAG search engine using sentence-transformers, ChromaDB, and FastAPI handling 10M queries/day.",
            ),
            WorkExperienceItem(
                title="Machine Learning Engineer",
                company="DataCore Solutions",
                duration_years=2.0,
                description="Trained PyTorch models and deployed inference microservices via Docker.",
            ),
        ],
        projects=[
            ProjectItem(
                name="Multi-Tier Recruitment RAG Engine",
                description="Implemented cross-encoder re-ranking and vector search for automated resume screening.",
                technologies=["Python", "PyTorch", "ChromaDB", "Gemini 2.5 Pro"],
            )
        ],
        education=[
            EducationItem(degree="M.S. in Computer Science (AI Specialization)", institution="Stanford University", graduation_year=2021)
        ],
    )

    # 3. Sample Weak Match Candidate
    candidate_weak = CandidateProfile(
        id="cand-002",
        name="Jordan Miller",
        headline="Junior Frontend Developer",
        summary="1.5 years experience building responsive UI components in React, HTML5, and CSS.",
        skills=["JavaScript", "React", "HTML5", "CSS3", "TailwindCSS"],
        experience_years=1.5,
        work_history=[
            WorkExperienceItem(
                title="Junior Web Developer",
                company="Pixel Studio",
                duration_years=1.5,
                description="Created landing pages and interactive forms with React and CSS.",
            )
        ],
        projects=[
            ProjectItem(
                name="E-Commerce Storefront",
                description="Developed an online shopping cart in Next.js and Tailwind.",
                technologies=["React", "Next.js", "CSS"],
            )
        ],
        education=[
            EducationItem(degree="B.A. in Graphic Design", institution="State College", graduation_year=2024)
        ],
    )

    # 4. Run Matching Engine
    engine = RecruitmentMatchingEngine()

    print("🚀 Running candidate evaluation against Senior AI/ML Engineer JD...\n")
    results = engine.rank_candidates([candidate_strong, candidate_weak], sample_jd)

    for res in results:
        print_scorecard(res)


if __name__ == "__main__":
    run_demo()
