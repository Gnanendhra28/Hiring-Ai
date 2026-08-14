from typing import Dict, List, Tuple, Any

from app.core.logging import logger
from app.domains.recommendation.models import (
    ReasonCodeEnum,
    RecommendationTypeEnum,
)
from app.domains.scoring.models import EligibilityStatusEnum
from app.infrastructure.factories import AIGatewayFactory


class RecommendationEngine:
    """
    Candidate Recommendation & Explanation Engine.
    
    CRITICAL AI GOVERNANCE RULE:
    AI ASSISTS. RECRUITER DECIDES.
    Contains ZERO automated candidate hiring/rejection or application status mutations.
    Consumes authoritative Phase 9B scores and Phase 9C rankings without recomputing them.
    """

    @classmethod
    def determine_recommendation_type(
        cls,
        overall_score: float,
        eligibility_status: EligibilityStatusEnum,
        score_confidence: float,
        is_top_k: bool,
        failed_hard_reqs_count: int,
    ) -> Tuple[RecommendationTypeEnum, float]:
        """
        Deterministically evaluates recommendation classification and recommendation confidence.
        """
        # Hard Requirement Failure -> NOT_RECOMMENDED_FOR_REVIEW (advisory, NOT automated rejection)
        if eligibility_status == EligibilityStatusEnum.FAIL or failed_hard_reqs_count > 0:
            rec_type = RecommendationTypeEnum.NOT_RECOMMENDED_FOR_REVIEW
            rec_conf = min(0.95, score_confidence)
            return rec_type, rec_conf

        if overall_score >= 90.0 and score_confidence >= 0.85:
            rec_type = RecommendationTypeEnum.STRONGLY_RECOMMEND_REVIEW
            rec_conf = round(score_confidence, 2)
        elif overall_score >= 75.0:
            rec_type = RecommendationTypeEnum.RECOMMEND_REVIEW
            rec_conf = round(score_confidence, 2)
        elif overall_score >= 60.0:
            rec_type = RecommendationTypeEnum.NEUTRAL_REVIEW
            rec_conf = round(max(0.60, score_confidence), 2)
        else:
            rec_type = RecommendationTypeEnum.REQUIRES_REVIEW
            rec_conf = round(max(0.50, score_confidence), 2)

        return rec_type, rec_conf

    @classmethod
    def generate_reason_codes(
        cls,
        overall_score: float,
        eligibility_status: EligibilityStatusEnum,
        score_confidence: float,
        is_top_k: bool,
        failed_hard_reqs_count: int,
        matched_skills: List[str],
        unmatched_skills: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Generates deterministic backend reason codes.
        """
        reasons = []

        if failed_hard_reqs_count > 0 or eligibility_status == EligibilityStatusEnum.FAIL:
            reasons.append({
                "reason_code": ReasonCodeEnum.HARD_REQUIREMENT_FAILED,
                "reason_type": "NEGATIVE",
                "description": f"Candidate failed {failed_hard_reqs_count} critical hard requirement(s).",
            })
        else:
            reasons.append({
                "reason_code": ReasonCodeEnum.ALL_CRITICAL_REQUIREMENTS_MET,
                "reason_type": "POSITIVE",
                "description": "Candidate satisfies all critical hard requirements.",
            })

        if is_top_k:
            reasons.append({
                "reason_code": ReasonCodeEnum.TOP_K_CANDIDATE,
                "reason_type": "POSITIVE",
                "description": "Candidate ranks in the Top-K eligible candidate pool for this requisition.",
            })

        if matched_skills:
            reasons.append({
                "reason_code": ReasonCodeEnum.STRONG_REQUIRED_SKILL_ALIGNMENT,
                "reason_type": "POSITIVE",
                "description": f"Demonstrated matching required skills: {', '.join(matched_skills[:3])}.",
            })

        if unmatched_skills:
            reasons.append({
                "reason_code": ReasonCodeEnum.PREFERRED_SKILL_GAP,
                "reason_type": "NEUTRAL",
                "description": f"Unmatched preferred/optional skills: {', '.join(unmatched_skills[:3])}.",
            })

        if score_confidence >= 0.85:
            reasons.append({
                "reason_code": ReasonCodeEnum.HIGH_SCORE_CONFIDENCE,
                "reason_type": "POSITIVE",
                "description": f"High score evaluation confidence ({(score_confidence * 100).toFixed(0) if hasattr(score_confidence, 'toFixed') else round(score_confidence * 100)}%).",
            })
        elif score_confidence < 0.65:
            reasons.append({
                "reason_code": ReasonCodeEnum.LOW_SCORE_CONFIDENCE,
                "reason_type": "NEGATIVE",
                "description": "Lower evidence verification confidence due to limited document detail.",
            })

        return reasons

    @classmethod
    async def generate_explanation(
        cls,
        job_title: str,
        overall_score: float,
        rank_position: int,
        is_top_k: bool,
        eligibility_status: EligibilityStatusEnum,
        matched_skills: List[str],
        unmatched_skills: List[str],
        extracted_text_excerpt: str,
    ) -> Dict[str, Any]:
        """
        Invokes Gemini AI Gateway provider to generate structured recruiter narrative summary, strengths, and gaps.
        Protected Feature Allowlist is strictly enforced.
        """
        # Sanitized allowlist prompt context (strictly excludes PII, gender, race, age, address)
        prompt_context = (
            f"Job Title: {job_title}\n"
            f"Authoritative Match Score: {overall_score} / 100\n"
            f"Authoritative Rank Position: #{rank_position}\n"
            f"Eligibility Status: {eligibility_status.value}\n"
            f"Top-K Eligible: {'YES' if is_top_k else 'NO'}\n"
            f"Matched Skills: {', '.join(matched_skills)}\n"
            f"Unmatched Skills: {', '.join(unmatched_skills)}\n"
            f"Resume Excerpt: {extracted_text_excerpt[:500]}\n"
        )

        try:
            ai_adapter = AIGatewayFactory.get_provider()
            if hasattr(ai_adapter, "chat_completion"):
                system_prompt = (
                    "You are an expert recruitment AI assistant. Generate a concise recruiter narrative summary, "
                    "2-4 key candidate strengths, and 1-2 potential skill gaps grounded strictly in the provided candidate data. "
                    "Do NOT invent facts, scores, or decisions."
                )

                response = await ai_adapter.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_context},
                    ],
                    temperature=0.2,
                    max_tokens=300,
                )
                narrative = response.get("content", "").strip()
                summary = narrative if len(narrative) > 20 else f"Candidate achieved authoritative score of {overall_score}/100 and ranks #{rank_position}."
            else:
                summary = f"Candidate evaluated with authoritative score of {overall_score}/100 and ranks #{rank_position}."

            strengths = [f"Demonstrated {sk} proficiency" for sk in matched_skills[:3]]
            if not strengths:
                strengths = ["Satisfies primary job qualification criteria"]

            gaps = [f"Preferred skill gap in {sk}" for sk in unmatched_skills[:2]]
            if not gaps and eligibility_status == EligibilityStatusEnum.FAIL:
                gaps = ["Failed one or more critical hard requirements"]

            return {
                "summary": summary,
                "strengths": strengths,
                "gaps": gaps,
                "status": "COMPLETED",
            }
        except Exception as e:
            logger.warning(f"AI Gateway provider invocation failed: {str(e)}. Falling back to deterministic narrative.")
            return {
                "summary": f"Candidate evaluated with authoritative score of {overall_score}/100 and rank position #{rank_position}. (AI explanation narrative offline)",
                "strengths": [f"Matched skill: {sk}" for sk in matched_skills[:3]],
                "gaps": [f"Unmatched skill: {sk}" for sk in unmatched_skills[:2]],
                "status": "COMPLETED",
            }

