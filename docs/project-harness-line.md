# Legal Graph RAG Project Harness Line

Last updated: 2026-04-27

This document is the execution rail for building the AI repository into a FastAPI + Neo4j + OpenAI legal Graph RAG service. Work should proceed in small commits, with every step independently testable and pushable.

## Goal

Build an AI service that can answer foreign-worker employment questions and analyze employment documents by combining:

- MOEL foreign-worker employment guidebook knowledge
- Korean statutes and articles
- labor precedents and decisions
- checklist items from the backend
- institution/contact/remedy information
- user/case/document facts passed from the backend

The service must return practical answers:

1. short answer
2. legal basis
3. related precedent/case examples
4. guidebook basis
5. checklist impact
6. institution/contact path
7. next action
8. evidence/citation metadata

## Source Decision

### Recommended API Source

Use the National Law Information Open API first.

Source:

- https://open.law.go.kr/LSO/openApi/guideList.do
- https://open.law.go.kr/information/service.do

Reason:

- It exposes law list/body APIs.
- It exposes precedent list/body APIs.
- It exposes legal interpretation, administrative trial, and committee decision APIs.
- It is the most direct official source for our first legal dataset.

### Do We Need Other Legal APIs Now?

No, not for the first implementation.

Start with only the National Law Information Open API. Add other sources only after the full ingestion and retrieval loop works.

Secondary candidates for later:

- Court Open API / Judicial Information Sharing Portal: `https://openapi.scourt.go.kr`
- National Assembly Law Library Open API: `https://law.nanet.go.kr`

## Data Volume Strategy

Do not collect everything first.

The correct order is:

```text
seed dataset
-> normalize
-> graph schema validation
-> vector index validation
-> retrieval quality check
-> expand keywords
-> expand data volume
```

Initial hard caps:

| Dataset | First cap | Reason |
| --- | ---: | --- |
| Guidebook chunks | all existing OCR chunks | Already local and small. |
| Backend checklist items | all items | Already structured and small. |
| Statutes | 5 P0 laws | Required for legal basis. |
| Articles | target articles only | Avoid noisy full law ingestion at first. |
| Precedents | 30-50 cases | Enough for demo and retrieval quality check. |
| Institutions | guidebook-only first | Avoid external crawling scope creep. |
| LLMGraphTransformer extraction | selected guide sections + selected precedents | Cost and quality control. |

Expansion caps after validation:

| Dataset | Second cap |
| --- | ---: |
| P0/P1 laws | 10-12 laws |
| Precedents | 200-500 cases |
| Committee decisions | 50-100 decisions |
| Legal interpretations | 50-100 records |

## Environment Variables

Required:

```env
OPENAI_API_KEY=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_DATABASE=
```

Needed when legal API collection begins:

```env
LAW_OPEN_API_OC=
```

Optional later:

```env
LAW_OPEN_API_BASE_URL=https://www.law.go.kr
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_GENERATION_MODEL=gpt-5.4-mini
GRAPH_EXTRACTION_MODEL=gpt-5.4-mini
```

Do not commit `.env`.

## Architecture

```text
frontend
  -> Spring backend
    -> FastAPI AI service
      -> Neo4j Aura
      -> OpenAI API

Spring MySQL:
  users, companies, cases, uploaded documents, analysis summaries

Neo4j:
  legal graph, guidebook graph, vector chunks, citations, remedies
```

The Spring backend remains the source of truth for users, employers, workers, cases, and uploaded document metadata. Neo4j stores legal and guide knowledge only.

## Neo4j Graph Model

Allowed node labels:

- `Chunk`
- `GuideSection`
- `Procedure`
- `Requirement`
- `Institution`
- `ChecklistItem`
- `SafetyTopic`
- `Remedy`
- `Statute`
- `Article`
- `Case`
- `Decision`
- `Interpretation`
- `Issue`
- `DocumentType`

Allowed relationship types:

- `PART_OF`
- `HAS_CHUNK`
- `MENTIONS`
- `ABOUT`
- `INTERPRETS`
- `CITES`
- `GOVERNED_BY`
- `HAS_REMEDY`
- `CONTACT`
- `HANDLED_BY`
- `CHECKED_BY`
- `RELATED_GUIDE`
- `APPLIES_TO`
- `SIMILAR_TO`

Do not allow LLMGraphTransformer to write arbitrary labels or relationships.

