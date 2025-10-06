# LifeBot — 건강/할일 관리 에이전트 시스템 (게임화)

## 📋 프로젝트 개요
대화형 입력을 통해 건강 지표와 할일을 추적하고, 레벨업 시스템으로 동기부여를 제공하는 AI 에이전트 시스템

---

## 🤖 에이전트 아키텍처

### 1. OrchestratorAgent (조율자)
**책임:**
- 사용자 입력을 적절한 에이전트로 라우팅
- 에이전트 간 메시지 전달 및 응답 조합
- 전체 대화 흐름 관리 및 에러 핸들링

**주요 기능:**
```python
- route_message(user_input) -> Response
- coordinate_agents(message) -> Result
- handle_error(error) -> FallbackResponse
```

### 2. ConversationAgent (대화형 파싱)
**책임:**
- 한국어 자연어 입력 파싱 및 의도 파악
- 불명확한 입력에 대한 명확화 질문
- 대화 컨텍스트 유지 및 복합 명령 처리

**주요 기능:**
```python
- parse_input(text) -> ParsedIntent
- detect_intent(text) -> IntentType
- ask_clarification(ambiguity) -> Question
- extract_entities(text) -> Entities  # 날짜, 수량, 카테고리
```

**파싱 전략:**
- 정규식 기반 패턴 매칭 (빠른 처리)
- LLM 폴백 (복잡한 문장)
- 학습: 자주 쓰는 표현 패턴화

### 3. DataManagerAgent (데이터 관리)
**책임:**
- SQLite DB CRUD 작업
- 데이터 검증 및 무결성 체크
- 통계 집계 (일일/주간/월간 요약)
- 중복 데이터 처리 결정

**주요 기능:**
```python
- store_health_metric(date, metric_type, value) -> Result
- store_custom_metric(date, name, value, unit) -> Result
- store_task(title, due, priority) -> Result
- get_summary(date_range) -> Summary
- get_streak(habit_name) -> int
```

### 4. CoachingAgent (알림 및 인사이트)
**책임:**
- 건강 지표 모니터링 및 패턴 분석
- 알림 규칙 체크 및 경고 생성
- 개인화된 조언 및 격려 메시지
- 마일스톤 축하

**주요 기능:**
```python
- analyze_patterns(user_data) -> Insights
- generate_alerts(metrics) -> List[Alert]
- celebrate_milestone(achievement) -> Message
- suggest_action(context) -> Recommendation
```

**알림 규칙:**
- 수면 < 6시간 → 경고
- 3일 연속 수면 부족 → 강한 경고
- 운동 0분 → 권고
- 단백질 < 목표치 → 권고
- 할일 마감 1일 전 → 리마인드
- 습관 streak 중단 → 격려

### 5. GamificationAgent (레벨업 시스템) ⭐ NEW
**책임:**
- 행동에 따른 경험치 부여
- 레벨 계산 및 레벨업 처리
- 업적(achievement) 달성 체크
- 동기부여 메시지 생성

**주요 기능:**
```python
- award_exp(action_type, value) -> ExpGain
- check_level_up() -> LevelUpResult
- check_achievements() -> List[Achievement]
- get_progress_summary() -> ProgressStats
```

**경험치 획득 규칙:**
- 할일 완료: +20 XP (우선순위에 따라 +10~+50)
- 수면 목표 달성: +15 XP
- 운동 완료: +10 XP (시간에 비례)
- 단백질 목표 달성: +10 XP
- 습관 streak 유지: +5 XP/일 (streak 길이에 따라 보너스)
- 공부/커리어: +30 XP (시간 기록 시)
- 연속 기록: 7일 → +100 XP 보너스

**레벨 시스템:**
- Level 1: 0 XP
- Level 2: 100 XP
- Level 3: 250 XP
- Level N: `100 * N * (N-1) / 2` XP (누적)

**업적 시스템:**
- "아침형 인간": 7일 연속 7시간 이상 수면
- "운동 마스터": 30일 연속 운동 기록
- "철인": 할일 100개 완료
- "완벽주의자": 모든 목표 달성 7일 연속

---

## 🗄️ 데이터베이스 스키마 (하이브리드)

### 1. daily_health (일일 핵심 건강 지표)
```sql
CREATE TABLE daily_health (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    sleep_h REAL,
    workout_min INTEGER,
    protein_g REAL,
    weight_kg REAL,
    note TEXT,
    created_at TIMESTAMP
)
```

### 2. custom_metrics (유연한 메트릭)
```sql
CREATE TABLE custom_metrics (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    metric_name TEXT NOT NULL,  -- 'BMI', '혈압', '체지방률' 등
    value REAL NOT NULL,
    unit TEXT,
    category TEXT,
    note TEXT,
    created_at TIMESTAMP
)
```

