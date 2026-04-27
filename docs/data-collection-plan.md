# Data Collection Plan for Legal Graph RAG

Last updated: 2026-04-27

This document defines the concrete datasets that must be collected before building the FastAPI + Neo4j Graph RAG service. The goal is to support user questions and document analysis for foreign-worker employment workflows with related guidebook sections, statutes, precedents, institutions, checklist items, and recommended actions.

## Target User Scenarios

The data collection scope is driven by these product scenarios.

1. A worker uploads a payslip and asks whether overtime pay, minimum wage, deductions, or required payslip items are missing.
2. A worker uploads or references an employment contract and asks whether contract period, wage, work hours, dormitory deduction, insurance, or leave terms are risky.
3. An employer asks what documents, reports, insurance, education, or immigration steps are required for a foreign worker.
4. A user asks where to contact for employment permit, workplace change, visa/residence, occupational accident, unpaid wage, or counseling.
5. The answer must show a practical path: summary, related guidebook section, legal basis, similar cases, checklist impact, institution/contact, and next actions.

## Storage Targets

Neo4j Aura is the legal knowledge store.

- Graph nodes and relationships: issues, statutes, cases, guide sections, institutions, remedies, checklist items.
- Vector index: chunk embeddings generated with OpenAI `text-embedding-3-large`.
- Application/user records remain in the Spring backend MySQL. Do not copy raw personal data into Neo4j.

## Non-Negotiable Data Boundaries

Do not collect or persist these into the legal knowledge graph.

- Worker name, phone number, email, alien registration number, passport number, address, account number.
- Employer representative name, business registration number, detailed workplace address.
- Raw uploaded document files.
- Raw OCR text from user uploads before masking.
- Full user chat logs unless a separate retention policy is added.

The AI service may receive only allowlisted case/document facts from the backend, such as industry, region, document type, wage amount, wage period, work hours, overtime mention status, dormitory deduction status, and masked evidence references.

## Immediate Collection Scope

### 1. Existing MOEL Foreign Worker Employment Guidebook

Status: already present in this repository.

Local source files:

- `ocr_results/*.txt`
- `외국인근로자_ocr_split/*.pdf`

Collect and normalize these entities from the guidebook.

| Entity | Required fields | Notes |
| --- | --- | --- |
| `GuideSection` | `sectionId`, `title`, `partTitle`, `pageStart`, `pageEnd`, `sourceFile` | Use table of contents and page markers where possible. |
| `Procedure` | `name`, `description`, `requiredActor`, `trigger`, `deadline`, `institutionName` | Example: employment permit issuance, workplace change, residence report. |
| `Requirement` | `name`, `appliesTo`, `condition`, `deadline`, `penaltyOrRisk` | Example: insurance enrollment, written contract, dormitory information. |
| `Institution` | `name`, `role`, `phone`, `url`, `regionScope` | Extract employment center, immigration office, counseling center, HRD Korea, labor offices if present. |
| `ChecklistCandidate` | `codeCandidate`, `title`, `reason`, `relatedIssue` | Used to map guidebook content to backend checklist items. |
| `SafetyTopic` | `name`, `hazards`, `preventionSteps`, `ppe` | Tractor, brush cutter, pesticides, ladder, fisheries, agriculture. |
| `Remedy` | `name`, `whenToUse`, `steps`, `institutionName` | Practical next actions for user questions. |
| `Chunk` | `chunkId`, `text`, `sourceType=GUIDE`, `sourceId`, `page`, `embedding` | Vector retrieval unit. |

Guidebook issue tags to extract:

- Employment permit system
- Employment permit issuance
- Standard employment contract
- Foreign worker registration/residence
- Workplace change
- Employment change report
- Re-employment/re-entry special system
- Departure/return process
- Mandatory insurance
- National health insurance
- Dormitory facility standards
- Dormitory information disclosure
- Wage, work hours, rest, holiday, leave
- Minimum wage
- Severance pay
- Workplace harassment
- Workplace sexual harassment
- Occupational safety and health
- Agriculture/fisheries safety
- Pesticide poisoning
- Tractor safety
- Brush cutter safety
- Contact institutions and counseling channels

### 2. Statutes and Articles

Primary source: National Law Information Open API from the Ministry of Government Legislation.

