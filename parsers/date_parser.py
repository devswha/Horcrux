"""
한국어 날짜 표현 파싱
예: "어제", "오늘", "3일 전", "지난주 금요일"
"""
import re
from datetime import datetime, timedelta
from typing import Optional


class DateParser:
    """한국어 날짜 표현 파서"""

    def __init__(self):
        # 상대적 날짜 키워드
        self.relative_dates = {
            "오늘": 0,
            "today": 0,
            "어제": -1,
            "yesterday": -1,
            "그제": -2,
            "그저께": -2,
            "내일": 1,
            "tomorrow": 1,
            "모레": 2,
        }

        # N일 전/후 패턴
        self.days_ago_pattern = re.compile(r'(\d+)\s*일\s*(전|앞|이전)')
        self.days_later_pattern = re.compile(r'(\d+)\s*일\s*(후|뒤|이후)')

        # 주 단위 패턴
        self.weeks_ago_pattern = re.compile(r'(\d+)\s*주\s*(전|앞|이전)')
        self.weeks_later_pattern = re.compile(r'(\d+)\s*주\s*(후|뒤|이후)')

        # 절대 날짜 패턴 (YYYY-MM-DD, MM/DD 등)
        self.absolute_date_pattern = re.compile(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})')
        self.month_day_pattern = re.compile(r'(\d{1,2})월\s*(\d{1,2})일')

    def parse(self, text: str, reference_date: Optional[datetime] = None) -> Optional[str]:
        """
        한국어 날짜 표현을 YYYY-MM-DD 형식으로 변환

        Args:
            text: 날짜 표현 ("어제", "3일 전" 등)
            reference_date: 기준 날짜 (기본: 오늘)

        Returns:
            YYYY-MM-DD 형식의 날짜 문자열, 파싱 실패 시 None
        """
        if not reference_date:
            reference_date = datetime.now()

        text = text.strip()

        # 1. 상대적 키워드 체크
        for keyword, offset in self.relative_dates.items():
            if keyword in text:
                target_date = reference_date + timedelta(days=offset)
                return target_date.strftime("%Y-%m-%d")

        # 2. N일 전/후 패턴
        match = self.days_ago_pattern.search(text)
        if match:
            days = int(match.group(1))
            target_date = reference_date - timedelta(days=days)
            return target_date.strftime("%Y-%m-%d")

        match = self.days_later_pattern.search(text)
        if match:
            days = int(match.group(1))
            target_date = reference_date + timedelta(days=days)
            return target_date.strftime("%Y-%m-%d")

        # 3. N주 전/후 패턴
        match = self.weeks_ago_pattern.search(text)
        if match:
            weeks = int(match.group(1))
            target_date = reference_date - timedelta(weeks=weeks)
            return target_date.strftime("%Y-%m-%d")

        match = self.weeks_later_pattern.search(text)
        if match:
            weeks = int(match.group(1))
            target_date = reference_date + timedelta(weeks=weeks)
            return target_date.strftime("%Y-%m-%d")

        # 4. 절대 날짜 (YYYY-MM-DD)
        match = self.absolute_date_pattern.search(text)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            try:
                target_date = datetime(year, month, day)
                return target_date.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # 5. MM월 DD일 패턴
        match = self.month_day_pattern.search(text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year = reference_date.year
            try:
                target_date = datetime(year, month, day)
                return target_date.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # 파싱 실패
        return None

    def extract_date_from_sentence(self, sentence: str) -> Optional[str]:
        """
        문장에서 날짜 표현 추출 및 파싱

        Args:
            sentence: 입력 문장

        Returns:
            파싱된 날짜 또는 None
        """
        # 단어별로 체크
        words = sentence.split()
        for word in words:
            parsed = self.parse(word)
            if parsed:
                return parsed

        # 전체 문장에서 패턴 매칭
        parsed = self.parse(sentence)
        if parsed:
            return parsed

        # 날짜 표현이 없으면 오늘로 간주
        return datetime.now().strftime("%Y-%m-%d")
