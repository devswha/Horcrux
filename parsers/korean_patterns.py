"""
한국어 자연어 패턴 정의
의도(intent) 파악을 위한 정규식 패턴들
"""
import re
from typing import Dict, List, Pattern


class KoreanPatterns:
    """한국어 패턴 정의 클래스"""

    def __init__(self):
        # 수면 패턴
        self.sleep_patterns: List[Pattern] = [
            re.compile(r'(\d+\.?\d*)\s*시간\s*(잤|수면|睡|자)'),
            re.compile(r'(잤|수면|자)\s*(\d+\.?\d*)\s*시간'),
            re.compile(r'수면\s*시간'),
            re.compile(r'못\s*잤|안\s*잤'),
        ]

        # 운동 패턴
        self.workout_patterns: List[Pattern] = [
            re.compile(r'(\d+)\s*분\s*(운동|헬스|러닝|조깅|달리기|걷기|수영)'),
            re.compile(r'(운동|헬스|러닝|조깅|달리기|걷기|수영)\s*(\d+)\s*분'),
            re.compile(r'(\d+\.?\d*)\s*시간\s*(운동|헬스|러닝|조깅|달리기|걷기|수영)'),
            re.compile(r'(운동|헬스|러닝|조깅|달리기|걷기|수영)\s*(\d+\.?\d*)\s*시간'),
            re.compile(r'(운동|헬스|러닝|조깅)했'),
            re.compile(r'(운동|헬스|러닝|조깅)\s*안?\s*했'),
        ]

        # 단백질 패턴
        self.protein_patterns: List[Pattern] = [
            re.compile(r'(\d+\.?\d*)\s*(g|그램)\s*(단백질|프로틴)'),
            re.compile(r'(단백질|프로틴)\s*(\d+\.?\d*)\s*(g|그램)'),
            re.compile(r'단백질|프로틴'),
        ]

        # 체중 패턴
        self.weight_patterns: List[Pattern] = [
            re.compile(r'(\d+\.?\d*)\s*(kg|키로)'),
            re.compile(r'체중\s*(\d+\.?\d*)'),
            re.compile(r'몸무게'),
        ]

        # 할일 추가 패턴
        self.task_add_patterns: List[Pattern] = [
            re.compile(r'(.+?)\s*(해야|할\s*것|하기|할일|todo)'),
            re.compile(r'(할일|todo|task)\s*(.+)'),
            re.compile(r'(.+?)\s*해야\s*해'),
            re.compile(r'(.+?)\s*하자'),
        ]

        # 할일 완료 패턴
        self.task_complete_patterns: List[Pattern] = [
            re.compile(r'(.+?)\s*(완료|끝|했어|했다|함|done)'),
            re.compile(r'(완료|끝|done)\s*(.+)'),
            re.compile(r'할일\s*(\d+)\s*(완료|끝|done)'),
        ]

        # 습관 패턴
        self.habit_patterns: List[Pattern] = [
            re.compile(r'(금연|운동|독서|명상|물\s*마시기)\s*(\d+)일째'),
            re.compile(r'(금연|운동|독서|명상)\s*(성공|실패|스킵)'),
        ]

        # 요약/조회 패턴
        self.summary_patterns: List[Pattern] = [
            re.compile(r'(오늘|어제|이번주)\s*(요약|정리|상황|어때)'),
            re.compile(r'요약|정리|summary'),
            re.compile(r'어떻|어떠|어때'),
        ]

        # 진행도/레벨 패턴
        self.progress_patterns: List[Pattern] = [
            re.compile(r'(레벨|level|진행|progress|경험치|xp)'),
            re.compile(r'(몇|얼마나)\s*(레벨|진행)'),
        ]

        # 습관 생성 패턴
        self.habit_create_patterns: List[Pattern] = [
            re.compile(r'(.+?)\s*(습관|habit)\s*(추가|만들|생성)'),
            re.compile(r'(습관|habit)\s*(.+?)\s*(추가|만들|생성)'),
        ]

    def match_intent(self, text: str) -> str:
        """
        입력 텍스트에서 의도(intent) 파악

        Args:
            text: 사용자 입력

        Returns:
            의도 문자열 ('sleep', 'workout', 'task_add', 'summary', 'unknown' 등)
        """
        text = text.strip()

        # 우선순위 순서대로 체크
        # 1. 요약/조회 (다른 키워드와 겹칠 수 있으므로 먼저 체크)
        if self._matches_any(text, self.summary_patterns):
            return "summary"

        # 2. 진행도
        if self._matches_any(text, self.progress_patterns):
            return "progress"

        # 3. 건강 지표 (할일보다 우선)
        # 수면
        if self._matches_any(text, self.sleep_patterns):
            return "sleep"

        # 운동
        if self._matches_any(text, self.workout_patterns):
            return "workout"

        # 단백질
        if self._matches_any(text, self.protein_patterns):
            return "protein"

        # 체중
        if self._matches_any(text, self.weight_patterns):
            return "weight"

        # 4. 할일 완료 (추가보다 먼저 체크)
        if self._matches_any(text, self.task_complete_patterns):
            return "task_complete"

        # 5. 할일 추가
        if self._matches_any(text, self.task_add_patterns):
            return "task_add"

        # 6. 습관 생성
        if self._matches_any(text, self.habit_create_patterns):
            return "habit_create"

        # 7. 습관 기록
        if self._matches_any(text, self.habit_patterns):
            return "habit_log"

        # 알 수 없는 의도
        return "unknown"

    def extract_task_title(self, text: str) -> str:
        """할일 제목 추출"""
        # "~해야 해" 패턴
        match = re.search(r'(.+?)\s*해야\s*해?', text)
        if match:
            return match.group(1).strip()

        # "~하기" 패턴
        match = re.search(r'(.+?)\s*하기', text)
        if match:
            return match.group(1).strip()

        # "할일 ~" 패턴
        match = re.search(r'할일\s+(.+)', text)
        if match:
            return match.group(1).strip()

        # 전체 텍스트에서 키워드 제거
        cleaned = text
        for keyword in ["해야", "할것", "하기", "할일", "todo", "해", "하자"]:
            cleaned = cleaned.replace(keyword, "")

        return cleaned.strip()

    def extract_task_id(self, text: str) -> int:
        """할일 ID 추출 (완료 시)"""
        # "할일 5 완료"
        match = re.search(r'할일\s*(\d+)', text)
        if match:
            return int(match.group(1))

        # 단순 숫자
        match = re.search(r'(\d+)\s*(완료|끝|done)', text)
        if match:
            return int(match.group(1))

        return -1

    def _matches_any(self, text: str, patterns: List[Pattern]) -> bool:
        """하나 이상의 패턴과 매칭되는지 확인"""
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False