The official Open API guide lists law list/body APIs, article-level law body APIs, precedent list/body APIs, legal interpretation APIs, administrative trial APIs, and committee decision APIs.

Source URLs:

- https://open.law.go.kr/LSO/openApi/guideList.do
- https://open.law.go.kr/information/service.do

Collect these laws first.

| Priority | Law | Why |
| --- | --- | --- |
| P0 | 근로기준법 | Wage, work hours, overtime/night/holiday pay, written conditions, dismissal, rest, leave. |
| P0 | 최저임금법 | Minimum wage checks for contracts and payslips. |
| P0 | 외국인근로자의 고용 등에 관한 법률 | Employment permit, foreign-worker specific employer duties. |
| P0 | 출입국관리법 | Residence, workplace change, foreign registration, visa-related duties. |
| P0 | 산업안전보건법 | Safety education, employer safety duties, occupational accident prevention. |
| P1 | 근로자퇴직급여 보장법 | Severance pay and retirement benefit questions. |
| P1 | 임금채권보장법 | Unpaid wage protection/remedy context. |
| P1 | 산업재해보상보험법 | Occupational accident compensation path. |
| P1 | 고용보험법 | Employment insurance context. |
| P1 | 국민건강보험법 | Health insurance enrollment and foreign-worker guidebook links. |
| P1 | 국민연금법 | National pension return/lump-sum and guidebook links. |

For each law/article, collect:

- `lawId`
- `lawName`
- `lawType`
- `enforcementDate`
- `articleId`
- `articleNo`
- `articleTitle`
- `articleText`
- `paragraphs`
- `sourceUrl`
- `collectedAt`

Initial article focus:

- 근로조건 서면 명시
- 임금 지급
- 임금명세서 교부 및 기재사항
- 근로시간
- 연장/야간/휴일근로
- 휴게
- 주휴일/휴일/휴가
- 최저임금 효력
- 퇴직급여
- 해고 제한
- 직장 내 괴롭힘
- 안전보건교육
- 산업재해 보고/조치
- 외국인근로자 고용허가
- 고용변동 신고
- 사업장 변경
- 외국인등록/체류 관련 조항

### 3. Precedents

Primary source: National Law Information Open API precedent list/body APIs.

Secondary candidates:

- Court Open API / Judicial Information Sharing Portal: https://openapi.scourt.go.kr/kgso000m02.do
- National Assembly Law Library Open API: https://law.nanet.go.kr/bbs/openapi/define.do

Collect precedents by issue-based keyword searches. Start with a small high-signal labor set, then expand.

P0 precedent keywords:

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

P1 precedent keywords:

- 부당해고
- 해고예고
- 직장 내 괴롭힘
- 직장 내 성희롱
- 차별금지
- 농업 근로자
- 어업 근로자
- 계절근로
- 파견
- 도급
- 근로자성
- 사용자성

For each precedent, collect:

- `caseId` from source
- `court`
- `caseNumber`
- `decisionDate`
- `caseName` or `title`
- `caseType`
- `holding`
- `summary`
- `facts`
- `reasoning`
- `disposition`
- `referencedStatutes`
- `citedCases`
- `sourceUrl`
- `rawTextHash`
- `collectedAt`

Graph extraction rules:

- Deterministic parser handles `court`, `caseNumber`, `decisionDate`, source ID, referenced statute strings, and cited case strings.
- LLMGraphTransformer handles only semantic extraction: `Issue`, `Holding`, `Remedy`, and relationships between cases, issues, and articles.
- Use strict allowed nodes and relationships. Do not allow open-ended entity labels.

### 4. Committee Decisions and Interpretations

Collect after P0 statute and precedent ingestion works.

Sources from National Law Information Open API:

- 노동위원회 결정문 목록/본문
- 고용보험심사위원회 결정문 목록/본문
- 법령해석례 목록/본문
- 행정심판례 목록/본문

Why this matters:

- Some employment disputes are better represented by labor committee decisions than court precedents.
- Users may ask practical remedy questions such as unpaid wage, dismissal, workplace change, industrial accident, or insurance disputes.

Initial keywords:

- 부당해고
- 임금체불
- 휴업수당
- 고용보험
- 산재
- 외국인근로자
- 사업장 변경

### 5. Backend Checklist Catalog

Status: already present in backend repository.

Source file:

