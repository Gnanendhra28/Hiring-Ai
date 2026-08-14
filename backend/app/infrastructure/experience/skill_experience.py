from typing import Dict, List, Any, Tuple, Optional
from app.domains.document_intelligence.models import SkillDurationStatusEnum
from app.infrastructure.experience.calculator import ExperienceCalculator

class SkillExperienceCalculator:
    """
    Deterministic Skill-Specific Experience Calculator.
    Correlates candidate skills with structured employment experience records.
    Calculates exact skill-specific duration based on employment evidence.
    Sets skill_duration_status = UNKNOWN if exact skill-employment duration evidence is unavailable.
    """

    @classmethod
    def calculate_skill_experience(
        cls,
        raw_skill_name: str,
        canonical_skill_name: str,
        evidence_text: Optional[str],
        experiences: List[Dict[str, Any]],
    ) -> Tuple[Optional[float], SkillDurationStatusEnum]:
        if not experiences or not evidence_text:
            return None, SkillDurationStatusEnum.UNKNOWN

        matched_employment_dicts = []
        skill_term = canonical_skill_name.lower()
        raw_term = raw_skill_name.lower()

        for exp in experiences:
            exp_text = f"{exp.get('company_name', '')} {exp.get('job_title', '')} {exp.get('evidence_text', '')}".lower()
            # Check if skill is evidenced within this employment record
            if skill_term in exp_text or raw_term in exp_text:
                matched_employment_dicts.append(exp)

        if not matched_employment_dicts:
            # Skill appears only in a general skills list, summary, or project without dates
            return None, SkillDurationStatusEnum.UNKNOWN

        # Calculate deterministic non-overlapping duration across matched jobs
        exp_calc = ExperienceCalculator.calculate_total_experience(matched_employment_dicts)

        if exp_calc["total_months"] > 0:
            return exp_calc["total_years"], SkillDurationStatusEnum.DETERMINISTIC_CALCULATED

        return None, SkillDurationStatusEnum.UNKNOWN
