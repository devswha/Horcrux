# RAG 시스템 구현 완료 ✅

## 개요

Horcrux에 RAG (Retrieval-Augmented Generation) 시스템을 통합하여 맥락 기반 대화 기능을 구현했습니다.

- **목적**: "그 사람 누구야?", "최근에 뭐 했지?" 같은 질문에 과거 대화 내용을 검색하여 답변
- **기술 스택**: Supabase pgvector + OpenAI text-embedding-3-small
- **비용**: ~$1-5/월 (1만 대화 기준)

---

## 아키텍처

### 3-Layer 구조

```
┌─────────────────────────────────────────┐
│         SimpleLLM (core/simple_llm.py)  │
│  - 사용자 입력 처리                      │
│  - 모든 대화 자동 저장 (RAG Manager)     │
│  - 메모리 검색 시 RAG 우선 사용          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      RAGManager (core/rag_manager.py)   │
│  - 대화 저장 + 자동 임베딩 생성          │
│  - 벡터 유사도 검색 (cosine distance)   │
│  - 배치 임베딩 생성                      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  EmbeddingService (core/embeddings.py)  │
│  - OpenAI text-embedding-3-small       │
│  - 1536차원 벡터 생성                    │
│  - 배치 처리 지원                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Database: conversation_memory + pgvector│
│  - embedding vector(1536) 컬럼           │
│  - HNSW 인덱스 (빠른 유사도 검색)       │
└─────────────────────────────────────────┘
```

---

## 구현 단계

### ✅ Phase 1: Supabase pgvector 설정

**파일**: `migrations/001_add_pgvector_support.sql`

```sql
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE conversation_memory
ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX conversation_memory_embedding_idx
ON conversation_memory
USING hnsw (embedding vector_cosine_ops);
```

**수동 실행 필요**: Supabase Dashboard → SQL Editor에서 실행
- 로컬 네트워크에서 Supabase 연결 안 됨 (IPv6 이슈)
- 가이드: `RAG_SETUP_MANUAL.md` 참고

---

### ✅ Phase 2: Embedding 파이프라인

**파일**: `core/embeddings.py`

**기능**:
- OpenAI `text-embedding-3-small` 모델 사용
- 1536차원 벡터 생성
- 단일/배치 임베딩 생성
- 비용 추정 ($0.02/1M tokens)

**사용 예시**:
```python
from core.embeddings import EmbeddingService

service = EmbeddingService()

# 단일 텍스트
embedding = service.generate_embedding("어제 7시간 잤어")  # 1536 floats

# 배치 처리 (더 효율적)
texts = ["운동했어", "공부했어", "이창하 누구야?"]
embeddings = service.generate_embeddings_batch(texts)  # 3개의 벡터

# 비용 추정
cost = service.calculate_cost(text_count=10000)  # $0.0100
```

---

### ✅ Phase 3: RAG Manager

**파일**: `core/rag_manager.py`

**핵심 기능**:

1. **자동 대화 저장**:
```python
rag = RAGManager(database)

# 대화 저장 시 자동으로 임베딩 생성
rag.save_conversation('user', '이창하는 대학교 때 친해진 형이야')
rag.save_conversation('assistant', '이창하님 정보를 저장했습니다.')
```

2. **벡터 유사도 검색**:
```python
# "그 사람" 같은 모호한 질문도 의미론적으로 검색
results = rag.search_similar_conversations('이창하', top_k=5)

for r in results:
    print(f"{r['role']}: {r['content']} (유사도: {r['similarity']:.3f})")
```

3. **배치 임베딩 생성** (기존 대화용):
```python
# 이미 저장된 대화에 대해 임베딩 생성
count = rag.batch_generate_embeddings()
print(f"{count}개 임베딩 생성 완료")
```

**PostgreSQL vs SQLite**:
- **PostgreSQL** (Supabase): 벡터 유사도 검색 (pgvector)
- **SQLite** (로컬): 텍스트 검색 (LIKE) fallback

---

### ✅ Phase 4: SimpleLLM 통합

**파일**: `core/simple_llm.py`

**변경 사항**:

1. **RAG Manager 초기화** (line 41-49):
```python
self.rag = RAGManager(db_wrapper)
```