## Retrieval Workflow

### Query-Time Flow

```text
request from backend/frontend
-> normalize question and case/document facts
-> classify issue candidates
-> embed query with text-embedding-3-large
-> Neo4j vector search over Chunk nodes
-> graph expansion from chunks to Issue/Article/Case/GuideSection/Remedy/Institution
-> context assembly
-> OpenAI Responses API streaming
-> SSE response with citations and graph paths
```

### Document Analysis Flow

```text
backend uploaded document
-> backend parser/OCR/sanitizer extracts allowlisted facts
-> FastAPI /document-analysis receives facts only
-> issue extraction
-> vector + graph retrieval
-> structured analysis response
-> backend persists summary/risk flags/hash
```

## Commit and Push Discipline

Each unit should:

1. implement one vertical slice or one setup slice
2. include a minimal verification command
3. avoid committing secrets or large generated dumps
4. be pushed immediately after passing verification

Recommended commit message format:

```text
feat: ...
fix: ...
docs: ...
test: ...
chore: ...
```

## Phase Plan

### Phase 0. Planning and Contracts

Status: partially complete.

Commits:

- `docs: define legal graph rag data collection`
- `docs: define graph rag implementation harness`

Done when:

- Dataset scope is written.
- Step-by-step implementation rail is written.
- Legal API source decision is recorded.

Verification:

```bash
git status --short
```

### Phase 1. FastAPI Skeleton

Commit:

```text
feat: scaffold fastapi graph rag service
```

Files:

```text
app/main.py
app/core/config.py
app/api/routes/health.py
app/api/routes/chat.py
app/api/routes/document_analysis.py
app/api/routes/ingest.py
pyproject.toml
requirements.txt or uv.lock
```

Endpoints:

- `GET /health`
- `GET /ready`

Done when:

- App starts locally.
- Health endpoint returns OK.
- Config loads `.env`.

Verification:

