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
        system_prompt = """당신은 한국어 건강/할일 관리 봇의 파서입니다.
사용자 입력을 분석하여 의도와 정보를 추출하세요.

가능한 의도(intent):
- sleep: 수면 (시간 계산 필요시 자동 계산)
- workout: 운동
- protein: 단백질 섭취
- weight: 체중
- task_add: 할일 추가
- task_complete: 할일 완료
- study: 공부/학습
- summary: 요약
- progress: 진행도
- chat: 일반 대화

복합 명령인 경우 JSON 배열로, 단일 명령은 JSON 객체로 응답하세요.

예시:
- "새벽3시부터 12시까지 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 9}}, "confidence": 0.95}}
- "어제 7시간 자고 30분 운동했어" → [
    {{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "어제"}}, "confidence": 0.95}},
    {{"intent": "workout", "entities": {{"workout_minutes": 30, "date": "어제"}}, "confidence": 0.95}}
  ]

복잡한 수면 패턴도 계산해주세요:
- "11시에 잤다가 3시에 일어나서 다시 8시에 잤다가 14시에 일어났어" → 총 10시간 수면"""

        user_prompt = f"""사용자 입력: "{user_input}"

이 입력을 분석하여 JSON으로 응답하세요.
복합 명령이면 배열, 단일 명령이면 객체로 응답하세요."""

        try:
            # LangChain 메시지 생성
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # LLM 호출
            response = self.llm.invoke(messages)

            # JSON 파싱
            try:
                # response.content에서 JSON 추출
                content = response.content
                # JSON 부분만 추출 (```json ... ``` 형태 처리)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                parsed = json.loads(content.strip())

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
        tone: str = "friendly"
    ) -> str:
        """
        대화형 응답 생성

        Args:
            user_input: 사용자 입력
            context: 처리 결과 컨텍스트
            tone: 응답 톤 (friendly, professional, casual)

        Returns:
            대화형 응답
        """
        system_prompt = f"""당신은 친근하고 격려하는 헬스케어 어시스턴트입니다.
사용자의 건강 데이터를 기록하고 동기부여를 제공합니다.
한국어로 응답하며, 이모지를 적절히 사용합니다.
톤: {tone}"""

        user_prompt = f"""사용자: "{user_input}"

처리 결과: {context}

위 내용을 바탕으로 친근하고 격려하는 응답을 2-3문장으로 작성하세요."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            print(f"응답 생성 오류: {e}")
            return context  # 오류 시 기본 메시지 반환

    def chat(
        self,
        user_input: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        일반 대화 (챗봇 모드)

        Args:
            user_input: 사용자 입력
            chat_history: 대화 이력

        Returns:
            AI 응답
        """
        system_prompt = """당신은 LifeBot, 친근한 건강/할일 관리 어시스턴트입니다.
사용자와 자연스럽게 대화하며, 건강 관리를 격려합니다.
한국어로 응답하고, 이모지를 적절히 사용합니다."""

        messages = [SystemMessage(content=system_prompt)]

        # 대화 이력 추가
        if chat_history:
            for msg in chat_history[-5:]:  # 최근 5개만
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(SystemMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_input))

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            print(f"대화 오류: {e}")
            return "죄송해요, 잠시 문제가 있었어요. 다시 말씀해주세요! 😅"


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