from typing import Any
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

class OpenAIAIGatewayAdapter(AIGatewayProvider):
    """Production OpenAI AI Gateway Adapter using structured output JSON schemas, timeouts, and cost tracking."""

    def __init__(self):
        env = settings.APP_ENV.lower().strip()
        if env in ("staging", "production"):
            if not settings.AI_API_KEY or settings.AI_API_KEY in ("placeholder_ai_api_key", "secret", "change_me"):
                raise ValueError(
                    f"CRITICAL CONFIGURATION ERROR: AI_API_KEY is missing or invalid in {env.upper()} environment."
                )

    async def extract_candidate_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> AIResultEnvelope:
        model_name = settings.AI_STRONG_MODEL if force_strong_model else settings.AI_FAST_MODEL
        logger.info(f"[OpenAI AI Gateway] Processing candidate extraction via model={model_name} (force_strong={force_strong_model})")

        truncated_text = text[: settings.AI_MAX_INPUT_TOKENS * 4]
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }

        system_prompt = (
            "You are an expert candidate document intelligence extractor. Extract structured skills, experiences, "
            "educations, and facts from the resume text. Return valid JSON matching the CandidateExtractionSchema."
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume Text:\n{truncated_text}"},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API call failed with status {resp.status_code}: {resp.text}")

            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            if "mini" in model_name:
                cost = (input_tokens * 0.00015 / 1000) + (output_tokens * 0.0006 / 1000)
            else:
                cost = (input_tokens * 0.0025 / 1000) + (output_tokens * 0.010 / 1000)

            extraction = CandidateExtractionSchema.model_validate_json(raw_content)

            return AIResultEnvelope(
                extraction=extraction,
                model_used=model_name,
                provider="OPENAI",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=round(cost, 6),
                escalation_triggered=force_strong_model,
            )

    async def extract_job_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> JobAIResultEnvelope:
        model_name = settings.AI_STRONG_MODEL if force_strong_model else settings.AI_FAST_MODEL
        logger.info(f"[OpenAI AI Gateway] Processing job intelligence extraction via model={model_name} (force_strong={force_strong_model})")

        truncated_text = text[: settings.AI_MAX_INPUT_TOKENS * 4]
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }

        system_prompt = (
            "You are an expert job requisition requirement extractor. Extract structured skills, experience requirements, "
            "education, certifications, work mode, responsibilities, and job intent. Return valid JSON matching the JobExtractionSchema."
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Job Posting Text:\n{truncated_text}"},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API call failed with status {resp.status_code}: {resp.text}")

            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            if "mini" in model_name:
                cost = (input_tokens * 0.00015 / 1000) + (output_tokens * 0.0006 / 1000)
            else:
                cost = (input_tokens * 0.0025 / 1000) + (output_tokens * 0.010 / 1000)

            extraction = JobExtractionSchema.model_validate_json(raw_content)

            return JobAIResultEnvelope(
                extraction=extraction,
                model_used=model_name,
                provider="OPENAI",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=round(cost, 6),
                escalation_triggered=force_strong_model,
            )

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> dict[str, Any]:
        model_name = settings.AI_FAST_MODEL
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API call failed with status {resp.status_code}: {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = (input_tokens * 0.00015 / 1000) + (output_tokens * 0.0006 / 1000)

            return {
                "content": content,
                "model": model_name,
                "provider": "OPENAI",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": round(cost, 6),
            }

