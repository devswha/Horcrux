# 🔗 LangChain 체인 아키텍처

## 📊 현재 vs 개선 비교

### ❌ 현재 (langchain_llm.py) - 단순 Invoke

```python
# 1. 프롬프트를 직접 문자열로 작성
system_prompt = """당신은 한국어 건강/할일 관리 봇의 파서입니다..."""
user_prompt = f"""사용자 입력: "{user_input}" ..."""

# 2. 메시지 수동 생성
messages = [
    SystemMessage(content=system_prompt + "\n" + format_instructions),
    HumanMessage(content=user_prompt)
]

# 3. LLM 호출 (invoke)
response = self.llm.invoke(messages)

# 4. 수동 파싱
parsed = parser.parse(response.content)
```

**문제점:**
- ❌ 프롬프트 템플릿 재사용 불가
- ❌ 체인 연결이 없어 단계가 분리됨
- ❌ 에러 처리가 분산됨
- ❌ 디버깅 어려움

---

### ✅ 개선 (langchain_llm_v2.py) - LCEL 시퀸셜 체인

```python
# 1. 프롬프트 템플릿 정의 (재사용 가능)
self.intent_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template(human_template)
])

# 2. 시퀸셜 체인 구성 (LCEL 파이프 연산자)
self.intent_chain = self.intent_prompt_template | self.llm | self.json_parser
#                   ↑ 프롬프트              ↑ LLM  ↑ JSON 파서
#                   단계 1                  단계 2  단계 3

# 3. 체인 실행 (한 번의 호출)
parsed = self.intent_chain.invoke({"user_input": user_input})
```

**장점:**
- ✅ 프롬프트 템플릿 재사용 가능
- ✅ 체인이 자동으로 데이터 전달
- ✅ 에러 처리 통합
- ✅ 디버깅 용이 (각 단계 추적)
- ✅ 더 선언적이고 읽기 쉬움

---

## 🏗️ LCEL 시퀸셜 체인 구조

### 의도 파싱 체인

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣ ChatPromptTemplate (프롬프트 템플릿)                      │
│                                                             │
│  Input: {"user_input": "7시간 잤어"}                        │
│  ↓                                                          │
│  System: "당신은 한국어 건강/할일 관리 봇의 파서입니다..."      │
│  Human: "사용자 입력: '7시간 잤어' ..."                       │
│  ↓                                                          │
│  Output: [SystemMessage(...), HumanMessage(...)]           │
└─────────────────────────────────────────────────────────────┘
                           ↓ (파이프)
┌─────────────────────────────────────────────────────────────┐
│  2️⃣ ChatOpenAI (LLM)                                         │
│                                                             │
│  Input: [SystemMessage(...), HumanMessage(...)]            │
│  ↓                                                          │
│  OpenAI API 호출 (gpt-4o-mini)                              │
│  ↓                                                          │
│  Output: AIMessage(content='{"intent": "sleep", ...}')      │
└─────────────────────────────────────────────────────────────┘
                           ↓ (파이프)
┌─────────────────────────────────────────────────────────────┐
│  3️⃣ JsonOutputParser (JSON 파싱)                             │
│                                                             │
│  Input: AIMessage(content='{"intent": "sleep", ...}')       │
│  ↓                                                          │
│  JSON 파싱 (자동)                                            │
│  ↓                                                          │
│  Output: {"intent": "sleep", "entities": {...}, ...}        │
└─────────────────────────────────────────────────────────────┘
```

**파이프 연산자 (`|`)**:
- 각 단계의 출력을 다음 단계의 입력으로 자동 전달
- LangChain이 타입 변환과 에러 처리를 자동 수행

---

## 📝 프롬프트 템플릿 구조

### 1. Intent Parsing Template

```python
system_template = """당신은 한국어 건강/할일 관리 봇의 파서입니다.
사용자 입력을 분석하여 의도와 정보를 추출하세요.

가능한 의도(intent):
- sleep: 수면 (시간 계산 필요시 자동 계산)
- workout: 운동
- protein: 단백질 섭취
- weight: 체중
- task_add: 할일 추가
- task_complete: 할일 완료
- study: 공부/학습 (시간 기록)
- learning_log: 학습 기록 (새로운 지식/스킬 습득)
- summary: 요약
- progress: 진행도
- chat: 일반 대화

예시:
- "7시간 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 7}}, "confidence": 0.95}}
...

반드시 순수 JSON만 출력하세요."""

human_template = """사용자 입력: "{user_input}"

이 입력을 분석하여 JSON으로 응답하세요."""
```

**변수:**
- `{user_input}`: 사용자 입력이 자동으로 주입됨

**장점:**
- 프롬프트를 한 번 정의하면 모든 요청에 재사용
- 변수만 바꿔서 invoke 가능
- 프롬프트 버전 관리 용이

---

### 2. Response Generation Template

```python
system_template = """당신은 친근하고 격려하는 헬스케어 어시스턴트입니다.
사용자의 건강 데이터를 기록하고 동기부여를 제공합니다.
한국어로 응답하며, 이모지를 적절히 사용합니다.
톤: {tone}"""

human_template = """사용자: "{user_input}"

처리 결과: {context}

위 내용을 바탕으로 친근하고 격려하는 응답을 2-3문장으로 작성하세요."""
```

**변수:**
- `{user_input}`: 사용자 입력
- `{context}`: 처리 결과 (예: "✓ 수면 기록 완료: 7시간")
- `{tone}`: 응답 톤 (friendly, professional, casual)

---

### 3. Chat Template

```python
system_template = """당신은 Horcrux, 친근한 건강/할일 관리 어시스턴트입니다.
사용자와 자연스럽게 대화하며, 건강 관리를 격려합니다.
한국어로 응답하고, 이모지를 적절히 사용합니다."""

