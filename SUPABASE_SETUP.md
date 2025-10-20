# Supabase + Streamlit Cloud 배포 가이드

Horcrux를 Streamlit Cloud에 배포하고 Supabase PostgreSQL로 데이터를 영구 저장하는 방법입니다.

## 문제 상황

Streamlit Cloud는 ephemeral filesystem을 사용하기 때문에:
- SQLite 파일(`horcrux.db`)이 앱 재시작/재배포 시 삭제됨
- 데이터 영구 보존을 위해서는 외부 DB 필요 → **Supabase PostgreSQL 사용**

## 1. Supabase 프로젝트 생성

### 1-1. Supabase 계정 생성 및 프로젝트 생성

1. [https://supabase.com](https://supabase.com) 접속
2. "Start your project" 클릭 → GitHub 로그인
3. "New project" 클릭
4. 프로젝트 정보 입력:
   - **Name**: `horcrux-db` (또는 원하는 이름)
   - **Database Password**: 안전한 비밀번호 생성 (메모 필수!)
   - **Region**: `Northeast Asia (Seoul)` 선택 (한국 사용자의 경우 지연 최소화)
   - **Pricing Plan**: Free tier 선택
5. "Create new project" 클릭 (약 2분 소요)

### 1-2. 연결 정보 확인

프로젝트 생성 완료 후:

1. 좌측 메뉴에서 **Settings** → **Database** 클릭
2. **Connection string** 섹션에서 다음 정보 복사:
   - **Connection string (URI)**: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`
   - `[YOUR-PASSWORD]` 부분을 1-1에서 설정한 비밀번호로 교체

예시:
```
postgresql://postgres:MySecurePass123@db.abcdefghijk.supabase.co:5432/postgres
```

3. **API Settings** (좌측 메뉴: Settings → API)에서 다음 복사:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public** key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## 2. Streamlit Cloud 배포

### 2-1. GitHub Repository 연결

1. [https://share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정 로그인
3. "New app" 클릭
4. Repository 선택:
   - **Repository**: `devswha/Horcrux`
   - **Branch**: `main`
   - **Main file path**: `interfaces/app.py`

### 2-2. Secrets 설정

"Advanced settings" → "Secrets" 탭에서 다음 내용 입력:

```toml
# OpenAI API 키
OPENAI_API_KEY = "sk-..."

# Supabase 연결 정보
SUPABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"
SUPABASE_KEY = "your-supabase-anon-key"
```

**주의**:
- `SUPABASE_URL`: 위 1-2에서 복사한 Connection string 전체 입력
- `SUPABASE_KEY`: 위 1-2에서 복사한 anon public key 입력
- `OPENAI_API_KEY`: OpenAI API 키 입력

### 2-3. 배포 시작

1. "Deploy!" 클릭
2. 첫 배포는 약 3-5분 소요 (패키지 설치 포함)
3. 배포 완료 후 자동으로 URL 생성: `https://your-app-name.streamlit.app`

## 3. 데이터베이스 스키마 초기화

첫 배포 후 Streamlit 앱이 자동으로 스키마를 초기화합니다:

1. 앱 접속 → 로딩 중 콘솔에 "✓ PostgreSQL (Supabase) 연결 성공" 표시
2. 테이블이 없으면 자동으로 `init_schema()` 호출 → 13개 테이블 생성

**수동 확인 방법** (선택사항):

Supabase Dashboard → **Table Editor**에서 생성된 테이블 목록 확인:
- daily_health, custom_metrics, habits, habit_logs, tasks
- user_progress, exp_logs, learning_logs
- people, interactions, knowledge_entries, reflections, conversation_memory

## 4. 동작 원리

### Database 클래스 자동 전환

`core/database.py`는 환경 변수를 감지하여 자동으로 DB 선택:

```python
# 로컬 개발 (환경 변수 없음)
$ python3 interfaces/app.py
→ SQLite (horcrux.db) 사용

# Streamlit Cloud (환경 변수 있음)
SUPABASE_URL=postgresql://...
SUPABASE_KEY=...
→ PostgreSQL (Supabase) 사용
```

### SQL 문법 자동 변환

```python
# SQLite
CREATE TABLE daily_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
)

# PostgreSQL
CREATE TABLE daily_health (
    id SERIAL PRIMARY KEY,
    ...
)
```

코드에서 `self.db_type`을 감지하여 자동 변환.

## 5. 기존 배포 업데이트

기존 Streamlit Cloud 앱 (`https://horcrux-hg9pdyk9fgvzqwmdwxjdfj.streamlit.app/`)을 업데이트하는 경우:

1. Streamlit Cloud Dashboard → 앱 선택
2. **Settings** → **Secrets** 클릭
3. 위 2-2의 Secrets 내용 추가/업데이트
4. **Reboot app** 클릭 → 앱 재시작
5. 로그 확인: "✓ PostgreSQL (Supabase) 연결 성공" 표시되면 완료

## 6. 로컬 테스트 (선택사항)

Supabase 연결을 로컬에서 테스트하려면:

```bash
# .env 파일에 추가
SUPABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
SUPABASE_KEY="your-supabase-anon-key"

# psycopg2 설치
pip install psycopg2-binary

# 앱 실행
streamlit run interfaces/app.py
```

콘솔에 "✓ PostgreSQL (Supabase) 연결 성공" 표시되면 정상.

## 7. 트러블슈팅

### 오류: "No module named 'psycopg2'"

**원인**: PostgreSQL 드라이버 미설치

**해결**:
```bash
pip install psycopg2-binary
```

또는 `requirements.txt`에 추가:
```
psycopg2-binary==2.9.9
```

### 오류: "Connection refused" 또는 "Connection timeout"

**원인**: SUPABASE_URL 오류 또는 네트워크 문제

**해결**:
1. Supabase Dashboard → Settings → Database → Connection string 재확인
2. 비밀번호에 특수문자가 있으면 URL encoding 필요 (`@` → `%40`, `#` → `%23` 등)
3. Supabase 프로젝트가 paused 상태인지 확인 (Free tier는 1주일 비활동 시 일시정지)

### 오류: "relation does not exist"

**원인**: 테이블이 생성되지 않음

**해결**:
```python
# Python 콘솔에서 수동 실행
from core.database import Database
import os
os.environ['SUPABASE_URL'] = 'postgresql://...'
os.environ['SUPABASE_KEY'] = '...'

db = Database()
db.connect()
db.init_schema()
db.close()
```

### SQLite로 fallback되는 경우

**증상**: 콘솔에 "⚠ PostgreSQL 연결 실패, SQLite로 fallback" 표시

**원인**:
- `SUPABASE_URL` 또는 `SUPABASE_KEY` 환경 변수 미설정
- `psycopg2` 패키지 미설치
- Supabase 연결 정보 오류

**해결**: 위 6번 로컬 테스트 과정으로 연결 확인

## 8. 데이터 마이그레이션 (기존 SQLite → Supabase)

기존 로컬 SQLite 데이터를 Supabase로 이전하려면:

```bash
# 1. SQLite 데이터 덤프
sqlite3 horcrux.db .dump > data_dump.sql

# 2. Supabase SQL Editor에서 실행
# Supabase Dashboard → SQL Editor → New query
# data_dump.sql 내용 복사 → 실행

# 또는 Python 스크립트로 데이터 복사 (별도 스크립트 작성 필요)
```

## 요약

1. **Supabase 프로젝트 생성** → Connection string 복사
2. **Streamlit Cloud Secrets 설정** → SUPABASE_URL, SUPABASE_KEY 추가
3. **앱 재배포** → 자동으로 PostgreSQL 연결 및 테이블 생성
4. **데이터 영구 보존** ✓

문제 발생 시 Streamlit Cloud 로그 및 Supabase Dashboard → Logs 확인.