- `backend/src/main/resources/reference/checklists/moel-foreign-worker-employment-management.json`

Collect into Neo4j as `ChecklistItem` nodes, with fields:

- `code`
- `title`
- `description`
- `sectionCode`
- `sectionTitle`
- `cadence`
- `source=BACKEND_REFERENCE`

Connect checklist items to issues and guide sections.

Examples:

- `Issue: written employment terms` -> `ChecklistItem: LRA_WRITTEN_CONDITIONS`
- `Issue: minimum wage` -> `ChecklistItem: MWA_MINIMUM_WAGE`
- `Issue: dormitory deduction` -> guidebook dormitory section and relevant checklist item

### 6. Institution and Contact Directory

Initial source: MOEL guidebook OCR.

Secondary source candidates:

- Official MOEL pages
- EPS / employment permit service pages
- HiKorea / immigration pages
- HRD Korea pages

Do not start by scraping broad websites. First extract the institutions already listed in the guidebook.

Collect:

- `institutionId`
- `name`
- `category`: `EMPLOYMENT_CENTER`, `LABOR_OFFICE`, `IMMIGRATION`, `COUNSELING`, `HRD`, `INSURANCE`, `SAFETY`
- `roleDescription`
- `phone`
- `url`
- `region`
- `source`
- `sourcePage`

Expected institutions:

- 고용센터
- 지방고용노동관서
- 출입국·외국인청/사무소
- 한국산업인력공단
- 외국인력상담센터
- 근로복지공단
- 국민건강보험공단
- 국민연금공단
- 산업안전보건공단

## Neo4j Graph Schema

Allowed nodes:

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
- `Chunk`
- `DocumentType`

Allowed relationships:

- `PART_OF`
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
- `HAS_CHUNK`
- `SIMILAR_TO`

Do not allow the graph extraction pipeline to create arbitrary labels or relationship types.

## Minimum Viable Dataset

The first usable Graph RAG demo requires this exact set.

1. All existing guidebook OCR chunks.
2. Guidebook sections for wage/work hours, employment permit, workplace change, dormitory, insurance, safety, and institution/contact pages.
3. Backend checklist catalog.
4. Articles from:
   - 근로기준법
   - 최저임금법
   - 외국인근로자의 고용 등에 관한 법률
   - 출입국관리법
   - 산업안전보건법
5. At least 30-50 labor precedents across:
   - wage arrears
   - overtime/night/holiday pay
   - minimum wage
   - payslip/wage statement
   - employment contract written terms
   - severance pay
   - foreign worker employment permit/workplace change
   - dormitory/deduction
   - occupational accident
6. Institution/contact nodes from the guidebook.

## Collection Output Format

Before writing to Neo4j, save collected raw normalized records as JSONL under `data/raw` or `data/normalized`. Do not commit large raw dumps unless explicitly approved.

Recommended files:

- `data/normalized/guide_sections.jsonl`
- `data/normalized/guide_chunks.jsonl`
- `data/normalized/statutes.jsonl`
- `data/normalized/articles.jsonl`
- `data/normalized/cases.jsonl`
- `data/normalized/checklist_items.jsonl`
- `data/normalized/institutions.jsonl`

Example precedent record:

```json
{
  "caseId": "source-case-id",
  "court": "대법원",
  "caseNumber": "2020다00000",
  "decisionDate": "2020-01-01",
  "title": "임금 청구",
  "summary": "판례 요약",
  "referencedStatutes": ["근로기준법 제56조"],
  "citedCases": [],
  "sourceUrl": "https://...",
  "rawTextHash": "sha256..."
}
```

## Implementation Order

1. Create FastAPI project skeleton and Neo4j connection module.
2. Create Neo4j constraints and vector indexes.
3. Ingest existing guidebook chunks and checklist items.
4. Add OpenAI `text-embedding-3-large` embeddings to `Chunk` nodes.
5. Extract guidebook institutions, procedures, requirements, and remedies.
6. Collect P0 statutes and articles from National Law Information Open API.
7. Collect P0 precedents from National Law Information Open API.
8. Run LLMGraphTransformer with strict schema against guidebook sections and precedents.
9. Build hybrid retrieval: vector search -> graph expansion -> context assembly.
10. Add streaming chat endpoint and document-analysis endpoint.

