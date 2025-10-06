"""
한국어 수량 표현 파싱
예: "5시간", "30분", "100그램", "반시간"
"""
import re
from typing import Optional, Tuple


class NumberParser:
    """한국어 수량 표현 파서"""

    def __init__(self):
        # 한글 숫자
        self.korean_numbers = {
            "영": 0, "일": 1, "이": 2, "삼": 3, "사": 4,
            "오": 5, "육": 6, "칠": 7, "팔": 8, "구": 9,
            "십": 10, "백": 100, "천": 1000
        }

        # 특수 표현
        self.special_numbers = {
            "반": 0.5,
            "한": 1,
            "두": 2,
            "세": 3,
            "네": 4,
            "다섯": 5,
            "여섯": 6,
            "일곱": 7,
            "여덟": 8,
            "아홉": 9,
        }

        # 시간 패턴
        self.hour_patterns = [
            re.compile(r'(\d+\.?\d*)\s*시간'),
            re.compile(r'(\d+\.?\d*)\s*h'),
            re.compile(r'(\d+\.?\d*)\s*hr'),
        ]

        # 분 패턴
        self.minute_patterns = [
            re.compile(r'(\d+)\s*분'),
            re.compile(r'(\d+)\s*m(?:in)?'),
        ]

        # 그램 패턴
        self.gram_patterns = [
            re.compile(r'(\d+\.?\d*)\s*g(?:ram)?'),
            re.compile(r'(\d+\.?\d*)\s*그램'),
        ]

        # kg 패턴
        self.kg_patterns = [
            re.compile(r'(\d+\.?\d*)\s*kg'),
            re.compile(r'(\d+\.?\d*)\s*키로'),
        ]

    def parse_hours(self, text: str) -> Optional[float]:
        """
        시간 표현 파싱

        Args:
            text: "5시간", "3.5시간", "반시간" 등

        Returns:
            시간 (float) 또는 None
        """
        text = text.strip()

        # 특수 표현 체크
        if "반시간" in text or "반 시간" in text:
            return 0.5

        # 숫자 패턴 매칭
        for pattern in self.hour_patterns:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass

        # 한글 숫자 파싱
        korean_num = self._parse_korean_number(text)
        if korean_num is not None and "시간" in text:
            return float(korean_num)

        return None

    def parse_minutes(self, text: str) -> Optional[int]:
        """
        분 표현 파싱

        Args:
            text: "30분", "반시간" 등

        Returns:
            분 (int) 또는 None
        """
        text = text.strip()

        # 특수 표현
        if "반시간" in text or "반 시간" in text:
            return 30

        # 숫자 패턴 매칭
        for pattern in self.minute_patterns:
            match = pattern.search(text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass

        # 한글 숫자
        korean_num = self._parse_korean_number(text)
        if korean_num is not None and "분" in text:
            return int(korean_num)

        return None

    def parse_grams(self, text: str) -> Optional[float]:
        """
        그램 표현 파싱

        Args:
            text: "100g", "150그램" 등

        Returns:
            그램 (float) 또는 None
        """
        text = text.strip()

        # 숫자 패턴 매칭
        for pattern in self.gram_patterns:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass

        return None

    def parse_weight(self, text: str) -> Optional[float]:
        """
        체중 표현 파싱 (kg)

        Args:
            text: "70kg", "65.5키로" 등

        Returns:
            kg (float) 또는 None
        """
        text = text.strip()

        # 숫자 패턴 매칭
        for pattern in self.kg_patterns:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass

        return None

    def extract_number_unit_pairs(self, text: str) -> list:
        """
        문장에서 모든 숫자+단위 쌍 추출

        Args:
            text: 입력 문장

        Returns:
            [(value, unit), ...] 형태의 리스트
        """
        results = []

        # 시간
        hours = self.parse_hours(text)
        if hours is not None:
            results.append((hours, "hours"))

        # 분
        minutes = self.parse_minutes(text)
        if minutes is not None:
            results.append((minutes, "minutes"))

        # 그램
        grams = self.parse_grams(text)
        if grams is not None:
            results.append((grams, "grams"))

        # 체중
        weight = self.parse_weight(text)
        if weight is not None:
            results.append((weight, "kg"))

        return results

    def _parse_korean_number(self, text: str) -> Optional[int]:
        """
        한글 숫자 표현 파싱 (간단한 버전)

        Args:
            text: "다섯", "십" 등

        Returns:
            숫자 또는 None
        """
        # 특수 표현 체크
        for word, num in self.special_numbers.items():
            if word in text:
                return int(num)

        # 기본 한글 숫자
        for word, num in self.korean_numbers.items():
            if word in text:
                return num

        return None
