# AURA implementation plan

## Why this architecture is suitable for a CPU-only laptop

AURA is split into local application services and cloud AI services.

### Local
- FastAPI
- SQLite
- PDF extraction
- embedding storage
- cosine retrieval
- browser UI

### Cloud
- language reasoning
- web search
- embeddings

This avoids downloading a multi-GB local model and avoids GPU/CUDA requirements.

## Agent model

The current MVP uses one model with specialized system prompts. This is intentionally simpler and more reliable than running several local models.

Later, the router can choose specialized agents:

```text
User
 |
 v
AURA Orchestrator
 |
 +--> Study Agent
 +--> Coding Agent
 +--> Research Agent
 +--> Career Agent
 +--> Productivity Agent
 +--> General Agent
 |
 v
Tool Registry
 |
 +--> Web
 +--> Knowledge
 +--> Calendar
 +--> GitHub
 +--> Email
```

## Security rules for future action tools

Never allow an LLM to execute arbitrary shell commands directly.

Use:
1. allow-listed tools
2. strict schemas
3. user confirmation for destructive actions
4. isolated execution
5. timeouts
6. filesystem restrictions
7. audit logs

## Database migration

SQLite is used first to reduce setup problems. Once the MVP works, move to PostgreSQL.

## Vector storage

The MVP stores embeddings in SQLite as JSON. That is suitable for a student-scale prototype.

For a larger system, move to:
- pgvector
- Qdrant
- Weaviate
- another managed vector database

## Streaming

Add token streaming after the basic request/response path is stable.

## Voice

The UI already includes browser speech input where supported. A production voice assistant should use a dedicated audio pipeline and server-side speech models.