### 3. habits (습관 정의)
```sql
CREATE TABLE habits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,  -- '금연', '물 2L 마시기' 등
    goal_type TEXT,
    target_value REAL,
    created_at TIMESTAMP
)
```

### 4. habit_logs (습관 추적)
```sql
CREATE TABLE habit_logs (
    id INTEGER PRIMARY KEY,
    habit_id INTEGER NOT NULL,
    date DATE NOT NULL,
    status TEXT,  -- 'success', 'fail', 'skip'
    streak_count INTEGER DEFAULT 0,
    note TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (habit_id) REFERENCES habits(id),
    UNIQUE(habit_id, date)
)
```

### 5. tasks (할일)
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    due DATE,
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'done'
    priority TEXT DEFAULT 'normal',  -- 'low', 'normal', 'high', 'urgent'
    category TEXT,  -- 'career', 'study', 'personal' 등
    note TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
)
```

### 6. user_progress (레벨/경험치) ⭐ NEW
```sql
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY,
    level INTEGER DEFAULT 1,
    current_exp INTEGER DEFAULT 0,
    total_exp INTEGER DEFAULT 0,
    updated_at TIMESTAMP
)
```

### 7. exp_logs (경험치 획득 로그) ⭐ NEW
```sql
CREATE TABLE exp_logs (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    action_type TEXT NOT NULL,  -- 'task_complete', 'sleep_goal', 'workout' 등
    exp_gained INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP
)
```

### 8. achievements (업적 정의) ⭐ NEW
```sql
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    condition_type TEXT,
    condition_value TEXT,  -- JSON으로 조건 저장
    exp_reward INTEGER DEFAULT 0,
    icon TEXT,
    created_at TIMESTAMP
)
```

### 9. achievement_logs (업적 달성 기록) ⭐ NEW
```sql
CREATE TABLE achievement_logs (
    id INTEGER PRIMARY KEY,
    achievement_id INTEGER NOT NULL,
    achieved_at TIMESTAMP,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id)
)
```

---

## 🔄 에이전트 간 메시지 흐름

### 예시 시나리오: "어제 5시간 자고 30분 운동했어"

```
1. 사용자 입력
   ↓
2. OrchestratorAgent
   - 입력 수신
   ↓
3. ConversationAgent
   - 파싱: {intent: "log_multiple", entities: [
       {type: "sleep", date: "2025-10-01", hours: 5},
       {type: "workout", date: "2025-10-01", minutes: 30}
     ]}
   ↓
4. DataManagerAgent
   - daily_health에 2개 메트릭 저장
   - 저장 성공
   ↓
5. CoachingAgent
   - 수면 < 6시간 → "⚠️ 목표보다 2시간 부족"
   - 운동 30분 → "✓ 목표 달성"
   ↓
6. GamificationAgent
   - 수면: 부족으로 XP 없음
   - 운동: +10 XP
   - 레벨 체크: Level 3 (250/350 XP)
   ↓
7. OrchestratorAgent
   - 응답 조합 및 사용자에게 전달
```

**최종 응답:**
```
✓ 2개 기록 완료

💤 수면: 5시간 (⚠️ 목표보다 2시간 부족)
💪 운동: 30분 (✓ 목표 달성!) +10 XP

