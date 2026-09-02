"""
Tier 1: Dense Vector Semantic Search
Converts Job Descriptions and Candidate profiles into dense vector embeddings
using sentence-transformers (all-MiniLM-L6-v2) or deterministic TF-IDF cosine embeddings.
"""

import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from .models import CandidateProfile, JobDescription


class VectorSearchEngine:
    """
    Tier 1 Vector Search Engine.
    Handles embedding generation, ChromaDB vector collection management, and cosine similarity scoring.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: Optional[str] = None,
        collection_name: str = "candidate_profiles",
    ):
        self.model_name = model_name
        self.collection_name = collection_name
        self.use_transformers = False
        self.model = None
        self.client = None
        self.collection = None
        self._in_memory_index: Dict[str, Tuple[List[float], Dict[str, Any], str]] = {}

        try:
            from sentence_transformers import SentenceTransformer
            import chromadb
            from chromadb.config import Settings

            self.model = SentenceTransformer(model_name)
            self.use_transformers = True

            if persist_directory:
                os.makedirs(persist_directory, exist_ok=True)
                self.client = chromadb.PersistentClient(path=persist_directory)
            else:
                self.client = chromadb.Client(Settings(anonymized_telemetry=False, is_persistent=False))

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            # Fallback to in-memory cosine similarity engine
            self.use_transformers = False

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a dense vector embedding."""
        if self.use_transformers and self.model:
            embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return embedding.tolist()

        # Deterministic character-gram / token frequency vector hashing
        tokens = re.findall(r"\b\w+\b", text.lower())
        dim = 128
        vec = [0.0] * dim
        for t in tokens:
            idx = abs(hash(t)) % dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def index_candidates(self, candidates: List[CandidateProfile]) -> None:
        """Indexes candidate profiles."""
        if not candidates:
            return

        for cand in candidates:
            dense_text = cand.to_dense_text()
            emb = self.generate_embedding(dense_text)
            meta = {
                "candidate_id": cand.id,
                "name": cand.name,
                "experience_years": cand.experience_years,
                "skills_count": len(cand.skills),
            }
            self._in_memory_index[cand.id] = (emb, meta, dense_text)

        if self.collection is not None:
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            for cand in candidates:
                dense_text = cand.to_dense_text()
                emb = self.generate_embedding(dense_text)
                documents.append(dense_text)
                embeddings.append(emb)
                metadatas.append({
                    "candidate_id": cand.id,
                    "name": cand.name,
                    "experience_years": cand.experience_years,
                    "skills_count": len(cand.skills),
                })
                ids.append(cand.id)

            self.collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )

    def query_similarity(self, jd: JobDescription, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Queries similarity using the dense embedding of the Job Description.
        Returns a list of (candidate_id, similarity_score_0_to_100).
        """
        jd_dense_text = jd.to_dense_text()
        jd_embedding = self.generate_embedding(jd_dense_text)

        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_embeddings=[jd_embedding],
                    n_results=top_k,
                    include=["metadatas", "distances"],
                )
                ranked: List[Tuple[str, float]] = []
                if results and "ids" in results and results["ids"] and len(results["ids"][0]) > 0:
                    ids = results["ids"][0]
                    distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)
                    for cand_id, distance in zip(ids, distances):
                        similarity = 1.0 - distance
                        score_100 = round(max(0.0, min(100.0, similarity * 100.0)), 2)
                        ranked.append((cand_id, score_100))
                    return ranked
            except Exception:
                pass

        # In-memory cosine query
        scores = []
        for cand_id, (c_emb, meta, _) in self._in_memory_index.items():
            cos = sum(a * b for a, b in zip(c_emb, jd_embedding))
            scores.append((cand_id, round(max(0.0, min(100.0, cos * 100.0)), 2)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def score_single_candidate(self, candidate: CandidateProfile, jd: JobDescription) -> float:
        """Computes Tier 1 dense vector cosine similarity score (0 - 100)."""
        cand_emb = self.generate_embedding(candidate.to_dense_text())
        jd_emb = self.generate_embedding(jd.to_dense_text())
        cosine_sim = sum(a * b for a, b in zip(cand_emb, jd_emb))
        return round(max(0.0, min(100.0, cosine_sim * 100.0)), 2)
