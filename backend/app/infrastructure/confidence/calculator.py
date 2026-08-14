from typing import Dict, Any

class ConfidenceCalculator:
    """
    Independent Confidence Calibration Engine.
    Combines LLM confidence, text extraction quality, evidence quote verification,
    Pydantic schema validity, and date ordering consistency into a calibrated confidence score.
    """

    # Signal Weights (Sum to 1.0)
    WEIGHT_LLM: float = 0.30
    WEIGHT_EVIDENCE: float = 0.35
    WEIGHT_TEXT_QUALITY: float = 0.15
    WEIGHT_SCHEMA_VALIDITY: float = 0.10
    WEIGHT_DATE_CONSISTENCY: float = 0.10

    @classmethod
    def calculate_confidence(
        self,
        llm_confidence: float,
        text_quality_score: float,
        verified_evidence_ratio: float,
        schema_valid: bool = True,
        dates_valid: bool = True,
    ) -> Dict[str, Any]:
        c_llm = max(0.0, min(1.0, llm_confidence))
        s_text = max(0.0, min(1.0, text_quality_score))
        s_ev = max(0.0, min(1.0, verified_evidence_ratio))
        s_schema = 1.0 if schema_valid else 0.2
        s_date = 1.0 if dates_valid else 0.5

        final_score = (
            (c_llm * self.WEIGHT_LLM)
            + (s_ev * self.WEIGHT_EVIDENCE)
            + (s_text * self.WEIGHT_TEXT_QUALITY)
            + (s_schema * self.WEIGHT_SCHEMA_VALIDITY)
            + (s_date * self.WEIGHT_DATE_CONSISTENCY)
        )

        final_confidence = round(max(0.0, min(1.0, final_score)), 2)

        if final_confidence >= 0.85:
            tier = "HIGH"
        elif final_confidence >= 0.65:
            tier = "MEDIUM"
        elif final_confidence >= 0.40:
            tier = "LOW"
        else:
            tier = "UNVERIFIED"

        return {
            "final_confidence": final_confidence,
            "tier": tier,
            "signals": {
                "llm_confidence": c_llm,
                "text_quality_score": s_text,
                "verified_evidence_ratio": s_ev,
                "schema_valid": schema_valid,
                "dates_valid": dates_valid,
            },
        }