📊 Level 3 (260/350 XP) | 🏆 업적 8/20
```

---

## 📁 프로젝트 구조

```
LifeBot/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # BaseAgent 추상 클래스
│   ├── orchestrator.py        # OrchestratorAgent
│   ├── conversation.py        # ConversationAgent
│   ├── data_manager.py        # DataManagerAgent
│   ├── coaching.py            # CoachingAgent
│   └── gamification.py        # GamificationAgent ⭐
├── core/
│   ├── database.py            # DB 스키마 및 연결
│   ├── models.py              # 데이터 모델 (Message, Intent, Alert 등)
│   ├── message_bus.py         # 에이전트 간 메시지 라우팅 (Phase 2)
│   └── config.py              # 설정 (목표치, XP 규칙 등)
├── parsers/
│   ├── korean_patterns.py     # 한국어 정규식 패턴
│   ├── date_parser.py         # 날짜 파싱 ("어제", "3일 전" 등)
│   ├── number_parser.py       # 수량 파싱 ("5시간", "30분" 등)
│   └── llm_parser.py          # LLM 기반 파싱 (선택적)
├── rules/
│   ├── health_rules.py        # 건강 알림 규칙
│   ├── habit_rules.py         # 습관 추적 규칙
│   ├── exp_rules.py           # 경험치 획득 규칙 ⭐
│   └── achievement_rules.py   # 업적 달성 조건 ⭐
├── interfaces/
│   ├── cli.py                 # CLI 인터페이스
│   └── web.py                 # 웹 UI (Streamlit, 향후)
├── tests/
│   ├── test_agents/
│   ├── test_parsers/
│   ├── test_rules/
│   └── test_integration/
├── main.py                    # 엔트리 포인트
├── requirements.txt
├── config.yaml                # 설정 파일
└── README.md
```

---

## 🛤️ 개발 로드맵

### Phase 1: MVP — 기본 인프라 (1주)
- [ ] **DB 구축** (2일)
  - [ ] database.py: 9개 테이블 스키마 생성
  - [ ] 인덱스 및 제약조건 설정
  - [ ] 초기 데이터 seeding (기본 업적, 설정)

- [ ] **데이터 관리 에이전트** (2일)
  - [ ] DataManagerAgent 클래스 구현
  - [ ] CRUD 함수 (건강 지표, 할일, 습관)
  - [ ] 통계 집계 함수
  - [ ] 단위 테스트 (pytest)

- [ ] **게임화 에이전트** (1일)
  - [ ] GamificationAgent 클래스 구현
  - [ ] 경험치 계산 로직
  - [ ] 레벨업 체크
  - [ ] 기본 업적 정의 (5개)

- [ ] **간단한 CLI** (1일)
  - [ ] 기본 입력/출력
  - [ ] 수동 명령어 (add, list, summary)
  - [ ] 통합 테스트

### Phase 2: 자연어 파싱 (1주)
- [ ] **한국어 파서** (3일)
  - [ ] korean_patterns.py: 정규식 패턴 정의
  - [ ] date_parser.py: 날짜 표현 파싱
  - [ ] number_parser.py: 수량 표현 파싱
  - [ ] ConversationAgent: 의도 분류 및 엔티티 추출
  - [ ] 복합 명령 처리
  - [ ] 파서 테스트 (100개 예시)

- [ ] **코칭 에이전트** (2일)
  - [ ] CoachingAgent 클래스 구현
  - [ ] 알림 규칙 엔진
  - [ ] 패턴 분석 (3일 연속, 트렌드 등)
  - [ ] 메시지 템플릿

- [ ] **조율자 에이전트** (1일)
  - [ ] OrchestratorAgent 구현
  - [ ] 에이전트 간 라우팅
  - [ ] 응답 조합 로직

- [ ] **CLI 개선** (1일)
  - [ ] 자연어 입력 통합
  - [ ] 이모지 및 포맷팅
  - [ ] 확인 질문 처리

### Phase 3: 고급 기능 (1-2주)
- [ ] **LLM 통합** (선택적)
  - [ ] llm_parser.py: OpenAI/Claude API
  - [ ] 애매한 입력 처리
  - [ ] 개인화된 조언 생성

- [ ] **고급 업적 시스템**
  - [ ] 20개 업적 정의
  - [ ] 업적 달성 체크 자동화
  - [ ] 희귀 업적 및 숨은 업적

- [ ] **메시지 버스 아키텍처**
  - [ ] message_bus.py 구현
  - [ ] 비동기 메시지 처리
  - [ ] 에이전트 독립성 강화

### Phase 4: 웹 UI & 시각화 (2주)
- [ ] **Streamlit 대시보드**
  - [ ] 채팅 인터페이스
  - [ ] 건강 지표 차트 (matplotlib/plotly)
  - [ ] 레벨/경험치 프로그레스 바
  - [ ] 업적 갤러리

- [ ] **고급 분석**
  - [ ] 주간/월간 리포트
  - [ ] 상관관계 분석
  - [ ] 예측 모델 (수면 패턴 예측)

---

## 🌍 향후 확장 계획

### Phase 5+: 미래 기능
- [ ] 다중 사용자 지원 (인증, 데이터 격리)
- [ ] 외부 연동 (Google Calendar, Fitbit, Apple Health)
- [ ] 텔레그램/슬랙 봇 연동
- [ ] 모바일 앱 (React Native)
- [ ] 소셜 기능 (친구와 경쟁, 리더보드)
- [ ] AI 추천 시스템 (개인화된 목표 제안)

---

## 🧪 테스트 전략

### 단위 테스트
- `test_agents/`: 각 에이전트 기능 테스트
- `test_parsers/`: 파싱 정확도 테스트 (100개 예시)
- `test_rules/`: 알림 규칙 및 XP 규칙 테스트

### 통합 테스트
- `test_integration/`: 전체 플로우 테스트
  - 입력 → 파싱 → 저장 → 알림 → XP 부여 → 응답

### 데이터 검증
- 날짜 유효성 (미래 날짜 경고)
- 수치 범위 (수면 24시간 초과, 음수 등)
- 중복 데이터 처리

---

## 💡 한국어 자연어 처리

### 시제 표현
- 과거: "어제", "그제", "3일 전", "지난주"
- 현재: "오늘", "지금"
- 미래: "내일", "모레", "다음주"

### 조사 처리
- 과거: "잤어", "잤다", "잤음"
- 계획: "해야해", "해야 한다", "할 것"
- 진행: "하고 있어", "진행중"

### 수량 표현
- 시간: "5시간", "다섯시간", "5h", "반나절"
- 분: "30분", "반시간", "30m"
- 그램: "100g", "100그램"

### 정규식 패턴 예시
```python
# 수면
r'(\d+)\s*시간\s*(잤|수면|睡)'
r'(어제|오늘|그제)\s*(\d+)\s*시간'

