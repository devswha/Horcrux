#!/usr/bin/env python3
"""
LifeBot - 건강/할일 관리 에이전트 시스템 (자연어 버전)
Phase 2: 한국어 자연어 처리 지원
"""
import sys
from core.database import Database
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent


class LifeBotNaturalCLI:
    """자연어 입력 지원 CLI"""

    def __init__(self):
        # DB 초기화
        self.db = Database()
        self.db.connect()

        # 에이전트 초기화
        self.conversation = ConversationAgent()
        self.data_manager = DataManagerAgent(self.db.conn)
        self.gamification = GamificationAgent(self.db.conn)
        self.coaching = CoachingAgent(self.db.conn)
        self.orchestrator = OrchestratorAgent(
            self.conversation,
            self.data_manager,
            self.gamification,
            self.coaching
        )

    def run(self):
        """CLI 메인 루프"""
        print("=" * 60)
        print("🤖 LifeBot - 건강/할일 관리 시스템 (자연어 버전)")
        print("=" * 60)
        print()

        # 현재 진행도 표시
        self.show_progress()

        print("\n💬 자연어로 입력하세요:")
        print('  예시: "어제 5시간 잤어"')
        print('        "30분 운동했어"')
        print('        "카드비 계산해야 해"')
        print('        "할일 1 완료"')
        print('        "오늘 요약"')
        print('        "진행도"')
        print()
        print("  명령어: help, quit")
        print()

        while True:
            try:
                user_input = input("💬 > ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "quit" or user_input == "종료":
                    print("👋 종료합니다")
                    break

                if user_input.lower() == "help" or user_input == "도움말":
                    self.show_help()
                    continue

                # 자연어 처리
                result = self.orchestrator.handle_user_input(user_input)

                # 결과 출력
                if result.get("success"):
                    print(result.get("message", ""))
                else:
                    print(f"❌ {result.get('message', '처리 실패')}")

                print()

            except KeyboardInterrupt:
                print("\n\n👋 종료합니다")
                break
            except Exception as e:
                print(f"❌ 에러: {e}")
                import traceback
                traceback.print_exc()

    def show_progress(self):
        """진행도 표시"""
        progress = self.gamification.get_progress_summary()

        level = progress["level"]
        current_exp = progress["current_exp"]
        next_exp = progress["next_level_exp"]
        percent = progress["progress_percent"]
        achievements = progress["achievements"]

        bar_length = 20
        filled = int(percent // 5)
        bar = "=" * filled + " " * (bar_length - filled)

        print(f"📊 Level {level} ({current_exp}/{next_exp} XP) | 🏆 업적 {achievements}")
        print(f"진행도: [{bar}] {percent}%")

    def show_help(self):
        """도움말 표시"""
        print("""
💬 자연어 입력 예시:

【건강 기록】
  "어제 5시간 잤어"
  "오늘 7시간 수면"
  "30분 운동했어"
  "헬스 1시간"
  "단백질 100g"
  "체중 70kg"

【할일 관리】
  "카드비 계산해야 해"
  "프로젝트 마무리 하기"
  "할일 1 완료"
  "할일 2 끝"

【조회】
  "오늘 요약"
  "어제 요약"
  "진행도"
  "레벨"

【명령어】
  help - 이 도움말
  quit - 종료
""")

    def close(self):
        """종료"""
        self.db.close()


def main():
    """메인 함수"""
    cli = LifeBotNaturalCLI()

    try:
        cli.run()
    finally:
        cli.close()


if __name__ == "__main__":
    main()
