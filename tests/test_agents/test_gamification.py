"""
GamificationAgent 테스트
"""
import sqlite3
import pytest
from core.database import Database
from agents.gamification import GamificationAgent


@pytest.fixture
def db():
    """테스트용 DB"""
    database = Database(":memory:")
    database.connect()
    database.init_schema()
    database.seed_initial_data()
    yield database
    database.close()


@pytest.fixture
def agent(db):
    """테스트용 GamificationAgent"""
    return GamificationAgent(db.conn)


def test_award_exp_task_complete(agent):
    """할일 완료 경험치 부여 테스트"""
    result = agent.award_exp("task_complete", "normal", "테스트 할일 완료")

    assert result["success"] is True
    assert result["exp_gained"] == 20  # normal task


def test_award_exp_sleep_goal(agent):
    """수면 목표 달성 경험치 테스트"""
    result = agent.award_exp("sleep_goal", 7, "7시간 수면")

    assert result["success"] is True
    assert result["exp_gained"] == 15


def test_level_up(agent):
    """레벨업 테스트"""
    # 100 XP 획득 (Level 1 → 2)
    last_result = None
    for _ in range(5):
        last_result = agent.award_exp("task_complete", "normal", "할일 완료")

    # award_exp 내부에서 이미 레벨업 체크를 하므로
    # 마지막 award_exp 결과를 확인
    assert last_result["level_up"] is True
    assert last_result["new_level"] == 2


def test_get_progress_summary(agent):
    """진행도 요약 테스트"""
    # 경험치 획득
    agent.award_exp("task_complete", "normal", "할일 완료")

    # 진행도 조회
    progress = agent.get_progress_summary()

    assert progress["level"] >= 1
    assert progress["current_exp"] >= 20
    assert "achievements" in progress


def test_exp_calculation_priority(agent):
    """우선순위에 따른 경험치 계산 테스트"""
    # Low priority: 20 * 0.5 = 10
    exp_low = agent._calculate_exp("task_complete", "low")
    assert exp_low == 10

    # High priority: 20 * 1.5 = 30
    exp_high = agent._calculate_exp("task_complete", "high")
    assert exp_high == 30

    # Urgent priority: 20 * 2.5 = 50
    exp_urgent = agent._calculate_exp("task_complete", "urgent")
    assert exp_urgent == 50
