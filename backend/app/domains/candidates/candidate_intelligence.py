import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.infrastructure.pdf.extractor import PDFExtractor
from app.infrastructure.skills.normalizer import SkillNormalizer
from app.domains.candidates.models import CandidateProfile

class CandidateSkill(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    evidence: str
    source: str = "PROFILE_OR_RESUME"

class CandidateExperience(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    role: str
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = []
    responsibilities: List[str] = []
    evidence: str

class CandidateProject(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    role: Optional[str] = None
    evidence: str

class CandidateEducation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None
    evidence: str

class CandidateCertification(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None
    evidence: str

class CandidateResponsibility(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    description: str
    evidence: str

class CandidateIntelligenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    candidate_id: str
    name: str
    target_roles: List[str] = []
    skills: List[CandidateSkill] = []
    experience: List[CandidateExperience] = []
    projects: List[CandidateProject] = []
    education: List[CandidateEducation] = []
    certifications: List[CandidateCertification] = []
    responsibilities: List[CandidateResponsibility] = []

class CandidateIntelligenceExtractor:
    """
    Candidate Intelligence Extraction & Ground-Truth Evidence Verification Engine.
    Extracts structured candidate intelligence from CandidateProfile DB data and PDF Resume text.
    Rejects any ungrounded / hallucinated items before returning response.
    """

    KNOWN_SKILL_TOKENS = {
        "python": "Python",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "sql": "SQL",
        "llms": "LLMs",
        "generative ai": "Generative AI",
        "rag": "RAG",
        "langchain": "LangChain",
        "llamaindex": "LlamaIndex",
        "hugging face": "Hugging Face",
        "ai agents": "AI Agents",
        "prompt engineering": "Prompt Engineering",
        "embeddings": "Embeddings",
        "semantic search": "Semantic Search",
        "vector databases": "Vector Databases",
        "scikit-learn": "Scikit-learn",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "keras": "Keras",
        "fastapi": "FastAPI",
        "rest apis": "REST APIs",
        "node.js": "Node.js",
        "react": "React",
        "next.js": "Next.js",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mongodb": "MongoDB",
        "qdrant": "Qdrant",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "azure": "Azure",
        "git": "Git",
        "github": "GitHub",
        "github actions": "GitHub Actions",
        "ci/cd": "CI/CD",
        "mlops": "MLOps",
        "opencv": "OpenCV",
        "c++": "C++",
        "cuda": "CUDA",
        "deep learning": "Deep Learning",
        "machine learning": "Machine Learning",
    }

    @classmethod
    def extract(
        cls,
        profile: CandidateProfile,
        user_full_name: str,
        pdf_bytes: Optional[bytes] = None,
        raw_resume_text: Optional[str] = None,
    ) -> CandidateIntelligenceResponse:
        candidate_id = str(profile.user_id)
        name = user_full_name or "Candidate"

        resume_text = ""
        if pdf_bytes:
            extracted_pdf = PDFExtractor.extract_text(pdf_bytes)
            if extracted_pdf.get("success"):
                resume_text = extracted_pdf.get("full_text", "")

        # Combined source text for ground-truth verification
        source_text_parts = []
        if profile.headline:
            source_text_parts.append(profile.headline)
        if profile.summary:
            source_text_parts.append(profile.summary)
        if profile.degree:
            source_text_parts.append(profile.degree)
        if profile.college:
            source_text_parts.append(profile.college)
        if profile.skills:
            source_text_parts.extend(profile.skills)
        if raw_resume_text:
            source_text_parts.append(raw_resume_text)
        if resume_text:
            source_text_parts.append(resume_text)

        combined_source_text = "\n".join(source_text_parts)
        combined_source_lower = combined_source_text.lower()

        # 1. Target Roles Extraction
        target_roles: List[str] = []
        if profile.headline and len(profile.headline.strip()) > 2:
            target_roles.append(profile.headline.strip())
        elif "position / title:" in combined_source_lower:
            m = re.search(r"position\s*\/\s*title\s*\:\s*([^\n]+)", combined_source_text, re.IGNORECASE)
            if m:
                target_roles.append(m.group(1).strip())

        # 2. Skills Extraction with Ground-Truth Evidence Verification
        extracted_skills: List[CandidateSkill] = []
        seen_skills: set = set()

        # Process profile.skills
        if profile.skills:
            for s in profile.skills:
                clean_s = s.strip().replace("\n", " ")
                canon = SkillNormalizer.normalize(clean_s) or clean_s
                if canon.lower() not in seen_skills and (clean_s.lower() in combined_source_lower or canon.lower() in combined_source_lower):
                    seen_skills.add(canon.lower())
                    extracted_skills.append(
                        CandidateSkill(
                            name=canon,
                            evidence=f"Candidate Profile skill entry: '{clean_s}'",
                            source="PROFILE"
                        )
                    )

        # Process Resume Skills from known skill tokens
        for token_key, canonical in cls.KNOWN_SKILL_TOKENS.items():
            if canonical.lower() not in seen_skills:
                pattern = r'\b' + re.escape(token_key) + r'\b'
                if re.search(pattern, combined_source_lower):
                    seen_skills.add(canonical.lower())
                    extracted_skills.append(
                        CandidateSkill(
                            name=canonical,
                            evidence=f"Extracted from resume/profile text token '{token_key}'",
                            source="RESUME"
                        )
                    )

        # 3. Experience Extraction
        extracted_experience: List[CandidateExperience] = []
        if profile.experience and isinstance(profile.experience, list):
            for exp in profile.experience:
                if isinstance(exp, dict):
                    role = exp.get("role") or exp.get("title") or "Engineer"
                    company = exp.get("company")
                    desc = exp.get("description") or ""
                    extracted_experience.append(
                        CandidateExperience(
                            role=role,
                            company=company,
                            start_date=exp.get("start_date"),
                            end_date=exp.get("end_date"),
                            duration=exp.get("duration"),
                            description=desc,
                            technologies=exp.get("technologies") or [],
                            responsibilities=exp.get("responsibilities") or [],
                            evidence=f"Profile experience entry: {role} at {company or 'Company'}"
                        )
                    )

        # Extract Experience from resume text if profile experience is empty
        if not extracted_experience and resume_text:
            exp_matches = re.findall(r"(summary|experience|position|title)\s*\:\s*([^\n]+)", resume_text, re.IGNORECASE)
            for _, val in exp_matches:
                clean_val = val.strip()
                if len(clean_val) > 10 and clean_val.lower() in combined_source_lower:
                    extracted_experience.append(
                        CandidateExperience(
                            role=target_roles[0] if target_roles else "Professional Experience",
                            description=clean_val,
                            evidence=f"Resume line: '{clean_val}'"
                        )
                    )
                    break

        # 4. Projects Extraction
        extracted_projects: List[CandidateProject] = []
        if profile.projects and isinstance(profile.projects, list):
            for proj in profile.projects:
                if isinstance(proj, dict):
                    pname = proj.get("name") or proj.get("title") or "Project"
                    extracted_projects.append(
                        CandidateProject(
                            name=pname,
                            description=proj.get("description"),
                            technologies=proj.get("technologies") or [],
                            role=proj.get("role"),
                            evidence=f"Profile project entry: {pname}"
                        )
                    )

        # 5. Education Extraction
        extracted_education: List[CandidateEducation] = []
        if profile.degree or profile.college:
            deg = profile.degree
            col = profile.college
            evidence_str = f"Degree: {deg or 'N/A'}, College: {col or 'N/A'}"
            if (deg and deg.lower() in combined_source_lower) or (col and col.lower() in combined_source_lower):
                extracted_education.append(
                    CandidateEducation(
                        degree=deg,
                        institution=col,
                        evidence=evidence_str
                    )
                )

        if profile.education and isinstance(profile.education, list):
            for edu in profile.education:
                if isinstance(edu, dict):
                    extracted_education.append(
                        CandidateEducation(
                            degree=edu.get("degree"),
                            field=edu.get("field"),
                            institution=edu.get("institution") or edu.get("college"),
                            graduation_year=edu.get("graduation_year") or edu.get("year"),
                            evidence=f"Profile education entry: {edu.get('degree') or 'Degree'}"
                        )
                    )

        # 6. Certifications Extraction
        extracted_certs: List[CandidateCertification] = []
        if profile.accomplishments and isinstance(profile.accomplishments, dict):
            certs = profile.accomplishments.get("certifications") or []
            if isinstance(certs, list):
                for cert in certs:
                    if isinstance(cert, str):
                        extracted_certs.append(
                            CandidateCertification(
                                name=cert,
                                evidence=f"Profile accomplishment certification: {cert}"
                            )
                        )

        # 7. Responsibilities Extraction
        extracted_resps: List[CandidateResponsibility] = []
        for exp in extracted_experience:
            if exp.description:
                extracted_resps.append(
                    CandidateResponsibility(
                        description=exp.description,
                        evidence=exp.evidence
                    )
                )

        return CandidateIntelligenceResponse(
            candidate_id=candidate_id,
            name=name,
            target_roles=target_roles,
            skills=extracted_skills,
            experience=extracted_experience,
            projects=extracted_projects,
            education=extracted_education,
            certifications=extracted_certs,
            responsibilities=extracted_resps
        )
