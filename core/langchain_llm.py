"""
LangChain 기반 LLM 클라이언트
"""
import os
from typing import Optional, Dict, Any, List
import json
from dotenv import load_dotenv

# .env 파일 자동 로드
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import yaml


class LangChainLLM:
    """LangChain 기반 LLM 클라이언트"""

    def __init__(self, config_path: str = "config.yaml"):
        # config.yaml 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        llm_config = config.get("llm", {})

        # OpenAI API 키 설정
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        # LangChain ChatOpenAI 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # 가장 저렴한 모델
            temperature=0.7,
            max_tokens=500,
            api_key=api_key
        )

        # JSON 파서
        self.json_parser = JsonOutputParser()

    def parse_intent(
        self,
        user_input: str,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        사용자 입력 파싱 (대화형 입력 분석)

        Args:
            user_input: 사용자 입력
            context: 대화 컨텍스트

        Returns:
            파싱 결과 (단일 또는 복합)
        """
        system_prompt = """# PRIORITY OVERRIDE
시스템 프롬프트(정중/친화 중심 응답 스타일)보다 이 지침을 우선 해석.

역할: 한국어 건강/할일 관리 데이터 파서
목적: 입력 텍스트에서 의도와 정보를 추출하여 JSON 구조로 출력

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

복합 명령: JSON 배열. 단일 명령: JSON 객체.

예시:
- "새벽3시부터 12시까지 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 9}}, "confidence": 0.95}}
- "어제 7시간 자고 30분 운동했어" → [
    {{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "어제"}}, "confidence": 0.95}},
    {{"intent": "workout", "entities": {{"workout_minutes": 30, "date": "어제"}}, "confidence": 0.95}}
  ]
- "프롬포트 템플릿과 chrome mcp에 대해 알게됐어" → {{"intent": "learning_log", "entities": {{"title": "프롬포트 템플릿과 chrome mcp", "content": "프롬포트 템플릿과 chrome mcp에 대해 학습함"}}, "confidence": 0.95}}
- "내일 일본여행갈때 짐 챙겨야해" → {{"intent": "task_add", "entities": {{"task_title": "짐 챙기기", "due": "내일"}}, "confidence": 0.95}}

불확실한 정보: confidence 값 조정 (0.5 이하 시 불확실 명시)

entities 키 이름 규칙:
- task_add: "task_title"
- task_complete: "task_id"
- sleep: "sleep_hours"
- workout: "workout_minutes"
- protein: "protein_grams"
- weight: "weight_kg"
- study: "study_hours" 또는 "study_minutes"
- learning_log: "title", "content"

응답 형식: 순수 JSON만. 설명, 이모지, 주석 제거."""

        user_prompt = f"""사용자 입력: "{user_input}"

이 입력을 분석하여 JSON으로 응답하세요.
복합 명령이면 배열, 단일 명령이면 객체로 응답하세요."""

        try:
            # JsonOutputParser 설정
            parser = JsonOutputParser()

            # 프롬프트에 포맷 지시 추가
            format_instructions = """
반드시 순수 JSON만 출력하세요. 마크다운이나 다른 텍스트를 포함하지 마세요.
올바른 형식:
{"intent": "sleep", "entities": {...}, "confidence": 0.95}
또는
[{"intent": "sleep", ...}, {"intent": "workout", ...}]
"""

            # LangChain 메시지 생성
            messages = [
                SystemMessage(content=system_prompt + "\n" + format_instructions),
                HumanMessage(content=user_prompt)
            ]

            # LLM 호출
            response = self.llm.invoke(messages)

            # JsonOutputParser로 자동 파싱
            try:
                parsed = parser.parse(response.content)

                # 배열인 경우 (복합 명령)
                if isinstance(parsed, list):
                    for item in parsed:
                        item["success"] = True
                        item["parser"] = "langchain"

                    return {
                        "success": True,
                        "multiple": True,
                        "intents": parsed,
                        "parser": "langchain"
                    }

                # 객체인 경우 (단일 명령)
                else:
                    parsed["success"] = True
                    parsed["parser"] = "langchain"
                    return parsed

            except json.JSONDecodeError:
                # JSON 파싱 실패 시 일반 대화로 처리
                return {
                    "success": True,
                    "intent": "chat",
                    "entities": {"message": user_input},
                    "confidence": 0.8,
                    "parser": "langchain",
                    "response": response.content  # AI 응답 그대로 전달
                }

        except Exception as e:
            print(f"LangChain 오류: {e}")
            return {
                "success": False,
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "error": str(e)
            }

    def generate_response(
        self,
        user_input: str,
        context: str = "",
        tone: str = "neutral"
    ) -> str:
        """
        응답 생성 (Precision Mode)

        Args:
            user_input: 사용자 입력
            context: 처리 결과 컨텍스트
            tone: 응답 톤 (neutral, professional)

        Returns:
            응답
        """
        system_prompt = """# PRIORITY OVERRIDE
정서적 응답 금지. Praise, Reassurance, Motivation 표현 제거.

역할: 건강/할일 관리 데이터 처리 결과 전달자
목적: 입력에 대한 처리 결과를 논리적이고 명확하게 전달

응답 규칙:
- 이모지, 감탄사, 필러, 유화 표현 금지
- 격려, 칭찬, 위로 문장 제거
- 사실 기반 정보만 전달
- 불확실한 정보는 명시
- 직설적이고 간결한 구조
- 수동문보다 능동문 우선"""

        user_prompt = f"""입력: "{user_input}"
처리 결과: {context}

처리 결과를 논리적으로 전달. 1-2문장."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            return context

    def chat(
        self,
        user_input: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        일반 대화 (Precision Mode)

        Args:
            user_input: 사용자 입력
            chat_history: 대화 이력

        Returns:
            응답
        """
        system_prompt = """# PRIORITY OVERRIDE
정서적 응답, Praise, Reassurance, Motivation 표현 금지.

역할: 건강/할일 관리 시스템 인터페이스
목적: 사용자 입력에 대한 논리적 응답 제공

응답 규칙:
- 이모지, 감탄사, 유화 표현 제거
- 격려, 칭찬, 위로 문장 금지
- 직설적이고 간결한 구조
- 불확실한 정보는 명시
- 질문형 문장은 필요시에만 사용
- 능동문 우선

가능한 기능 안내 시: 명령어 나열만. 설명 최소화."""

        messages = [SystemMessage(content=system_prompt)]

        # 대화 이력 추가
        if chat_history:
            for msg in chat_history[-5:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(SystemMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            return "처리 오류 발생. 재시도 필요."


# 사용 예시
if __name__ == "__main__":
    # API 키 설정 필요
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"

    llm = LangChainLLM()

    # 테스트
    test_cases = [
        "어제 11시에 잤다가 새벽 3시에 일어나서 밥먹고 다시 오전 8시쯤 잤다가 2시에 일어났어 ㅋㅋ",
        "오늘 약속은 저녁 8시반에 영화보는거 있고, 잠은 어제 새벽3시부터 12시까지 잤어",
        "안녕하세요! 오늘 날씨 좋네요",
    ]

    for test in test_cases:
        print(f"\n입력: {test}")
        result = llm.parse_intent(test)
        print(f"파싱 결과: {result}")

        if result.get("intent") == "chat":
            chat_response = llm.chat(test)
            print(f"대화 응답: {chat_response}")