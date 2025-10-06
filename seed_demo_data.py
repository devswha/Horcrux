#!/usr/bin/env python3
"""
데모 데이터 생성 스크립트
웹 UI 테스트를 위한 샘플 데이터
"""
from datetime import datetime, timedelta
from core.database import Database
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent


def seed_demo_data():
    """데모 데이터 생성"""
    print("🌱 데모 데이터 생성 중...")

    db = Database()
    db.connect()

    data_manager = DataManagerAgent(db.conn)
    gamification = GamificationAgent(db.conn)

    # 지난 7일간 데이터 생성
    today = datetime.now().date()

    for i in range(7, 0, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")

        # 수면 (5-8시간 랜덤)
        import random
        sleep_h = random.uniform(5.5, 8.0)
        workout_min = random.randint(0, 60)
        protein_g = random.uniform(80, 120)

        data_manager.store_health_metric(
            date,
            sleep_h=round(sleep_h, 1),
            workout_min=workout_min,
            protein_g=round(protein_g, 1)
        )

        print(f"  ✓ {date}: 수면 {sleep_h:.1f}h, 운동 {workout_min}분, 단백질 {protein_g:.0f}g")

        # 경험치 부여
        if sleep_h >= 7:
            gamification.award_exp("sleep_goal", sleep_h, f"{date} 수면")
        if workout_min >= 30:
            gamification.award_exp("workout", workout_min, f"{date} 운동")
        if protein_g >= 100:
            gamification.award_exp("protein_goal", protein_g, f"{date} 단백질")

    # 할일 추가
    tasks = [
        ("주간 보고서 작성", "high", "career"),
        ("운동 30분", "normal", "health"),
        ("책 읽기", "low", "personal"),
        ("이메일 답장", "urgent", "work"),
        ("장보기", "normal", "personal"),
    ]

    for i, (title, priority, category) in enumerate(tasks):
        result = data_manager.store_task(
            title,
            priority=priority,
            category=category
        )
        print(f"  ✓ 할일 추가: {title}")

        # 일부 완료
        if i < 2:
            data_manager.complete_task(result['task_id'])
            gamification.award_exp("task_complete", priority, f"{title} 완료")
            print(f"    → 완료 처리")

    # 습관 추가
    habits = ["운동", "독서", "물 2L 마시기"]
    for habit in habits:
        data_manager.create_habit(habit)
        print(f"  ✓ 습관 추가: {habit}")

        # 최근 3일 기록
        for i in range(3):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            status = "success" if random.random() > 0.3 else "fail"
            data_manager.log_habit(habit, date, status)

    # 진행도 확인
    progress = gamification.get_progress_summary()

    print("\n" + "=" * 50)
    print(f"✓ 데모 데이터 생성 완료!")
    print(f"📊 Level {progress['level']} ({progress['current_exp']}/{progress['next_level_exp']} XP)")
    print(f"🏆 업적 {progress['achievements']}")
    print("=" * 50)

    db.close()


if __name__ == "__main__":
    seed_demo_data()
