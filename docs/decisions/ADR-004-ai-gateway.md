# ADR-004: AI Gateway Architecture & Model Fallback Strategy

## Status
Approved

## Context
The platform utilizes AI models for text extraction, job requirement normalization, semantic retrieval, and candidate-job screening. Direct dependency on a single LLM vendor introduces risks of rate-limiting, outage, high latency, and vendor lock-in.

## Decision
We implement a central **AI Gateway** layer in `backend/app/ai/gateway/` that acts as the sole access point for all LLM and embedding operations.

## Capabilities
1. **Provider Abstraction**: Unified interface supporting OpenAI, Azure OpenAI, Anthropic, and local/open-source models.
2. **Dynamic Model Routing & Fallback**: Fast/economical models are invoked first for initial assessment; strong reasoning models are triggered on low confidence or edge cases.
3. **Structured Validation**: All outputs are enforced via strict Pydantic schemas. Unparseable responses trigger retries or human escalations.
4. **Observability & Cost Metering**: Every call logs token usage, latency, estimated cost, model version, and prompt version tied to the organization tenant.

## Consequences
- Guarantees cost efficiency, explainable outputs, and complete operational transparency.
