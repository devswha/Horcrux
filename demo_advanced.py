#!/usr/bin/env python3
"""
LifeBot 고급 데모 - 다양한 입력 테스트
"""
from core.database import Database
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent


def demo():
    """다양한 자연어 입력 테스트"""
    print("=" * 60)
    print("🤖 LifeBot 고급 데모 - 다양한 입력 패턴 테스트")
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

    # 테스트 카테고리별 입력
    test_cases = [
        ("📅 날짜 표현 테스트", [
            "어제 7시간 잤어",
            "3일 전 6시간 수면",
            "오늘 1시간 운동했어",
        ]),

        ("⏱️ 시간 표현 테스트", [
            "헬스 1시간",  # 시간 → 분 변환
            "반시간 조깅",
            "45분 러닝했어",
        ]),

        ("📝 할일 다양한 표현", [
            "이메일 답장하기",
            "회의 자료 준비해야 해",
            "장보기 하자",
        ]),

        ("✅ 할일 완료", [
            "할일 3 완료",
            "할일 4 끝",
        ]),

        ("📊 조회", [
            "오늘 요약",
            "진행도",
            "레벨",
        ]),
    ]

    for category, inputs in test_cases:
        print(f"\n{'=' * 60}")
        print(category)
        print('=' * 60)
        print()

        for user_input in inputs:
            print(f"💬 > {user_input}")

            result = orchestrator.handle_user_input(user_input)

            if result.get("success"):
                print(result.get("message", ""))
            else:
                print(f"❌ {result.get('message', '처리 실패')}")

            print()

    # 최종 진행도
    print("=" * 60)
    print("🏆 최종 진행도")
    print("=" * 60)
    result = orchestrator.handle_user_input("진행도")
    print(result.get("message", ""))

    db.close()


if __name__ == "__main__":
    demo()
