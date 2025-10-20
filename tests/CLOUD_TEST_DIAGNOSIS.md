# Streamlit Cloud 테스트 진단 결과

## 날짜
2025-01-20

## URL
https://horcrux-hg9pdyk9fgvzqwmdwxjdfj.streamlit.app/

---

## 문제 확인

### 테스트 결과
✅ **Test 1**: "이창하는 대학교 때 친해진 형이야" → 성공
   - 응답: "이창하 정보 저장. 관계: 형."
   - people 테이블에 저장 완료

❌ **Test 2**: "그 사람 누구야?" → **실패**
   - 응답: "불확실. 추가 정보가 필요합니다."
   - 예상: "이창하는 대학교 때 친해진 형입니다."

---

## 근본 원인

### RAG 시스템 미초기화

**원인**: `OPENAI_API_KEY` 환경 변수가 Streamlit Cloud Secrets에 설정되지 않음

**영향 체인**:
```
1. EmbeddingService.__init__() 실행
   ↓ (OPENAI_API_KEY 없음)
2. ValueError("OPENAI_API_KEY not found in environment") 발생
   ↓
3. RAGManager.__init__() 실패
   ↓
4. SimpleLLM.__init__() 에서 except 블록으로 이동
   ↓
5. self.rag = None 설정
   ↓
6. query_memory 실행 시 RAG 검색 건너뜀
   ↓
7. 기본 SQL 검색만 실행 (LIKE '%그 사람%')
   ↓
8. "이창하" 데이터와 매칭 실패
   ↓
9. 응답: "불확실. 추가 정보가 필요합니다."
```

### 코드 위치

**core/simple_llm.py:40-48**
```python
# RAG 초기화 (대화 메모리 + 벡터 검색)
try:
    db_wrapper = Database()
    db_wrapper.conn = db_conn
    db_wrapper.db_type = 'postgres' if os.getenv("SUPABASE_URL") else 'sqlite'
    self.rag = RAGManager(db_wrapper)
except Exception as e:
    print(f"⚠️  RAG 초기화 실패: {e}")
    self.rag = None  # ← RAG 비활성화
```

**core/embeddings.py:20-22**
```python
self.api_key = api_key or os.getenv("OPENAI_API_KEY")
if not self.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment")
```

**core/simple_llm.py:558**
```python
# RAG 기반 대화 검색 (최우선)
if self.rag:  # ← None이면 건너뜀!
    try:
        conversations = self.rag.search_similar_conversations(query, top_k=5)
```

---

## 해결 방법

### 1. Streamlit Cloud Secrets 설정

1. **Streamlit Cloud 대시보드 접속**
   - https://share.streamlit.io/

2. **앱 설정 열기**
   - Horcrux 앱 선택
   - Settings → Secrets 탭

3. **Secrets 추가**
   ```toml
   # .streamlit/secrets.toml

   OPENAI_API_KEY = "sk-..."  # 실제 키로 교체

   SUPABASE_URL = "postgresql://postgres:devswha1%21@db.hfaucafjyxyrzhhlcyvy.supabase.co:5432/postgres"
   SUPABASE_KEY = "eyJhbGci..."  # 실제 키로 교체
   ```

4. **저장 및 재배포**
   - "Save" 클릭
   - 앱 자동 재시작

### 2. 로컬 테스트 (선택 사항)

로컬에서도 동일한 문제가 있으면 `.env` 파일에 추가:

```bash
# .env
OPENAI_API_KEY=sk-...
SUPABASE_URL=postgresql://...
SUPABASE_KEY=eyJhbGci...
```

---

## 검증 방법

### Secrets 설정 후 테스트 시나리오

```
1. "이창하는 대학교 때 친해진 형이야"
   → "이창하 정보 저장. 관계: 형."

2. "그 사람 누구야?"
   → ✅ "이창하는 대학교 때 친해진 형입니다." (성공!)

3. "어제 7시간 자고 30분 운동했어"
   → "수면 7h 기록. 목표 충족. 운동 30min 기록. 목표 충족."

4. "운동 얼마나 했지?"
   → ✅ "어제 30분 운동하셨습니다." (벡터 검색으로 찾음)
```

### 로그 확인

앱 시작 시 다음 메시지가 표시되어야 함:
```
✓ PostgreSQL (Supabase) 연결 성공
✓ RAG Manager initialized  ← 이 메시지가 중요!
```

만약 다음 메시지가 표시되면 여전히 문제:
```
⚠️  RAG 초기화 실패: OPENAI_API_KEY not found in environment
```

---

## 로컬 vs 클라우드 비교

### 현재 상태 (OPENAI_API_KEY 없음)

| 기능 | 로컬 (SQLite) | 클라우드 (PostgreSQL) |
|------|---------------|----------------------|
| 데이터 저장 | ✅ | ✅ |
| 명확한 검색 ("이창하") | ✅ | ✅ |
| 모호한 검색 ("그 사람") | ❌ | ❌ |
| RAG 시스템 | ❌ 미초기화 | ❌ 미초기화 |
| 벡터 임베딩 | ❌ | ❌ |

### 수정 후 (OPENAI_API_KEY 설정)

| 기능 | 로컬 (SQLite) | 클라우드 (PostgreSQL) |
|------|---------------|----------------------|
| 데이터 저장 | ✅ | ✅ |
| 명확한 검색 ("이창하") | ✅ | ✅ |
| 모호한 검색 ("그 사람") | ⚠️ (텍스트만) | ✅ **벡터 검색!** |
| RAG 시스템 | ✅ 초기화됨 | ✅ 초기화됨 |
| 벡터 임베딩 | ⚠️ (생성하지만 미저장) | ✅ **pgvector 저장** |

---

## 비용 예상

### OpenAI API 비용
- **모델**: text-embedding-3-small
- **가격**: $0.02 / 1M tokens
- **예상**: 월 1만 대화 기준 ~$0.10 (약 100원)

### 총 예상 월 비용
- OpenAI Embeddings: ~$0.10
- Supabase (무료 티어): $0
- **합계**: ~$1-5/월 (대화량에 따라)

---

## 다음 단계

### 즉시 실행
1. ✅ Streamlit Cloud Secrets에 `OPENAI_API_KEY` 추가
2. ✅ 앱 재시작 확인
3. ✅ 테스트 시나리오 재실행

### 성공 시
1. 클라우드 테스트 결과 문서화
2. GitHub에 커밋
3. RAG 시스템 완전 활성화 선언 🎉

### 실패 시
1. Streamlit Cloud 로그 확인
2. OPENAI_API_KEY 형식 검증
3. 로컬에서 `.env` 테스트

---

## 결론

**문제**: OPENAI_API_KEY 미설정으로 RAG 시스템 비활성화
**해결**: Streamlit Cloud Secrets에 키 추가
**예상**: 벡터 검색 완전 활성화로 모든 테스트 통과

**현재 상태**: PostgreSQL + pgvector 인프라는 완벽하게 구축됨 ✅
**필요 사항**: API 키 설정만 하면 즉시 작동 가능 🚀
