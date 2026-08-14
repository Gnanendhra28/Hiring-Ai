from typing import Dict

class SkillNormalizer:
    """
    Skill Normalization Engine & Canonical Ontology.
    Maps raw extracted skill strings and aliases to canonical representations while preserving original evidence.
    """

    # Exact Canonical Skill Mappings
    CANONICAL_ALIASES: Dict[str, str] = {
        # AI / ML
        "rag": "RAG",
        "retrieval augmented generation": "RAG",
        "retrieval-augmented generation": "RAG",
        "llm": "LLMs",
        "large language models": "LLMs",
        "generative ai": "Generative AI",
        "genai": "Generative AI",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "deep learning": "Deep Learning",
        "nlp": "Natural Language Processing",
        "natural language processing": "Natural Language Processing",
        # Languages
        "python": "Python",
        "python3": "Python",
        "python programming": "Python",
        "typescript": "TypeScript",
        "ts": "TypeScript",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "golang": "Go",
        "go lang": "Go",
        # Databases & Vector Stores
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "postgres db": "PostgreSQL",
        "pgvector": "pgvector",
        "redis": "Redis",
        "mongodb": "MongoDB",
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
        "docker": "Docker",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
    }

    # Distinct Non-Equivalencies Guard
    NON_EQUIVALENT_PAIRS = [
        ("RAG", "ChatGPT"),
        ("Kubernetes", "Docker"),
        ("FastAPI", "Flask"),
        ("Python", "Java"),
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

        return False
