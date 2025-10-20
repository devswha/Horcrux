# Supabase Pooler 설정 가이드 (즉시 실행)

## 문제
Streamlit Cloud가 IPv6를 지원하지 않아 PostgreSQL 연결 실패

## 해결책
Supabase Connection Pooler 사용 (IPv4 전용, 포트 6543)

---

## 1단계: Supabase에서 Pooler URL 얻기

### 방법 1: Supabase 대시보드 (권장)

1. **Supabase 대시보드 접속**
   - https://supabase.com/dashboard/project/hfaucafjyxyrzhhlcyvy

2. **Database Settings 이동**
   - 좌측 메뉴: Settings (⚙️) → Database

3. **Connection Pooling 섹션 찾기**
   - "Connection Pooling" 또는 "Pooler" 섹션

4. **Transaction Mode 선택**
   - Mode: Transaction (권장)
   - Port: 6543

5. **Connection String 복사**
   - 형식: `postgresql://postgres.hfaucafjyxyrzhhlcyvy:[PASSWORD]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres`

### 방법 2: 직접 구성 (빠름)

비밀번호가 `devswha1!`라면:

```
postgresql://postgres.hfaucafjyxyrzhhlcyvy:devswha1%21@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
```

**참고**: `!` → `%21` (URL 인코딩)

---

## 2단계: Streamlit Cloud Secrets 업데이트

1. **Streamlit Cloud 대시보드 접속**
   - https://share.streamlit.io/

2. **Horcrux 앱 선택**
   - 앱 목록에서 "Horcrux" 찾기

3. **Settings → Secrets**
   - 우측 상단: ⚙️ (Settings)
   - 좌측 메뉴: Secrets

4. **SUPABASE_URL 수정**

**수정 전**:
```toml
SUPABASE_URL = "postgresql://postgres:devswha1%21@db.hfaucafjyxyrzhhlcyvy.supabase.co:5432/postgres"
```

**수정 후**:
```toml
SUPABASE_URL = "postgresql://postgres.hfaucafjyxyrzhhlcyvy:devswha1%21@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
```

**전체 Secrets**:
```toml
OPENAI_API_KEY = "sk-proj-..."

SUPABASE_URL = "postgresql://postgres.hfaucafjyxyrzhhlcyvy:devswha1%21@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"

SUPABASE_KEY = "eyJhbGci..."
```

5. **저장 및 재배포**
   - "Save" 버튼 클릭
   - 앱이 자동으로 재시작됨 (30초~1분)

---

## 3단계: 검증

### 디버그 패널 확인 (앱 화면)

1. **Streamlit 앱 접속**
   - https://horcrux-hg9pdyk9fgvzqwmdwxjdfj.streamlit.app/

2. **사이드바 → "🔍 디버그 정보" 확장**

3. **확인 사항**:
   ```
   ✅ DB 타입: postgres (이전: sqlite)
   ✅ RAG 활성화: True
   ✅ PostgreSQL 연결 실패: (메시지 없음)
   ```

4. **환경 변수 상태**:
   ```
   ✅ OPENAI_API_KEY
   ✅ SUPABASE_URL
   ✅ SUPABASE_KEY
   ```

### 기능 테스트 (채팅 화면)

**Test 1**: 데이터 저장
```
User: "이창하는 대학교 때 친해진 형이야"
Expected: "이창하 정보 저장. 관계: 형."
```

**Test 2**: 벡터 검색 (핵심!)
```
User: "그 사람 누구야?"
Expected: "이창하는 대학교 때 친해진 형입니다."
```

**Test 3**: 건강 데이터
```
User: "어제 7시간 자고 30분 운동했어"
Expected: "수면 7h 기록. 운동 30min 기록."
```

**Test 4**: 맥락 기반 검색
```
User: "운동 얼마나 했지?"
Expected: "어제 30분 운동하셨습니다." (벡터 검색으로 찾음)
```

---

## 문제 해결

### ❌ 여전히 "DB 타입: sqlite"로 표시됨

1. **Streamlit Cloud 로그 확인**
   - 앱 설정 → Logs
   - `⚠ PostgreSQL 연결 실패` 메시지 확인

2. **Pooler URL 재확인**
   - 호스트: `aws-0-ap-northeast-2.pooler.supabase.com`
   - 포트: `6543`
   - 사용자: `postgres.hfaucafjyxyrzhhlcyvy`

3. **비밀번호 인코딩 확인**
   - `!` → `%21`
   - `@` → `%40`
   - `#` → `%23`

### ❌ "그 사람 누구야?" 여전히 실패

1. **RAG 활성화 확인**
   - 디버그 패널: "RAG 활성화: True"

2. **Supabase conversation_memory 테이블 확인**
   - Supabase Dashboard → Table Editor
   - `conversation_memory` 테이블에 데이터 있는지 확인
   - `embedding` 컬럼에 벡터 값 있는지 확인

3. **OPENAI_API_KEY 확인**
   - 디버그 패널에서 ✅ 표시 확인

---

## 변경 사항 요약

| 항목 | Direct Connection (기존) | Connection Pooler (신규) |
|------|--------------------------|-------------------------|
| 호스트 | `db.xxx.supabase.co` | `aws-0-ap-northeast-2.pooler.supabase.com` |
| 포트 | `5432` | `6543` |
| 사용자명 | `postgres` | `postgres.hfaucafjyxyrzhhlcyvy` |
| IPv6 | ✅ (로컬 작동) | ❌ (IPv4만) |
| Streamlit Cloud | ❌ (IPv6 미지원) | ✅ (IPv4 지원) |
| Connection Pooling | ❌ | ✅ (성능 향상) |

---

## 참고

- **상세 문서**: STREAMLIT_CLOUD_IPv6_FIX.md
- **배포 상태**: STREAMLIT_CLOUD_DEPLOYMENT_STATUS.md
- **Supabase 문서**: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler
