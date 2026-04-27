# AI Orchestrator Workflow

Last updated: 2026-04-27

This document defines how the AI service decides which retrieval path to use for each request. Not every question needs precedents. Some questions need only a plain answer, some need the MOEL guidebook, some need statutes, and only dispute-like questions need precedent retrieval.

## Core Decision

Use Neo4j as both:

- graph database
- vector store through Neo4j vector indexes on `Chunk.embedding`

Do not add a separate vector database in the first implementation. If Neo4j vector search becomes too slow or too costly at larger scale, introduce a dedicated vector DB later. For the MVP, one Neo4j knowledge store keeps graph traversal, citations, and vector search in one place.

## Product Modes

### 1. Chatbot Mode

Purpose:

- Answer worker/employer questions.
- Explain employment rules and procedures.
- Show related guidebook, statute, precedent, institution, and next action only when relevant.

Endpoint:

- `POST /chat/stream`

Response:

- Server-Sent Events for streaming answer text.
- Metadata events for citations, graph paths, and recommended actions.

### 2. Document Analysis Mode

Purpose:

- Analyze structured facts extracted from uploaded documents.
- Contract and payslip analysis are not the same as free-form chat.
- Return structured risks, checklist suggestions, field findings, and recommended actions.

Endpoint:

- `POST /document-analysis`

Input:

- Backend offchain-analysis contract.
- Only allowlisted facts and masked evidence references.
- No raw uploaded document, no raw OCR text, no personal identifiers.

Response:

- Synchronous JSON that Spring can persist.

### 3. Ingestion Mode

Purpose:

- Collect, normalize, embed, and graph-transform legal and guidebook data.
- This is offline/batch work, not user-facing runtime retrieval.

Endpoints/scripts:

- `scripts/ingest_guidebook.py`
- `scripts/collect_statutes.py`
- `scripts/collect_precedents.py`
- `scripts/extract_graph_relationships.py`

## Orchestrator Components

```text
RequestNormalizer
-> IntentRouter
-> FactBuilder
-> RetrievalPlanner
-> Retriever(s)
-> GraphExpander
-> ContextBuilder
-> Generator
-> ResponseStreamer or StructuredResponseBuilder
```

### RequestNormalizer

Responsibilities:

- Normalize Korean spacing and punctuation lightly.
- Preserve legal terms.
- Attach role, language, case context, and document facts if present.

### IntentRouter

Classifies request into one main intent and optional sub-intents.

Allowed intents:

- `GREETING`
- `GENERAL_EMPLOYMENT_INFO`
- `GUIDE_PROCEDURE`
- `STATUTE_EXPLANATION`
- `PRECEDENT_REQUIRED`
- `DOCUMENT_ANALYSIS`
- `PAYSLIP_ANALYSIS`
- `CONTRACT_ANALYSIS`
- `INSTITUTION_CONTACT`
- `CHECKLIST_HELP`
- `SAFETY_HELP`
- `ESCALATION`

### FactBuilder

Builds safe facts from backend input.

Allowed facts:

- role
- industry
- region
- language code
- worker status category
- document type
- wage amount and period
- work hours
- overtime/night/holiday mention booleans
- break time
- dormitory provided
- dormitory deduction amount
- insurance/education/residence status booleans
- masked evidence references

Blocked facts:

- names
- phone numbers
- emails
- alien registration numbers
- passport numbers
- detailed addresses
- business registration numbers
- raw uploaded files
- raw OCR text

### RetrievalPlanner

Chooses retrieval plan.

Allowed retrieval plans:

- `NONE`
- `GUIDE_ONLY`
- `STATUTE_ONLY`
- `GUIDE_STATUTE`
- `CASE_ONLY`
- `STATUTE_CASE`
- `GUIDE_STATUTE_CASE`
- `CHECKLIST_ONLY`
- `INSTITUTION_ONLY`
- `SAFETY_GUIDE`

The planner must avoid precedent retrieval unless the question actually benefits from case examples.

## When to Use Each Retrieval Plan

### `NONE`

Use for:

- greetings
- simple UI/help responses
- "what can you do?"
- short clarification questions

Example:

- "안녕"
- "너 뭐 할 수 있어?"

### `GUIDE_ONLY`

Use for:

- practical procedure
- employment permit flow
- workplace change steps
- required documents
- institution routing

Examples:

- "사업장 변경은 어디서 해요?"
- "외국인근로자 고용허가 절차 알려줘"

### `STATUTE_ONLY`

Use for:

- direct legal rule explanation
- article-based answers
- no factual dispute or precedent need

Examples:

- "연장근로수당이 뭐야?"
- "최저임금은 계약서에 어떻게 반영돼야 해?"

### `GUIDE_STATUTE`

Use for:

- legal rule plus practical workflow
- common user questions where answer should include both basis and next step

Examples:

- "임금명세서에 뭐가 들어가야 해?"
- "기숙사비를 월급에서 공제해도 돼?"

### `STATUTE_CASE`

Use for:

- dispute-like questions
- user asks for "판례", "사례", "비슷한 사건"
- ambiguity in legal interpretation
- burden of proof or evidentiary issues
- unpaid wage, dismissal, worker status, severance disputes

Examples:

- "연장근로수당을 못 받았는데 비슷한 판례 있어?"
- "프리랜서라고 계약했는데 근로자로 인정된 사례가 있어?"

### `GUIDE_STATUTE_CASE`

Use for:

- high-risk user questions needing practical steps, law, and case examples
- document analysis with legal risk
- settlement/reporting/escalation advice

Examples:

- "임금명세서에 연장근로수당이 없고 실제로 야근했는데 어떻게 해야 해?"
- "외국인근로자가 사업장 변경을 거절당했는데 사례와 해결 방법 알려줘"

