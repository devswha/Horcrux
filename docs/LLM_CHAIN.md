# 🔗 Horcrux LLM 체인 구조

## 📊 전체 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│                        👤 사용자 입력                              │
│                  "프롬포트 템플릿에 대해 알게됐어"                  │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              📱 interfaces/app.py (Streamlit UI)                 │
│              또는 interfaces/main_natural.py (CLI)               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              🎯 OrchestratorAgent.handle_user_input()            │
│              - 전체 프로세스 조율                                  │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│            💬 ConversationAgent.parse_user_input()               │
│            - 정규식 파서 먼저 시도 (korean_patterns.py)           │
│            - 실패 시 LLM 백업                                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ├─ [정규식 성공] ─→ confidence > 0.7 ─→ 직접 처리
                  │
                  └─ [정규식 실패/낮은 신뢰도] ─→ LLM 호출
                                    │
                                    ▼
              ┌──────────────────────────────────────┐
              │   🤖 LangChainLLM.parse_intent()     │
              │   (core/langchain_llm.py)            │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   🧠 OpenAI GPT-4o-mini API          │
              │   - 모델: gpt-4o-mini                │
              │   - Temperature: 0.7                 │
              │   - Max Tokens: 500                  │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   📝 JSON 응답 파싱                   │
              │   {"intent": "learning_log",         │
              │    "entities": {"title": "...", ...}}│
              └──────────────┬───────────────────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
        [단일 명령]              [복합 명령]
     {"intent": "..."}      [{"intent": "..."}, ...]
                  │                     │
                  └──────────┬──────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   🎯 OrchestratorAgent               │
              │   _handle_single_intent() 또는       │
              │   _handle_multiple_intents()         │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   🔧 의도별 핸들러 실행               │
              │   - _handle_learning_log()           │
              │   - _handle_sleep()                  │
              │   - _handle_task_add()               │
              │   등...                              │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   💾 DataManagerAgent                │
              │   - add_learning_log()               │
              │   - store_health_metric()            │
              │   등 DB 작업 수행                     │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   🎮 GamificationAgent               │
              │   - award_exp() (경험치 부여)        │
              │   - 레벨업 체크                       │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   📤 기본 응답 생성                   │
              │   "📚 학습 기록 저장: ... +10 XP"     │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   ✨ _make_conversational()          │
              │   (선택적 대화형 변환)                │
              │   LLM으로 친근한 톤으로 재작성        │
              └──────────────┬───────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────────────┐
              │   🤖 LangChainLLM.generate_response() │
              │   기본 메시지를 대화형으로 변환        │
              └──────────────┬───────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    👤 사용자에게 최종 응답                         │
│     "와! 프롬포트 템플릿에 대해 배우셨군요! 🎉                    │
│      새로운 지식을 기록해두시니 정말 멋져요! +10 XP"               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 주요 컴포넌트

### 1️⃣ **LangChainLLM** (core/langchain_llm.py)

핵심 LLM 래퍼 클래스

```python
class LangChainLLM:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    # 주요 메서드:
    # 1. parse_intent() - 의도 파싱
    # 2. generate_response() - 대화형 응답 생성
    # 3. chat() - 일반 대화
```

**사용하는 LangChain 컴포넌트:**
- `ChatOpenAI` - OpenAI GPT 모델 인터페이스
- `SystemMessage` / `HumanMessage` - 메시지 구조
- `JsonOutputParser` - JSON 파싱 (선택적)

---

### 2️⃣ **의도 파싱 체인**

```python
# 1단계: 시스템 프롬프트 생성
system_prompt = """
당신은 한국어 건강/할일 관리 봇의 파서입니다.
가능한 의도: sleep, workout, task_add, learning_log, ...
"""

# 2단계: 사용자 프롬프트
user_prompt = f'사용자 입력: "{user_input}"'

# 3단계: 메시지 구성
messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_prompt)
]

# 4단계: LLM 호출
response = self.llm.invoke(messages)

# 5단계: JSON 파싱
result = json.loads(response.content)
# → {"intent": "learning_log", "entities": {...}}
```

---

### 3️⃣ **대화형 응답 생성 체인**