human_template = "{user_input}"
```

**변수:**
- `{user_input}`: 사용자 입력

---

## 🔧 체인 사용 예시

### 1. 의도 파싱

```python
# 초기화 (한 번만)
llm = LangChainLLM()

# 체인 실행
result = llm.parse_intent("7시간 잤어")
# → {"intent": "sleep", "entities": {"sleep_hours": 7}, "confidence": 0.95, ...}
```

**내부 동작:**
```python
# LCEL 체인이 자동으로 수행:
{"user_input": "7시간 잤어"}
↓
프롬프트 템플릿에 주입
↓
LLM 호출
↓
JSON 파싱
↓
결과 반환
```

---

### 2. 응답 생성

```python
response = llm.generate_response(
    user_input="7시간 잤어",
    context="✓ 수면 기록 완료: 7시간 +15 XP",
    tone="friendly"
)
# → "잘하셨어요! 7시간 푹 주무셨네요! 💤 ..."
```

---

### 3. 일반 대화

```python
response = llm.chat("안녕하세요!")
# → "안녕하세요! 오늘 건강 관리는 어떻게 하고 계세요? 😊"
```

---

## 📊 기존 vs LCEL 성능 비교

| 항목 | 기존 (Invoke) | LCEL 체인 | 개선 |
|------|---------------|-----------|------|
| **코드 라인 수** | ~160줄 | ~240줄 | +50% (템플릿 정의 포함) |
| **재사용성** | ❌ 낮음 | ✅ 높음 | 프롬프트 재사용 |
| **가독성** | ⚠️ 보통 | ✅ 우수 | 선언적 구조 |
| **유지보수** | ⚠️ 어려움 | ✅ 쉬움 | 템플릿 분리 |
| **디버깅** | ❌ 어려움 | ✅ 쉬움 | 단계별 추적 |
| **응답 속도** | 1.59초 | ~1.6초 | 동일 |
| **정확도** | 100% | 100% | 동일 |

---

## 🎯 LCEL의 핵심 개념

### 1. 파이프 연산자 (`|`)

```python
chain = prompt | llm | parser
```

- Unix 파이프와 유사한 개념
- 각 단계의 출력 → 다음 단계의 입력
- 타입 변환 자동 수행

---

### 2. Runnable 인터페이스

모든 LangChain 컴포넌트는 `Runnable` 인터페이스 구현:

```python
# 공통 메서드
runnable.invoke(input)       # 동기 실행
runnable.batch([input1, ...]) # 배치 실행
runnable.stream(input)       # 스트리밍 실행
```

---

### 3. 체인 조합

```python
# 병렬 실행 (RunnableParallel)
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel({
    "intent": intent_chain,
    "sentiment": sentiment_chain
})

# 조건부 실행 (RunnableBranch)
from langchain_core.runnables import RunnableBranch

conditional_chain = RunnableBranch(
    (lambda x: x["intent"] == "chat", chat_chain),
    (lambda x: x["intent"] == "sleep", sleep_chain),
    default_chain
)
```

---

## 🚀 마이그레이션 가이드

### 1. 기존 코드 교체

```bash
# 기존 파일 백업
cp core/langchain_llm.py core/langchain_llm_old.py

# 새 버전으로 교체
cp core/langchain_llm_v2.py core/langchain_llm.py
```

### 2. 테스트 실행

```bash
python3 tests/test_llm_only.py
```

### 3. 웹 서버 재시작

```bash
./run.sh web
```

---

## 📈 향후 확장 가능성

### 1. Few-shot Learning

```python
# 예시를 프롬프트에 동적 추가
examples = [
    ("7시간 잤어", {"intent": "sleep", ...}),
    ("30분 운동했어", {"intent": "workout", ...}),
]

few_shot_template = FewShotChatMessagePromptTemplate(
    example_prompt=example_template,
    examples=examples
)
```

---

### 2. 메모리 추가

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
chain_with_memory = RunnableWithMessageHistory(
    intent_chain,
    memory
)
```

---

### 3. 에이전트 체인

```python
# 여러 에이전트를 체인으로 연결
full_chain = (
    parse_chain        # 1. 파싱
    | decision_chain   # 2. 의사결정
    | action_chain     # 3. 행동 실행
    | response_chain   # 4. 응답 생성
)
```

---

## 📚 참고 자료

- **LangChain LCEL 공식 문서**: https://python.langchain.com/docs/expression_language/
- **Prompt Templates**: https://python.langchain.com/docs/modules/model_io/prompts/
- **Output Parsers**: https://python.langchain.com/docs/modules/model_io/output_parsers/
- **Runnables**: https://python.langchain.com/docs/expression_language/interface

---

## 🎓 결론

### 현재 상태 (langchain_llm.py)
- ✅ 작동함
- ⚠️ 코드가 절차적
- ⚠️ 재사용성 낮음

### LCEL 버전 (langchain_llm_v2.py)
- ✅ 더 선언적이고 읽기 쉬움
- ✅ 프롬프트 템플릿 재사용
- ✅ 체인 확장 용이
- ✅ 디버깅 편리

**추천:** LCEL 버전으로 마이그레이션하여 장기적 유지보수성 향상
