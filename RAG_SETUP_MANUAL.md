# RAG 시스템 수동 설정 가이드

로컬 네트워크에서 Supabase PostgreSQL 연결이 안 되므로, Supabase Dashboard에서 직접 설정합니다.

## 1단계: pgvector 확장 활성화 (2분 소요)

### Supabase Dashboard에서 SQL 실행

1. **Supabase Dashboard 접속**: https://supabase.com/dashboard
2. **Horcrux 프로젝트 선택**: `https://hfaucafjyxyrzhhlcyvy.supabase.co`
3. **SQL Editor 열기**: 좌측 메뉴 → SQL Editor 클릭
4. **New query** 클릭
5. 아래 SQL 복사 → 붙여넣기 → **Run** 버튼 클릭:

```sql
-- Migration: Add pgvector support for RAG system
-- Phase 1: Enable pgvector extension and add embedding column

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to conversation_memory table (1536 dimensions for text-embedding-3-small)
ALTER TABLE conversation_memory
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for fast similarity search using HNSW (better than IVFFlat for most cases)
CREATE INDEX IF NOT EXISTS conversation_memory_embedding_idx
ON conversation_memory
USING hnsw (embedding vector_cosine_ops);
```

### 실행 결과 확인

성공 시 다음과 같은 메시지 표시:
```
Success. No rows returned
```

### 검증

**Table Editor**에서 `conversation_memory` 테이블 확인:
- 새로운 `embedding` 열이 추가됨 (타입: vector)

**SQL Editor**에서 다음 쿼리로 확인:
```sql
-- pgvector 확장 확인
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- embedding 열 확인
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'conversation_memory' AND column_name = 'embedding';

-- 인덱스 확인
SELECT indexname
FROM pg_indexes
WHERE tablename = 'conversation_memory' AND indexname = 'conversation_memory_embedding_idx';
```

예상 결과:
```
extname | extversion
--------|------------
vector  | 0.8.0

column_name | data_type
------------|----------
embedding   | USER-DEFINED

indexname
-------------------------------------
conversation_memory_embedding_idx
```

---

## 문제 해결

### 오류: "extension \"vector\" does not exist"

**원인**: pgvector가 Supabase에서 활성화되지 않음

**해결**: Supabase 무료 티어는 pgvector를 지원합니다. 단, 프로젝트가 최신 버전이어야 합니다.
1. Dashboard → Settings → General → "Pause Project" 클릭
2. "Resume Project" 클릭하여 재시작
3. 다시 SQL 실행

### 오류: "relation \"conversation_memory\" does not exist"

**원인**: 테이블이 아직 생성되지 않음

**해결**:
1. 로컬에서 Streamlit 앱 실행: `streamlit run interfaces/app.py`
2. 앱이 자동으로 테이블 생성
3. 또는 `python3 core/database.py` 실행하여 스키마 초기화
4. 다시 SQL 실행

### 오류: "access method \"hnsw\" does not exist"

**원인**: pgvector 0.5.0 이하 버전 사용 중 (HNSW는 0.5.0+에서 지원)

**해결**: IVFFlat 인덱스로 대체:
```sql
-- 기존 인덱스 삭제
DROP INDEX IF EXISTS conversation_memory_embedding_idx;

-- IVFFlat 인덱스 생성
CREATE INDEX conversation_memory_embedding_idx
ON conversation_memory
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 다음 단계

✅ Phase 1 완료 후:
- Phase 2: OpenAI 임베딩 모델 통합
- Phase 3: RAG 검색 구현
- Phase 4: 응답 생성 개선

**완료되면 알려주세요!** 다음 단계 진행하겠습니다.
