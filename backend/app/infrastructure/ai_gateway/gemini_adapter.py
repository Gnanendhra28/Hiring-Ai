import asyncio
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.ai_gateway.base import (
    AIGatewayProvider,
    AIResultEnvelope,
    CandidateExtractionSchema,
    JobAIResultEnvelope,
    JobExtractionSchema,
)

class GeminiAIGatewayAdapter(AIGatewayProvider):
    """
    Production Google Gemini AI Gateway Adapter using REST API,
    structured output validation, timeouts, cost tracking, and fail-fast credentials.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or settings.AI_API_KEY
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

        env = settings.APP_ENV.lower().strip()
        if env in ("staging", "production"):
            if not self.api_key or self.api_key in (
                "placeholder_gemini_api_key",
                "placeholder_ai_api_key",
                "secret",
                "change_me",
            ):
                raise ValueError(
                    f"CRITICAL CONFIGURATION ERROR: GEMINI_API_KEY is missing or invalid in {env.upper()} environment."
                )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> Dict[str, Any]:
        """
        Executes Google Gemini REST API generateContent call for narrative recommendations & explanations.
        Includes bounded retries with exponential backoff for transient errors (429, 500, 502, 503, 504, timeouts).
        Fails fast immediately for permanent client errors (400, 401, 403, 404).
        """
        logger.info(f"[Gemini AI Gateway] Executing chat completion via model={self.model}")

        system_instruction = ""
        user_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = content
            else:
                user_parts.append(content)

        prompt_text = "\n".join(user_parts)
        if system_instruction:
            prompt_text = f"System Instruction: {system_instruction}\n\n{prompt_text}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
        max_attempts = 3
        attempt = 0
        backoff_base = 0.1  # Initial backoff: 0.1s, 0.2s

        while attempt < max_attempts:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        text_out = ""
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text_out = parts[0].get("text", "").strip()

                        usage = data.get("usageMetadata", {})
                        input_tokens = usage.get("promptTokenCount", len(prompt_text) // 4)
                        output_tokens = usage.get("candidatesTokenCount", len(text_out) // 4)

                        # Gemini pricing estimate
                        cost = (input_tokens * 0.000075 / 1000) + (output_tokens * 0.00030 / 1000)

                        try:
                            from app.core.metrics import metrics
                            metrics.increment("ai_provider_calls_total", labels={"provider": "GEMINI", "status": "success"})
                            metrics.increment("ai_tokens_total", value=input_tokens, labels={"provider": "GEMINI", "type": "input"})
                            metrics.increment("ai_tokens_total", value=output_tokens, labels={"provider": "GEMINI", "type": "output"})
                            metrics.increment("ai_estimated_cost_usd_total", value=cost, labels={"provider": "GEMINI"})
                        except Exception:
                            pass

                        return {
                            "content": text_out,
                            "model": self.model,
                            "provider": "GEMINI",
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "estimated_cost": round(cost, 6),
                        }

                    if resp.status_code in TRANSIENT_STATUS_CODES:
                        if attempt < max_attempts:
                            delay = backoff_base * (2 ** (attempt - 1))
                            logger.warning(
                                f"[Gemini AI Gateway] Transient error {resp.status_code} (Attempt {attempt}/{max_attempts}). "
                                f"Retrying in {delay:.2f}s..."
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(f"[Gemini AI Gateway] Max retries exhausted ({max_attempts}) for status {resp.status_code}.")
                            raise RuntimeError(f"Gemini API call failed with status {resp.status_code}: {resp.text}")

                    # Permanent client error (400, 401, 403, 404, etc.) -> DO NOT RETRY!
                    logger.error(f"[Gemini AI Gateway] Permanent client error status {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"Gemini API call failed with status {resp.status_code}: {resp.text}")

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                if attempt < max_attempts:
                    delay = backoff_base * (2 ** (attempt - 1))
                    logger.warning(
                        f"[Gemini AI Gateway] Network/timeout exception (Attempt {attempt}/{max_attempts}): {net_err}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"[Gemini AI Gateway] Max retries exhausted ({max_attempts}) for network error: {net_err}")
                    raise RuntimeError(f"Gemini API network error after {max_attempts} attempts: {str(net_err)}")

        raise RuntimeError("Gemini API call failed: Max attempts reached.")



    async def extract_candidate_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> AIResultEnvelope:
        logger.info(f"[Gemini AI Gateway] Processing candidate extraction via model={self.model}")
        truncated_text = text[: settings.AI_MAX_INPUT_TOKENS * 4]

        system_prompt = (
            "You are an expert candidate document intelligence extractor. Extract structured skills, experiences, "
            "educations, and facts from the resume text. Return valid JSON matching the CandidateExtractionSchema."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Resume Text:\n{truncated_text}"},
        ]

        result = await self.chat_completion(messages, temperature=0.1, max_tokens=settings.AI_MAX_OUTPUT_TOKENS)
        raw_json = result.get("content", "{}")

        # Parse output JSON into Pydantic schema
        try:
            extraction = CandidateExtractionSchema.model_validate_json(raw_json)
        except Exception:
            # Try finding JSON block if formatted in markdown ```json ... ```
            if "```json" in raw_json:
                json_str = raw_json.split("```json")[1].split("```")[0].strip()
                extraction = CandidateExtractionSchema.model_validate_json(json_str)
            else:
                extraction = CandidateExtractionSchema()

        return AIResultEnvelope(
            extraction=extraction,
            model_used=self.model,
            provider="GEMINI",
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            estimated_cost=result.get("estimated_cost", 0.0),
            escalation_triggered=force_strong_model,
        )

    async def extract_job_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> JobAIResultEnvelope:
        logger.info(f"[Gemini AI Gateway] Processing job extraction via model={self.model}")
        truncated_text = text[: settings.AI_MAX_INPUT_TOKENS * 4]

        system_prompt = (
            "You are an expert job requirement extractor. Extract structured skills, experience requirements, "
            "education, certifications, work mode, responsibilities, and intent. Return valid JSON matching JobExtractionSchema."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Job Posting Text:\n{truncated_text}"},
        ]

        result = await self.chat_completion(messages, temperature=0.1, max_tokens=settings.AI_MAX_OUTPUT_TOKENS)
        raw_json = result.get("content", "{}")

        try:
            extraction = JobExtractionSchema.model_validate_json(raw_json)
        except Exception:
            if "```json" in raw_json:
                json_str = raw_json.split("```json")[1].split("```")[0].strip()
                extraction = JobExtractionSchema.model_validate_json(json_str)
            else:
                extraction = JobExtractionSchema()

        return JobAIResultEnvelope(
            extraction=extraction,
            model_used=self.model,
            provider="GEMINI",
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            estimated_cost=result.get("estimated_cost", 0.0),
            escalation_triggered=force_strong_model,
        )