# 운동
r'(\d+)\s*분\s*(운동|헬스|러닝|조깅)'

# 할일
r'(.+?)\s*(해야|할\s*것|하기)'

# 날짜
r'(어제|오늘|내일|모레|그제)'
r'(\d+)\s*일\s*(전|후)'
```

---

## ⚙️ 설정 관리

### config.yaml
```yaml
# 건강 목표치
health_targets:
  sleep_hours: 7
  workout_minutes: 30
  protein_grams: 100

# 알림 임계값
alerts:
  sleep_warning: 6
  consecutive_days_check: 3

# 경험치 규칙
exp_rules:
  task_complete: 20
  task_priority_multiplier:
    low: 0.5
    normal: 1.0
    high: 1.5
    urgent: 2.5
  sleep_goal: 15
  workout_base: 10
  protein_goal: 10
  habit_streak: 5
  study_per_hour: 30

# 레벨 공식
level_formula: "100 * N * (N - 1) / 2"

# LLM 설정 (선택적)
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4o-mini"
  api_key_env: "OPENAI_API_KEY"

# DB 설정
database:
  path: "lifebot.db"
  backup_enabled: true
```

---

## 📊 UX 예시

### 대화 흐름 1: 기본 입력
```
사용자: "어제 5시간 잤어"
봇: ✓ 수면 기록 완료 (2025-10-01: 5시간)
    ⚠️ 목표(7시간)보다 2시간 부족합니다.

    📊 Level 3 (250/350 XP)
```

### 대화 흐름 2: 복합 입력
```
사용자: "어제 5시간 자고 30분 운동했어"
봇: ✓ 2개 기록 완료

    💤 수면: 5시간 (⚠️ 목표 -2h)
    💪 운동: 30분 (✓ 목표 달성!) +10 XP

    📊 Level 3 (260/350 XP) | 🏆 8/20
```

### 대화 흐름 3: 할일 완료
```
사용자: "카드비 계산 완료했어"
봇: ✓ 할일 완료!
    +20 XP

    🎉 Level UP! 3 → 4
    🏆 새 업적: "철인" (할일 100개 완료) +100 XP

    📊 Level 4 (30/500 XP) | 🏆 9/20
```

### 대화 흐름 4: 요약
```
사용자: "오늘 요약"
봇: 📊 2025-10-02 요약

    💤 수면: 7시간 (✓ 목표 달성) +15 XP
    💪 운동: 30분 (✓) +10 XP
    🍗 단백질: 기록 없음
    📝 할일: 완료 2/5

    🔥 Streak: 금연 7일째! (다음 마일스톤: 14일)

    📊 Level 4 (55/500 XP) | 🏆 9/20
```

---

## 🚀 시작하기

### 개발 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# DB 초기화
python -m core.database init

# CLI 실행
python main.py
```

### 테스트 실행
```bash
# 전체 테스트
pytest

# 단위 테스트만
pytest tests/test_agents/

# 커버리지
pytest --cov=agents --cov=parsers
```

---

## 📝 개발 체크리스트

### Phase 1 (현재)
- [ ] DB 스키마 설계 및 구현
- [ ] DataManagerAgent 기본 CRUD
- [ ] GamificationAgent 경험치 로직
- [ ] 간단한 CLI

### Phase 2
- [ ] 한국어 파서 구현
- [ ] CoachingAgent 알림 규칙
- [ ] OrchestratorAgent 조율
- [ ] 자연어 CLI

### Phase 3
- [ ] LLM 통합
- [ ] 고급 업적 시스템
- [ ] 메시지 버스

### Phase 4
- [ ] 웹 UI (Streamlit)
- [ ] 데이터 시각화
- [ ] 리포트 생성
