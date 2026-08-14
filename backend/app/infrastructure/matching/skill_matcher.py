from typing import Dict, Any, List, Optional, Tuple
from app.domains.matching.models import MatchStatusEnum
from app.infrastructure.pdf.evidence_verifier import EvidenceVerifier
from app.infrastructure.skills.normalizer import SkillNormalizer

class SkillMatcher:
    """
    Skill & Technology Feature Matching Engine.
    Uses SkillNormalizer to map canonical skill names and enforce non-equivalency guards.
    Integrates EvidenceVerifier to validate evidence quotes against candidate document text.
    """

    @staticmethod
    def match_skill(
        raw_required_skill: str,
        canonical_required_skill: str,
        candidate_skills: List[Dict[str, Any]],
        candidate_resume_text: str = "",
        is_protected_feature: bool = False,
    ) -> Tuple[MatchStatusEnum, float, str, Optional[str], str]:
        """
        Evaluates a single skill requirement against candidate extracted skills and resume text.
        Returns (match_status, confidence, reason, evidence_quote, verification_status).
        """
        if is_protected_feature:
            return (
                MatchStatusEnum.PROTECTED_EXCLUDED,
                0.0,
                "Requirement flagged as protected feature; excluded from candidate matching.",
                None,
                "EXCLUDED",
            )

        norm_req = SkillNormalizer.normalize(canonical_required_skill or raw_required_skill)

        # 1. Exact / Canonical Match in Extracted Candidate Skills
        for cand_skill in candidate_skills:
            cand_raw = cand_skill.get("skill_name", "")
            cand_canon = SkillNormalizer.normalize(cand_raw)

            if cand_canon == norm_req:
                quote = cand_raw
                v_status, v_mult = EvidenceVerifier.verify_evidence(quote, candidate_resume_text) if candidate_resume_text else ("VERIFIED", 1.0)
                v_str = v_status.value if hasattr(v_status, "value") else str(v_status)
                return (
                    MatchStatusEnum.MATCHED,
                    round(0.95 * v_mult, 2),
                    f"Canonical skill match: '{cand_canon}' matches required '{norm_req}'.",
                    quote,
                    v_str,
                )

        # 2. Text Substring Search in Candidate Resume Text
        if candidate_resume_text:
            v_status, v_mult = EvidenceVerifier.verify_evidence(raw_required_skill, candidate_resume_text)
            v_str = v_status.value if hasattr(v_status, "value") else str(v_status)
            if v_str != "UNVERIFIED":
                return (
                    MatchStatusEnum.MATCHED,
                    round(0.85 * v_mult, 2),
                    f"Skill evidence text found in candidate resume: '{raw_required_skill}'.",
                    raw_required_skill,
                    v_str,
                )

        # 3. Absence of Evidence -> UNKNOWN (Never NOT_MATCHED)
        return (
            MatchStatusEnum.UNKNOWN,
            0.50,
            f"No candidate evidence found for skill '{norm_req}' (absence of evidence).",
            None,
            "UNVERIFIED",
        )