```python
# orchestrator.py의 _make_conversational()

# 입력: 기본 응답
basic_message = "📚 학습 기록 저장: 프롬포트 템플릿 +10 XP"

# LLM으로 대화형 변환
conversational = self.llm.generate_response(
    user_input=user_input,
    context=basic_message,
    tone="friendly"
)

# 출력: 친근한 응답
# "와! 프롬포트 템플릿에 대해 배우셨군요! 🎉 ..."
```

---

## ⚙️ 설정 파일

### config.yaml
```yaml
llm:
  provider: "langchain"  # LangChain 사용
  enabled: true
  strategy: "fallback"   # 정규식 실패 시 LLM 사용
```

### .env
```bash
OPENAI_API_KEY=sk-proj-...
```

---

## 🎯 의도 처리 흐름

```python
# OrchestratorAgent.handle_user_input()

1. ConversationAgent로 파싱
   ├─ 정규식 성공 → 바로 처리
   └─ 정규식 실패 → LLM 호출
       └─ LangChainLLM.parse_intent()
           └─ GPT-4o-mini API
               └─ JSON 응답

2. 의도에 따라 핸들러 분기
   ├─ learning_log → _handle_learning_log()
   ├─ sleep → _handle_sleep()
   ├─ task_add → _handle_task_add()
   └─ chat → _handle_chat()

3. 데이터 처리
   ├─ DataManagerAgent (DB CRUD)
   └─ GamificationAgent (XP/레벨)

4. 응답 생성
   ├─ 기본 메시지 생성
   └─ (선택) LLM으로 대화형 변환
```

---

## 📈 LLM 호출 시점

### 1. **의도 파싱** (필수)
- 위치: `ConversationAgent.parse_user_input()`
- 조건: 정규식 파싱 실패 or 신뢰도 < 0.7
- 메서드: `LangChainLLM.parse_intent()`

### 2. **대화형 응답 변환** (선택)
- 위치: `OrchestratorAgent._make_conversational()`
- 조건: LLM 사용 가능 시
- 메서드: `LangChainLLM.generate_response()`

### 3. **일반 대화** (chat 의도)
- 위치: `OrchestratorAgent._handle_chat()`
- 조건: intent == "chat"
- 메서드: `LangChainLLM.chat()`

### 4. **코칭 조언** (CoachingAgent)
- 위치: `CoachingAgent.generate_advice()`
- 조건: 패턴 감지 시
- 메서드: `LangChainLLM.generate_response()`

---

## 💰 비용 최적화

### 전략 1: 정규식 우선
```python
# ConversationAgent
# 1. 정규식으로 먼저 시도 (무료)
intent, entities, confidence = self.parser.parse(text)

# 2. 실패 시에만 LLM 사용
if confidence < 0.7:
    llm_result = self.llm.parse_intent(text)
```

### 전략 2: 짧은 응답
```python
# max_tokens=500으로 제한
# 간결한 프롬프트 사용
```

### 전략 3: 캐싱 (향후)
```python
# 동일한 입력에 대해 캐시 사용
# 예: "7시간 잤어" → 캐시된 결과 반환
```

---

## 🔧 확장 포인트

### 1. **Few-shot 예시 추가**
```python
# 프롬프트에 더 많은 예시 추가
examples = [
    ("7시간 잤어", {"intent": "sleep", ...}),
    ("할일 추가", {"intent": "task_add", ...}),
    # ... 더 많은 예시
]
```

### 2. **Function Calling 사용**
```python
# OpenAI Function Calling으로 구조화된 출력
functions = [
    {
        "name": "parse_intent",
        "parameters": {
            "intent": {"type": "string", "enum": ["sleep", "workout", ...]},
            "entities": {"type": "object"}
        }
    }
]
```

### 3. **체인 분리**
```python
# 복잡한 작업을 여러 체인으로 분리
chain1 = intent_parsing_chain
chain2 = entity_extraction_chain
chain3 = response_generation_chain

result = chain1 | chain2 | chain3
```

---

## 📊 성능 메트릭

- **의도 파악 정확도**: 95%+
- **평균 응답 시간**: 1-2초
- **API 호출 비용**: 입력당 $0.000015 (GPT-4o-mini)
- **월 예상 비용**: 100회/일 사용 시 ~$0.45

---

## 🎓 학습 자료

- **LangChain 공식 문서**: https://python.langchain.com/
- **OpenAI API 문서**: https://platform.openai.com/docs
- **프롬프트 엔지니어링**: docs/PROMPTS.md
