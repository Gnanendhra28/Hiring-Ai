from app.infrastructure.parsing.section_parser import JobSectionParser
from app.infrastructure.validation.job_intelligence_validator import JobIntelligenceValidator

# Job 1: Real-World Generative AI Engineer Job Posting
JOB_1_TITLE = "Generative AI Engineer"
JOB_1_TEXT = """
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

Responsibilities:
Build and deploy generative AI applications
Develop prompt engineering and RAG pipelines
Experiment with foundation models
Implement LLM evaluation frameworks
Optimize inference latency, token usage, and application cost
"""

# Job 2: Frontend Lead Engineer Job Posting
JOB_2_TITLE = "Frontend Lead Engineer"
JOB_2_TEXT = """
Required Key Skills:
React
TypeScript
Next.js
Tailwind CSS
HTML5

Preferred Qualifications & Skills:
GraphQL
Redux
Vitest

Good to Have Knowledge:
WebAssembly
Docker

Experience:
5+ years

Education:
B.Tech in Computer Science
"""

# Job 3: Cloud Data Engineer Job Posting
JOB_3_TITLE = "Cloud Data Engineer"
JOB_3_TEXT = """
Required Key Skills:
SQL
Apache Spark
Apache Airflow
Snowflake
Python

Preferred Qualifications & Skills:
Databricks
dbt

Good to Have Knowledge:
Terraform

Experience:
3-5 years

Education:
Bachelor's degree
"""

def test_job_1_generative_ai_accurate_extraction():
    sections = JobSectionParser.parse_sections(JOB_1_TEXT)

    raw_reqs = [
        {"raw_value": "Python", "requirement_level": "REQUIRED", "evidence_text": "Python"},
        {"raw_value": "LLMs", "requirement_level": "REQUIRED", "evidence_text": "LLMs"},
        {"raw_value": "Generative AI", "requirement_level": "REQUIRED", "evidence_text": "Generative AI"},
        {"raw_value": "Prompt Engineering", "requirement_level": "REQUIRED", "evidence_text": "Prompt Engineering"},
        {"raw_value": "Transformers", "requirement_level": "REQUIRED", "evidence_text": "Transformers"},
        {"raw_value": "RAG", "requirement_level": "REQUIRED", "evidence_text": "RAG"},
        {"raw_value": "Hugging Face", "requirement_level": "PREFERRED", "evidence_text": "Hugging Face"},
        {"raw_value": "PyTorch", "requirement_level": "PREFERRED", "evidence_text": "PyTorch"},
        {"raw_value": "LangChain", "requirement_level": "PREFERRED", "evidence_text": "LangChain"},
        {"raw_value": "Vector Databases", "requirement_level": "PREFERRED", "evidence_text": "Vector Databases"},
        {"raw_value": "FastAPI", "requirement_level": "PREFERRED", "evidence_text": "FastAPI"},
        {"raw_value": "Fine-tuning", "requirement_level": "NICE_TO_HAVE", "evidence_text": "Fine-tuning"},
        {"raw_value": "LoRA", "requirement_level": "NICE_TO_HAVE", "evidence_text": "LoRA"},
        {"raw_value": "Kubernetes", "requirement_level": "NICE_TO_HAVE", "evidence_text": "Kubernetes"},
        {"raw_value": "AWS", "requirement_level": "NICE_TO_HAVE", "evidence_text": "AWS"},
        {"raw_value": "MLflow", "requirement_level": "NICE_TO_HAVE", "evidence_text": "MLflow"},
        # Attempt to insert un-supported hallucinated skills
        {"raw_value": "OpenCV", "requirement_level": "REQUIRED", "evidence_text": "OpenCV"},
        {"raw_value": "Computer Vision", "requirement_level": "REQUIRED", "evidence_text": "Computer Vision"},
        {"raw_value": "Deep Learning", "requirement_level": "REQUIRED", "evidence_text": "Deep Learning"},
    ]

    report = JobIntelligenceValidator.validate_and_filter_requirements(
        raw_text=JOB_1_TEXT,
        requirements=raw_reqs,
        sections=sections,
    )

    validated = report["validated_requirements"]
    validated_names = [r["canonical_value"] for r in validated]

    # Verify 7 fields extraction
    required = [r["canonical_value"] for r in validated if r["requirement_level"] == "REQUIRED"]
    preferred = [r["canonical_value"] for r in validated if r["requirement_level"] == "PREFERRED"]
    good_to_have = [r["canonical_value"] for r in validated if r["requirement_level"] == "NICE_TO_HAVE"]

    assert "Python" in required
    assert "LLMs" in required
    assert "Generative AI" in required
    assert "Prompt Engineering" in required
    assert "Transformers" in required
    assert "RAG" in required

    assert "Hugging Face" in preferred
    assert "PyTorch" in preferred
    assert "LangChain" in preferred
    assert "Vector Databases" in preferred
    assert "FastAPI" in preferred

    assert "Fine-tuning" in good_to_have
    assert "LoRA" in good_to_have
    assert "Kubernetes" in good_to_have
    assert "AWS" in good_to_have
    assert "MLflow" in good_to_have

    # CRITICAL NON-HALLUCINATION ASSERTIONS: OpenCV, Computer Vision, Deep Learning MUST NOT BE PRESENT
    assert "OpenCV" not in validated_names
    assert "Computer Vision" not in validated_names
    assert "Deep Learning" not in validated_names

