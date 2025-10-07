"""
대화형 파싱 에이전트 (LLM 전용)
- 한국어 자연어 입력 파싱
- 의도 파악 (intent classification)
- 엔티티 추출 (entity extraction)
- LangChain + GPT-4o-mini 사용
"""
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent

# 정규식 파서 제거 (LLM으로 완전 대체)
# from parsers.korean_patterns import KoreanPatterns
# from parsers.date_parser import DateParser
# from parsers.number_parser import NumberParser


class ConversationAgent(BaseAgent):
    """대화형 파싱 에이전트"""

    def __init__(self, llm_client=None):
        super().__init__("Conversation")

        # 정규식 파서 (더 이상 사용하지 않음 - LLM 전용)
        # self.patterns = KoreanPatterns()
        # self.date_parser = DateParser()
        # self.number_parser = NumberParser()

        # LLM 클라이언트 (필수)
        self.llm = llm_client

        if not self.llm:
            print("⚠️ LLM 클라이언트가 없습니다. parse_input이 작동하지 않습니다.")

        # 대화 히스토리 (간단한 컨텍스트 유지)
        self.history: List[str] = []
        self.max_history = 5

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        action = message.get("action")

        if action == "parse":
            text = message.get("data", {}).get("text", "")
            return self.parse_input(text)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def parse_input(self, text: str) -> Dict[str, Any]:
        """
        사용자 입력 파싱 (LLM 전용)

        Args:
            text: 사용자 입력 텍스트

        Returns:
            파싱 결과 {
                "intent": "sleep"|"workout"|"task_add"등,
                "entities": {...},
                "confidence": 0.0~1.0,
                "success": True/False
            }
        """
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Empty input"
            }

        # 히스토리에 추가
        self.history.append(text)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # LLM으로 직접 파싱 (정규식 제거)
        if not self.llm:
            return {
                "success": False,
                "error": "LLM이 설정되지 않았습니다."
            }

        print(f"🤖 LLM 파싱: {text}")
        llm_result = self._parse_with_llm(text)

        if llm_result.get("success"):
            # 복합 명령인 경우
            if llm_result.get("multiple"):
                print(f"✅ 복합 명령: {len(llm_result.get('intents', []))}개 의도")
            else:
                print(f"✅ 단일 명령: {llm_result.get('intent')}")

            return llm_result

        # LLM 파싱 실패 시
        print(f"⚠️ LLM 파싱 실패")
        return {
            "success": False,
            "error": "파싱 실패",
            "original_text": text
        }

    def _extract_entities(self, intent: str, text: str) -> Dict[str, Any]:
        """
        의도별 엔티티 추출

        Args:
            intent: 의도
            text: 원본 텍스트

        Returns:
            엔티티 딕셔너리
        """
        entities = {}

        # 날짜 추출 (대부분의 의도에서 필요)
        date = self.date_parser.extract_date_from_sentence(text)
        if date:
            entities["date"] = date

        # 의도별 처리
        if intent == "sleep":
            hours = self.number_parser.parse_hours(text)
            if hours is not None:
                entities["sleep_hours"] = hours

        elif intent == "workout":
            # 먼저 분 단위 체크
            minutes = self.number_parser.parse_minutes(text)
            if minutes is not None:
                entities["workout_minutes"] = minutes
            else:
                # 시간 단위 체크 (시간 → 분 변환)
                hours = self.number_parser.parse_hours(text)
                if hours is not None:
                    entities["workout_minutes"] = int(hours * 60)

        elif intent == "protein":
            grams = self.number_parser.parse_grams(text)
            if grams is not None:
                entities["protein_grams"] = grams

        elif intent == "weight":
            weight = self.number_parser.parse_weight(text)
            if weight is not None:
                entities["weight_kg"] = weight

        elif intent == "task_add":
            title = self.patterns.extract_task_title(text)
            if title:
                entities["task_title"] = title

        elif intent == "task_complete":
            task_id = self.patterns.extract_task_id(text)
            if task_id > 0:
                entities["task_id"] = task_id
            else:
                # ID가 없으면 제목으로 찾기
                title = self.patterns.extract_task_title(text)
                if title:
                    entities["task_title"] = title

        elif intent == "summary":
            # 날짜는 이미 추출됨
            pass

        elif intent == "progress":
            # 진행도는 엔티티 없음
            pass

        return entities

    def _calculate_confidence(self, intent: str, entities: Dict[str, Any]) -> float:
        """
        신뢰도 계산

        Args:
            intent: 의도
            entities: 엔티티

        Returns:
            0.0 ~ 1.0 신뢰도
        """
        if intent == "unknown":
            return 0.0

        # 기본 신뢰도
        confidence = 0.5

        # 엔티티가 충분히 추출되었는지 확인
        if intent == "sleep" and "sleep_hours" in entities:
            confidence = 0.9
        elif intent == "workout" and "workout_minutes" in entities:
            confidence = 0.9
        elif intent == "protein" and "protein_grams" in entities:
            confidence = 0.9
        elif intent == "weight" and "weight_kg" in entities:
            confidence = 0.9
        elif intent == "task_add" and "task_title" in entities:
            confidence = 0.85
        elif intent == "task_complete" and ("task_id" in entities or "task_title" in entities):
            confidence = 0.85
        elif intent == "summary":
            confidence = 0.95
        elif intent == "progress":
            confidence = 0.95

        return confidence

    def ask_clarification(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        명확화 질문 생성

        Args:
            intent: 의도
            entities: 추출된 엔티티

        Returns:
            명확화 질문 문자열
        """
        if intent == "sleep" and "sleep_hours" not in entities:
            return "몇 시간 주무셨나요?"

        elif intent == "workout" and "workout_minutes" not in entities:
            return "몇 분 운동하셨나요?"

        elif intent == "protein" and "protein_grams" not in entities:
            return "단백질을 몇 그램 섭취하셨나요?"

        elif intent == "weight" and "weight_kg" not in entities:
            return "체중이 몇 kg인가요?"

        elif intent == "task_add" and "task_title" not in entities:
            return "어떤 할일인가요?"

        elif intent == "task_complete" and "task_id" not in entities and "task_title" not in entities:
            return "어떤 할일을 완료하셨나요? (번호 또는 제목)"

        elif intent == "unknown":
            return "무엇을 도와드릴까요? (수면/운동/할일/요약 등)"

        return ""

    def parse_multiple(self, text: str) -> List[Dict[str, Any]]:
        """
        복합 명령 파싱 (예: "어제 5시간 자고 30분 운동했어")

        Args:
            text: 입력 텍스트

        Returns:
            파싱 결과 리스트
        """
        results = []

        # 간단한 구현: '그리고', '고', ',' 등으로 분리
        separators = ["그리고", "하고", ","]
        parts = [text]

        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts

        # 각 부분 파싱
        for part in parts:
            part = part.strip()
            if not part:
                continue

            result = self.parse_input(part)
            if result.get("success") and result.get("intent") != "unknown":
                results.append(result)

        return results if results else [self.parse_input(text)]

    def _parse_with_llm(self, text: str) -> Dict[str, Any]:
        """
        LLM을 사용한 파싱 (백업)

        Args:
            text: 입력 텍스트

        Returns:
            파싱 결과
        """
        if not self.llm:
            return {
                "success": False,
                "error": "LLM not available"
            }

        try:
            # LLM으로 의도 파싱
            result = self.llm.parse_intent(text, context=self.history)

            if result.get("success"):
                result["parser"] = "llm"
                result["original_text"] = text
                return result
            else:
                return {
                    "success": False,
                    "error": "LLM parsing failed"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"LLM error: {str(e)}"
            }
