"""
기본 에이전트 추상 클래스
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        메시지 처리 (각 에이전트가 구현)

        Args:
            message: 입력 메시지

        Returns:
            처리 결과 메시지
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name})>"
