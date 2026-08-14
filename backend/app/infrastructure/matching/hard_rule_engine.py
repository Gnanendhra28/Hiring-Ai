from typing import Optional, Tuple
from app.domains.matching.models import MatchStatusEnum

class HardRequirementEngine:
    """
    Deterministic Hard Requirement Evaluation Engine.
    Evaluates requirements flagged with hard_constraint = True.
    Supported Operators: GTE, LTE, EQUALS, RANGE.
    Absence of candidate evidence returns UNKNOWN (never NOT_MATCHED).
    Semantic similarity can NEVER override a failed hard requirement.
    """

    @staticmethod
    def evaluate_experience(
        required_operator: Optional[str],
        required_min_months: Optional[float],
        required_max_months: Optional[float],
        candidate_experience_months: Optional[float],
    ) -> Tuple[MatchStatusEnum, str]:
        """
        Evaluates numeric experience requirements in normalized MONTHS.
        """
        if required_min_months is None and required_max_months is None:
            return MatchStatusEnum.NOT_APPLICABLE, "No numeric experience threshold specified."

        if candidate_experience_months is None:
            return MatchStatusEnum.UNKNOWN, "Candidate experience duration is unknown (absence of evidence)."

        op = (required_operator or "GTE").upper()

        if op in ["GTE", "MIN"]:
            min_target = required_min_months or 0.0
            if candidate_experience_months >= min_target:
                return MatchStatusEnum.MATCHED, f"Candidate has {candidate_experience_months:.0f} months experience, satisfying >= {min_target:.0f} months requirement."
            else:
                return MatchStatusEnum.NOT_MATCHED, f"Candidate has {candidate_experience_months:.0f} months experience, failing >= {min_target:.0f} months requirement."

        elif op in ["LTE", "MAX"]:
            max_target = required_max_months or required_min_months or 0.0
            if candidate_experience_months <= max_target:
                return MatchStatusEnum.MATCHED, f"Candidate has {candidate_experience_months:.0f} months experience, satisfying <= {max_target:.0f} months requirement."
            else:
                return MatchStatusEnum.NOT_MATCHED, f"Candidate has {candidate_experience_months:.0f} months experience, failing <= {max_target:.0f} months requirement."

        elif op == "EQUALS":
            target = required_min_months or 0.0
            if abs(candidate_experience_months - target) <= 2.0:  # 2 month tolerance
                return MatchStatusEnum.MATCHED, f"Candidate experience ({candidate_experience_months:.0f} months) matches required {target:.0f} months."
            else:
                return MatchStatusEnum.NOT_MATCHED, f"Candidate experience ({candidate_experience_months:.0f} months) does not match required {target:.0f} months."

        elif op == "RANGE":
            min_target = required_min_months or 0.0
            max_target = required_max_months or (min_target * 2.0)
            if min_target <= candidate_experience_months <= max_target:
                return MatchStatusEnum.MATCHED, f"Candidate experience ({candidate_experience_months:.0f} months) within required range [{min_target:.0f}, {max_target:.0f}] months."
            else:
                return MatchStatusEnum.NOT_MATCHED, f"Candidate experience ({candidate_experience_months:.0f} months) outside required range [{min_target:.0f}, {max_target:.0f}] months."

        return MatchStatusEnum.UNKNOWN, "Unsupported experience comparison operator."

    @staticmethod
    def evaluate_work_mode(
        required_work_mode: str,
        candidate_work_mode: Optional[str],
    ) -> Tuple[MatchStatusEnum, str]:
        """
        Evaluates work mode compatibility (REMOTE, HYBRID, ONSITE).
        """
        if not required_work_mode:
            return MatchStatusEnum.NOT_APPLICABLE, "No work mode constraint specified."

        if not candidate_work_mode:
            return MatchStatusEnum.UNKNOWN, "Candidate work mode preference unknown."

        req = required_work_mode.upper()
        cand = candidate_work_mode.upper()

        if req == cand:
            return MatchStatusEnum.MATCHED, f"Work mode preference '{cand}' matches requirement '{req}'."
        
        # Remote work mode is generally compatible with hybrid
        if req == "REMOTE" or cand == "REMOTE":
            return MatchStatusEnum.PARTIALLY_MATCHED, f"Work mode '{cand}' partially compatible with '{req}'."

        return MatchStatusEnum.NOT_MATCHED, f"Candidate work mode preference '{cand}' conflicts with required '{req}'."
