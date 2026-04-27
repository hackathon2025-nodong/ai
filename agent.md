# Agent Operating Guide

Last updated: 2026-04-27

This file tells future coding agents how to work in this AI repository. It is intentionally practical: follow it when implementing the FastAPI + Neo4j + OpenAI legal Graph RAG service.

## Mission

Build the AI repository into a service that supports:

- streamed AI chatbot answers
- employment contract analysis
- payslip analysis
- guidebook/statute/precedent/institution retrieval
- Neo4j graph + vector hybrid retrieval

The service should help foreign workers and employers understand employment documents and practical next steps. It must not become a raw personal data store.

## Current Architectural Decision

Use:

- FastAPI for the AI service
- Neo4j Aura for graph data and vector indexes
- OpenAI `text-embedding-3-large` for embeddings
- OpenAI Responses API for generation and streaming
- National Law Information Open API as the first legal source

Do not add a separate vector database until Neo4j vector indexes are proven insufficient.

## Required Reading Before Work

Read these first:

1. `docs/project-harness-line.md`
2. `docs/data-collection-plan.md`
3. `docs/ai-orchestrator-workflow.md`
4. `README.md`

If touching backend integration, also read:

- `../backend/docs/offchain-analysis-contract.md`
- `../backend/src/main/java/com/kworkerharmony/backend/document/infrastructure/HttpDocumentAnalysisAdapter.java`
- `../backend/src/main/java/com/kworkerharmony/backend/document/port/DocumentAnalysisPort.java`

## Work Style

Proceed in small, pushable slices.

Each slice must have:

- a clear commit
- a minimal verification command
- no secrets committed
- no large generated data committed unless explicitly approved

Preferred sequence:

```text
implement one phase
-> run verification
-> git status
-> commit
-> push
```

## Commit Units

Use the phase commits from `docs/project-harness-line.md`.

Examples:

```text
feat: scaffold fastapi graph rag service
feat: add neo4j client and graph schema setup
feat: ingest guidebook chunks into neo4j
feat: embed guidebook chunks with openai
feat: add national law api client
feat: collect p0 labor precedents
feat: implement vector graph hybrid retriever
feat: add streaming graph rag chat endpoint
```

Do not bundle unrelated phases.

## Routing Principles

Not every request needs precedents.

Use the orchestrator policy in `docs/ai-orchestrator-workflow.md`.

Default behavior:

- simple greeting: no retrieval
- procedure question: guidebook retrieval
- direct legal rule question: statute retrieval
- practical legal question: guidebook + statute
- dispute or "판례/사례" question: statute + precedent
- high-risk document finding: guidebook + statute + precedent
- contact question: institution retrieval
- safety question: guidebook safety retrieval

Precedent retrieval should be opt-in by intent, not automatic for all questions.

## Data Boundaries

Never store these in Neo4j:

- worker names
- phone numbers
- emails
- alien registration numbers
- passport numbers
- detailed addresses
- business registration numbers
- raw uploaded files
- raw user-upload OCR text
- full chat logs without an explicit retention policy

Allowed runtime facts from backend:

- role
- industry
- region
- document type
- wage amount
- wage period
- work hours
- overtime/night/holiday mention booleans
- dormitory provided
- dormitory deduction amount
- masked evidence references

## Graph Extraction Rules

LLMGraphTransformer is an ingestion tool, not a runtime answer tool.

Use it for:

- extracting semantic issues
- connecting cases to issues
- connecting guide sections to remedies
- connecting issues to checklist items

Do not use it to invent:

- case numbers
- court names
- decision dates
- article numbers
- phone numbers
- URLs

Those fields must come from deterministic parsing or official source metadata.

Use strict allowed nodes and relationships.

Allowed labels and relationships are defined in `docs/project-harness-line.md`.

## Source Priority

Preferred answer sources:

1. user-provided safe facts
2. MOEL guidebook
3. statutes/articles
4. precedents/decisions
5. institution directory
6. checklist catalog

Precedents should support disputed legal application, not replace statute/guide explanations.

## Runtime Endpoints

Target AI endpoints:

- `GET /health`
- `GET /ready`
- `POST /chat/stream`
- `POST /document-analysis`

Internal/admin scripts:

- guidebook ingestion
- checklist ingestion
- statute collection
- precedent collection
- graph relationship extraction
- evaluation queries

## Verification Expectations

For Python changes:

```bash
python -m compileall app scripts
```

For Neo4j schema:

```bash
python scripts/setup_neo4j_schema.py
```

For retrieval:

```bash
python scripts/query_graph_rag.py "임금명세서에 연장근로수당이 없어요"
```

For FastAPI:

```bash
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

Use the exact commands only after the corresponding files exist.

## Environment

Required local `.env` keys:

```env
OPENAI_API_KEY=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_DATABASE=
```

Needed for law collection:

```env
LAW_OPEN_API_OC=
```

Never print secret values in logs or final answers.

## Data Volume Controls

Start small.

Initial caps:

- guidebook: all existing local OCR chunks
- statutes: 5 P0 laws
- precedents: 30-50 cases
- LLMGraphTransformer: limited sample before full run

Only expand after retrieval quality is checked.

## Stop Points

If time is tight, keep a demoable stop point:

1. guidebook vector RAG
2. guidebook + checklist graph
3. guidebook + statutes
4. guidebook + statutes + 30-50 precedents
5. full LLMGraphTransformer Graph RAG

Each stop point should still answer user questions with citations.

## Answer Quality Rules

The service should:

- separate legal information from legal advice
- cite the source type used
- provide practical next actions
- include institution/contact path when relevant
- say when no precedent was found
- avoid hallucinating legal case numbers or article numbers
- ask for clarification when facts are insufficient

## Current Next Step

Unless redirected, proceed with:

1. Phase 1: FastAPI skeleton
2. Phase 2: Neo4j connectivity and schema
3. Phase 3: guidebook chunk ingestion

Legal API collection begins only after `LAW_OPEN_API_OC` is available.

