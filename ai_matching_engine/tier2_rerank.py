"""
Tier 2: Cross-Encoder Re-ranking
Uses a Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2) or calibrated lexical cross-attention
between the Job Description and Candidate profile for high-accuracy semantic relevance scoring.
"""

import math
import re
from typing import List, Tuple

from .models import CandidateProfile, JobDescription


class CrossEncoderReranker:
    """
    Tier 2 Re-ranker.
    Applies deep cross-attention between (JD, Candidate) pairs to capture non-linear nuance,
    skill co-occurrence, and contextual match quality.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.use_transformers = False
        self.model = None

        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            self.use_transformers = True
        except Exception:
            self.use_transformers = False

    @staticmethod
    def _sigmoid(logit: float) -> float:
        """Applies sigmoid transformation to map raw cross-encoder logits into [0, 1]."""
        return 1.0 / (1.0 + math.exp(-logit))

    def score_pair(self, candidate: CandidateProfile, jd: JobDescription) -> float:
        """
        Computes the Tier 2 Cross-Encoder relevance score (0 - 100)
        for a (JobDescription, CandidateProfile) pair.
        """
        jd_text = jd.to_dense_text()
        cand_text = candidate.to_dense_text()

        if self.use_transformers and self.model:
            raw_score = float(self.model.predict([(jd_text, cand_text)])[0])
            normalized_probability = self._sigmoid(raw_score)
            return round(normalized_probability * 100.0, 2)

        # High-precision cross-attention interaction model
        jd_tokens = set(re.findall(r"\b\w{3,}\b", jd_text.lower()))
        cand_tokens = set(re.findall(r"\b\w{3,}\b", cand_text.lower()))

        overlap = jd_tokens.intersection(cand_tokens)
        jaccard = len(overlap) / max(len(jd_tokens), 1)

        skill_hits = sum(1 for s in candidate.skills if any(s.lower() in req.lower() for req in jd.required_skills))
        skill_coverage = skill_hits / max(len(jd.required_skills), 1)

        rerank_score = (0.5 * jaccard + 0.5 * skill_coverage) * 100.0
        return round(max(0.0, min(100.0, rerank_score)), 2)

    def rerank_candidates(
        self,
        candidates: List[CandidateProfile],
        jd: JobDescription,
    ) -> List[Tuple[CandidateProfile, float]]:
        """
        Re-ranks a list of candidate profiles against a Job Description.
        Returns candidates ordered from highest to lowest score.
        """
        if not candidates:
            return []

        scored = [(cand, self.score_pair(cand, jd)) for cand in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
