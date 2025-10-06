"""
KoreanPatterns 테스트
"""
import pytest
from parsers.korean_patterns import KoreanPatterns


@pytest.fixture
def patterns():
    return KoreanPatterns()


def test_match_sleep_intent(patterns):
    """수면 의도 파악"""
    assert patterns.match_intent("5시간 잤어") == "sleep"
    assert patterns.match_intent("어제 7시간 수면") == "sleep"


def test_match_workout_intent(patterns):
    """운동 의도 파악"""
    assert patterns.match_intent("30분 운동했어") == "workout"
    assert patterns.match_intent("헬스 1시간") == "workout"


def test_match_task_add_intent(patterns):
    """할일 추가 의도"""
    assert patterns.match_intent("카드비 계산해야 해") == "task_add"
    assert patterns.match_intent("프로젝트 마무리 하기") == "task_add"


def test_match_task_complete_intent(patterns):
    """할일 완료 의도"""
    assert patterns.match_intent("할일 1 완료") == "task_complete"
    assert patterns.match_intent("카드비 완료했어") == "task_complete"


def test_match_summary_intent(patterns):
    """요약 의도"""
    assert patterns.match_intent("오늘 요약") == "summary"
    assert patterns.match_intent("어제 정리") == "summary"


def test_match_progress_intent(patterns):
    """진행도 의도"""
    assert patterns.match_intent("레벨") == "progress"
    assert patterns.match_intent("진행도") == "progress"


def test_extract_task_title(patterns):
    """할일 제목 추출"""
    assert patterns.extract_task_title("카드비 계산해야 해") == "카드비 계산"
    assert patterns.extract_task_title("프로젝트 마무리 하기") == "프로젝트 마무리"


def test_extract_task_id(patterns):
    """할일 ID 추출"""
    assert patterns.extract_task_id("할일 1 완료") == 1
    assert patterns.extract_task_id("5 완료") == 5
