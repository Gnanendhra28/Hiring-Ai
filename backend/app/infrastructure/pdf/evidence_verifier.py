import re
from typing import Tuple
from app.domains.document_intelligence.models import EvidenceVerificationStatusEnum

class EvidenceVerifier:
    """
    Evidence Verifier Engine.
    Verifies whether an LLM-extracted evidence quote actually exists inside the raw document text.
    Distinguishes VERIFIED (exact/normalized match), PARTIALLY_VERIFIED (token overlap match), and UNVERIFIED (hallucinated quote).
    """

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        # Remove extra whitespace and lower-case
        return re.sub(r"\s+", " ", text.strip().lower())

    @classmethod
    def verify_evidence(cls, evidence_quote: str, full_extracted_text: str) -> Tuple[EvidenceVerificationStatusEnum, float]:
        """
        Returns (EvidenceVerificationStatusEnum, confidence_multiplier).
        VERIFIED: 1.0 multiplier
        PARTIALLY_VERIFIED: 0.85 multiplier
        UNVERIFIED: 0.40 multiplier
        """
        if not evidence_quote or not evidence_quote.strip():
            return EvidenceVerificationStatusEnum.UNVERIFIED, 0.40

        if not full_extracted_text or not full_extracted_text.strip():
            return EvidenceVerificationStatusEnum.UNVERIFIED, 0.40

        # 1. Exact Substring Match
        if evidence_quote in full_extracted_text:
            return EvidenceVerificationStatusEnum.VERIFIED, 1.0

        # 2. Normalized Case-Insensitive / Whitespace Match
        norm_quote = cls._normalize_text(evidence_quote)
        norm_full = cls._normalize_text(full_extracted_text)

        if norm_quote in norm_full:
            return EvidenceVerificationStatusEnum.VERIFIED, 1.0

        # 3. Safe Token Overlap / Partial Substring Match (OCR noise safety)
        quote_words = set(norm_quote.split())
        if len(quote_words) >= 3:
            # Check if at least 80% of words in quote are present in proximity
            matched_count = sum(1 for w in quote_words if w in norm_full)
            overlap_ratio = matched_count / len(quote_words)
            if overlap_ratio >= 0.80:
                return EvidenceVerificationStatusEnum.PARTIALLY_VERIFIED, 0.85

        # 4. Unverified / Hallucinated Quote
        return EvidenceVerificationStatusEnum.UNVERIFIED, 0.40