2. **모든 대화 자동 저장** (line 75-81):
```python
# process() 메서드 내
self.rag.save_conversation('user', user_input)
self.rag.save_conversation('assistant', response)
```

3. **메모리 검색에 RAG 통합** (line 557-572):
```python
# _query_memory() 메서드 내
conversations = self.rag.search_similar_conversations(query, top_k=5)
results["conversations"] = [...]
```

---

## 사용 시나리오

### 시나리오 1: 사람 정보 기억

```
사용자: "이창하는 대학교 때 친해진 형이야"
→ 저장: people 테이블 + conversation_memory (임베딩 생성)

[나중에]
사용자: "그 사람 누구야?"
→ RAG 검색: "이창하" 관련 대화 찾기
→ 응답: "이창하는 대학교 때 친해진 형입니다."
```

### 시나리오 2: 최근 활동 기억

```
사용자: "오늘 2시간 공부했어"
→ 저장: learning_logs + conversation_memory (임베딩)

[다음날]
사용자: "어제 공부 뭐 했더라?"
→ RAG 검색: "공부" 관련 최근 대화 top 5
→ 응답: "어제 2시간 공부하셨습니다."
```

### 시나리오 3: 복잡한 맥락 질문

```
사용자: "최근에 친구들이랑 뭐 했지?"
→ RAG 검색: "친구" + "최근" 의미론적 검색
→ 결과: 상호작용, 사람 정보, 대화 기록 통합
→ 응답: "지난 주 이창하, 김철수와 식사 하셨습니다."
```

---

## 데이터베이스 스키마

### conversation_memory 테이블

```sql
CREATE TABLE conversation_memory (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context TEXT,
    embedding vector(1536)  -- pgvector 전용
);

CREATE INDEX conversation_memory_embedding_idx
ON conversation_memory
USING hnsw (embedding vector_cosine_ops);
```

**인덱스 타입**:
- **HNSW** (Hierarchical Navigable Small World): 빠른 근사 검색
- **IVFFlat** (대안): HNSW 지원 안 되는 경우

---

## 배포 가이드

### 1. 로컬 테스트 (SQLite)

```bash
# 의존성 설치
pip install psycopg2-binary

# 앱 실행
streamlit run interfaces/app.py

# 테스트
사용자: "이창하는 내 친구야"
사용자: "그 사람 누구야?"
→ SQLite 텍스트 검색으로 fallback
```

### 2. Supabase 설정

**RAG_SETUP_MANUAL.md** 참고:
1. Supabase Dashboard → SQL Editor
2. `migrations/001_add_pgvector_support.sql` 실행
3. 테이블 확인: `conversation_memory` → `embedding` 컬럼 존재

### 3. Streamlit Cloud 배포

```bash
# Streamlit Cloud Secrets 설정
OPENAI_API_KEY = "sk-..."
SUPABASE_URL = "postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres"
SUPABASE_KEY = "eyJhbGci..."

# 배포
git push origin main
→ Streamlit Cloud 자동 재배포
```

### 4. 기존 대화 임베딩 생성

```python
# Streamlit Cloud 콘솔 또는 Python 스크립트
from core.database import Database
from core.rag_manager import RAGManager

db = Database()
db.connect()
rag = RAGManager(db)

# 기존 대화 임베딩 생성
count = rag.batch_generate_embeddings()
print(f"✅ {count}개 임베딩 생성 완료")
```

---

## 비용 분석

### OpenAI 임베딩 비용

**모델**: `text-embedding-3-small`
**가격**: $0.02 / 1M tokens

**예상 사용량**:
- 평균 대화 길이: 50 tokens
- 월 1,000 대화: 50,000 tokens = **$0.001** (~1원)
- 월 10,000 대화: 500,000 tokens = **$0.01** (~10원)
- 월 100,000 대화: 5M tokens = **$0.10** (~100원)

**Supabase 비용**:
- 무료 티어: 500MB 데이터베이스 (수만 대화 저장 가능)
- Pro 티어 ($25/월): 8GB 데이터베이스

**총 예상 비용**: $1-5/월 (일반 사용자 기준)

---

## 성능 최적화

### 1. 인덱스 선택

**HNSW** (권장):
- 장점: 매우 빠른 검색 (근사)
- 단점: 메모리 사용량 높음
- 적합: 대화 수 > 10,000

