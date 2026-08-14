from typing import Dict, List, Any
from datetime import datetime

from app.domains.scoring.models import EligibilityStatusEnum

class RankingEngine:
    """
    Deterministic Candidate Ranking & Top-K Selection Engine.
    
    CRITICAL AI GOVERNANCE RULE:
    Zero LLM calls. Consumes authoritative Phase 9B candidate scores only.
    Applies multi-level deterministic tie-breaking and eligibility-aware Top-K selection.
    """

    @classmethod
    def rank_candidates(
        cls,
        candidate_scores: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate score objects deterministically.

        Each item in candidate_scores expected to contain:
        - candidate_job_score: CandidateJobScore OR dict
        - score: float (0.0 - 100.0)
        - score_confidence: float (0.0 - 1.0)
        - eligibility_status: EligibilityStatusEnum
        - failed_hard_reqs_count: int
        - matched_reqs_count: int
        - created_at: datetime
        - candidate_id: uuid.UUID
        """
        if not candidate_scores:
            return []

        def tie_breaker_key(item: Dict[str, Any]):
            eligibility = item.get("eligibility_status")
            if isinstance(eligibility, str):
                is_eligible = 1 if eligibility == "PASS" else 0
            else:
                is_eligible = 1 if eligibility == EligibilityStatusEnum.PASS else 0

            score = float(item.get("score", 0.0))
            confidence = float(item.get("score_confidence", 0.0))
            failed_hard = int(item.get("failed_hard_reqs_count", 0))
            matched_reqs = int(item.get("matched_reqs_count", 0))
            
            created_at = item.get("created_at")
            created_at_timestamp = created_at.timestamp() if isinstance(created_at, datetime) else 0.0

            cand_id_str = str(item.get("candidate_id", ""))

            # Python sorts tuples lexicographically ASC.
            # We invert numbers where higher is better by using negative values.
            return (
                -is_eligible,            # 1. Eligible (PASS) first (-1 < 0)
                -score,                  # 2. Score DESC (-95.0 < -90.0)
                -confidence,             # 3. Confidence DESC (-0.95 < -0.80)
                failed_hard,             # 4. Failed hard reqs ASC (0 < 1)
                -matched_reqs,           # 5. Matched reqs DESC (-5 < -3)
                created_at_timestamp,    # 6. Created at ASC (earlier is better)
                cand_id_str,             # 7. Candidate ID ASC (alphabetical tie-breaker)
            )

        # Execute deterministic multi-level sort
        sorted_candidates = sorted(candidate_scores, key=tie_breaker_key)

        ranked_results = []
        for idx, item in enumerate(sorted_candidates, start=1):
            rank_position = idx
            eligibility = item.get("eligibility_status")
            
            if isinstance(eligibility, str):
                is_pass = eligibility == "PASS"
            else:
                is_pass = eligibility == EligibilityStatusEnum.PASS

            # Top-K semantics: Only eligible candidates can consume a Top-K slot
            is_top_k = is_pass and (rank_position <= top_k)

            ranked_item = dict(item)
            ranked_item["rank_position"] = rank_position
            ranked_item["is_top_k"] = is_top_k
            ranked_results.append(ranked_item)

        return ranked_results
