import re
from typing import Tuple

PROTECTED_CHARACTERISTIC_PATTERNS = [
    r"\b(male|female|man|woman|gender|sex)\b",
    r"\b(race|ethnicity|skin color|caste|white|black|asian|hispanic)\b",
    r"\b(age|years old|young|elderly)\b",
    r"\b(religion|christian|muslim|hindu|jewish|buddhist|faith)\b",
    r"\b(married|single|marital status|children|family|pregnant)\b",
    r"\b(disability|handicap|health condition)\b",
]

class ProtectedFeatureFilter:
    """
    Safety & Compliance Filter.
    Scans job requirements for discriminatory or protected candidate criteria.
    Flags protected features so they are excluded from automated matching features.
    """

    @classmethod
    def evaluate(cls, requirement_text: str) -> Tuple[bool, str]:
        if not requirement_text:
            return False, ""

        norm_text = requirement_text.lower()
        for pattern in PROTECTED_CHARACTERISTIC_PATTERNS:
            if re.search(pattern, norm_text):
                return True, f"Requirement contains protected characteristic pattern: '{pattern}'"

        return False, ""
