#!/usr/bin/env python3
"""
웹 대시보드 기능 CLI 데모
(원격 서버용 - 웹 브라우저 없이 확인)
"""
import pandas as pd
from datetime import datetime, timedelta
from core.database import Database
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent


def print_header(title):
    """헤더 출력"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def demo_sidebar():
    """사이드바 - 진행도 표시"""
    print_header("📊 사이드바 (진행도)")

    db = Database()
    db.connect()
    gamification = GamificationAgent(db.conn)

    progress = gamification.get_progress_summary()

    print(f"\n🤖 LifeBot")
    print("-" * 60)
    print(f"레벨: Level {progress['level']}")
    print(f"경험치: {progress['current_exp']}/{progress['next_level_exp']} XP")

    # 프로그레스 바
    percent = progress['progress_percent']
    bar_length = 40
    filled = int(percent / 100 * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"진행도: [{bar}] {percent:.1f}%")

    print(f"업적: {progress['achievements']}")

    db.close()


def demo_chat():
    """채팅 탭"""
    print_header("💬 채팅 탭")

    print("\n자연어로 입력 가능:")
    print("  • 어제 7시간 잤어")
    print("  • 30분 운동했어")
    print("  • 카드비 계산해야 해")
    print("  • 할일 1 완료")
    print("  • 오늘 요약")

    print("\n빠른 입력 버튼:")
    print("  [💤 수면 기록] [💪 운동 기록] [📝 할일 추가] [📊 오늘 요약]")

    print("\n💬 대화 히스토리 예시:")
    print("-" * 60)
    print("👤 사용자: 어제 7시간 잤어")
    print("🤖 봇: ✓ 수면 기록 완료: 7.0시간")
    print("     ✓ 목표 달성! 좋은 수면이었습니다.")
    print("       +15 XP")
    print()
    print("👤 사용자: 30분 운동했어")
    print("🤖 봇: ✓ 운동 기록 완료: 30분")
    print("     ✓ 목표 달성! 30분 운동 훌륭합니다!")
    print("       +10 XP")


def demo_dashboard():
    """대시보드 탭"""
    print_header("📊 대시보드 탭")

    db = Database()
    db.connect()
    data_manager = DataManagerAgent(db.conn)

    # 오늘 요약
    today = datetime.now().strftime("%Y-%m-%d")
    summary = data_manager.get_summary(today)

    print("\n📌 오늘의 메트릭 카드:")
    print("-" * 60)

    # 메트릭 4개
    sleep = summary['health'].get('sleep_h')
    workout = summary['health'].get('workout_min')
    protein = summary['health'].get('protein_g')
    tasks = summary['tasks']

    print(f"💤 수면:    {sleep}시간" if sleep else "💤 수면:    기록 없음", end="")
    if sleep:
        diff = sleep - 7
        print(f"  (목표 대비 {diff:+.1f}h)")
    else:
        print()

    print(f"💪 운동:    {workout}분" if workout else "💪 운동:    기록 없음", end="")
    if workout:
        diff = workout - 30
        print(f"     (목표 대비 {diff:+}분)")
    else:
        print()

    print(f"🍗 단백질:  {protein}g" if protein else "🍗 단백질:  기록 없음", end="")
    if protein:
        diff = protein - 100
        print(f"      (목표 대비 {diff:+.0f}g)")
    else:
        print()

    print(f"📝 할일:    {tasks['done']}/{tasks['total']}         ({tasks['done']}개 완료)")

    # 주간 트렌드
    print("\n📈 주간 트렌드 차트:")
    print("-" * 60)

    cursor = db.conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT date, sleep_h, workout_min
        FROM daily_health
        WHERE date >= ?
        ORDER BY date
    """, (week_ago,))

    rows = cursor.fetchall()

    if rows:
        print("\n수면 시간 (시간):")
        print("  날짜        수면   목표(7h)")
        for row in rows:
            date = row['date']
            sleep = row['sleep_h'] or 0
            bar = "█" * int(sleep * 2)
            status = "✓" if sleep >= 7 else "⚠"
            print(f"  {date}  {sleep:4.1f}h  {bar} {status}")

        print("\n운동 시간 (분):")
        print("  날짜        운동   목표(30분)")
        for row in rows:
            date = row['date']
            workout = row['workout_min'] or 0
            bar = "█" * int(workout / 10)
            status = "✓" if workout >= 30 else "⚠"
            print(f"  {date}  {workout:3}분  {bar} {status}")

    # 할일 목록
    print("\n📝 할일 목록:")
    print("-" * 60)

    tasks_list = data_manager.get_pending_tasks()

    if tasks_list:
        for task in tasks_list:
            priority_emoji = {
                "urgent": "🔴",
                "high": "🟠",
                "normal": "🟢",
                "low": "🔵"
            }.get(task['priority'], "⚪")

            due_str = f" (마감: {task['due']})" if task['due'] else ""
            print(f"  {priority_emoji} [{task['id']}] {task['title']}{due_str}")
    else:
        print("  할일이 없습니다!")

    db.close()


