"""
LLM 클라이언트 - Claude/OpenAI/Ollama API 추상화
"""
import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import yaml


class LLMClient(ABC):
    """LLM 클라이언트 추상 클래스"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        pass

    @abstractmethod
    def parse_intent(
        self,
        user_input: str,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """의도 파싱 (대화형 입력 분석)"""
        pass


class ClaudeLLMClient(LLMClient):
    """Claude API 클라이언트"""

    def __init__(self, config: Dict[str, Any]):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic 라이브러리가 필요합니다. "
                "pip install anthropic 로 설치하세요."
            )

        api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(
                f"{api_key_env} 환경 변수가 설정되지 않았습니다. "
                ".env 파일을 확인하세요."
            )

        self.client = Anthropic(api_key=api_key)
        self.model = config.get("model", "claude-3-5-sonnet-20241022")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            system=system_prompt or "",
            messages=messages
        )

        return response.content[0].text

    def parse_intent(
        self,
        user_input: str,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """의도 파싱"""
        prompt = f"""사용자 입력을 분석하여 JSON으로 응답하세요.

사용자 입력: "{user_input}"

분석 항목:
1. intent: 의도 (sleep, workout, protein, weight, task_add, task_complete, study, habit_check, summary, progress 중 하나)
2. entities: 추출된 정보
   - sleep: sleep_hours (시간 계산 필요 시 자동 계산. 예: "새벽3시부터 12시까지" → 9시간)
   - workout: workout_minutes (분 단위)
   - protein: protein_grams (그램)
   - weight: weight_kg (킬로그램)
   - task_add: task_title (할일 제목)
   - task_complete: task_id 또는 task_title
   - study: study_hours 또는 study_minutes (공부/공부중/학습 등)
   - date: 날짜 ("어제"면 어제 날짜, "오늘"이면 오늘 날짜)
3. confidence: 신뢰도 (0.0~1.0)

**중요**:
- 여러 의도가 포함된 경우 JSON 배열로 반환하세요
- 단일 의도면 JSON 객체로 반환하세요

단일 의도 예시:
- "새벽3시부터 12시까지 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 9}}, "confidence": 0.95}}

복합 의도 예시:
- "어제 7시간 자고 30분 운동했어" → [
    {{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "어제"}}, "confidence": 0.95}},
    {{"intent": "workout", "entities": {{"workout_minutes": 30, "date": "어제"}}, "confidence": 0.95}}
  ]
- "오늘 약속은 영화보기고, 어제 새벽3시부터 12시까지 잤어" → [
    {{"intent": "task_add", "entities": {{"task_title": "영화보기"}}, "confidence": 0.9}},
    {{"intent": "sleep", "entities": {{"sleep_hours": 9, "date": "어제"}}, "confidence": 0.95}}
  ]

JSON만 응답하세요 (배열 또는 객체):"""

        if context:
            prompt += f"\n\n대화 컨텍스트:\n" + "\n".join(context[-3:])

        response = self.generate(
            prompt,
            system_prompt="JSON만 응답하는 파서입니다.",
            temperature=0.3
        )

        # JSON 파싱
        import json
        try:
            parsed = json.loads(response.strip())

            # 배열인 경우 (복합 명령)
            if isinstance(parsed, list):
                # 모든 항목에 success 플래그 추가
                for item in parsed:
                    item["success"] = True
                    item["parser"] = "llm"

                return {
                    "success": True,
                    "multiple": True,
                    "intents": parsed,  # 복합 의도들
                    "parser": "llm"
                }

            # 객체인 경우 (단일 명령)
            else:
                parsed["success"] = True
                parsed["parser"] = "llm"
                return parsed

        except json.JSONDecodeError:
            return {
                "success": False,
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "error": "JSON 파싱 실패"
            }


class OpenAILLMClient(LLMClient):
    """OpenAI API 클라이언트"""

    def __init__(self, config: Dict[str, Any]):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai 라이브러리가 필요합니다. "
                "pip install openai 로 설치하세요."
            )

        api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(
                f"{api_key_env} 환경 변수가 설정되지 않았습니다. "
                ".env 파일을 확인하세요."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = config.get("model", "gpt-4o-mini")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=messages
        )

        return response.choices[0].message.content

    def parse_intent(
        self,
        user_input: str,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """의도 파싱"""
        prompt = f"""사용자 입력을 분석하여 JSON으로 응답하세요.

