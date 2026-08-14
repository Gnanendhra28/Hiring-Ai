# Distributed Redis Rate Limiting Runbook

## Overview
Defines multi-node distributed sliding-window rate limiting configuration using Azure Cache for Redis.

## Fail-Safe Architecture
- Provider Interface: `IRateLimiterProvider`
- Primary Production Adapter: `RedisRateLimiterAdapter`
- Local & Fail-Safe Fallback: `InMemoryRateLimiterAdapter`
- Behavior: If Redis connectivity fails, the rate limiter logs a warning and falls back to in-memory window limiting without raising HTTP 500 errors.