def test_job_2_frontend_lead_accurate_extraction():
    sections = JobSectionParser.parse_sections(JOB_2_TEXT)
    assert "REQUIRED_SKILLS" in sections
    assert "React" in sections["REQUIRED_SKILLS"]
    assert "TypeScript" in sections["REQUIRED_SKILLS"]
    assert "Next.js" in sections["REQUIRED_SKILLS"]

    raw_reqs = [
        {"raw_value": "React", "requirement_level": "REQUIRED", "evidence_text": "React"},
        {"raw_value": "TypeScript", "requirement_level": "REQUIRED", "evidence_text": "TypeScript"},
        {"raw_value": "Next.js", "requirement_level": "REQUIRED", "evidence_text": "Next.js"},
        {"raw_value": "GraphQL", "requirement_level": "PREFERRED", "evidence_text": "GraphQL"},
    ]

    report = JobIntelligenceValidator.validate_and_filter_requirements(
        raw_text=JOB_2_TEXT,
        requirements=raw_reqs,
        sections=sections,
    )
    names = [r["canonical_value"] for r in report["validated_requirements"]]

    assert "React" in names
    assert "TypeScript" in names
    assert "Next.js" in names

    # Assert Job 2 does NOT contain Job 1 skills (LLMs, RAG, PyTorch)
    assert "LLMs" not in names
    assert "RAG" not in names
    assert "PyTorch" not in names

def test_job_3_cloud_data_engineer_accurate_extraction():
    sections = JobSectionParser.parse_sections(JOB_3_TEXT)
    assert "REQUIRED_SKILLS" in sections
    assert "SQL" in sections["REQUIRED_SKILLS"]
    assert "Snowflake" in sections["REQUIRED_SKILLS"]

    raw_reqs = [
        {"raw_value": "SQL", "requirement_level": "REQUIRED", "evidence_text": "SQL"},
        {"raw_value": "Apache Spark", "requirement_level": "REQUIRED", "evidence_text": "Apache Spark"},
        {"raw_value": "Snowflake", "requirement_level": "REQUIRED", "evidence_text": "Snowflake"},
        {"raw_value": "Databricks", "requirement_level": "PREFERRED", "evidence_text": "Databricks"},
    ]

    report = JobIntelligenceValidator.validate_and_filter_requirements(
        raw_text=JOB_3_TEXT,
        requirements=raw_reqs,
        sections=sections,
    )
    names = [r["canonical_value"] for r in report["validated_requirements"]]

    assert "SQL" in names
    assert "Snowflake" in names
    assert "Databricks" in names

    # Assert Job 3 does NOT contain Job 2 or Job 1 skills (React, RAG, OpenCV)
    assert "React" not in names
    assert "RAG" not in names
    assert "OpenCV" not in names

def test_multi_job_isolation_and_no_data_leakage():
    sec_1 = JobSectionParser.parse_sections(JOB_1_TEXT)
    sec_2 = JobSectionParser.parse_sections(JOB_2_TEXT)
    sec_3 = JobSectionParser.parse_sections(JOB_3_TEXT)

    # Verify each job section text is distinct
    assert sec_1["REQUIRED_SKILLS"] != sec_2["REQUIRED_SKILLS"]
    assert sec_2["REQUIRED_SKILLS"] != sec_3["REQUIRED_SKILLS"]
    assert sec_1["REQUIRED_SKILLS"] != sec_3["REQUIRED_SKILLS"]

    # Verify no cross-job skill bleeding
    assert "React" not in sec_1["REQUIRED_SKILLS"]
    assert "RAG" not in sec_2["REQUIRED_SKILLS"]
    assert "TypeScript" not in sec_3["REQUIRED_SKILLS"]
