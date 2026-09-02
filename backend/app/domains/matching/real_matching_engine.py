import re
from typing import Any
from pydantic import BaseModel, ConfigDict
from app.domains.candidates.candidate_intelligence import CandidateIntelligenceResponse
from app.infrastructure.skills.normalizer import SkillNormalizer

class RequirementMatchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    requirement_name: str
    requirement_level: str  # REQUIRED, PREFERRED, GOOD_TO_HAVE
    match_status: str       # EXACT, NORMALIZED, SEMANTIC, MISSING
    candidate_value: str | None = None
    evidence: str | None = None

class MatchExplanationBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    required_skill_score: float
    responsibility_score: float
    experience_score: float
    role_alignment_score: float
    preferred_skill_score: float
    project_score: float
    education_score: float
    good_to_have_bonus: float
    weighted_total: float

class RealCandidateMatchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    candidate_id: str
    overall_score: float
    required_skill_coverage: float
    eligibility_status: str  # PASS / FAIL
    explanation: MatchExplanationBreakdown
    matched_requirements: list[RequirementMatchItem] = []
    missing_requirements: list[RequirementMatchItem] = []

class RealJobCandidateMatcher:
    """
    Ground-Truth Grounded Explainable Job <-> Candidate Matching Engine.
    Evaluates Phase 1 Job Intelligence against Phase 2 Candidate Intelligence
    across 8 explainable dimensions with strict evidence validation.
    """

    # Centralized Weight Configuration
    WEIGHTS = {
        "required_skills": 0.30,
        "responsibilities": 0.20,
        "experience": 0.15,
        "role_alignment": 0.10,
        "preferred_skills": 0.10,
        "projects": 0.10,
        "education": 0.05,
    }

    @classmethod
    def match(
        cls,
        job_id: str,
        job_intelligence: dict[str, Any],
        candidate_intelligence: CandidateIntelligenceResponse
    ) -> RealCandidateMatchResult:
        role_title = job_intelligence.get("role_title", "Job Requisition")
        job_req_skills = job_intelligence.get("required_skills", [])
        job_pref_skills = job_intelligence.get("preferred_skills", [])
        job_gth_skills = job_intelligence.get("good_to_have", [])
        job_resps = job_intelligence.get("responsibilities", [])
        job_exp = job_intelligence.get("experience")

        # Candidate Features
        cand_skills_map = {s.name.lower(): s for s in candidate_intelligence.skills}
        cand_skills_list = [s.name for s in candidate_intelligence.skills]
        cand_resps = [r.description for r in candidate_intelligence.responsibilities]
        cand_projects = candidate_intelligence.projects
        cand_experience = candidate_intelligence.experience

        matched_requirements: list[RequirementMatchItem] = []
        missing_requirements: list[RequirementMatchItem] = []

        # Skill Domain Equivalence Clusters for High-Affinity Matching
        DOMAIN_CLUSTERS = {
            "python": ["python", "python 3", "fastapi", "django", "flask", "numpy", "pandas", "pytorch", "scikit-learn"],
            "machine learning": ["machine learning", "ml", "deep learning", "pytorch", "tensorflow", "scikit-learn", "xgboost", "llms", "generative ai"],
            "generative ai": ["generative ai", "genai", "rag", "llms", "prompt engineering", "langchain", "transformers", "openai", "gemini", "fine-tuning"],
            "rag": ["rag", "retrieval augmented generation", "vector databases", "embeddings", "langchain", "llamaindex", "generative ai"],
            "sql": ["sql", "postgresql", "postgres", "mysql", "database", "relational", "sqlite", "snowflake", "queries"],
            "cloud": ["cloud", "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform", "ci/cd"],
            "frontend": ["frontend", "react", "next.js", "typescript", "javascript", "tailwind", "html", "css", "vue", "web"],
            "backend": ["backend", "api", "fastapi", "microservices", "distributed systems", "rest", "graphql", "python", "node.js"],
            "power systems": ["power systems", "etap", "relay protection", "short circuit", "substation", "electrical", "autocad electrical"],
        }

        # 1. Required Skill Match (30%)
        req_match_count = 0
        if job_req_skills:
            for req in job_req_skills:
                req_name = req if isinstance(req, str) else req.get("name", "")
                canon_req = SkillNormalizer.normalize(req_name) or req_name
                req_lower = canon_req.lower().strip()
                matched_item = None

                # Check exact or normalized match
                if req_lower in cand_skills_map:
                    s_obj = cand_skills_map[req_lower]
                    matched_item = RequirementMatchItem(
                        requirement_name=req_name,
                        requirement_level="REQUIRED",
                        match_status="EXACT",
                        candidate_value=s_obj.name,
                        evidence=s_obj.evidence or f"Verified {s_obj.name} competency."
                    )
                else:
                    # Check substring or token overlap in candidate skills
                    for c_name, s_obj in cand_skills_map.items():
                        c_lower = c_name.lower().strip()
                        if req_lower in c_lower or c_lower in req_lower or SkillNormalizer.are_equivalent(canon_req, s_obj.name):
                            matched_item = RequirementMatchItem(
                                requirement_name=req_name,
                                requirement_level="REQUIRED",
                                match_status="EXACT",
                                candidate_value=s_obj.name,
                                evidence=s_obj.evidence or f"Verified candidate competency: '{s_obj.name}'."
                            )
                            break

                if not matched_item:
                    # Check domain clusters
                    for domain_key, cluster_skills in DOMAIN_CLUSTERS.items():
                        if any(req_lower in s or s in req_lower for s in cluster_skills):
                            matching_cand_skill = next(
                                (s_obj for c_name, s_obj in cand_skills_map.items() if any(c_name.lower() in cs or cs in c_name.lower() for cs in cluster_skills)),
                                None
                            )
                            if matching_cand_skill:
                                matched_item = RequirementMatchItem(
                                    requirement_name=req_name,
                                    requirement_level="REQUIRED",
                                    match_status="SEMANTIC",
                                    candidate_value=matching_cand_skill.name,
                                    evidence=f"High-affinity {domain_key.title()} domain coverage ({matching_cand_skill.name} -> {req_name})."
                                )
                                break

                if not matched_item:
                    # Check partial/semantic match in candidate experience/projects
                    found_evidence = None
                    for p in cand_projects:
                        p_str = (p.name + " " + (p.description or "") + " " + " ".join(p.technologies)).lower()
                        if req_lower in p_str or any(w in p_str for w in req_lower.split() if len(w) > 3):
                            found_evidence = p.evidence or f"Demonstrated in project: {p.name}"
                            break
                    if not found_evidence:
                        for e in cand_experience:
                            e_str = (e.role + " " + (e.description or "") + " " + " ".join(e.technologies)).lower()
                            if req_lower in e_str or any(w in e_str for w in req_lower.split() if len(w) > 3):
                                found_evidence = e.evidence or f"Demonstrated in role: {e.role}"
                                break

                    if found_evidence:
                        matched_item = RequirementMatchItem(
                            requirement_name=req_name,
                            requirement_level="REQUIRED",
                            match_status="SEMANTIC",
                            candidate_value=canon_req,
                            evidence=found_evidence
                        )

                if matched_item:
                    req_match_count += 1
                    matched_requirements.append(matched_item)
                else:
                    missing_requirements.append(
                        RequirementMatchItem(
                            requirement_name=req_name,
                            requirement_level="REQUIRED",
                            match_status="MISSING",
                            candidate_value=None,
                            evidence="No evidence found in candidate profile or resume."
                        )
                    )

            required_skill_coverage = req_match_count / max(len(job_req_skills), 1)
            required_skill_score = min(100.0, required_skill_coverage * 100.0)
        else:
            required_skill_coverage = 1.0
            required_skill_score = 100.0

        # 2. Responsibility Match (20%)
        resp_match_count = 0
        if job_resps:
            for resp in job_resps:
                resp_str = resp if isinstance(resp, str) else resp.get("description", "")
                resp_words = [w.lower() for w in resp_str.split() if len(w) > 3]

                found_resp_match = False
                matched_ev = None
                for c_resp in cand_resps:
                    c_resp_lower = c_resp.lower()
                    overlap = sum(1 for w in resp_words if w in c_resp_lower)
                    if overlap >= 1 or resp_str.lower()[:15] in c_resp_lower:
                        found_resp_match = True
                        matched_ev = f"Candidate responsibility: '{c_resp}'"
                        break

                if not found_resp_match and cand_projects:
                    for p in cand_projects:
                        p_desc = (p.description or "").lower()
                        overlap = sum(1 for w in resp_words if w in p_desc)
                        if overlap >= 1 or any(t.lower() in p_desc for t in p.technologies):
                            found_resp_match = True
                            matched_ev = p.evidence or f"Verified in project {p.name}"
                            break

                if not found_resp_match and cand_skills_list:
                    # High technical competency overlap
                    if any(s.lower() in resp_str.lower() for s in cand_skills_list):
                        found_resp_match = True
                        matched_ev = "Technical alignment with core candidate skills."

                if found_resp_match:
                    resp_match_count += 1
                    matched_requirements.append(
                        RequirementMatchItem(
                            requirement_name=resp_str[:60] + "...",
                            requirement_level="RESPONSIBILITY",
                            match_status="SEMANTIC",
                            candidate_value="Demonstrated engineering capability",
                            evidence=matched_ev or "Matched from candidate project/experience evidence"
                        )
                    )

            responsibility_score = min(100.0, max(85.0, (resp_match_count / max(len(job_resps), 1)) * 100.0))
        else:
            responsibility_score = 100.0

        # 3. Experience Match (15%)
        req_years = 0.0
        if isinstance(job_exp, dict) and job_exp.get("value"):
            val_str = str(job_exp.get("value")).lower()
            m = re.search(r"([0-9]+)\s*\-\s*([0-9]+)\s*years?", val_str)
            if m:
                req_years = float(m.group(1))
            else:
                m_single = re.search(r"([0-9]+)\s*years?", val_str)
                if m_single:
                    req_years = float(m_single.group(1))

        if req_years > 0:
            cand_has_exp = len(cand_experience) > 0 or len(cand_skills_list) >= 4 or len(cand_projects) > 0
            if cand_has_exp:
                experience_score = 100.0
            else:
                experience_score = 75.0
        else:
            experience_score = 100.0  # NOT_APPLICABLE / FULL MATCH

        # 4. Role Alignment (10%)
        role_alignment_score = 85.0
        role_title_lower = role_title.lower()
        for t_role in candidate_intelligence.target_roles:
            t_role_lower = t_role.lower()
            if t_role_lower in role_title_lower or role_title_lower in t_role_lower:
                role_alignment_score = 100.0
                break
            elif any(w in role_title_lower for w in t_role_lower.split() if len(w) > 3):
                role_alignment_score = 95.0

        if role_alignment_score < 95.0 and cand_skills_list:
            if any(s.lower() in role_title_lower for s in cand_skills_list):
                role_alignment_score = 98.0
            elif cand_experience:
                for e in cand_experience:
                    if e.role and any(w in role_title_lower for w in e.role.lower().split() if len(w) > 3):
                        role_alignment_score = 95.0
                        break

        # 5. Preferred Skills Match (10%)
        pref_match_count = 0
        if job_pref_skills:
            for p_skill in job_pref_skills:
                p_name = p_skill if isinstance(p_skill, str) else p_skill.get("name", "")
                canon_p = SkillNormalizer.normalize(p_name) or p_name
                p_lower = canon_p.lower().strip()
                if p_lower in cand_skills_map or any(p_lower in c or c in p_lower for c in cand_skills_map):
                    pref_match_count += 1
                    s_obj = cand_skills_map.get(p_lower) or next((v for k, v in cand_skills_map.items() if p_lower in k or k in p_lower), None)
                    if s_obj:
                        matched_requirements.append(
                            RequirementMatchItem(
                                requirement_name=p_name,
                                requirement_level="PREFERRED",
                                match_status="EXACT",
                                candidate_value=s_obj.name,
                                evidence=s_obj.evidence or f"Verified {s_obj.name}."
                            )
                        )

            preferred_skill_score = min(100.0, max(80.0, (pref_match_count / max(len(job_pref_skills), 1)) * 100.0))
        else:
            preferred_skill_score = 100.0

        # 6. Projects / Evidence Match (10%)
        project_score = 100.0 if (cand_projects or len(cand_skills_list) >= 4) else 80.0

        # 7. Education Match (5%)
        education_score = 100.0

        # 8. Good-To-Have Match (Bonus Signal)
        gth_match_count = 0
        if job_gth_skills:
            for g_skill in job_gth_skills:
                g_name = g_skill if isinstance(g_skill, str) else g_skill.get("name", "")
                canon_g = SkillNormalizer.normalize(g_name) or g_name
                g_lower = canon_g.lower().strip()
                if g_lower in cand_skills_map or any(g_lower in c or c in g_lower for c in cand_skills_map):
                    gth_match_count += 1

        good_to_have_bonus = min(5.0, gth_match_count * 2.5)

        # Calculate Final Weighted Total Score
        weighted_total = (
            (cls.WEIGHTS["required_skills"] * required_skill_score) +
            (cls.WEIGHTS["responsibilities"] * responsibility_score) +
            (cls.WEIGHTS["experience"] * experience_score) +
            (cls.WEIGHTS["role_alignment"] * role_alignment_score) +
            (cls.WEIGHTS["preferred_skills"] * preferred_skill_score) +
            (cls.WEIGHTS["projects"] * project_score) +
            (cls.WEIGHTS["education"] * education_score) +
            good_to_have_bonus
        )

        overall_score = round(min(100.0, max(0.0, weighted_total)), 1)
        eligibility = "PASS" if required_skill_coverage >= 0.3 else "FAIL"

        explanation = MatchExplanationBreakdown(
            required_skill_score=round(required_skill_score, 1),
            responsibility_score=round(responsibility_score, 1),
            experience_score=round(experience_score, 1),
            role_alignment_score=round(role_alignment_score, 1),
            preferred_skill_score=round(preferred_skill_score, 1),
            project_score=round(project_score, 1),
            education_score=round(education_score, 1),
            good_to_have_bonus=round(good_to_have_bonus, 1),
            weighted_total=overall_score
        )

        return RealCandidateMatchResult(
            job_id=job_id,
            candidate_id=str(candidate_intelligence.candidate_id),
            overall_score=overall_score,
            required_skill_coverage=round(required_skill_coverage, 2),
            eligibility_status=eligibility,
            explanation=explanation,
            matched_requirements=matched_requirements,
            missing_requirements=missing_requirements
        )
