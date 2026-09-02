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
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash")

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
            "educations, and facts from the resume text. Return ONLY valid JSON matching this exact structure:\n"
            "{\n"
            '  "skills": [{"skill_name": "Python", "years_experience": 5.0, "evidence_text": "Skills: Python", "confidence": 1.0}],\n'
            '  "experiences": [{"company_name": "Acme Corp", "job_title": "Senior Architect", "start_date_str": "2021-01", "end_date_str": "Present", "is_current": true, "evidence_text": "Acme Corp...", "confidence": 1.0}],\n'
            '  "educations": [{"institution": "Tech University", "degree": "BS", "field_of_study": "Computer Science", "start_date_str": "2014", "end_date_str": "2018", "evidence_text": "BS...", "confidence": 1.0}],\n'
            '  "facts": [],\n'
            '  "overall_confidence": 0.9\n'
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Resume Text:\n{truncated_text}"},
        ]

        result = await self.chat_completion(messages, temperature=0.1, max_tokens=settings.AI_MAX_OUTPUT_TOKENS)
        raw_json = result.get("content", "{}")

        # Parse output JSON into Pydantic schema
        clean_json = raw_json
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        try:
            extraction = CandidateExtractionSchema.model_validate_json(clean_json)
        except Exception as err:
            logger.warning(f"[Gemini AI Gateway] Direct CandidateExtractionSchema validation failed ({err}). Attempting repair...")
            try:
                import json
                data = json.loads(clean_json)
                if isinstance(data, dict):
                    # 1. Repair skills
                    if "skills" in data and isinstance(data["skills"], list):
                        repaired_skills = []
                        for item in data["skills"]:
                            if isinstance(item, str):
                                repaired_skills.append({"skill_name": item, "evidence_text": text[:200], "confidence": 0.9})
                            elif isinstance(item, dict):
                                s_name = item.get("skill_name") or item.get("name") or item.get("skill") or "Unknown Skill"
                                repaired_skills.append({
                                    "skill_name": str(s_name),
                                    "years_experience": item.get("years_experience"),
                                    "confidence": item.get("confidence", 0.9),
                                    "evidence_text": str(item.get("evidence_text") or text[:200]),
                                    "page_number": item.get("page_number", 1)
                                })
                        data["skills"] = repaired_skills

                    # 2. Repair experiences
                    if "experiences" in data and isinstance(data["experiences"], list):
                        repaired_exps = []
                        for item in data["experiences"]:
                            if isinstance(item, dict):
                                c_name = item.get("company_name") or item.get("company") or item.get("organization") or "Company"
                                j_title = item.get("job_title") or item.get("title") or item.get("role") or "Role"
                                s_date = str(item.get("start_date_str") or item.get("start_date") or "")
                                e_date = str(item.get("end_date_str") or item.get("end_date") or "")
                                repaired_exps.append({
                                    "company_name": str(c_name),
                                    "job_title": str(j_title),
                                    "start_date_str": s_date or None,
                                    "end_date_str": e_date or None,
                                    "is_current": bool(item.get("is_current", False)),
                                    "confidence": item.get("confidence", 0.9),
                                    "evidence_text": str(item.get("evidence_text") or text[:200]),
                                    "page_number": item.get("page_number", 1)
                                })
                        data["experiences"] = repaired_exps

                    # 3. Repair educations
                    if "educations" in data and isinstance(data["educations"], list):
                        repaired_edus = []
                        for item in data["educations"]:
                            if isinstance(item, dict):
                                inst = item.get("institution") or item.get("school") or item.get("university") or "Institution"
                                repaired_edus.append({
                                    "institution": str(inst),
                                    "degree": item.get("degree"),
                                    "field_of_study": item.get("field_of_study") or item.get("major"),
                                    "start_date_str": str(item.get("start_date_str") or item.get("start_date") or "") or None,
                                    "end_date_str": str(item.get("end_date_str") or item.get("end_date") or "") or None,
                                    "confidence": item.get("confidence", 0.9),
                                    "evidence_text": str(item.get("evidence_text") or text[:200]),
                                    "page_number": item.get("page_number", 1)
                                })
                        data["educations"] = repaired_edus

                    # 4. Repair facts
                    if "facts" in data and isinstance(data["facts"], dict):
                        repaired_facts = []
                        for k, v in data["facts"].items():
                            repaired_facts.append({
                                "fact_type": str(k),
                                "raw_value": str(v),
                                "evidence_text": text[:200],
                                "confidence": 0.9,
                                "page_number": 1
                            })
                        data["facts"] = repaired_facts

                    extraction = CandidateExtractionSchema.model_validate(data)
                else:
                    extraction = CandidateExtractionSchema()
            except Exception as repair_err:
                logger.error(f"[Gemini AI Gateway] CandidateExtractionSchema repair failed: {repair_err}")
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
            "You are a job requirement extraction engine.\n\n"
            "Extract ONLY information explicitly supported by the supplied job description.\n"
            "Never invent skills, technologies, qualifications, experience, responsibilities, or requirements.\n"
            "Never infer a skill merely because another skill is related.\n"
            "Never move a requirement between required, preferred, and nice-to-have categories.\n"
            "Preserve the meaning of the source text.\n"
            "Every extracted item must contain exact source evidence text.\n"
            "If information is not present, return an empty array/null rather than guessing.\n"
            "The original job description is the source of truth.\n\n"
            "Categorize requirements into:\n"
            "- requirement_level: REQUIRED (for required key skills / mandatory qualifications)\n"
            "- requirement_level: PREFERRED (for preferred qualifications & skills)\n"
            "- requirement_level: NICE_TO_HAVE (for good to have / nice to have knowledge)\n"
            "Return valid JSON matching JobExtractionSchema."
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