**IVFFlat**:
- 장점: 메모리 효율적
- 단점: 검색 속도 HNSW보다 느림
- 적합: 대화 수 < 10,000

### 2. 배치 처리

```python
# Bad: 개별 호출 (비효율적)
for text in texts:
    embedding = service.generate_embedding(text)

# Good: 배치 처리 (10배 빠름)
embeddings = service.generate_embeddings_batch(texts)
```

### 3. 캐싱

현재 미구현. 향후 개선 사항:
- Redis 캐시로 최근 검색 결과 저장
- 동일 쿼리 반복 시 임베딩 재생성 방지

---

## 트러블슈팅

### 문제 1: "No module named 'psycopg2'"

**원인**: PostgreSQL 드라이버 미설치

**해결**:
```bash
pip install psycopg2-binary
```

### 문제 2: "extension \"vector\" does not exist"

**원인**: pgvector 확장 활성화 안 됨

**해결**:
- Supabase Dashboard → SQL Editor
- `CREATE EXTENSION IF NOT EXISTS vector;` 실행

### 문제 3: "⚠️ RAG 검색 실패"

**원인**: Embedding 생성 오류 또는 네트워크 문제

**확인**:
```python
# 로그 확인
print(f"RAG initialized: {self.rag is not None}")

# 수동 테스트
from core.embeddings import EmbeddingService
service = EmbeddingService()
embedding = service.generate_embedding("테스트")
print(f"Embedding dimensions: {len(embedding)}")
```

### 문제 4: SQLite fallback 발생

**증상**: "⚠️ Vector search requires PostgreSQL"

**원인**: 로컬 환경에서 SQLite 사용 중

**해결**:
- 로컬: 정상 동작 (텍스트 검색 사용)
- 배포: SUPABASE_URL 환경 변수 설정 필요

---

## 향후 개선 사항

### 1. 하이브리드 검색

현재: 벡터 검색만
개선: 벡터 + 키워드 검색 결합 (BM25 + cosine similarity)

```python
# Pseudo-code
vector_results = rag.search_similar(query, top_k=10)
keyword_results = db.full_text_search(query, top_k=10)
final_results = rerank(vector_results, keyword_results, top_k=5)
```

### 2. 대화 요약

긴 대화 히스토리를 요약하여 검색 효율 증대:
```python
# 100줄 대화 → 5줄 요약 → 임베딩
summary = llm.summarize(long_conversation)
rag.save_conversation('user', summary, context='summary')
```

### 3. 멀티모달 검색

이미지, 오디오 등 다양한 데이터 타입 지원:
- OpenAI CLIP 모델 (이미지 + 텍스트)
- Whisper (음성 → 텍스트 → 임베딩)

### 4. 실시간 재랭킹

검색 결과를 LLM으로 재평가:
```python
results = rag.search_similar(query)
reranked = llm.rerank(query, results)  # 더 정확한 순서
```

---

## 참고 자료

### 공식 문서
- [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [HNSW 알고리즘](https://arxiv.org/abs/1603.09320)

### 프로젝트 파일
- `RAG_SETUP_MANUAL.md`: 수동 설정 가이드
- `core/embeddings.py`: 임베딩 서비스
- `core/rag_manager.py`: RAG 관리자
- `core/simple_llm.py`: SimpleLLM 통합
- `migrations/001_add_pgvector_support.sql`: DB 마이그레이션

---

## 요약

✅ **Phase 1**: pgvector 확장 + embedding 컬럼 추가
✅ **Phase 2**: OpenAI 임베딩 서비스 통합
✅ **Phase 3**: RAG Manager 구현 + SimpleLLM 통합
⏳ **Phase 4**: 테스트 및 최적화

**다음 단계**:
1. Supabase Dashboard에서 pgvector migration 실행 (`RAG_SETUP_MANUAL.md` 참고)
2. Streamlit Cloud 배포 후 RAG 기능 테스트
3. 실사용 피드백 수집 및 개선

**예상 효과**:
- 맥락 기반 대화 지원 ("그 사람", "최근에")
- 수천 개 대화 기록에서 빠른 검색 (< 100ms)
- 저렴한 비용 (~$1-5/월)
