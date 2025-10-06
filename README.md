# LifeBot 🤖

건강/할일 관리 에이전트 시스템 with 게임화 (레벨업 시스템)

## 프로젝트 개요

대화형 입력을 통해 건강 지표와 할일을 추적하고, 레벨업 시스템으로 동기부여를 제공하는 AI 에이전트 시스템

## 현재 상태: 모든 Phase 완료 ✅

### Phase 1: 기본 인프라 ✅
- ✅ DB 구축 (9개 테이블)
- ✅ DataManagerAgent 구현
- ✅ GamificationAgent 구현
- ✅ 간단한 CLI 인터페이스

### Phase 2: 한국어 자연어 처리 ✅
- ✅ 한국어 파서 (날짜, 수량, 패턴)
- ✅ ConversationAgent (의도 파악)
- ✅ CoachingAgent (알림 규칙)
- ✅ OrchestratorAgent (에이전트 조율)
- ✅ 자연어 CLI

### Phase 4: 웹 UI & 시각화 ✅
- ✅ Streamlit 대시보드
- ✅ 채팅 인터페이스
- ✅ 건강 지표 차트 (Plotly)
- ✅ 레벨/경험치 프로그레스 바
- ✅ 업적 갤러리 (20개)
- ✅ 주간 통계 및 분석

## 빠른 시작

### 1. 데이터베이스 초기화

```bash
python3 core/database.py
```

### 2. 실행

#### 웹 대시보드 (추천) 🌟

```bash
streamlit run app.py
```

웹 브라우저에서 `http://localhost:8501` 접속

**기능:**
- 💬 **채팅**: 자연어로 대화하며 기록
- 📊 **대시보드**: 오늘 요약, 주간 트렌드 차트
- 📈 **분석**: 주간 통계, 경험치 내역
- 🏆 **업적**: 업적 갤러리 및 진행도

#### 자연어 CLI

```bash
python3 main_natural.py
```

**사용 예시:**
```
💬 > 어제 5시간 잤어
✓ 수면 기록 완료: 5.0시간
⚠️ 목표(7시간)보다 2.0시간 부족합니다. 충분한 수면이 중요해요!

💬 > 30분 운동했어
✓ 운동 기록 완료: 30분
✓ 목표 달성! 30분 운동 훌륭합니다!
  +10 XP

💬 > 카드비 계산해야 해
✓ 할일 추가: [1] 카드비 계산

💬 > 할일 1 완료
✓ 할일 완료: 카드비 계산
  +20 XP

💬 > 오늘 요약
📊 2025-10-05 요약

💤 수면: 5.0시간
💪 운동: 30분
🍗 단백질: 기록 없음
📝 할일: 완료 1/1

💬 > 진행도
📊 Level 1 (30/100 XP) | 🏆 업적 0/6
진행도: [======              ] 30.0%
```

#### 명령어 버전 (Phase 1)

```bash
python3 main.py
```

**사용 예시:**
```
명령> add_sleep 7
✓ 수면 기록 완료: 7.0시간
  +15 XP

명령> add_workout 30
✓ 운동 기록 완료: 30분
  +10 XP

명령> summary
📊 2025-10-05 요약
...
```

## 주요 기능

### 건강 지표 추적
- 수면 시간
- 운동 시간
- 단백질 섭취량
- 체중
- 커스텀 메트릭 (BMI, 혈압 등)

### 할일 관리
- 할일 추가/완료
- 우선순위 설정
- 마감일 관리

### 습관 추적
- 습관 생성
- Streak 카운트
- 성공/실패 기록

### 레벨업 시스템
- 행동에 따른 경험치 획득
  - 할일 완료: +20 XP
  - 수면 목표 달성: +15 XP
  - 운동: +10 XP
  - 공부/커리어: +30 XP
- 레벨업 시스템 (Level 1 → 2: 100 XP)
- 업적 시스템 (6개 기본 업적)

## 아키텍처

### 에이전트
1. **OrchestratorAgent** - 조율자 (Phase 2)
2. **ConversationAgent** - 자연어 파싱 (Phase 2)
3. **DataManagerAgent** - 데이터 관리 ✅
4. **CoachingAgent** - 알림 및 인사이트 (Phase 2)
5. **GamificationAgent** - 레벨업 시스템 ✅

### 데이터베이스 스키마
- `daily_health`: 일일 건강 지표
- `custom_metrics`: 커스텀 메트릭
- `habits` / `habit_logs`: 습관 추적
- `tasks`: 할일
- `user_progress`: 레벨/경험치
- `exp_logs`: 경험치 로그
- `achievements` / `achievement_logs`: 업적

## 스크린샷

웹 대시보드의 주요 기능:
- 💬 채팅: 자연어 입력 및 실시간 대화
- 📊 대시보드: 건강 메트릭 카드 + 주간 트렌드 차트
- 📈 분석: 주간 통계 + 경험치 분석
- 🏆 업적: 업적 갤러리 + 달성률

자세한 사용법은 [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) 참조

### Phase 3: LLM 통합 & 고급 기능 ✅

- ✅ LLM 통합 (Claude/OpenAI API)
  - `core/llm_client.py`: LLM 추상화 레이어
  - ConversationAgent: 정규식 실패 시 LLM 백업
  - CoachingAgent: LLM 기반 개인화된 조언
- ✅ 고급 업적 시스템 (6개 → 20개 확장)
  - 수면, 운동, 영양, 할일, 습관, 종합 카테고리
  - 실시간 업적 체크 로직 구현
- ✅ 설정 파일 및 환경 변수 관리
  - `config.yaml`: LLM 설정, 타겟, XP 규칙
  - `.env.example`: API 키 템플릿

**LLM 사용법:**
```bash
# 1. API 키 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 또는 OPENAI_API_KEY 입력

# 2. config.yaml에서 LLM 활성화
llm:
  enabled: true
  provider: "claude"  # or "openai"
  strategy: "fallback"  # 정규식 실패 시에만 사용
```

## 개발 환경

**필수:**
- Python 3.8+
- SQLite3
- PyYAML
- Streamlit (웹 UI)
- Plotly (차트)

**선택 (Phase 3 LLM):**
- anthropic (Claude API)
- openai (OpenAI API)
- python-dotenv (환경 변수)

**설치:**
```bash
# 기본 의존성
pip install -r requirements.txt

# LLM 기능 사용 시 (선택)
pip install anthropic openai python-dotenv
```

## 주요 파일 구조

```
LifeBot/
├── agents/              # 에이전트 (5개)
│   ├── conversation.py  # 자연어 파싱 + LLM 백업
│   ├── coaching.py      # 알림 + LLM 조언
│   ├── data_manager.py  # 데이터 CRUD
│   ├── gamification.py  # XP/레벨/업적
│   └── orchestrator.py  # 조율자
├── core/
│   ├── database.py      # DB 스키마 (9 테이블)
│   └── llm_client.py    # LLM 추상화 (Phase 3)
├── parsers/             # 한국어 파서
├── app.py               # 웹 대시보드 (Streamlit)
├── main_natural.py      # 자연어 CLI
├── config.yaml          # 설정
└── .env.example         # API 키 템플릿
```

## 라이선스

MIT
