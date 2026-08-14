# ADR-002: PostgreSQL with pgvector for Relational Data and Vector Retrieval

## Status
Approved

## Context
The application needs a transactional database for multi-tenant recruitment data (users, jobs, applications) and a vector storage engine to index and search candidate/job embeddings for semantic retrieval.

## Decision
We select **PostgreSQL** with the **`pgvector`** extension as the primary database and vector index.

## Rationale
1. **ACID Compliance**: Crucial for application state transitions, verification, and audit logs.
2. **Unified Data Store**: Avoids complex dual-write sync issues and operational overhead of separate vector databases (e.g. Pinecone).
3. **Multi-Tenant Isolation**: Supports standard PostgreSQL Row Level Security (RLS) policies and indexed filtering (`WHERE organization_id = ...`) alongside vector similarity operators.

## Consequences
- **Positive**: Simplified backup/restore, unified SQL query interface, strong consistency.
- **Negative**: Extremely high vector volumes (tens of millions) might eventually require specialized indexing or horizontal shard scaling.
- **Mitigation**: Vector index design uses HNSW / IVFFlat indexes, and the repository layer abstracts vector queries to allow dedicated vector engines if required in the future.
