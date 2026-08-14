# ADR-003: Azure Service Bus for Event-Driven Messaging Architecture

## Status
Approved

## Context
Long-running workflows (resume processing, OCR, entity extraction, AI matching, email sending) must run asynchronously out-of-band without blocking HTTP requests.

## Decision
We select **Azure Service Bus** as the primary messaging infrastructure, behind an `EventBus` application interface abstraction.

## Rationale & Message Semantics
1. **At-Least-Once Processing & Idempotency**: All consumers implement idempotent execution keyed on `event_id`, `correlation_id`, and `organization_id`.
2. **Selective Message Sessions (Non-Global FIFO)**: Service Bus message sessions are enabled ONLY for specific aggregates/workflows where strict sequence ordering is strictly required (e.g. application state progression). Global FIFO ordering across all queues is NOT assumed, enabling max consumer parallelism.
3. **Dead-Letter Queues (DLQ) & Retries**: Automated retry policies with exponential backoff and poison message isolation via DLQs.
4. **EventBus Abstraction Layer**: Allows seamless switching to Apache Kafka or Azure Event Hubs if application throughput targets increase.

## Consequences
- Workers are simplified by relying on session-level ordering only when necessary, while standard events process concurrently.
