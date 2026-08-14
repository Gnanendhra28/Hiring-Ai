import re
from typing import Dict, Any, Optional

class DeterministicJobParser:
    """
    Deterministic Requirement Parser.
    Extracts numeric experience, work modes, and education levels from job description text
    without consuming LLM tokens for simple deterministic patterns.
    """

    @classmethod
    def parse_experience_string(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Parses patterns like '3+ years', '5 years', '2-4 years', 'minimum 3 years'.
        Returns dict with minimum_value (in months), operator, and hard_constraint.
        """
        if not text:
            return None

        # Pattern: "2-4 years" or "2 to 4 years"
        range_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)\s*years?", text, re.IGNORECASE)
        if range_match:
            min_yrs = float(range_match.group(1))
            max_yrs = float(range_match.group(2))
            return {
                "operator": "RANGE",
                "minimum_value": min_yrs * 12.0,
                "maximum_value": max_yrs * 12.0,
                "unit": "MONTHS",
                "hard_constraint": True,
            }

        # Pattern: "3+ years" or "3 + years" or "at least 3 years" or "minimum 3 years"
        plus_match = re.search(r"(?:at least|minimum)?\s*(\d+)\s*\+?\s*years?", text, re.IGNORECASE)
        if plus_match:
            yrs = float(plus_match.group(1))
            return {
                "operator": "GTE",
                "minimum_value": yrs * 12.0,
                "maximum_value": None,
                "unit": "MONTHS",
                "hard_constraint": True,
            }

        return None

    @classmethod
    def parse_work_mode(cls, text: str) -> str:
        norm = text.lower() if text else ""
        if "remote" in norm:
            return "REMOTE"
        if "hybrid" in norm:
            return "HYBRID"
        if "onsite" in norm or "on-site" in norm or "office" in norm:
            return "ONSITE"
        return "UNSPECIFIED"
