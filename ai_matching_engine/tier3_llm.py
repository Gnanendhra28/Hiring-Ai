"""
Tier 3: LLM Structured Evaluator
Prompts a Large Language Model (Gemini / OpenAI) to act as an expert technical recruiter,
evaluating Candidate vs Job Description and returning structured Pydantic output.
"""

import json
import os
import re
from typing import Optional
from dotenv import load_dotenv

from .models import CandidateProfile, JobDescription, LLMEvaluationOutput

load_dotenv()


class LLMEvaluator:
    """
    Tier 3 LLM Evaluator.
    Performs deep qualitative reasoning over skill alignment, experience seniority, and domain relevance,
    enforcing structured Pydantic validation on the output.
    """

    SYSTEM_PROMPT = """You are an expert Executive Technical Recruiter and Senior Engineering Hiring Manager.
Your task is to thoroughly evaluate a Candidate Profile against a target Job Description (JD).

Scoring Guidelines:
1. skills_score (0-100): Evaluate the match between candidate's technical skills and mandatory/preferred JD requirements.
2. experience_score (0-100): Evaluate the candidate's years of experience, seniority level, and relevant past responsibilities against the JD.
3. total_score (0-100): Holistic weighted evaluation of candidate fit for the specific role.
4. justification: A concise, executive recruiter explanation of the fit and primary strengths/gaps (strictly maximum 2 sentences).

You MUST respond strictly with a valid JSON object matching this exact schema:
{
  "total_score": <int 0-100>,
  "skills_score": <int 0-100>,
  "experience_score": <int 0-100>,
  "justification": "<concise text, max 2 sentences>"
}
"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initializes the LLM Evaluator.
        Auto-detects available API keys (Gemini / OpenAI) if provider is not explicitly set.
        """
        self.api_key = api_key
        self.provider = provider
        self.model_name = model_name

        if not self.provider:
            if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
                self.provider = "gemini"
                self.model_name = model_name or "gemini-2.5-pro"
            elif os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
                self.model_name = model_name or "gpt-4o"
            else:
                self.provider = "gemini"
                self.model_name = model_name or "gemini-2.5-pro"

    def _build_user_prompt(self, candidate: CandidateProfile, jd: JobDescription) -> str:
        """Constructs the prompt containing candidate and JD details."""
        return f"""### TARGET JOB DESCRIPTION:
Title: {jd.title}
Department: {jd.department or 'N/A'}
Required Experience: {jd.experience_required_years} years
Mandatory Skills: {', '.join(jd.required_skills)}
Preferred Skills: {', '.join(jd.preferred_skills)}
Key Responsibilities: {'; '.join(jd.responsibilities)}
Full Description:
{jd.description}

----------------------------------------

### CANDIDATE RESUME PROFILE:
Name: {candidate.name}
Headline: {candidate.headline}
Summary: {candidate.summary}
Total Experience: {candidate.experience_years} years
Skills: {', '.join(candidate.skills)}

Work Experience:
{json.dumps([w.model_dump() for w in candidate.work_history], indent=2)}

Projects:
{json.dumps([p.model_dump() for p in candidate.projects], indent=2)}

Education:
{json.dumps([e.model_dump() for e in candidate.education], indent=2)}

Evaluate the candidate against the job description now. Output JSON only.
"""

    def evaluate(self, candidate: CandidateProfile, jd: JobDescription) -> LLMEvaluationOutput:
        """
        Evaluates the candidate against the Job Description and returns structured LLMEvaluationOutput.
        """
        user_prompt = self._build_user_prompt(candidate, jd)

        # 1. Try Gemini
        if self.provider == "gemini":
            result = self._evaluate_with_gemini(user_prompt)
            if result:
                return result

        # 2. Try OpenAI
        if self.provider == "openai":
            result = self._evaluate_with_openai(user_prompt)
            if result:
                return result

        # 3. Deterministic Local Recruiter Reasoning Fallback (when offline or API key missing)
        return self._deterministic_fallback_evaluation(candidate, jd)

    def _evaluate_with_gemini(self, prompt: str) -> Optional[LLMEvaluationOutput]:
        """Calls Google Gemini API with JSON structured output."""
        api_key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name or "gemini-1.5-pro",
                system_instruction=self.SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(prompt)
            data = json.loads(response.text)
            return LLMEvaluationOutput.model_validate(data)
        except Exception as e:
            print(f"[LLMEvaluator] Gemini call failed or fell back: {e}")
            return None

    def _evaluate_with_openai(self, prompt: str) -> Optional[LLMEvaluationOutput]:
        """Calls OpenAI API with structured JSON output."""
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.beta.chat.completions.parse(
                model=self.model_name or "gpt-4o",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=LLMEvaluationOutput,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"[LLMEvaluator] OpenAI call failed or fell back: {e}")
            return None

    def _deterministic_fallback_evaluation(
        self,
        candidate: CandidateProfile,
        jd: JobDescription,
    ) -> LLMEvaluationOutput:
        """
        High-precision deterministic rule evaluator used when external LLM credentials are not configured.
        """
        # Calculate Skill Match Percentage
        cand_skills_lower = {s.lower().strip() for s in candidate.skills}
        for p in candidate.projects:
            for tech in p.technologies:
                cand_skills_lower.add(tech.lower().strip())

        matched_req = [s for s in jd.required_skills if any(s.lower() in cs for cs in cand_skills_lower)]
        matched_pref = [s for s in jd.preferred_skills if any(s.lower() in cs for cs in cand_skills_lower)]

        req_coverage = len(matched_req) / max(len(jd.required_skills), 1)
        pref_coverage = len(matched_pref) / max(len(jd.preferred_skills), 1) if jd.preferred_skills else 1.0

        skills_score = int(round(min(100.0, (req_coverage * 80.0) + (pref_coverage * 20.0))))

        # Calculate Experience Score
        exp_diff = candidate.experience_years - jd.experience_required_years
        if exp_diff >= 2:
            experience_score = 95
        elif exp_diff >= 0:
            experience_score = 88
        elif exp_diff >= -1:
            experience_score = 75
        else:
            experience_score = max(40, int(round((candidate.experience_years / max(jd.experience_required_years, 1.0)) * 80)))

        total_score = int(round((skills_score * 0.6) + (experience_score * 0.4)))

        if total_score >= 80:
            justification = f"Candidate demonstrates strong alignment with {len(matched_req)}/{len(jd.required_skills)} required skills and meets the {jd.experience_required_years}+ years experience threshold."
        elif total_score >= 60:
            justification = f"Candidate covers essential technical competencies but has partial gaps in preferred domain specializations."
        else:
            justification = f"Candidate lacks several mandatory technical requirements for the {jd.title} role."

        return LLMEvaluationOutput(
            total_score=total_score,
            skills_score=skills_score,
            experience_score=experience_score,
            justification=justification[:250],
        )