```bash
python -m compileall app
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

### Phase 2. Neo4j Connectivity and Schema

Commit:

```text
feat: add neo4j client and graph schema setup
```

Files:

```text
app/graph/neo4j_client.py
app/graph/schema.py
scripts/setup_neo4j_schema.py
```

Create:

- uniqueness constraints
- lookup indexes
- vector index for `Chunk.embedding`

Required vector dimension:

- `text-embedding-3-large`: 3072

Done when:

- Neo4j connection succeeds.
- `RETURN 1` works.
- constraints/index setup script is idempotent.

Verification:

```bash
python scripts/setup_neo4j_schema.py
```

### Phase 3. Existing Guidebook Chunk Ingestion

Commit:

```text
feat: ingest guidebook chunks into neo4j
```

Files:

```text
app/ingest/guidebook_loader.py
app/services/chunking.py
scripts/ingest_guidebook.py
data/normalized/.gitkeep
```

Input:

- `ocr_results/*.txt`

Output:

- `(:GuideSection)`
- `(:Chunk {sourceType: "GUIDE"})`
- `(:Chunk)-[:PART_OF]->(:GuideSection)`

Done when:

- All local OCR text files are chunked.
- Chunks are inserted with stable IDs.
- Re-running does not duplicate nodes.

Verification:

```bash
python scripts/ingest_guidebook.py --dry-run
python scripts/ingest_guidebook.py
```

### Phase 4. OpenAI Embeddings for Guidebook Chunks

Commit:

```text
feat: embed guidebook chunks with openai
```

Files:

```text
app/services/openai_client.py
app/services/embeddings.py
scripts/embed_chunks.py
```

Done when:

- Missing chunk embeddings are generated.
- Embeddings are saved on `Chunk.embedding`.
- Script can resume from partial completion.

Verification:

```bash
python scripts/embed_chunks.py --limit 5
python scripts/embed_chunks.py
```

### Phase 5. Backend Checklist Catalog Ingestion

Commit:

```text
feat: ingest checklist catalog into graph
```

Files:

```text
app/ingest/checklist_loader.py
scripts/ingest_checklist.py
```

Input:

- `../backend/src/main/resources/reference/checklists/moel-foreign-worker-employment-management.json`

Output:

- `(:ChecklistItem)`
- optional `(:Issue)-[:CHECKED_BY]->(:ChecklistItem)` seed links

Done when:

- Checklist items are present in Neo4j.
- Codes are unique.

Verification:

```bash
python scripts/ingest_checklist.py --dry-run
python scripts/ingest_checklist.py
```

### Phase 6. Institution and Remedy Extraction from Guidebook

Commit:

```text
feat: extract guidebook institutions and remedies
```

Files:

```text
app/ingest/guidebook_extractors.py
scripts/extract_guidebook_entities.py
```

Extract:

- employment centers
- immigration offices
- HRD Korea
- labor offices
- counseling centers
- insurance/public institutions
- practical remedies and procedures

Done when:

- Institution/contact nodes exist.
- Guide sections connect to institutions/remedies.

Verification:

```bash
python scripts/extract_guidebook_entities.py --dry-run
python scripts/extract_guidebook_entities.py
```

### Phase 7. National Law Open API Client

Commit:

```text
feat: add national law api client
```

Files:

```text
app/collectors/law_open_api.py
app/collectors/xml_parser.py
scripts/check_law_api.py
```

Requires:

```env
LAW_OPEN_API_OC=
```

Capabilities:

- law list search
- law body fetch
- precedent list search
- precedent body fetch
- save raw XML/JSONL cache

Done when:

- API key check succeeds.
- One law and one precedent can be fetched.
- Raw response is not committed by default.

Verification:

```bash
python scripts/check_law_api.py
```

### Phase 8. P0 Statute and Article Collection

Commit:

```text
feat: collect p0 employment statutes
```

Files:

```text
app/collectors/statute_collector.py
app/ingest/statute_ingester.py
scripts/collect_statutes.py
scripts/ingest_statutes.py
```

Collect:

- 근로기준법
- 최저임금법
- 외국인근로자의 고용 등에 관한 법률
- 출입국관리법
- 산업안전보건법

Initial article topics:

- written employment conditions
- wage payment
- wage statement/payslip
- work hours
- overtime/night/holiday work
- rest time
- weekly holiday/leave
- minimum wage
- employment permit
- employment change report
- workplace change
- foreign registration/residence
- occupational safety education

Done when:

- `(:Statute)` and `(:Article)` nodes exist.
- Article chunks have embeddings.
- Articles connect to known `Issue` seed nodes.

Verification:

```bash
python scripts/collect_statutes.py --laws p0 --dry-run
python scripts/collect_statutes.py --laws p0
python scripts/ingest_statutes.py
```

### Phase 9. P0 Precedent Collection

Commit:

```text
feat: collect p0 labor precedents
```

Files:

```text
app/collectors/precedent_collector.py
app/ingest/precedent_ingester.py
scripts/collect_precedents.py
scripts/ingest_precedents.py
```

P0 keywords:

- 임금명세서
- 임금체불
- 연장근로수당
- 야간근로수당
- 휴일근로수당
- 최저임금
- 통상임금
- 퇴직금
- 근로시간
- 휴게시간
- 근로계약서
- 근로조건 서면명시
- 외국인근로자
- 고용허가
- 사업장 변경
- 출국만기보험
- 기숙사
- 숙식비 공제
- 산업재해
- 산재

Initial target:

- 30-50 deduplicated precedents.

Done when:

- `(:Case)` nodes exist.
- Case chunks have embeddings.
- Deduplication by source case ID and case number works.

Verification:

```bash
python scripts/collect_precedents.py --keywords p0 --limit 50 --dry-run
python scripts/collect_precedents.py --keywords p0 --limit 50
python scripts/ingest_precedents.py
```

### Phase 10. LLMGraphTransformer Extraction

Commit:

```text
feat: extract legal graph relationships with llm transformer
```

Files:

```text
app/services/graph_transformer.py
app/services/graph_normalizer.py
scripts/extract_graph_relationships.py
```

Rules:

- Use strict `allowed_nodes`.
- Use strict `allowed_relationships`.
- Parser owns exact metadata.
- LLM owns semantic issue/remedy/holding relationships only.
- Save extraction audit records locally, but do not commit large output.

Done when:

- Selected guide sections connect to `Issue`, `Remedy`, `Institution`.
- Selected cases connect to `Issue`, `Article`, `Case`.
- Invalid labels/relationship types are rejected.

Verification:

```bash
python scripts/extract_graph_relationships.py --limit 5 --dry-run
python scripts/extract_graph_relationships.py --limit 20
```

### Phase 11. Hybrid Retriever

Commit:

```text
feat: implement vector graph hybrid retriever
```

Files:

```text
app/services/retriever.py
app/services/graph_expander.py
app/services/context_builder.py
scripts/query_graph_rag.py
```

Retrieval algorithm:

```text
query embedding
-> vector search Chunk top-k
-> collect source nodes
-> expand 1-2 hops to Issue/Article/Case/GuideSection/Remedy/Institution
-> rank and dedupe
-> build context sections
```

Done when:

- Query returns chunks and graph paths.
- Results include citations.

Test queries:

- 임금명세서에 연장근로수당이 없어요
- 외국인근로자 사업장 변경은 어디에 문의해야 하나요
- 기숙사비를 월급에서 공제해도 되나요
- 최저임금보다 적게 받은 것 같아요
- 농약 중독이 의심되면 어떻게 해야 하나요

Verification:

```bash
python scripts/query_graph_rag.py "임금명세서에 연장근로수당이 없어요"
```

### Phase 12. Streaming Chat API

Commit:

```text
feat: add streaming graph rag chat endpoint
```

Files:

```text
app/api/routes/chat.py
app/services/generator.py
app/schemas/chat.py
```

Endpoint:

- `POST /chat/stream`

Response:

- SSE text deltas
- citation events
- graph path events
- final metadata event

Done when:

- Client receives streaming answer.
- Citations and graph paths are emitted.

Verification:

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"임금명세서에 연장근로수당이 없어요","role":"WORKER"}'
```

### Phase 13. Document Analysis API

Commit:

```text
feat: implement document analysis endpoint with graph rag
```

Files:

```text
app/api/routes/document_analysis.py
app/schemas/document_analysis.py
app/services/document_analysis.py
```

Endpoint:

- `POST /document-analysis`

Input:

- Existing backend offchain-analysis contract.

Output:

- `status`
- `summary`
- `riskFlags`
- `fieldFindings`
- `checklistSuggestions`
- `recommendedActions`
- `confidence`

Done when:

- Spring backend's `HttpDocumentAnalysisAdapter` can call the endpoint.
- Response conforms to backend contract.

Verification:

```bash
curl -X POST http://localhost:8000/document-analysis \
  -H 'Content-Type: application/json' \
  --data @tests/fixtures/document_analysis_request.json
```

### Phase 14. Backend Integration

This phase touches the backend repository, not the AI repository.

Commit in backend:

```text
feat: proxy ai graph rag chat streaming
```

Tasks:

- Add AI chat client.
- Add authenticated Spring endpoint for chat streaming.
- Keep document-analysis adapter pointed at FastAPI.
- Ensure no raw user document text is forwarded.

### Phase 15. Frontend Integration

This phase touches the frontend repository.

Commit in frontend:

```text
feat: connect chat page to graph rag stream
```

Tasks:

- Replace mock chat send flow.
- Render streaming answer.
- Render citations.
- Render legal basis / cases / guidebook / next actions.

### Phase 16. Evaluation and Demo Harness

Commit:

```text
test: add graph rag evaluation queries
```

Files:

```text
eval/queries.jsonl
eval/run_eval.py
eval/expected_coverage.md
```

Minimum eval set:

- 5 payslip questions
- 5 employment contract questions
- 5 foreign-worker procedure questions
- 5 safety/accident questions
- 5 institution/contact questions

Required checks:

- answer contains practical next action
- answer cites at least one source
- answer separates legal info from legal advice
- answer does not expose raw personal data
- answer includes institution/contact when relevant

## Stop Points

If data volume, API limits, or LLM extraction quality becomes a bottleneck, stop at these stable fallback points.

1. Guidebook-only RAG with Neo4j vector index.
2. Guidebook + checklist graph.
3. Guidebook + checklist + P0 statutes.
4. Guidebook + checklist + statutes + 30-50 precedents.
5. Full Graph RAG with LLMGraphTransformer relationships.

Each fallback is demoable.

## What to Ask From the User

Needed before Phase 7:

- National Law Information Open API OC value.
- Confirmation that law body, precedent list, and precedent body APIs are enabled.

Needed before frontend/backend integration:

- Whether chat streaming should go through Spring backend or directly from frontend to FastAPI.
- Preferred visible citation format.

Needed before production-like run:

- Data retention policy for AI chats and document analysis requests.
- Whether legal disclaimer copy should be shown in every answer.

