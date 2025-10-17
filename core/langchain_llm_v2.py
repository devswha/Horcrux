"""
LangChain LCEL 기반 LLM 클라이언트 (시퀸셜 체인 버전)
"""
import os
from typing import Optional, Dict, Any, List
import json
from dotenv import load_dotenv

load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
import yaml


class LangChainLLM:
    """LangChain LCEL 기반 LLM 클라이언트"""

    def __init__(self, config_path: str = "config.yaml"):
        # config.yaml 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # OpenAI API 키 설정
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        # LangChain ChatOpenAI 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            api_key=api_key
        )

        # JSON 파서
        self.json_parser = JsonOutputParser()

        # 프롬프트 템플릿 정의 (재사용 가능)
        self.intent_prompt_template = self._create_intent_prompt_template()
        self.response_prompt_template = self._create_response_prompt_template()
        self.chat_prompt_template = self._create_chat_prompt_template()

        # 시퀸셜 체인 구성 (LCEL)
        self.intent_chain = self.intent_prompt_template | self.llm | self.json_parser

    def _create_intent_prompt_template(self) -> ChatPromptTemplate:
        """의도 파싱용 프롬프트 템플릿"""
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

복합 명령인 경우 JSON 배열로, 단일 명령은 JSON 객체로 응답하세요.

예시:
- "새벽3시부터 12시까지 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 9}}, "confidence": 0.95}}
- "어제 7시간 자고 30분 운동했어" → [
    {{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "어제"}}, "confidence": 0.95}},
    {{"intent": "workout", "entities": {{"workout_minutes": 30, "date": "어제"}}, "confidence": 0.95}}
  ]
- "프롬포트 템플릿과 chrome mcp에 대해 알게됐어" → {{"intent": "learning_log", "entities": {{"title": "프롬포트 템플릿과 chrome mcp", "content": "프롬포트 템플릿과 chrome mcp에 대해 학습함"}}, "confidence": 0.95}}
- "내일 일본여행갈때 짐 챙겨야해" → {{"intent": "task_add", "entities": {{"task_title": "짐 챙기기", "due": "내일"}}, "confidence": 0.95}}

복잡한 수면 패턴도 계산해주세요:
- "11시에 잤다가 3시에 일어나서 다시 8시에 잤다가 14시에 일어났어" → 총 10시간 수면

학습 기록 (learning_log)은 '알게됐어', '배웠어', '깨달았어', '기억해둬' 등의 표현이 있을 때 사용하세요.

**중요: entities 키 이름 규칙**
- task_add: "task_title" (할일 제목)
- task_complete: "task_id" (할일 ID)
- sleep: "sleep_hours" (수면 시간)
- workout: "workout_minutes" (운동 시간, 분 단위)
- protein: "protein_grams" (단백질, 그램)
- weight: "weight_kg" (체중, kg)
- study: "study_hours" 또는 "study_minutes" (공부 시간)
- learning_log: "title" (학습 내용 제목), "content" (상세 내용)

반드시 순수 JSON만 출력하세요. 마크다운이나 다른 텍스트를 포함하지 마세요.
올바른 형식:
{{"intent": "sleep", "entities": {{}}, "confidence": 0.95}}
또는
[{{"intent": "sleep", ...}}, {{"intent": "workout", ...}}]"""

        human_template = """사용자 입력: "{user_input}"

이 입력을 분석하여 JSON으로 응답하세요.
복합 명령이면 배열, 단일 명령이면 객체로 응답하세요."""

        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    def _create_response_prompt_template(self) -> ChatPromptTemplate:
        """응답 생성용 프롬프트 템플릿"""
        system_template = """당신은 친근하고 격려하는 헬스케어 어시스턴트입니다.
사용자의 건강 데이터를 기록하고 동기부여를 제공합니다.
한국어로 응답하며, 이모지를 적절히 사용합니다.
톤: {tone}"""

        human_template = """사용자: "{user_input}"

처리 결과: {context}

위 내용을 바탕으로 친근하고 격려하는 응답을 2-3문장으로 작성하세요."""

        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    def _create_chat_prompt_template(self) -> ChatPromptTemplate:
        """일반 대화용 프롬프트 템플릿"""
        system_template = """당신은 Horcrux, 친근한 건강/할일 관리 어시스턴트입니다.
사용자와 자연스럽게 대화하며, 건강 관리를 격려합니다.
한국어로 응답하고, 이모지를 적절히 사용합니다."""

        human_template = "{user_input}"

        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    def parse_intent(
        self,
        user_input: str,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        사용자 입력 파싱 (시퀸셜 체인 사용)

        Args:
            user_input: 사용자 입력
            context: 대화 컨텍스트 (현재 미사용)

        Returns:
            파싱 결과 (단일 또는 복합)
        """
        try:
            # 시퀸셜 체인 실행: Prompt → LLM → JsonParser
            parsed = self.intent_chain.invoke({"user_input": user_input})

            # 배열인 경우 (복합 명령)
            if isinstance(parsed, list):
                for item in parsed:
                    item["success"] = True
                    item["parser"] = "langchain_lcel"

                return {
                    "success": True,
                    "multiple": True,
                    "intents": parsed,
                    "parser": "langchain_lcel"
                }

            # 객체인 경우 (단일 명령)
            else:
                parsed["success"] = True
                parsed["parser"] = "langchain_lcel"
                return parsed

        except json.JSONDecodeError:
            # JSON 파싱 실패 시 일반 대화로 처리
            return {
                "success": True,
                "intent": "chat",
                "entities": {"message": user_input},
                "confidence": 0.8,
                "parser": "langchain_lcel"
            }

        except Exception as e:
            print(f"LangChain 오류: {e}")
            import traceback
            traceback.print_exc()
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
        대화형 응답 생성 (시퀸셜 체인 사용)

        Args:
            user_input: 사용자 입력
            context: 처리 결과 컨텍스트
            tone: 응답 톤

        Returns:
            대화형 응답
        """
        try:
            # 시퀸셜 체인 실행
            response_chain = self.response_prompt_template | self.llm
            response = response_chain.invoke({
                "user_input": user_input,
                "context": context,
                "tone": tone
            })
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
            chat_history: 대화 이력 (향후 구현)

        Returns:
            AI 응답
        """
        try:
            # 시퀸셜 체인 실행
            chat_chain = self.chat_prompt_template | self.llm
            response = chat_chain.invoke({"user_input": user_input})
            return response.content.strip()

        except Exception as e:
            print(f"대화 오류: {e}")
            return "죄송해요, 잠시 문제가 있었어요. 다시 말씀해주세요! 😅"


# 사용 예시
if __name__ == "__main__":
    llm = LangChainLLM()

    # 테스트
    test_cases = [
        "7시간 잤어",
        "어제 8시간 자고 30분 운동했어",
        "프롬포트 템플릿과 chrome mcp에 대해 알게됐어",
    ]

    for test in test_cases:
        print(f"\n입력: {test}")
        result = llm.parse_intent(test)
        print(f"파싱 결과: {result}")
