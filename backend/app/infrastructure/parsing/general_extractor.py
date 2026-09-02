import re
from typing import Any, Dict, List, Optional
from app.infrastructure.skills.normalizer import SkillNormalizer

class GeneralJobExtractor:
    """
    Section-Aware, Semantic, and Natural-Language Evidence-Grounded Job Description Extractor.
    Extracts Role Title, Required Skills, Preferred Skills, Good to Have Skills,
    Responsibilities, Experience, and Education from ANY job description text format
    (bullet lists, numbered lists, prose paragraphs, mixed markdown, plain-text).
    """

    KNOWN_SKILL_MAP = {
        "aws": "AWS",
        "azure": "Azure",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "redis": "Redis",
        "terraform": "Terraform",
        "circleci": "CircleCI",
        "nix": "Nix",
        "docker": "Docker",
        "ruby": "Ruby",
        "rails": "Ruby on Rails",
        "ruby/rails": "Ruby on Rails",
        "python": "Python",
        "openai": "OpenAI",
        "react": "React",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "graphql": "GraphQL",
        "d3": "D3",
        "cortex": "Cortex",
        "backend": "Backend Development",
        "finance": "Finance",
        "product design": "Product Design",
        "operations": "Operations",
        "opensearch": "OpenSearch",
        "snowflake": "Snowflake",
        "langfuse": "Langfuse",
        "vector databases": "Vector Databases",
        "vector database": "Vector Databases",
        "vector dbs": "Vector Databases",
        "fintech": "Fintech",
        "compliance": "Compliance",
        "machine learning": "Machine Learning",
        "scikit-learn": "Scikit-learn",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "sql": "SQL",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "pytorch": "PyTorch",
        "mlflow": "MLflow",
        "mlops": "MLOps",
        "kubernetes": "Kubernetes",
        "airflow": "Airflow",
        "spark": "Apache Spark",
        "apache spark": "Apache Spark",
        "rag": "RAG",
        "llms": "LLMs",
        "generative ai": "Generative AI",
        "prompt engineering": "Prompt Engineering",
        "transformers": "Transformers",
        "hugging face": "Hugging Face",
        "langchain": "LangChain",
        "fastapi": "FastAPI",
        "fine-tuning": "Fine-tuning",
        "lora": "LoRA",
        "ci/cd": "CI/CD",
        "etap": "ETAP",
        "autocad electrical": "AutoCAD Electrical",
        "relay protection": "Relay Protection",
        "power systems": "Power Systems",
        "electrical distribution": "Electrical Distribution",
        "load flow analysis": "Load Flow Analysis",
        "short circuit analysis": "Short Circuit Analysis",
        "hv/mv systems": "HV/MV Systems",
        "substation design": "Substation Design",
        "protection coordination": "Protection Coordination",
        "digsilent powerfactory": "DIgSILENT PowerFactory",
        "digsilent": "DIgSILENT PowerFactory",
        "iec": "IEC Standards",
        "ieee": "IEEE Standards",
        "renewable-energy integration": "Renewable Energy Integration",
        "scada": "SCADA Systems",
        "scada systems": "SCADA Systems",
        "plcs": "PLCs",
        "industrial control networks": "Industrial Control Networks",
        "smart grid": "Smart Grid Systems",
        "grid interconnection studies": "Grid Interconnection Studies",
        "project planning": "Project Planning",
        "vendor coordination": "Vendor Coordination",
        "site commissioning": "Site Commissioning",
    }

    LEAD_IN_PATTERNS = [
        r"^candidates\s+(?:must\s+have|should\s+have|with|who\s+have)\s+(?:a\s+)?(?:strong\s+|solid\s+|hands-on\s+)?(?:experience\s+(?:in|with)\s+)?",
        r"^(?:strong\s+|solid\s+|hands-on\s+|substantial\s+)?experience\s+(?:with|in)\s+",
        r"^proficiency\s+(?:with|in)\s+",
        r"^familiarity\s+with\s+",
        r"^knowledge\s+of\s+",
        r"^understanding\s+of\s+",
        r"^exposure\s+to\s+",
        r"^working\s+with\s+",
        r"^strong\s+background\s+in\s+",
        r"^ability\s+to\s+use\s+",
        r"^prior\s+experience\s+in\s+",
        r"^prior\s+exposure\s+to\s+",
        r"^bonus\s+points\s+for\s*",
    ]

    TRAILING_SIGNAL_PATTERNS = [
        r"\s+is\s+preferred\.?$",
        r"\s+will\s+be\s+preferred\.?$",
        r"\s+is\s+desirable\.?$",
        r"\s+would\s+be\s+a\s+plus\.?$",
        r"\s+would\s+be\s+an?\s+advantage\.?$",
        r"\s+is\s+a\s+plus\.?$",
        r"\s+is\s+beneficial\.?$",
        r"\s+is\s+required\s+for\s+this\s+role\.?$",
        r"\s+is\s+required\.?$",
        r"\s+are\s+required\.?$",
        r"\s+or\s+similar\s+tools\.?$",
        r"\s+or\s+equivalent\.?$",
        r"\s+and\s+local\s+electrical\s+safety\s+standards\.?$",
    ]

    @classmethod
    def clean_phrase(cls, text: str) -> str:
        t = re.sub(r"^[\#\*\-\•\d\.\:\s]+", "", text).replace("**", "").strip()
        for pat in cls.LEAD_IN_PATTERNS:
            t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()
        for pat in cls.TRAILING_SIGNAL_PATTERNS:
            t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()
        return t

    @classmethod
    def split_phrase_into_items(cls, text: str) -> List[str]:
        cleaned = cls.clean_phrase(text)
        if not cleaned:
            return []

        # Split on conjunctions and separators
        parts = re.split(r"[,;]|\s+and\s+|\s+or\s+|\s+&\s+|\s+as\s+well\s+as\s+", cleaned, flags=re.IGNORECASE)
        results = []
        for p in parts:
            p_clean = re.sub(r"[\.\,\;]+$", "", p.strip()).strip()
            if not p_clean:
                continue
            # Remove minor lead-in leftovers
            p_clean = re.sub(r"^(with|in|of|to)\s+", "", p_clean, flags=re.IGNORECASE).strip()

            low_p = p_clean.lower()

            # Find multi-token spans if space/slash separated
            matched_spans = []
            for token_key, canonical in cls.KNOWN_SKILL_MAP.items():
                pattern = r'\b' + re.escape(token_key) + r'\b'
                for match in re.finditer(pattern, low_p):
                    matched_spans.append((match.start(), match.end(), canonical))

            if matched_spans:
                matched_spans.sort(key=lambda x: x[0])
                for _, _, canon in matched_spans:
                    if canon not in results:
                        results.append(canon)
            elif low_p in cls.KNOWN_SKILL_MAP:
                results.append(cls.KNOWN_SKILL_MAP[low_p])
            elif len(p_clean) < 50 and not any(k in low_p for k in ["responsible", "date posted", "equal opportunity", "bengaluru", "location", "openings"]):
                norm = SkillNormalizer.normalize(p_clean) or p_clean.title()
                results.append(norm)

        return results

    @classmethod
    def extract(cls, raw_text: str, job_title: Optional[str] = None) -> Dict[str, Any]:
        # Split raw text into sentences and lines
        raw_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        sentences: List[tuple[str, str]] = []
        for l in raw_lines:
            sub_s = re.split(r"(?<=[.!?])\s+", l.strip())
            for s in sub_s:
                if s.strip():
                    sentences.append((s.strip(), l.strip()))

        required_skills: List[Dict[str, Any]] = []
        preferred_skills: List[Dict[str, Any]] = []
        good_to_have: List[Dict[str, Any]] = []
        responsibilities: List[Dict[str, Any]] = []
        education_list: List[Dict[str, Any]] = []
        experience_info: Optional[Dict[str, Any]] = None

        seen_required: set = set()
        seen_preferred: set = set()
        seen_good: set = set()
        seen_resps: set = set()

        current_mode = "INTRO"

        re_resp_header = re.compile(
            r"^(key\s+)?responsibilities|what\s+you'll\s+do|duties|role\s+overview|job\s+responsibilities",
            re.IGNORECASE,
        )
        re_pref_header = re.compile(
            r"^preferred\s+qualifications\s*&\s*skills|^preferred\s+qualifications|^preferred\s+skills|^desired\s+skills|^preferred\s+experience|^desirable|^ideal\s+candidate|^you'd\s+be\s+a\s+great\s+fit",
            re.IGNORECASE,
        )
        re_gth_header = re.compile(
            r"^good\s+to\s+have\s+knowledge|^good\s+to\s+have|^nice\s+to\s+have|^bonus\s+skills|^optional\s+skills|^bonus|^additional\s+skills|^it\s+would\s+be\s+great\s+if",
            re.IGNORECASE,
        )
        re_req_header = re.compile(
            r"^required\s+key\s+skills|^required\s+qualifications|^required\s+skills|^mandatory\s+skills|^must\s+have|^core\s+skills|^technical\s+skills|^requirements|^minimum\s+qualifications|^essential\s+skills",
            re.IGNORECASE,
        )
        re_edu_header = re.compile(r"^education|^academic\s+background|^degrees?", re.IGNORECASE)
        re_meta_header = re.compile(
            r"^about\s+the\s+company|^work\s+location|^schedule|^location|^number\s+of\s+openings|^openings|^date\s+posted|^closing\s+date",
            re.IGNORECASE,
        )

        for sentence, orig_line in sentences:
            clean_line = re.sub(r"^[\#\*\-\•\d\.\:\s]+", "", sentence).replace("**", "").strip()
            if not clean_line:
                continue

            header_candidate = clean_line.lower()

            # Experience Extraction
            exp_match = re.search(
                r"(required\s+experience\s*\:\s*([0-9\-\+\s\w]+years?)|([0-9]\-[0-9]\s*years?|[0-9]+\+?\s*years?|minimum\s+[0-9]+\s*years?|at\s+least\s+[0-9]+\s*years?))",
                clean_line,
                re.IGNORECASE,
            )
            if exp_match and not experience_info:
                val = exp_match.group(2) if exp_match.group(2) else exp_match.group(1)
                experience_info = {"value": val.strip(), "evidence": orig_line}

            # Education Extraction
            edu_match = re.search(
                r"((?:bachelor'?s|master'?s|ph\.?d|degree|b\.?s|m\.?s|b\.?e|m\.?e|b\.?tech|m\.?tech)\s+(?:degree\s+)?(?:in\s+)?([a-z\s]+))",
                clean_line,
                re.IGNORECASE,
            )
            if edu_match and not any(e["evidence"] == orig_line for e in education_list):
                education_list.append({"name": edu_match.group(1).strip().title(), "evidence": orig_line})

            # Header Detection
            if re_resp_header.search(header_candidate):
                current_mode = "RESPONSIBILITIES"
            elif re_pref_header.search(header_candidate):
                current_mode = "PREFERRED"
            elif re_gth_header.search(header_candidate):
                current_mode = "NICE_TO_HAVE"
            elif re_req_header.search(header_candidate):
                current_mode = "REQUIRED"
            elif re_edu_header.search(header_candidate):
                current_mode = "EDUCATION"
            elif re_meta_header.search(header_candidate):
                current_mode = "METADATA"
                continue

            if current_mode == "METADATA":
                continue

            # Pure Header Check (skip lines that are only section titles)
            is_pure_header = len(clean_line) < 45 and not any(k in header_candidate for k in ["experience", "opensearch", "python", "aws", "sql", "etap"]) and (
                clean_line.endswith(":") or clean_line.startswith("#") or clean_line.startswith("*") or header_candidate.replace(":", "").strip() in [
                    "required key skills", "required skills", "preferred qualifications & skills", "preferred qualifications", "preferred skills",
                    "good to have knowledge", "good to have", "nice to have", "key responsibilities", "responsibilities"
                ]
            )
            if is_pure_header:
                continue

            # Responsibilities Collection
            if current_mode == "RESPONSIBILITIES":
                if len(clean_line) > 15 and clean_line.lower() not in seen_resps:
                    seen_resps.add(clean_line.lower())
                    responsibilities.append({
                        "description": clean_line,
                        "evidence": orig_line,
                        "source_section": "Key Responsibilities",
                    })
                continue

            # Skill Collection for SKILL sections & Natural Language Signals
            effective_level = current_mode
            low_line = clean_line.lower()

            if (
                "will be preferred" in low_line
                or "is preferred" in low_line
                or "is desirable" in low_line
                or "preference" in low_line
                or "desirable" in low_line
                or "would be preferred" in low_line
            ):
                effective_level = "PREFERRED"
            elif (
                "would be a plus" in low_line
                or "is a plus" in low_line
                or "good to have" in low_line
                or "nice to have" in low_line
                or "bonus" in low_line
                or "advantage" in low_line
                or "beneficial" in low_line
                or "optional" in low_line
            ):
                effective_level = "NICE_TO_HAVE"
            elif "must have" in low_line or "is required" in low_line or "mandatory" in low_line or "essential" in low_line:
                if effective_level not in ("PREFERRED", "NICE_TO_HAVE"):
                    effective_level = "REQUIRED"

            if effective_level in ("REQUIRED", "PREFERRED", "NICE_TO_HAVE"):
                extracted_items = cls.split_phrase_into_items(clean_line)
                for item in extracted_items:
                    canon = SkillNormalizer.normalize(item) or item
                    low_canon = canon.lower()
                    if effective_level == "PREFERRED" and low_canon not in seen_preferred:
                        seen_preferred.add(low_canon)
                        preferred_skills.append({
                            "name": canon,
                            "evidence": orig_line,
                            "source_section": "Preferred Qualifications & Skills",
                        })
                    elif effective_level == "NICE_TO_HAVE" and low_canon not in seen_good:
                        seen_good.add(low_canon)
                        good_to_have.append({
                            "name": canon,
                            "evidence": orig_line,
                            "source_section": "Good to Have Knowledge",
                        })
                    elif effective_level == "REQUIRED" and low_canon not in seen_required:
                        seen_required.add(low_canon)
                        required_skills.append({
                            "name": canon,
                            "evidence": orig_line,
                            "source_section": "Required Key Skills",
                        })

        # Deduplicate across levels: REQUIRED > PREFERRED > NICE_TO_HAVE
        seen_preferred_lowers = {s["name"].lower() for s in preferred_skills}
        seen_good_lowers = {s["name"].lower() for s in good_to_have}

        filtered_required = [
            s for s in required_skills
            if s["name"].lower() not in seen_preferred_lowers and s["name"].lower() not in seen_good_lowers
        ]

        return {
            "role_title": job_title or "Job Requisition",
            "required_skills": filtered_required,
            "preferred_skills": preferred_skills,
            "good_to_have": good_to_have,
            "responsibilities": responsibilities,
            "experience": experience_info or {"value": None, "evidence": None},
            "education": education_list,
        }
