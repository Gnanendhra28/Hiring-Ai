
class SkillNormalizer:
    """
    Skill Normalization Engine & Canonical Ontology.
    Maps raw extracted skill strings and aliases to canonical representations while preserving original evidence.
    """

    # Exact Canonical Skill Mappings
    CANONICAL_ALIASES: dict[str, str] = {
        # AI / ML & GenAI Taxonomy
        "rag": "RAG",
        "retrieval augmented generation": "RAG",
        "retrieval-augmented generation": "RAG",
        "llm": "LLMs",
        "llms": "LLMs",
        "large language model": "LLMs",
        "large language models": "LLMs",
        "generative ai": "Generative AI",
        "genai": "Generative AI",
        "prompt engineering": "Prompt Engineering",
        "transformers": "Transformers",
        "hugging face": "Hugging Face",
        "huggingface": "Hugging Face",
        "pytorch": "PyTorch",
        "langchain": "LangChain",
        "llamaindex": "LlamaIndex",
        "llama-index": "LlamaIndex",
        "vector databases": "Vector Databases",
        "vector database": "Vector Databases",
        "vector db": "Vector Databases",
        "vectordb": "Vector Databases",
        "chromadb": "ChromaDB",
        "qdrant": "Qdrant",
        "pinecone": "Pinecone",
        "faiss": "FAISS",
        "weaviate": "Weaviate",
        "fine-tuning": "Fine-tuning",
        "finetuning": "Fine-tuning",
        "fine tuning": "Fine-tuning",
        "lora": "LoRA",
        "qlora": "QLoRA",
        "mlflow": "MLflow",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "deep learning": "Deep Learning",
        "computer vision": "Computer Vision",
        "opencv": "OpenCV",
        "cuda": "CUDA",
        "tensorrt": "TensorRT",
        "nlp": "Natural Language Processing",
        "natural language processing": "Natural Language Processing",
        "scikit-learn": "Scikit-learn",
        "scikitlearn": "Scikit-learn",
        "sklearn": "Scikit-learn",
        "openai": "OpenAI",
        "opensearch": "OpenSearch",
        "tensorflow": "TensorFlow",
        "tf": "TensorFlow",
        "keras": "Keras",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "airflow": "Airflow",
        "apache airflow": "Airflow",
        "spark": "Apache Spark",
        "apache spark": "Apache Spark",
        "snowflake": "Snowflake",
        "dbt": "dbt",
        "databricks": "Databricks",
        "bigquery": "BigQuery",

        # Languages
        "python": "Python",
        "python3": "Python",
        "python 3": "Python",
        "python programming": "Python",
        "typescript": "TypeScript",
        "ts": "TypeScript",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "golang": "Go",
        "go lang": "Go",
        "c++": "C++",
        "cpp": "C++",
        "rust": "Rust",
        "java": "Java",
        "c#": "C#",

        # Databases & Vector Stores
        "sql": "SQL",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "postgres db": "PostgreSQL",
        "pgvector": "pgvector",
        "redis": "Redis",
        "mongodb": "MongoDB",
        "mysql": "MySQL",

        # Frameworks & Infrastructure
        "fastapi": "FastAPI",
        "fast api": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "react": "React",
        "react.js": "React",
        "reactjs": "React",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "node": "Node.js",
        "docker": "Docker",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "Google Cloud",
        "google cloud platform": "Google Cloud",
        "azure": "Microsoft Azure",
        "microsoft azure": "Microsoft Azure",
        "graphql": "GraphQL",
        "rest apis": "REST APIs",
        "rest api": "REST APIs",
        "restful": "REST APIs",
        "ci/cd": "CI/CD",
        "git": "Git",
        "github": "GitHub",
        "github actions": "GitHub Actions",

        # Power Engineering & Electrical Taxonomy
        "power systems": "Power Systems",
        "power system": "Power Systems",
        "electrical distribution": "Electrical Distribution",
        "power distribution": "Electrical Distribution",
        "autocad electrical": "AutoCAD Electrical",
        "autocad": "AutoCAD",
        "relay protection": "Relay Protection",
        "protection relays": "Relay Protection",
        "protective relaying": "Relay Protection",
        "load flow analysis": "Load Flow Analysis",
        "load flow": "Load Flow Analysis",
        "short circuit analysis": "Short Circuit Analysis",
        "short circuit": "Short Circuit Analysis",
        "hv/mv systems": "HV/MV Systems",
        "high voltage": "HV/MV Systems",
        "medium voltage": "HV/MV Systems",
        "substation design": "Substation Design",
        "substation": "Substation Design",
        "etap": "ETAP",
        "matlab": "MATLAB",
        "simulink": "Simulink",
        "matlab/simulink": "MATLAB/Simulink",
        "pscad": "PSCAD",
        "scada": "SCADA",
        "plc": "PLC",
    }

    # Semantic Ontology Hierarchy (Maps parents to sub-competencies)
    DOMAIN_TAXONOMY: dict[str, set[str]] = {
        "Generative AI": {"LLMs", "RAG", "Prompt Engineering", "Fine-tuning", "LoRA", "Transformers", "LangChain", "LlamaIndex", "Hugging Face"},
        "Machine Learning": {"Deep Learning", "PyTorch", "TensorFlow", "Scikit-learn", "XGBoost", "LightGBM", "Keras", "Model Training", "Model Evaluation"},
        "Computer Vision": {"OpenCV", "CUDA", "TensorRT", "Deep Learning", "PyTorch", "Image Processing"},
        "Power Systems": {"Electrical Distribution", "Relay Protection", "Load Flow Analysis", "Short Circuit Analysis", "HV/MV Systems", "Substation Design", "ETAP", "PSCAD", "SCADA"},
        "Backend Engineering": {"Python", "FastAPI", "PostgreSQL", "REST APIs", "Docker", "Redis", "Microservices"},
    }

    # Distinct Non-Equivalencies Guard
    NON_EQUIVALENT_PAIRS = [
        ("RAG", "ChatGPT"),
        ("Kubernetes", "Docker"),
        ("FastAPI", "Flask"),
        ("Python", "Java"),
        ("Power Systems", "Machine Learning"),
    ]

    @classmethod
    def normalize(cls, raw_skill: str) -> str:
        if not raw_skill or not raw_skill.strip():
            return "Unknown"

        cleaned = raw_skill.strip().lower()
        if cleaned in cls.CANONICAL_ALIASES:
            return cls.CANONICAL_ALIASES[cleaned]

        # Capitalize words as fallback
        return raw_skill.strip().title()

    @classmethod
    def are_equivalent(cls, skill_a: str, skill_b: str) -> bool:
        norm_a = cls.normalize(skill_a)
        norm_b = cls.normalize(skill_b)

        if norm_a == norm_b:
            return True

        for pair_1, pair_2 in cls.NON_EQUIVALENT_PAIRS:
            if (norm_a == pair_1 and norm_b == pair_2) or (norm_a == pair_2 and norm_b == pair_1):
                return False

        # Check semantic parent-child inclusion
        for domain, children in cls.DOMAIN_TAXONOMY.items():
            if norm_a == domain and norm_b in children:
                return True
            if norm_b == domain and norm_a in children:
                return True

        return False
