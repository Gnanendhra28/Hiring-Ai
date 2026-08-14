from typing import Dict, List, Tuple, Any

from app.domains.matching.models import (
    CandidateRequirementMatch,
    CandidateSemanticMatch,
    MatchStatusEnum,
)
from app.domains.scoring.models import (
    ConfidenceTierEnum,
    EligibilityStatusEnum,
    FactorTypeEnum,
    ScoringConfiguration,
)

class ScoringEngine:
    """
    Deterministic Candidate Scoring Engine.
    Converts Phase 9A feature-level matching results into individual factor scores,
    applicable weight normalized contributions, hard requirement eligibility checks,
    overall candidate score (0-100), and score confidence tiers.

    CRITICAL AI GOVERNANCE RULE:
    Zero LLM involvement in score calculation or candidate ranking.
    Scoring is 100% deterministic and reproducible.
    """

    @staticmethod
    def validate_weights(config: ScoringConfiguration) -> bool:
        weights = [
            config.required_skills_weight if config.required_skills_weight is not None else 0.30,
            config.semantic_match_weight if config.semantic_match_weight is not None else 0.20,
            config.experience_weight if config.experience_weight is not None else 0.20,
            config.education_weight if config.education_weight is not None else 0.10,
            config.preferred_skills_weight if config.preferred_skills_weight is not None else 0.10,
            config.other_requirements_weight if config.other_requirements_weight is not None else 0.10,
        ]

        for w in weights:
            if w < 0.0 or w > 1.0:
                return False

        total_w = sum(weights)
        return abs(total_w - 1.0) < 1e-4


    @classmethod
    def calculate_candidate_score(
        cls,
        config: ScoringConfiguration,
        req_matches: List[CandidateRequirementMatch],
        sem_matches: List[CandidateSemanticMatch],
    ) -> Dict[str, Any]:
        """
        Calculates deterministic candidate score, factor breakdown, eligibility, and confidence.
        """
        # 1. Hard Requirement Gate Evaluation
        hard_results = []
        eligibility_status = EligibilityStatusEnum.PASS
        failed_hard_reqs = 0

        for rm in req_matches:
            if rm.hard_constraint:
                if rm.match_status == MatchStatusEnum.NOT_MATCHED:
                    eligibility_status = EligibilityStatusEnum.FAIL
                    failed_hard_reqs += 1
                
                hard_results.append({
                    "requirement_id": rm.job_requirement_id,
                    "status": rm.match_status.value if hasattr(rm.match_status, "value") else str(rm.match_status),
                    "candidate_value": rm.candidate_value,
                    "required_value": rm.raw_required_value,
                    "operator": None,
                    "reason": rm.reason,
                    "confidence": rm.confidence,
                    "evidence_text": rm.evidence_text,
                })

        # 2. Categorize Requirement Matches by Factor Type
        req_skills = []
        pref_skills = []
        exp_reqs = []
        edu_reqs = []
        other_reqs = []

        for rm in req_matches:
            # Skip protected excluded features from all factor scores
            if rm.match_status == MatchStatusEnum.PROTECTED_EXCLUDED:
                continue

            r_type = rm.requirement_type.upper() if isinstance(rm.requirement_type, str) else rm.requirement_type.name.upper()
            r_level = rm.requirement_level.upper() if isinstance(rm.requirement_level, str) else rm.requirement_level.name.upper()

            if r_level == "PREFERRED" or r_type == "PREFERRED_SKILL":
                pref_skills.append(rm)
            elif r_type in ["SKILL", "TECHNOLOGY", "REQUIRED_SKILL"]:
                req_skills.append(rm)
            elif r_type == "EXPERIENCE":
                exp_reqs.append(rm)
            elif r_type == "EDUCATION":
                edu_reqs.append(rm)
            else:
                other_reqs.append(rm)

        # 3. Assess Factor Applicability
        factor_applicability = {
            FactorTypeEnum.REQUIRED_SKILLS: len(req_skills) > 0,
            FactorTypeEnum.SEMANTIC_MATCH: len(sem_matches) > 0,
            FactorTypeEnum.EXPERIENCE: len(exp_reqs) > 0,
            FactorTypeEnum.EDUCATION: len(edu_reqs) > 0,
            FactorTypeEnum.PREFERRED_SKILLS: len(pref_skills) > 0,
            FactorTypeEnum.OTHER_REQUIREMENTS: len(other_reqs) > 0,
        }

        configured_weights = {
            FactorTypeEnum.REQUIRED_SKILLS: config.required_skills_weight if config.required_skills_weight is not None else 0.30,
            FactorTypeEnum.SEMANTIC_MATCH: config.semantic_match_weight if config.semantic_match_weight is not None else 0.20,
            FactorTypeEnum.EXPERIENCE: config.experience_weight if config.experience_weight is not None else 0.20,
            FactorTypeEnum.EDUCATION: config.education_weight if config.education_weight is not None else 0.10,
            FactorTypeEnum.PREFERRED_SKILLS: config.preferred_skills_weight if config.preferred_skills_weight is not None else 0.10,
            FactorTypeEnum.OTHER_REQUIREMENTS: config.other_requirements_weight if config.other_requirements_weight is not None else 0.10,
        }


        # Applicable Weight Normalization
        applicable_weight_sum = sum(
            configured_weights[ft] for ft, app in factor_applicability.items() if app
        )

        normalized_weights = {}
        for ft in FactorTypeEnum:
            if factor_applicability[ft] and applicable_weight_sum > 0:
                normalized_weights[ft] = configured_weights[ft] / applicable_weight_sum
            else:
                normalized_weights[ft] = 0.0

        # 4. Calculate Factor Normalized Scores (0.0 - 1.0) & Raw Scores (0 - 100)
        factor_scores_data = []

        # Required Skills Factor
        req_norm_score, req_reason = cls._calculate_skill_factor_score(req_skills, "Required Skills")
        factor_scores_data.append(cls._build_factor_data(
            FactorTypeEnum.REQUIRED_SKILLS, req_norm_score, configured_weights[FactorTypeEnum.REQUIRED_SKILLS],
            normalized_weights[FactorTypeEnum.REQUIRED_SKILLS], factor_applicability[FactorTypeEnum.REQUIRED_SKILLS], req_reason
        ))

        # Semantic Match Factor
        sem_norm_score, sem_reason = cls._calculate_semantic_factor_score(sem_matches)
        factor_scores_data.append(cls._build_factor_data(
            FactorTypeEnum.SEMANTIC_MATCH, sem_norm_score, configured_weights[FactorTypeEnum.SEMANTIC_MATCH],
            normalized_weights[FactorTypeEnum.SEMANTIC_MATCH], factor_applicability[FactorTypeEnum.SEMANTIC_MATCH], sem_reason
        ))

        # Experience Factor
        exp_norm_score, exp_reason = cls._calculate_experience_factor_score(exp_reqs)
        factor_scores_data.append(cls._build_factor_data(
            FactorTypeEnum.EXPERIENCE, exp_norm_score, configured_weights[FactorTypeEnum.EXPERIENCE],
            normalized_weights[FactorTypeEnum.EXPERIENCE], factor_applicability[FactorTypeEnum.EXPERIENCE], exp_reason
        ))

        # Education Factor
        edu_norm_score, edu_reason = cls._calculate_education_factor_score(edu_reqs)
        factor_scores_data.append(cls._build_factor_data(
            FactorTypeEnum.EDUCATION, edu_norm_score, configured_weights[FactorTypeEnum.EDUCATION],
            normalized_weights[FactorTypeEnum.EDUCATION], factor_applicability[FactorTypeEnum.EDUCATION], edu_reason
        ))

        # Preferred Skills Factor
        pref_norm_score, pref_reason = cls._calculate_skill_factor_score(pref_skills, "Preferred Skills")
        factor_scores_data.append(cls._build_factor_data(
            FactorTypeEnum.PREFERRED_SKILLS, pref_norm_score, configured_weights[FactorTypeEnum.PREFERRED_SKILLS],
            normalized_weights[FactorTypeEnum.PREFERRED_SKILLS], factor_applicability[FactorTypeEnum.PREFERRED_SKILLS], pref_reason
        ))

        # Other Requirements Factor
        other_norm_score, other_reason = cls._calculate_other_factor_score(other_reqs)
        factor_scores_data.append(cls._build_factor_data(
            FactorTypeEnum.OTHER_REQUIREMENTS, other_norm_score, configured_weights[FactorTypeEnum.OTHER_REQUIREMENTS],
            normalized_weights[FactorTypeEnum.OTHER_REQUIREMENTS], factor_applicability[FactorTypeEnum.OTHER_REQUIREMENTS], other_reason
        ))

        # 5. Overall Candidate Score Calculation
        overall_score = sum(f["weighted_contribution"] for f in factor_scores_data)
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)

        # 6. Score Confidence Calculation
        all_confidences = [rm.confidence for rm in req_matches if rm.confidence is not None]
        all_confidences.extend([sm.similarity_score for sm in sem_matches if sm.similarity_score is not None])
        
        avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.85
        avg_conf = round(max(0.0, min(1.0, avg_conf)), 2)

        if avg_conf >= 0.85:
            conf_tier = ConfidenceTierEnum.HIGH
        elif avg_conf >= 0.65:
            conf_tier = ConfidenceTierEnum.MEDIUM
        else:
            conf_tier = ConfidenceTierEnum.LOW

        return {
            "overall_score": overall_score,
            "eligibility_status": eligibility_status,
            "score_confidence": avg_conf,
            "confidence_tier": conf_tier,
            "factor_scores": factor_scores_data,
            "hard_requirement_results": hard_results,
        }

    @staticmethod
    def _build_factor_data(
        factor_type: FactorTypeEnum,
        normalized_score: float,
        configured_weight: float,
        normalized_weight: float,
        applicable: bool,
        reason: str,
    ) -> Dict[str, Any]:
        raw_score = round(normalized_score * 100.0, 1)
        weighted_contrib = round(normalized_score * normalized_weight * 100.0, 1) if applicable else 0.0

        return {
            "factor_type": factor_type,
            "raw_score": raw_score,
            "normalized_score": round(normalized_score, 3),
            "configured_weight": round(configured_weight, 3),
            "normalized_weight": round(normalized_weight, 3),
            "weighted_contribution": weighted_contrib,
            "applicable": applicable,
            "reason": reason,
            "confidence": 0.90 if applicable else 1.0,
        }

    @staticmethod
    def _calculate_skill_factor_score(skills: List[CandidateRequirementMatch], label: str) -> Tuple[float, str]:
        if not skills:
            return 0.0, f"No {label.lower()} specified for job requisition."

        matched_weight = 0.0
        for s in skills:
            if s.match_status == MatchStatusEnum.MATCHED:
                matched_weight += 1.0
            elif s.match_status == MatchStatusEnum.PARTIALLY_MATCHED:
                matched_weight += 0.5
            elif s.match_status == MatchStatusEnum.UNKNOWN:
                matched_weight += 0.0
            else:
                matched_weight += 0.0

        score = matched_weight / len(skills)
        matched_count = sum(1 for s in skills if s.match_status == MatchStatusEnum.MATCHED)
        reason = f"{matched_count}/{len(skills)} {label.lower()} matched."
        return score, reason

    @staticmethod
    def _calculate_semantic_factor_score(sem_matches: List[CandidateSemanticMatch]) -> Tuple[float, str]:
        if not sem_matches:
            return 0.0, "No semantic context embeddings available."

        sim_sum = sum(sm.similarity_score for sm in sem_matches if sm.similarity_score is not None)
        score = sim_sum / len(sem_matches)
        score = max(0.0, min(1.0, score))
        reason = f"Average pgvector semantic similarity across {len(sem_matches)} context pairs is {round(score, 3)}."
        return score, reason

    @staticmethod
    def _calculate_experience_factor_score(exp_reqs: List[CandidateRequirementMatch]) -> Tuple[float, str]:
        if not exp_reqs:
            return 1.0, "No explicit experience requirements specified."

        scores = []
        for req in exp_reqs:
            if req.match_status == MatchStatusEnum.MATCHED:
                scores.append(1.0)
            elif req.match_status == MatchStatusEnum.PARTIALLY_MATCHED:
                scores.append(0.7)
            elif req.match_status == MatchStatusEnum.UNKNOWN:
                scores.append(0.5)
            else:
                scores.append(0.0)

        score = sum(scores) / len(scores)
        reason = f"Evaluated {len(exp_reqs)} experience requirement(s)."
        return score, reason

    @staticmethod
    def _calculate_education_factor_score(edu_reqs: List[CandidateRequirementMatch]) -> Tuple[float, str]:
        if not edu_reqs:
            return 1.0, "No explicit education requirements specified."

        scores = []
        for req in edu_reqs:
            if req.match_status == MatchStatusEnum.MATCHED:
                scores.append(1.0)
            elif req.match_status == MatchStatusEnum.PARTIALLY_MATCHED:
                scores.append(0.5)
            elif req.match_status == MatchStatusEnum.UNKNOWN:
                scores.append(0.5) # Neutral for unknown education
            else:
                scores.append(0.0)

        score = sum(scores) / len(scores)
        reason = f"Evaluated {len(edu_reqs)} education requirement(s)."
        return score, reason

    @staticmethod
    def _calculate_other_factor_score(other_reqs: List[CandidateRequirementMatch]) -> Tuple[float, str]:
        if not other_reqs:
            return 1.0, "No other requirements specified."

        scores = []
        for req in other_reqs:
            if req.match_status == MatchStatusEnum.MATCHED:
                scores.append(1.0)
            elif req.match_status == MatchStatusEnum.PARTIALLY_MATCHED:
                scores.append(0.5)
            elif req.match_status == MatchStatusEnum.UNKNOWN:
                scores.append(0.5)
            else:
                scores.append(0.0)

        score = sum(scores) / len(scores)
        reason = f"Evaluated {len(other_reqs)} other requirement(s)."
        return score, reason
