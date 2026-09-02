from typing import Any
from app.infrastructure.parsing.section_parser import JobSectionParser
from app.infrastructure.skills.normalizer import SkillNormalizer

class JobIntelligenceValidator:
    """
    Validation and Conflict Detection Engine for Job Intelligence.
    Enforces evidence grounding, non-hallucination rules, categorization integrity,
    and detects conflicts between legacy/manual skills and AI-extracted evidence.
    """

    @classmethod
    def validate_and_filter_requirements(
        cls,
        raw_text: str,
        requirements: list[dict[str, Any]],
        sections: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Validates extracted requirements against raw job text.
        Filters out hallucinated requirements lacking source evidence.
        Returns validated requirements list along with validation report.
        """
        if not sections:
            sections = JobSectionParser.parse_sections(raw_text)

        raw_text_lower = raw_text.lower()

        validated_requirements: list[dict[str, Any]] = []
        filtered_out: list[dict[str, Any]] = []

        for req in requirements:
            raw_val = req.get("raw_value", "").strip()
            canonical_val = req.get("canonical_value") or SkillNormalizer.normalize(raw_val)
            evidence = req.get("evidence_text", "").strip()

            # 1. Evidence Grounding Check
            evidence_found = False
            if evidence and evidence.lower() in raw_text_lower:
                evidence_found = True
            elif raw_val and raw_val.lower() in raw_text_lower:
                evidence = raw_val
                evidence_found = True
            elif canonical_val and canonical_val.lower() in raw_text_lower:
                evidence = canonical_val
                evidence_found = True

            # Check if skill alias is in raw_text
            if not evidence_found:
                for alias, canon in SkillNormalizer.CANONICAL_ALIASES.items():
                    if canon.lower() == canonical_val.lower() and alias in raw_text_lower:
                        evidence_found = True
                        evidence = alias
                        break

            if not evidence_found:
                filtered_out.append({
                    "raw_value": raw_val,
                    "canonical_value": canonical_val,
                    "reason": "Missing source evidence in job description text.",
                })
                continue

            # Update requirement with verified evidence & canonical value
            req["evidence_text"] = evidence
            req["canonical_value"] = canonical_val
            req["evidence_verified"] = True
            validated_requirements.append(req)

        return {
            "validated_requirements": validated_requirements,
            "filtered_requirements": filtered_out,
            "total_extracted": len(requirements),
            "total_validated": len(validated_requirements),
            "validation_passed": len(filtered_out) == 0,
        }

    @classmethod
    def detect_conflicts(
        cls,
        existing_skills: list[str],
        extracted_requirements: list[dict[str, Any]],
        raw_text: str,
    ) -> dict[str, Any]:
        """
        Detects conflicts between pre-existing job skills and AI-extracted requirements.
        Identifies legacy skills that are unsupported by the actual job description text.
        """
        raw_text_lower = raw_text.lower()

        extracted_canonicals = {
            r.get("canonical_value", "").lower()
            for r in extracted_requirements
            if r.get("canonical_value")
        }

        conflicts: list[dict[str, Any]] = []

        for skill in existing_skills:
            norm_skill = SkillNormalizer.normalize(skill)
            skill_lower = skill.lower()
            norm_lower = norm_skill.lower()

            # Check if skill or its normalized alias exists in extracted requirements OR raw job text
            in_extracted = norm_lower in extracted_canonicals
            in_raw_text = (skill_lower in raw_text_lower) or (norm_lower in raw_text_lower)

            if not in_extracted and not in_raw_text:
                conflicts.append({
                    "type": "skill_mismatch",
                    "existing_skill": skill,
                    "canonical_skill": norm_skill,
                    "issue": f"Existing skill '{skill}' is not supported by evidence in the job description.",
                    "status": "UNSUPPORTED_LEGACY_SKILL",
                })

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
        }
