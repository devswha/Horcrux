#!/usr/bin/env python3
"""
웹 대시보드 기능 CLI 데모 (자동 실행)
"""
import time
from datetime import datetime, timedelta
from core.database import Database
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent


def print_header(title):
    """헤더 출력"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


print("\n")
print("╔" + "═" * 58 + "╗")
print("║" + " " * 10 + "🤖 LifeBot 웹 대시보드 데모 (CLI 버전)" + " " * 9 + "║")
print("╚" + "═" * 58 + "╝")

# DB 연결
db = Database()
db.connect()
data_manager = DataManagerAgent(db.conn)
gamification = GamificationAgent(db.conn)

# ============================================================
# 사이드바 - 진행도
# ============================================================
print_header("📊 사이드바 (진행도)")

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

# ============================================================
# 대시보드 - 오늘 요약
# ============================================================
print_header("📊 대시보드 - 오늘 요약")

today = datetime.now().strftime("%Y-%m-%d")
summary = data_manager.get_summary(today)

print("\n📌 메트릭 카드:")
print("-" * 60)

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

# ============================================================
# 주간 트렌드 차트
# ============================================================
print("\n📈 주간 트렌드:")
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
    print("\n수면 시간 추이 (목표: 7시간)")
    print("  날짜        수면")
    for row in rows:
        date = row['date']
        sleep = row['sleep_h'] or 0
        bar_len = int(sleep * 5)  # 1시간 = 5칸
        bar = "█" * bar_len
        status = "✓" if sleep >= 7 else "⚠"
        print(f"  {date}  {sleep:4.1f}h  {bar} {status}")

    print("\n운동 시간 추이 (목표: 30분)")
    print("  날짜        운동")
    for row in rows:
        date = row['date']
        workout = row['workout_min'] or 0
        bar_len = int(workout / 3)  # 3분 = 1칸
        bar = "█" * bar_len
        status = "✓" if workout >= 30 else "⚠"
        print(f"  {date}  {workout:3}분  {bar} {status}")

# ============================================================
# 할일 목록
# ============================================================
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

# ============================================================
# 분석 - 주간 통계
# ============================================================
print_header("📈 분석 - 주간 통계")

stats = data_manager.get_weekly_stats()

print(f"\n평균 수면:     {stats['avg_sleep']}시간")
print(f"총 운동 시간:  {stats['total_workout']}분")
print(f"완료한 할일:   {stats['completed_tasks']}개")

# 경험치 로그
print("\n💎 경험치 획득 내역 (최근 10개):")
print("-" * 60)

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
        desc = row['description'][:30] if row['description'] else ""
        print(f"{row['date']:<12} {row['action_type']:<20} {row['exp_gained']:>5}  {desc}")

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
        bar_len = int(percent / 5)
        bar = "█" * bar_len
        print(f"  {action:<20} {exp:>5} XP  {bar} {percent:.1f}%")

# ============================================================
# 업적 갤러리
# ============================================================
print_header("🏆 업적 갤러리")

# 모든 업적
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

# 완료
db.close()

print("\n" + "=" * 60)
print("✨ 웹 대시보드 기능 미리보기 완료!")
print("=" * 60)
print("\n실제 웹 UI는:")
print("  • 인터랙티브 차트 (확대/축소/호버)")
print("  • 실시간 채팅 인터페이스")
print("  • 아름다운 시각화 (Plotly)")
print("  • 반응형 레이아웃")
print("\n로컬 환경에서 'streamlit run app.py'로 실행해보세요! 🌐")