사용자 입력: "{user_input}"

분석 항목:
1. intent: 의도 (sleep, workout, protein, weight, task_add, task_complete, study, habit_check, summary, progress 중 하나)
2. entities: 추출된 정보
   - sleep: sleep_hours (시간 계산 필요 시 자동 계산. 예: "새벽3시부터 12시까지" → 9시간)
   - workout: workout_minutes (분 단위)
   - protein: protein_grams (그램)
   - weight: weight_kg (킬로그램)
   - task_add: task_title (할일 제목)
   - task_complete: task_id 또는 task_title
   - study: study_hours 또는 study_minutes (공부/공부중/학습 등)
   - date: 날짜 ("어제"면 어제 날짜, "오늘"이면 오늘 날짜)
3. confidence: 신뢰도 (0.0~1.0)

**중요**:
- 여러 의도가 포함된 경우 JSON 배열로 반환하세요
- 단일 의도면 JSON 객체로 반환하세요

단일 의도 예시:
- "새벽3시부터 12시까지 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 9}}, "confidence": 0.95}}

복합 의도 예시:
- "어제 7시간 자고 30분 운동했어" → [
    {{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "어제"}}, "confidence": 0.95}},
    {{"intent": "workout", "entities": {{"workout_minutes": 30, "date": "어제"}}, "confidence": 0.95}}
  ]
- "오늘 약속은 영화보기고, 어제 새벽3시부터 12시까지 잤어" → [
    {{"intent": "task_add", "entities": {{"task_title": "영화보기"}}, "confidence": 0.9}},
    {{"intent": "sleep", "entities": {{"sleep_hours": 9, "date": "어제"}}, "confidence": 0.95}}
  ]

JSON만 응답하세요 (배열 또는 객체):"""

        if context:
            prompt += f"\n\n대화 컨텍스트:\n" + "\n".join(context[-3:])

        response = self.generate(
            prompt,
            system_prompt="JSON만 응답하는 파서입니다.",
            temperature=0.3
        )

        # JSON 파싱
        import json
        try:
            parsed = json.loads(response.strip())

            # 배열인 경우 (복합 명령)
            if isinstance(parsed, list):
                # 모든 항목에 success 플래그 추가
                for item in parsed:
                    item["success"] = True
                    item["parser"] = "llm"

                return {
                    "success": True,
                    "multiple": True,
                    "intents": parsed,  # 복합 의도들
                    "parser": "llm"
                }

            # 객체인 경우 (단일 명령)
            else:
                parsed["success"] = True
                parsed["parser"] = "llm"
                return parsed

        except json.JSONDecodeError:
            return {
                "success": False,
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "error": "JSON 파싱 실패"
            }


class OllamaLLMClient(LLMClient):
    """Ollama API 클라이언트 (로컬 LLM)"""

    def __init__(self, config: Dict[str, Any]):
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ImportError(
                "ollama 라이브러리가 필요합니다. "
                "pip install ollama 로 설치하세요."
            )

        self.host = config.get("host", "http://localhost:11434")
        self.model = config.get("model", "llama3.2:3b")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": kwargs.get("temperature", self.temperature),
                    "num_predict": kwargs.get("max_tokens", self.max_tokens)
                }
            )

            return response['message']['content']

        except Exception as e:
            raise RuntimeError(f"Ollama 생성 실패: {str(e)}")

    def parse_intent(
        self,
        user_input: str,
        context: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """의도 파싱"""
        prompt = f"""사용자 입력을 분석하여 JSON으로 응답하세요.

사용자 입력: "{user_input}"

분석 항목:
1. intent: 의도 (sleep, workout, protein, weight, task_add, task_complete, study, habit_check, summary, progress 중 하나)
2. entities: 추출된 정보
   - sleep: sleep_hours (시간 계산 필요 시 자동 계산. 예: "새벽3시부터 12시까지" → 9시간)
   - workout: workout_minutes (분 단위)
   - protein: protein_grams (그램)
   - weight: weight_kg (킬로그램)
   - task_add: task_title (할일 제목)
   - task_complete: task_id 또는 task_title
   - study: study_hours 또는 study_minutes (공부/공부중/학습 등)
   - date: 날짜 ("어제"면 어제 날짜, "오늘"이면 오늘 날짜)
