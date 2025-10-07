#!/usr/bin/env python3
"""
LifeBot - 건강/할일 관리 에이전트 시스템 (MVP)
"""
import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가 (import 경로 해결)
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from core.database import Database
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent


class LifeBotCLI:
    """간단한 CLI 인터페이스 (Phase 1 MVP)"""

    def __init__(self):
        self.db = Database()
        self.db.connect()

        self.data_manager = DataManagerAgent(self.db.conn)
        self.gamification = GamificationAgent(self.db.conn)

    def run(self):
        """CLI 메인 루프"""
        print("=" * 50)
        print("🤖 LifeBot - 건강/할일 관리 시스템 (MVP)")
        print("=" * 50)
        print()

        # 현재 진행도 표시
        self.show_progress()

        print("\n명령어:")
        print("  1. add_sleep <시간>        - 수면 기록")
        print("  2. add_workout <분>        - 운동 기록")
        print("  3. add_task <제목>         - 할일 추가")
        print("  4. complete_task <ID>      - 할일 완료")
        print("  5. list_tasks              - 할일 목록")
        print("  6. summary                 - 오늘 요약")
        print("  7. progress                - 진행도")
        print("  8. quit                    - 종료")
        print()

        while True:
            try:
                command = input("\n명령> ").strip()

                if not command:
                    continue

                if command == "quit":
                    print("👋 종료합니다")
                    break

                self.handle_command(command)

            except KeyboardInterrupt:
                print("\n\n👋 종료합니다")
                break
            except Exception as e:
                print(f"❌ 에러: {e}")

    def handle_command(self, command: str):
        """명령어 처리"""
        parts = command.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "add_sleep" and arg:
            self.add_sleep(float(arg))

        elif cmd == "add_workout" and arg:
            self.add_workout(int(arg))

        elif cmd == "add_task" and arg:
            self.add_task(arg)

        elif cmd == "complete_task" and arg:
            self.complete_task(int(arg))

        elif cmd == "list_tasks":
            self.list_tasks()

        elif cmd == "summary":
            self.show_summary()

        elif cmd == "progress":
            self.show_progress()

        else:
            print("❌ 알 수 없는 명령어입니다")

    def add_sleep(self, hours: float):
        """수면 기록"""
        today = datetime.now().strftime("%Y-%m-%d")
        result = self.data_manager.store_health_metric(today, sleep_h=hours)

        if result["success"]:
            print(f"✓ 수면 기록 완료: {hours}시간")

            # 목표 달성 시 경험치
            if hours >= 7:
                exp_result = self.gamification.award_exp("sleep_goal", hours, f"수면 {hours}시간")
                self._show_exp_gain(exp_result)
            else:
                print(f"⚠️ 목표(7시간)보다 {7 - hours:.1f}시간 부족합니다")
        else:
            print(f"❌ 저장 실패: {result.get('error')}")

    def add_workout(self, minutes: int):
        """운동 기록"""
        today = datetime.now().strftime("%Y-%m-%d")
        result = self.data_manager.store_health_metric(today, workout_min=minutes)

        if result["success"]:
            print(f"✓ 운동 기록 완료: {minutes}분")

            # 경험치 부여
            exp_result = self.gamification.award_exp("workout", minutes, f"운동 {minutes}분")
            self._show_exp_gain(exp_result)
        else:
            print(f"❌ 저장 실패: {result.get('error')}")

    def add_task(self, title: str):
        """할일 추가"""
        result = self.data_manager.store_task(title)

        if result["success"]:
            print(f"✓ 할일 추가: [{result['task_id']}] {title}")
        else:
            print(f"❌ 추가 실패: {result.get('error')}")

    def complete_task(self, task_id: int):
        """할일 완료"""
        result = self.data_manager.complete_task(task_id)

        if result["success"]:
            priority = result.get("priority", "normal")
            print(f"✓ 할일 완료: {result.get('title')}")

            # 경험치 부여
            exp_result = self.gamification.award_exp("task_complete", priority, f"할일 완료: {result.get('title')}")
            self._show_exp_gain(exp_result)
        else:
            print(f"❌ 완료 실패: {result.get('error')}")

    def list_tasks(self):
        """할일 목록"""
        tasks = self.data_manager.get_pending_tasks()

        if not tasks:
            print("📝 할일이 없습니다")
            return

        print("\n📝 할일 목록:")
        for task in tasks:
            priority_emoji = {
                "urgent": "🔴",
                "high": "🟠",
                "normal": "🟢",
                "low": "🔵"
            }.get(task["priority"], "⚪")

            due_str = f" (마감: {task['due']})" if task['due'] else ""
            print(f"  {priority_emoji} [{task['id']}] {task['title']}{due_str}")

    def show_summary(self):
        """오늘 요약"""
        summary = self.data_manager.get_summary()

        print(f"\n📊 {summary['date']} 요약")
        print()

        # 건강 지표
        health = summary["health"]
        sleep = health.get("sleep_h")
        workout = health.get("workout_min")
        protein = health.get("protein_g")

        print(f"💤 수면: {sleep}시간" if sleep else "💤 수면: 기록 없음")
        print(f"💪 운동: {workout}분" if workout else "💪 운동: 기록 없음")
        print(f"🍗 단백질: {protein}g" if protein else "🍗 단백질: 기록 없음")

        # 할일
        tasks = summary["tasks"]
        print(f"📝 할일: 완료 {tasks['done']}/{tasks['total']}")

        # 습관
        if summary["habits"]:
            print("\n🔥 습관:")
            for habit in summary["habits"]:
                status_emoji = "✓" if habit["status"] == "success" else "✗"
                print(f"  {status_emoji} {habit['name']} (streak: {habit['streak']}일)")

    def show_progress(self):
        """진행도 표시"""
        progress = self.gamification.get_progress_summary()

        print(f"\n📊 Level {progress['level']} ({progress['current_exp']}/{progress['next_level_exp']} XP) | 🏆 업적 {progress['achievements']}")
        print(f"진행도: [{'=' * int(progress['progress_percent'] // 5)}{' ' * (20 - int(progress['progress_percent'] // 5))}] {progress['progress_percent']}%")

    def _show_exp_gain(self, exp_result: dict):
        """경험치 획득 표시"""
        if exp_result.get("success"):
            exp_gained = exp_result.get("exp_gained", 0)
            print(f"  +{exp_gained} XP")

            if exp_result.get("level_up"):
                old_level = exp_result.get("new_level", 1) - 1
                new_level = exp_result.get("new_level", 1)
                print(f"\n🎉 레벨업! {old_level} → {new_level}")

    def close(self):
        """종료"""
        self.db.close()


def main():
    """메인 함수"""
    cli = LifeBotCLI()

    try:
        cli.run()
    finally:
        cli.close()


if __name__ == "__main__":
    main()