### `INSTITUTION_ONLY`

Use for:

- where-to-contact questions
- phone/office/channel questions

Examples:

- "어디에 문의해야 해?"
- "고용센터랑 출입국 중 어디로 가야 돼?"

### `SAFETY_GUIDE`

Use for:

- agricultural/fishery/worksite safety questions
- guidebook safety topics
- emergency or occupational accident path

Examples:

- "농약 중독이 의심되면 어떻게 해?"
- "예초기 사용할 때 안전수칙 알려줘"

## Precedent Retrieval Policy

Precedents are expensive and can distract from simple answers. Use them only when one of these triggers is present.

Hard triggers:

- user explicitly asks for 판례, 사례, 유사 사건, 법원 판단
- dispute/claim framing: "못 받았어요", "거절당했어요", "신고하고 싶어요", "소송", "분쟁"
- factual ambiguity: worker status, actual work hours, overtime proof, dismissal reason, dormitory deduction validity
- high-risk document finding from analysis

Soft triggers:

- confidence is low with statute/guide only
- multiple legal interpretations are plausible
- user asks "이게 불법인가요?" with facts requiring legal application

Do not use precedents for:

- basic definitions
- simple procedure questions
- institution/contact lookup
- checklist status explanation
- guidebook-only safety guidance

## Chatbot Workflow

```text
1. Receive /chat/stream request
2. Normalize request
3. Route intent
4. Build safe facts
5. Select retrieval plan
6. Retrieve:
   - vector search over Chunk
   - optional graph expansion
   - optional precedent retrieval
7. Build context:
   - answer brief
   - guidebook facts
   - statute facts
   - precedent facts
   - institution/contact
   - next action
8. Generate with OpenAI Responses API
9. Stream:
   - answer_delta
   - citation
   - graph_path
   - final
```

### Chat SSE Events

Recommended events:

```text
event: plan
data: {"intent":"GUIDE_STATUTE","retrievalPlan":"GUIDE_STATUTE"}

event: answer_delta
data: {"text":"..."}

event: citation
data: {"sourceType":"STATUTE","title":"근로기준법","articleNo":"..."}

event: graph_path
data: {"nodes":[...],"relationships":[...]}

event: final
data: {"done":true,"confidence":0.82}
```

## Document Analysis Workflow

Document analysis should be more deterministic than chatbot mode.

```text
1. Receive /document-analysis request from Spring
2. Validate no blocked fields are present
3. Determine document type:
   - EMPLOYMENT_CONTRACT
   - PAYSLIP
   - VISA
   - RESIDENCE_PROOF
   - OTHER
4. Extract issue candidates from structured facts
5. Apply deterministic checks first
6. Retrieve guide/statute/case only for detected issues
7. Build structured response
8. Return JSON to Spring
```

### Contract Analysis Checks

Initial deterministic checks:

- contract period exists
- wage amount exists
- wage period exists
- work hours exist
- break time exists
- overtime/night/holiday terms mentioned
- dormitory provided and deduction amount present
- insurance/education/residence status if supplied

Retrieval:

- guide + statute for normal missing terms
- statute + case for wage/overtime/dispute-prone findings

### Payslip Analysis Checks

Initial deterministic checks:

- wage period exists
- gross wage exists
- deduction items exist
- net payment exists
- overtime/night/holiday pay presence if working facts indicate need
- minimum wage risk if wage and hours are sufficient to calculate

Retrieval:

- statute for required payslip items and wage payment rules
- precedent only if there is an actual unpaid wage/overtime dispute signal

## Context Assembly Rules

Keep context sections explicit.

```text
[User Facts]
[Guidebook Evidence]
[Statute Evidence]
[Precedent Evidence]
[Checklist Evidence]
[Institution/Remedy]
```

Precedent evidence should be concise:

- court
- case number
- decision date
- issue
- holding summary
- why it is relevant
- source URL if available

Do not paste long precedent bodies into generation context.

## Answer Style Rules

For chatbot answers:

- start with direct answer
- explain whether this is guide/procedure, statute, or precedent-based
- cite sources visibly
- include next action
- include institution/contact if relevant
- avoid definitive legal advice wording where facts are incomplete

For document analysis:

- return structured JSON
- include risk severity
- include checklist suggestions
- include evidence IDs only if known
- include confidence

## Dynamic Management

The orchestrator should be configurable without code changes where possible.

Future config files:

```text
config/retrieval_policy.yaml
config/issue_taxonomy.yaml
config/source_priority.yaml
config/document_checks.yaml
```

Recommended knobs:

- `precedent_enabled`
- `precedent_top_k`
- `guide_top_k`
- `statute_top_k`
- `graph_expansion_hops`
- `min_precedent_trigger_score`
- `default_generation_model`
- `default_embedding_model`
- `document_analysis_case_retrieval_enabled`

Initial defaults:

```yaml
precedent_enabled: true
precedent_top_k: 3
guide_top_k: 5
statute_top_k: 5
graph_expansion_hops: 2
min_precedent_trigger_score: 0.7
default_embedding_model: text-embedding-3-large
default_generation_model: gpt-5.4-mini
document_analysis_case_retrieval_enabled: true
```

## Fallback Behavior

If retrieval fails:

1. Answer from guide/statute if available.
2. If no legal source exists, ask for clarification.
3. Never invent case numbers, article numbers, or institution phone numbers.
4. Say that a precedent was not found when case retrieval returns empty.

If OpenAI generation fails:

1. Return retrieved citations and a brief fallback summary if possible.
2. Mark response as degraded.

If Neo4j fails:

1. Return service unavailable for document analysis.
2. For chat, return a short retry message.

