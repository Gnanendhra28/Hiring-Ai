import re
from typing import Any
from app.infrastructure.skills.normalizer import SkillNormalizer

class SemanticJobExtractor:
    """
    Semantic Job Description Extractor.
    Extracts Required Skills, Preferred Skills, Good to Have Skills, and Responsibilities
    from complete raw job posting text (both headed sections and unheaded paragraphs),
    binding exact source text evidence directly from the job description.
    """

    @classmethod
    def extract_semantic_intelligence(cls, raw_text: str, job_title: str | None = None) -> dict[str, Any]:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        requirements: list[dict[str, Any]] = []
        responsibilities: list[str] = []
        seen_canonical_skills: set = set()
        seen_responsibilities: set = set()

        current_mode = "REQUIRED"

        # Regex header patterns
        re_resp_header = re.compile(r"^(key\s+)?responsibilities|what\s+you'll\s+do|duties|role\s+overview|job\s+responsibilities", re.IGNORECASE)
        re_pref_header = re.compile(r"^preferred|desired\s+skills|preferred\s+experience|desirable", re.IGNORECASE)
        re_gth_header = re.compile(r"^good\s+to\s+have|nice\s+to\s+have|bonus\s+skills|optional\s+skills|bonus", re.IGNORECASE)
        re_req_header = re.compile(r"^required|mandatory\s+skills|must\s+have|core\s+skills|technical\s+skills", re.IGNORECASE)

        for line in lines:
            clean_line = re.sub(r"^[\#\*\-\•\d\.\:\s]+", "", line).strip()
            if not clean_line:
                continue

            header_candidate = clean_line.lower()

            # Check section header
            if re_resp_header.search(header_candidate):
                current_mode = "RESPONSIBILITIES"
                continue
            elif re_pref_header.search(header_candidate):
                current_mode = "PREFERRED"
                continue
            elif re_gth_header.search(header_candidate):
                current_mode = "NICE_TO_HAVE"
                continue
            elif re_req_header.search(header_candidate):
                current_mode = "REQUIRED"
                continue

            # Skip metadata headers
            if any(k in header_candidate for k in ["about the company", "work location", "date posted", "application closing"]):
                continue

            # Collect responsibilities
            if current_mode == "RESPONSIBILITIES" or any(v in header_candidate for v in ["develop", "build", "design", "train", "perform", "monitor", "collaborate", "implement", "deploy", "maintain"]):
                if len(clean_line) > 15 and clean_line not in seen_responsibilities:
                    responsibilities.append(clean_line)
                    seen_responsibilities.add(clean_line)

            # Determine line level
            line_level = current_mode if current_mode in ("REQUIRED", "PREFERRED", "NICE_TO_HAVE") else "REQUIRED"
            if "preferred" in header_candidate or "desirable" in header_candidate:
                line_level = "PREFERRED"
            elif "good to have" in header_candidate or "nice to have" in header_candidate or "plus" in header_candidate or "bonus" in header_candidate:
                line_level = "NICE_TO_HAVE"
            elif "must have" in header_candidate or "required" in header_candidate or "mandatory" in header_candidate:
                line_level = "REQUIRED"

            # Match taxonomy aliases in line
            for alias, canonical in SkillNormalizer.CANONICAL_ALIASES.items():
                if len(alias) <= 2 and not re.search(r'\b' + re.escape(alias) + r'\b', header_candidate):
                    continue
                if alias in header_candidate:
                    if canonical.lower() not in seen_canonical_skills:
                        seen_canonical_skills.add(canonical.lower())
                        requirements.append({
                            "requirement_type": "SKILL",
                            "raw_value": clean_line if len(clean_line) < 30 else alias.title(),
                            "canonical_value": canonical,
                            "requirement_level": line_level,
                            "hard_constraint": (line_level == "REQUIRED"),
                            "priority": "HIGH" if line_level == "REQUIRED" else "MEDIUM",
                            "confidence": 0.95,
                            "evidence_text": line,
                        })

        return {
            "requirements": requirements,
            "responsibilities": responsibilities,
        }
