# Streamlit Cloud 배포 준비 완료 ✅

## Supabase 연결 정보

**Project URL**: `https://hfaucafjyxyrzhhlcyvy.supabase.co`

**Connection String** (Supabase Dashboard → Settings → Database에서 확인):
```
postgresql://postgres:[YOUR_PASSWORD]@db.hfaucafjyxyrzhhlcyvy.supabase.co:5432/postgres
```

**API Key** (Supabase Dashboard → Settings → API에서 확인):
```
eyJhbGciOi... (anon/public key)
```

> 실제 값은 `.env` 파일 또는 Streamlit Cloud Secrets에서 설정하세요.

---

## 배포 절차 (3분 소요)

### 1. Streamlit Cloud 접속

https://share.streamlit.io 접속 후 로그인

### 2. 앱 선택

기존 앱: **horcrux-hg9pdyk9fgvzqwmdwxjdfj.streamlit.app** 선택

### 3. Secrets 설정

**Settings** → **Secrets** 클릭 후 다음 내용 **전체 복사 붙여넣기**:

```toml
# OpenAI API 키 (실제 키는 .env 또는 Streamlit secrets에서 가져오기)
OPENAI_API_KEY = "sk-proj-YOUR_OPENAI_API_KEY_HERE"

# Supabase PostgreSQL 연결 정보 (실제 비밀번호로 교체)
SUPABASE_URL = "postgresql://postgres:YOUR_DB_PASSWORD@db.hfaucafjyxyrzhhlcyvy.supabase.co:5432/postgres"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhmYXVjYWZqeXh5cnpoaGxjeXZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA5Mjc2NDYsImV4cCI6MjA3NjUwMzY0Nn0.NMqlMybcQVKnjoVJCHBFs9J40nN2Zz2foE2ZyCAWEnY"
```

**Save** 클릭

### 4. 앱 재시작

**Reboot app** 버튼 클릭 (또는 자동 재시작)

### 5. 확인

앱 로그에서 다음 메시지 확인:
- ✅ `✓ PostgreSQL (Supabase) 연결 성공`
- ✅ `✓ 데이터베이스 스키마 초기화 완료 (13개 테이블)`

---

## 배포 후 확인 사항

### Supabase Dashboard에서 테이블 확인

1. https://supabase.com/dashboard 접속
2. Horcrux 프로젝트 선택
3. **Table Editor** 클릭
4. 다음 13개 테이블 생성 확인:
   - daily_health
   - custom_metrics
   - habits
   - habit_logs
   - tasks
   - user_progress
   - exp_logs
   - learning_logs
   - people
   - interactions
   - knowledge_entries
   - reflections
   - conversation_memory

### 앱에서 테스트

1. https://horcrux-hg9pdyk9fgvzqwmdwxjdfj.streamlit.app/ 접속
2. 채팅 입력: "오늘 7시간 잤어"
3. 데이터 보기 탭 → 건강 데이터에서 기록 확인
4. Supabase Dashboard → Table Editor → daily_health 테이블에서도 동일한 데이터 확인

---

## 트러블슈팅

### 오류: "PostgreSQL 연결 실패, SQLite로 fallback"

**원인**: Secrets 설정이 안 되었거나 잘못됨

**해결**:
1. Streamlit Cloud → Settings → Secrets 확인
2. `SUPABASE_URL` 값이 정확한지 확인
3. 비밀번호에 특수문자가 있으면 그대로 입력 (URL encoding 불필요)

### 오류: "relation does not exist"

**원인**: 테이블이 자동 생성되지 않음

**해결**:
1. Streamlit Cloud 로그에서 `init_schema()` 실행 확인
2. 수동 생성 필요 시 아래 참고

---

## 수동 테이블 생성 (선택사항)

자동 생성 실패 시, Supabase Dashboard → SQL Editor에서 실행:

```sql
-- 파일: core/database.py의 init_schema() 메서드 SQL 참고
-- 13개 테이블 CREATE TABLE 문을 복사하여 실행
```

또는 Python으로:

```bash
python3 core/database.py
```

---

## 완료 후

배포 완료되면:
- ✅ 로컬 개발: SQLite (horcrux.db)
- ✅ 클라우드 배포: PostgreSQL (Supabase)
- ✅ 데이터 영구 보존
- ✅ 앱 재시작/재배포해도 데이터 유지

**배포 URL**: https://horcrux-hg9pdyk9fgvzqwmdwxjdfj.streamlit.app/