3. confidence: 신뢰도 (0.0~1.0)

**중요**:
- 여러 의도가 포함된 경우 JSON 배열로 반환하세요
- 단일 의도면 JSON 객체로 반환하세요

단일 의도 예시:
- "새벽3시부터 12시까지 잤어" → {{"intent": "sleep", "entities": {{"sleep_hours": 9}}, "confidence": 0.95}}

복합 의도 예시:
- "어제 7시간 자고 30분 운동했어" → [
    {{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "어제"}}, "confidence": 0.95}},
    {{"intent": "workout", "entities": {{"workout_minutes": 30, "date": "어제"}}, "confidence": 0.95}}
  ]
- "오늘 약속은 영화보기고, 어제 새벽3시부터 12시까지 잤어" → [
    {{"intent": "task_add", "entities": {{"task_title": "영화보기"}}, "confidence": 0.9}},
    {{"intent": "sleep", "entities": {{"sleep_hours": 9, "date": "어제"}}, "confidence": 0.95}}
  ]

JSON만 응답하세요 (배열 또는 객체):"""

        if context:
            prompt += f"\n\n대화 컨텍스트:\n" + "\n".join(context[-3:])

        response = self.generate(
            prompt,
            system_prompt="JSON만 응답하는 파서입니다.",
            temperature=0.3
        )

        # JSON 파싱
        import json
        try:
            parsed = json.loads(response.strip())

            # 배열인 경우 (복합 명령)
            if isinstance(parsed, list):
                # 모든 항목에 success 플래그 추가
                for item in parsed:
                    item["success"] = True
                    item["parser"] = "llm"

                return {
                    "success": True,
                    "multiple": True,
                    "intents": parsed,  # 복합 의도들
                    "parser": "llm"
                }

            # 객체인 경우 (단일 명령)
            else:
                parsed["success"] = True
                parsed["parser"] = "llm"
                return parsed

        except json.JSONDecodeError:
            return {
                "success": False,
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "error": "JSON 파싱 실패"
            }


class LLMClientFactory:
    """LLM 클라이언트 팩토리"""

    @staticmethod
    def create(config_path: str = "config.yaml") -> Optional[LLMClient]:
        """
        설정 파일로부터 LLM 클라이언트 생성

        Returns:
            LLMClient 또는 None (비활성화 시)
        """
        # config.yaml 로드
        if not os.path.exists(config_path):
            return None

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        llm_config = config.get("llm", {})

        # LLM 비활성화 시
        if not llm_config.get("enabled", False):
            return None

        provider = llm_config.get("provider", "claude")

        if provider == "claude":
            claude_config = llm_config.get("claude", {})
            return ClaudeLLMClient(claude_config)

        elif provider == "openai":
            openai_config = llm_config.get("openai", {})
            return OpenAILLMClient(openai_config)

        elif provider == "ollama":
            ollama_config = llm_config.get("ollama", {})
            return OllamaLLMClient(ollama_config)

        elif provider == "langchain":
            # LangChain 사용
            from core.langchain_llm import LangChainLLM
            return LangChainLLM(config_path)

        else:
            raise ValueError(f"지원하지 않는 LLM 제공자: {provider}")


# 사용 예시
if __name__ == "__main__":
    # LLM 클라이언트 생성
    llm = LLMClientFactory.create()

    if llm:
        print("✅ LLM 클라이언트 생성 성공")

        # 의도 파싱 테스트
        result = llm.parse_intent("어제 7시간 잤어")
        print(f"파싱 결과: {result}")

        # 텍스트 생성 테스트
        advice = llm.generate(
            "사용자가 3일 연속 5시간만 잤습니다. 짧은 조언을 주세요.",
            system_prompt="당신은 친절한 헬스케어 어시스턴트입니다."
        )
        print(f"조언: {advice}")
    else:
        print("⚠️  LLM 비활성화됨 (config.yaml 확인)")
