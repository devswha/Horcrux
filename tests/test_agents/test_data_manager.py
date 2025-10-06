"""
DataManagerAgent 테스트
"""
import sqlite3
import pytest
from datetime import datetime
from core.database import Database
from agents.data_manager import DataManagerAgent


@pytest.fixture
def db():
    """테스트용 DB"""
    database = Database(":memory:")
    database.connect()
    database.init_schema()
    yield database
    database.close()


@pytest.fixture
def agent(db):
    """테스트용 DataManagerAgent"""
    return DataManagerAgent(db.conn)


def test_store_health_metric(agent):
    """건강 지표 저장 테스트"""
    today = datetime.now().strftime("%Y-%m-%d")
    result = agent.store_health_metric(today, sleep_h=7.0, workout_min=30)

    assert result["success"] is True
    assert result["action"] in ["inserted", "updated"]


def test_store_task(agent):
    """할일 추가 테스트"""
    result = agent.store_task("테스트 할일", priority="high")

    assert result["success"] is True
    assert "task_id" in result
    assert result["title"] == "테스트 할일"


def test_complete_task(agent):
    """할일 완료 테스트"""
    # 먼저 할일 추가
    add_result = agent.store_task("완료할 할일")
    task_id = add_result["task_id"]

    # 완료 처리
    complete_result = agent.complete_task(task_id)

    assert complete_result["success"] is True
    assert complete_result["task_id"] == task_id


def test_create_habit(agent):
    """습관 생성 테스트"""
    result = agent.create_habit("금연", goal_type="daily")

    assert result["success"] is True
    assert "habit_id" in result


def test_log_habit_with_streak(agent):
    """습관 기록 및 streak 테스트"""
    # 습관 생성
    agent.create_habit("운동")

    # 첫날 기록
    result1 = agent.log_habit("운동", "2025-10-01", "success")
    assert result1["streak"] == 1

    # 둘째날 기록 (연속)
    result2 = agent.log_habit("운동", "2025-10-02", "success")
    assert result2["streak"] == 2


def test_get_summary(agent):
    """요약 조회 테스트"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 데이터 입력
    agent.store_health_metric(today, sleep_h=7.0, workout_min=30)
    agent.store_task("테스트 할일")

    # 요약 조회
    summary = agent.get_summary(today)

    assert summary["date"] == today
    assert summary["health"]["sleep_h"] == 7.0
    assert summary["health"]["workout_min"] == 30
    assert summary["tasks"]["total"] >= 1