def demo_analytics():
    """분석 탭"""
    print_header("📈 분석 탭")

    db = Database()
    db.connect()
    data_manager = DataManagerAgent(db.conn)

    # 주간 통계
    stats = data_manager.get_weekly_stats()

    print("\n📊 주간 통계:")
    print("-" * 60)
    print(f"평균 수면:     {stats['avg_sleep']}시간")
    print(f"총 운동 시간:  {stats['total_workout']}분")
    print(f"완료한 할일:   {stats['completed_tasks']}개")

    # 경험치 로그
    print("\n💎 경험치 획득 내역 (최근 10개):")
    print("-" * 60)

    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT date, action_type, exp_gained, description
        FROM exp_logs
        ORDER BY created_at DESC
        LIMIT 10
    """)

    exp_logs = cursor.fetchall()

    if exp_logs:
        print(f"{'날짜':<12} {'행동':<20} {'XP':>5}  설명")
        print("-" * 60)
        for row in exp_logs:
            print(f"{row['date']:<12} {row['action_type']:<20} {row['exp_gained']:>5}  {row['description']}")

        # 타입별 합계
        print("\n💡 경험치 획득 비율:")
        cursor.execute("""
            SELECT action_type, SUM(exp_gained) as total
            FROM exp_logs
            GROUP BY action_type
            ORDER BY total DESC
        """)

        type_stats = cursor.fetchall()
        total_exp = sum(row['total'] for row in type_stats)

        for row in type_stats:
            action = row['action_type']
            exp = row['total']
            percent = (exp / total_exp * 100) if total_exp > 0 else 0
            bar = "█" * int(percent / 5)
            print(f"  {action:<20} {exp:>5} XP  {bar} {percent:.1f}%")

    db.close()


def demo_achievements():
    """업적 탭"""
    print_header("🏆 업적 갤러리")

    db = Database()
    db.connect()

    # 모든 업적
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM achievements")
    achievements = cursor.fetchall()

    # 달성한 업적
    cursor.execute("""
        SELECT achievement_id, achieved_at
        FROM achievement_logs
    """)
    achieved = {row['achievement_id']: row['achieved_at'] for row in cursor.fetchall()}

    # 진행도
    achieved_count = len(achieved)
    total_count = len(achievements)
    percent = (achieved_count / total_count * 100) if total_count > 0 else 0

    bar_length = 40
    filled = int(percent / 100 * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)

    print(f"\n진행도: [{bar}] {achieved_count}/{total_count} ({percent:.0f}%)")

    print("\n📜 업적 목록:")
    print("-" * 60)

    for achievement in achievements:
        is_achieved = achievement['id'] in achieved

        if is_achieved:
            print(f"\n✅ {achievement['icon']} {achievement['name']}")
            print(f"   {achievement['description']}")
            print(f"   달성: {achieved[achievement['id']]}")
            print(f"   보상: +{achievement['exp_reward']} XP")
        else:
            print(f"\n🔒 {achievement['icon']} {achievement['name']}")
            print(f"   {achievement['description']}")
            print(f"   보상: +{achievement['exp_reward']} XP (미달성)")

    db.close()


def main():
    """메인 데모"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🤖 LifeBot 웹 대시보드 데모 (CLI 버전)" + " " * 9 + "║")
    print("╚" + "═" * 58 + "╝")

    # 사이드바
    demo_sidebar()

    input("\n계속하려면 Enter를 누르세요...")

    # 채팅
    demo_chat()

    input("\n계속하려면 Enter를 누르세요...")

    # 대시보드
    demo_dashboard()

    input("\n계속하려면 Enter를 누르세요...")

    # 분석
    demo_analytics()

    input("\n계속하려면 Enter를 누르세요...")

    # 업적
    demo_achievements()

    print("\n" + "=" * 60)
    print("✨ 데모 완료!")
    print("=" * 60)
    print("\n실제 웹 UI는 더 예쁘고 인터랙티브합니다! 🌐")
    print("로컬에서 'streamlit run app.py'로 실행해보세요.")


if __name__ == "__main__":
    main()
