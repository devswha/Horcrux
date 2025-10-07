"""
설정 관리 모듈
환경 변수와 config.yaml을 통합 관리
"""
import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

# .env 파일 자동 로드
load_dotenv()


class Config:
    """설정 관리 클래스"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        설정 초기화

        Args:
            config_path: config.yaml 파일 경로
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._override_with_env()

    def _load_config(self) -> Dict[str, Any]:
        """config.yaml 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ {self.config_path} 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
            return self._get_default_config()

    def _override_with_env(self):
        """환경 변수로 설정 덮어쓰기"""
        # 데이터베이스 경로
        if db_path := os.getenv("DATABASE_PATH"):
            self.config.setdefault("database", {})["path"] = db_path

        # 로그 레벨
        if log_level := os.getenv("LOG_LEVEL"):
            self.config.setdefault("logging", {})["level"] = log_level

        # 웹 서버 설정
        if web_port := os.getenv("WEB_PORT"):
            self.config.setdefault("web_ui", {})["port"] = int(web_port)

        if web_host := os.getenv("WEB_HOST"):
            self.config.setdefault("web_ui", {})["host"] = web_host

        # LLM 제공자
        if llm_provider := os.getenv("LLM_PROVIDER"):
            self.config.setdefault("llm", {})["provider"] = llm_provider

        # API 키들은 환경 변수에서 직접 읽도록
        # (보안상 config.yaml에 저장하지 않음)

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "health_targets": {
                "sleep_hours": 7,
                "workout_minutes": 30,
                "protein_grams": 100
            },
            "alerts": {
                "sleep_warning": 6,
                "consecutive_days_check": 3
            },
            "exp_rules": {
                "task_complete": 20,
                "sleep_goal": 15,
                "workout_base": 10,
                "protein_goal": 10,
                "habit_streak": 5,
                "study_per_hour": 30,
                "consecutive_bonus": 100
            },
            "llm": {
                "provider": "langchain",
                "enabled": True,
                "strategy": "fallback"
            },
            "database": {
                "path": "lifebot.db"
            },
            "logging": {
                "level": "INFO",
                "file": "lifebot.log",
                "console": True
            },
            "web_ui": {
                "chart_days": 7,
                "max_chat_history": 50,
                "theme": "light"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        설정 값 가져오기

        Args:
            key: 설정 키 (점 표기법 지원: "llm.provider")
            default: 기본값

        Returns:
            설정 값
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        """
        설정 값 변경

        Args:
            key: 설정 키 (점 표기법 지원)
            value: 설정 값
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            config = config.setdefault(k, {})

        config[keys[-1]] = value

    def save(self):
        """설정을 config.yaml에 저장"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def get_api_key(self, provider: str) -> str:
        """
        API 키 가져오기 (환경 변수에서만)

        Args:
            provider: LLM 제공자 (openai, anthropic)

        Returns:
            API 키 또는 None
        """
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "langchain": "OPENAI_API_KEY"  # LangChain은 OpenAI 키 사용
        }

        env_var = key_map.get(provider.lower())
        if env_var:
            return os.getenv(env_var)

        return None


# 전역 설정 인스턴스
config = Config()


if __name__ == "__main__":
    # 테스트
    print("=== 설정 테스트 ===")
    print(f"LLM Provider: {config.get('llm.provider')}")
    print(f"Database Path: {config.get('database.path')}")
    print(f"Sleep Target: {config.get('health_targets.sleep_hours')} hours")
    print(f"OpenAI API Key: {'설정됨' if config.get_api_key('openai') else '없음'}")