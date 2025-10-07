#!/usr/bin/env python3
"""
LifeBot 데모 스크립트
"""
from core.database import Database
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent


def demo():
    """자연어 입력 데모"""
    print("=" * 60)
    print("🤖 LifeBot 데모")
    print("=" * 60)
    print()

    # DB 초기화
    db = Database()
    db.connect()

    # 에이전트 초기화
    conversation = ConversationAgent()
    data_manager = DataManagerAgent(db.conn)
    gamification = GamificationAgent(db.conn)
    coaching = CoachingAgent(db.conn)
    orchestrator = OrchestratorAgent(
        conversation,
        data_manager,
        gamification,
        coaching
    )

    # 진행도 표시
    progress = gamification.get_progress_summary()
    print(f"📊 Level {progress['level']} ({progress['current_exp']}/{progress['next_level_exp']} XP) | 🏆 업적 {progress['achievements']}")
    print()

    # 테스트 입력들
    test_inputs = [
        "어제 5시간 잤어",
        "30분 운동했어",
        "단백질 100g",
        "카드비 계산해야 해",
        "프로젝트 마무리 하기",
        "할일 1 완료",
        "오늘 요약",
        "진행도",
    ]

    for user_input in test_inputs:
        print(f"💬 > {user_input}")

        result = orchestrator.handle_user_input(user_input)

        if result.get("success"):
            print(result.get("message", ""))
        else:
            print(f"❌ {result.get('message', '처리 실패')}")

        print()

    db.close()


if __name__ == "__main__":
    demo()
