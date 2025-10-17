# Horcrux 배포 가이드

Horcrux를 Streamlit Community Cloud에 무료로 배포하는 방법을 안내합니다.

## 사전 준비

- [x] GitHub 저장소: https://github.com/devswha/Horcrux
- [x] requirements.txt 준비 완료
- [x] .streamlit/config.toml 설정 완료
- [ ] Streamlit Cloud 계정 (GitHub로 로그인)

## 배포 단계

### 1. 변경사항 GitHub에 푸시

```bash
# 현재 변경사항 확인
git status

# 변경사항 스테이징
git add .

# 커밋
git commit -m "Add Streamlit Cloud deployment config"

# GitHub에 푸시
git push origin main
```

### 2. Streamlit Community Cloud 계정 생성

1. https://share.streamlit.io/ 접속
2. "Sign up" 클릭
3. **GitHub 계정으로 로그인** (권장)
4. Streamlit이 GitHub 저장소에 접근할 수 있도록 권한 부여

### 3. 앱 배포하기

1. Streamlit Cloud 대시보드에서 **"New app"** 클릭
2. 배포 설정:
   - **Repository**: `devswha/Horcrux`
   - **Branch**: `main`
   - **Main file path**: `interfaces/app.py`
3. **"Advanced settings"** 클릭하여 환경 변수 설정

### 4. Secrets 설정 (중요!)

앱이 정상 작동하려면 API 키를 설정해야 합니다:

1. "Advanced settings" → "Secrets" 탭
2. 다음 형식으로 입력:

```toml
OPENAI_API_KEY = "sk-proj-xxxxx"

# 선택 사항
ANTHROPIC_API_KEY = "sk-ant-xxxxx"
```

3. **"Save"** 클릭

### 5. 배포 시작

- **"Deploy!"** 버튼 클릭
- 배포 과정 (약 2-5분 소요):
  1. 저장소 클론
  2. 의존성 설치 (requirements.txt)
  3. 앱 시작
  4. 상태 확인

### 6. 배포 완료

- 배포가 완료되면 자동으로 앱 URL이 생성됩니다:
  - 예: `https://devswha-horcrux.streamlit.app`
- 이 URL을 통해 어디서든 앱에 접속 가능

## 배포 후 관리

### 자동 배포

- GitHub의 `main` 브랜치에 푸시할 때마다 **자동으로 재배포**
- 별도의 배포 명령 불필요

### 로그 확인

1. Streamlit Cloud 대시보드에서 앱 선택
2. "Manage app" → "Logs" 탭
3. 실시간 로그 및 에러 확인

### Secrets 수정

1. Streamlit Cloud 대시보드에서 앱 선택
2. "Settings" → "Secrets"
3. API 키 수정 후 저장
4. 앱이 자동으로 재시작됩니다

### 앱 중지/재시작

- "Manage app" → "Reboot" 또는 "Delete"

## 데이터베이스 주의사항

현재 Horcrux는 **SQLite 로컬 DB** (`horcrux.db`)를 사용합니다.

### 배포 환경에서의 제한사항

- Streamlit Cloud는 **휘발성 스토리지** 사용
- 앱 재시작 시 데이터가 **초기화**됩니다
- 데이터를 유지하려면 다음 옵션 고려:
  1. **Supabase** (PostgreSQL) - 무료 티어 제공
  2. **Turso** (libSQL) - SQLite 호환 클라우드 DB
  3. **MongoDB Atlas** - NoSQL 옵션

### 영구 데이터베이스로 마이그레이션 (추후)

```bash
# Supabase 예시
pip install supabase
# core/database.py 수정하여 Supabase 연결
```

## 문제 해결

### 배포 실패 시

1. **로그 확인**: "Manage app" → "Logs"
2. **흔한 에러**:
   - `ModuleNotFoundError`: requirements.txt에 패키지 추가
   - `OPENAI_API_KEY not found`: Secrets 설정 확인
   - `Port already in use`: 자동 해결됨 (재시작)

### 앱이 느릴 때

- 무료 티어는 리소스가 제한적입니다
- 사용하지 않으면 자동으로 슬립 모드 진입
- 첫 접속 시 깨어나는데 시간 소요 (cold start)

### API 키 보안

- **절대 코드에 하드코딩하지 마세요**
- Streamlit Cloud의 Secrets 기능 사용
- `.env` 파일은 `.gitignore`에 포함되어 있음

## 로컬 개발

배포 후에도 로컬 개발을 계속할 수 있습니다:

```bash
# 로컬에서 실행
streamlit run interfaces/app.py

# 또는
./run.sh web
```

## 참고 자료

- [Streamlit Cloud 공식 문서](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets 관리 가이드](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [배포 제한사항](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/resource-limits)

## 배포 체크리스트

- [ ] GitHub 저장소에 코드 푸시
- [ ] Streamlit Cloud 계정 생성
- [ ] 새 앱 생성 (Repository: devswha/Horcrux, Main file: interfaces/app.py)
- [ ] Secrets에 OPENAI_API_KEY 설정
- [ ] 배포 완료 및 URL 확인
- [ ] 웹 브라우저에서 앱 테스트
- [ ] 채팅 기능 및 데이터 보기 동작 확인

---

질문이나 문제가 발생하면 [GitHub Issues](https://github.com/devswha/Horcrux/issues)에 남겨주세요!
