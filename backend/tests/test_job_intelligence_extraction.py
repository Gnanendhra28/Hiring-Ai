from app.infrastructure.parsing.section_parser import JobSectionParser
from app.infrastructure.skills.normalizer import SkillNormalizer
from app.infrastructure.validation.job_intelligence_validator import JobIntelligenceValidator

REAL_WORLD_JOB_DESCRIPTION = """
Required Key Skills:
Python
LLMs
Generative AI
Prompt Engineering
Transformers
RAG

Preferred Qualifications & Skills:
Hugging Face
PyTorch
LangChain
Vector Databases
FastAPI

Good to Have Knowledge:
Fine-tuning
LoRA
Kubernetes
AWS
MLflow

Experience:
0–3 years

Education:
Bachelor's degree in CS, AI, or related field
"""

def test_section_parser_identifies_all_sections():
    sections = JobSectionParser.parse_sections(REAL_WORLD_JOB_DESCRIPTION)
    assert "REQUIRED_SKILLS" in sections
    assert "PREFERRED_SKILLS" in sections
    assert "NICE_TO_HAVE_SKILLS" in sections
    assert "EXPERIENCE" in sections
    assert "EDUCATION" in sections

    assert "Python" in sections["REQUIRED_SKILLS"]
    assert "RAG" in sections["REQUIRED_SKILLS"]
    assert "FastAPI" in sections["PREFERRED_SKILLS"]
    assert "MLflow" in sections["NICE_TO_HAVE_SKILLS"]

def test_skill_normalization_and_taxonomy():
    assert SkillNormalizer.normalize("retrieval augmented generation") == "RAG"
    assert SkillNormalizer.normalize("retrieval-augmented generation") == "RAG"
    assert SkillNormalizer.normalize("genai") == "Generative AI"
    assert SkillNormalizer.normalize("large language models") == "LLMs"
    assert SkillNormalizer.normalize("k8s") == "Kubernetes"
    assert SkillNormalizer.normalize("aws") == "AWS"
    assert SkillNormalizer.normalize("vector db") == "Vector Databases"

def test_no_hallucinated_skills_in_extracted_job_intelligence():
    # Simulated AI Extracted Output containing valid items + hallucinated item
    extracted = [
        {"raw_value": "Python", "requirement_level": "REQUIRED", "evidence_text": "Python"},
        {"raw_value": "LLMs", "requirement_level": "REQUIRED", "evidence_text": "LLMs"},
        {"raw_value": "Generative AI", "requirement_level": "REQUIRED", "evidence_text": "Generative AI"},
        {"raw_value": "Prompt Engineering", "requirement_level": "REQUIRED", "evidence_text": "Prompt Engineering"},
        {"raw_value": "Transformers", "requirement_level": "REQUIRED", "evidence_text": "Transformers"},
        {"raw_value": "RAG", "requirement_level": "REQUIRED", "evidence_text": "RAG"},
        {"raw_value": "Hugging Face", "requirement_level": "PREFERRED", "evidence_text": "Hugging Face"},
        {"raw_value": "PyTorch", "requirement_level": "PREFERRED", "evidence_text": "PyTorch"},
        {"raw_value": "FastAPI", "requirement_level": "PREFERRED", "evidence_text": "FastAPI"},
        {"raw_value": "LoRA", "requirement_level": "NICE_TO_HAVE", "evidence_text": "LoRA"},
        {"raw_value": "MLflow", "requirement_level": "NICE_TO_HAVE", "evidence_text": "MLflow"},
        # Hallucinated skills that DO NOT exist in source text
        {"raw_value": "OpenCV", "requirement_level": "REQUIRED", "evidence_text": "OpenCV"},
        {"raw_value": "Computer Vision", "requirement_level": "REQUIRED", "evidence_text": "Computer Vision"},
        {"raw_value": "Deep Learning", "requirement_level": "REQUIRED", "evidence_text": "Deep Learning"},
    ]

    report = JobIntelligenceValidator.validate_and_filter_requirements(
        raw_text=REAL_WORLD_JOB_DESCRIPTION,
        requirements=extracted,
    )

    validated_canonicals = [r["canonical_value"] for r in report["validated_requirements"]]

    # Assert valid skills are preserved
    assert "Python" in validated_canonicals
    assert "LLMs" in validated_canonicals
    assert "Generative AI" in validated_canonicals
    assert "Prompt Engineering" in validated_canonicals
    assert "Transformers" in validated_canonicals
    assert "RAG" in validated_canonicals
    assert "FastAPI" in validated_canonicals

    # CRITICAL NON-HALLUCINATION ASSERTIONS: OpenCV, Computer Vision, Deep Learning MUST BE FILTERED OUT
    assert "OpenCV" not in validated_canonicals
    assert "Computer Vision" not in validated_canonicals
    assert "Deep Learning" not in validated_canonicals

    filtered_names = [f["raw_value"] for f in report["filtered_requirements"]]
    assert "OpenCV" in filtered_names
    assert "Computer Vision" in filtered_names
    assert "Deep Learning" in filtered_names

def test_conflict_detection_flags_legacy_unsupported_skills():
    legacy_skills = ["Python", "OpenCV", "PyTorch", "Computer Vision", "Deep Learning"]

    extracted_valid = [
        {"raw_value": "Python", "canonical_value": "Python"},
        {"raw_value": "PyTorch", "canonical_value": "PyTorch"},
        {"raw_value": "RAG", "canonical_value": "RAG"},
    ]

    report = JobIntelligenceValidator.detect_conflicts(
        existing_skills=legacy_skills,
        extracted_requirements=extracted_valid,
        raw_text=REAL_WORLD_JOB_DESCRIPTION,
    )

    assert report["has_conflicts"] is True
    conflicting_skills = [c["existing_skill"] for c in report["conflicts"]]

    assert "OpenCV" in conflicting_skills
    assert "Computer Vision" in conflicting_skills
    assert "Deep Learning" in conflicting_skills
    assert "Python" not in conflicting_skills
    assert "PyTorch" not in conflicting_skills
