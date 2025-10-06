"""
데이터베이스 스키마 정의 및 초기화
9개 테이블: daily_health, custom_metrics, habits, habit_logs, tasks,
            user_progress, exp_logs, achievements, achievement_logs
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class Database:
    """SQLite 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "lifebot.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """데이터베이스 연결"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_schema(self):
        """모든 테이블 생성"""
        if not self.conn:
            raise RuntimeError("데이터베이스가 연결되지 않았습니다. connect()를 먼저 호출하세요.")

        cursor = self.conn.cursor()

        # 1. 일일 건강 메트릭 (핵심 지표)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                sleep_h REAL,
                workout_min INTEGER,
                protein_g REAL,
                weight_kg REAL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. 커스텀 메트릭 (BMI, 혈압 등)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                category TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. 습관 정의
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                goal_type TEXT,
                target_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. 습관 추적 로그
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT CHECK(status IN ('success', 'fail', 'skip')),
                streak_count INTEGER DEFAULT 0,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE(habit_id, date)
            )
        """)

        # 5. 할일
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due DATE,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'done')),
                priority TEXT DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high', 'urgent')),
                category TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # 6. 사용자 진행도 (레벨/경험치)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level INTEGER DEFAULT 1,
                current_exp INTEGER DEFAULT 0,
                total_exp INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. 경험치 획득 로그
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                action_type TEXT NOT NULL,
                exp_gained INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 8. 업적 정의
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                condition_type TEXT,
                condition_value TEXT,
                exp_reward INTEGER DEFAULT 0,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 9. 업적 달성 기록
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievement_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_id INTEGER NOT NULL,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
            )
        """)

        # 인덱스 생성
        self._create_indexes(cursor)

        self.conn.commit()
        print("✓ 데이터베이스 스키마 초기화 완료 (9개 테이블)")

    def _create_indexes(self, cursor):
        """성능 최적화를 위한 인덱스 생성"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_daily_health_date ON daily_health(date)",
            "CREATE INDEX IF NOT EXISTS idx_custom_metrics_date ON custom_metrics(date)",
            "CREATE INDEX IF NOT EXISTS idx_custom_metrics_name ON custom_metrics(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(date)",
            "CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_id ON habit_logs(habit_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)",
            "CREATE INDEX IF NOT EXISTS idx_exp_logs_date ON exp_logs(date)",
            "CREATE INDEX IF NOT EXISTS idx_exp_logs_action_type ON exp_logs(action_type)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

    def seed_initial_data(self):
        """초기 데이터 삽입 (기본 업적, 사용자 진행도)"""
        if not self.conn:
            raise RuntimeError("데이터베이스가 연결되지 않았습니다.")

        cursor = self.conn.cursor()

        # 사용자 진행도 초기화 (한 번만 실행)
        cursor.execute("SELECT COUNT(*) FROM user_progress")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO user_progress (level, current_exp, total_exp)
                VALUES (1, 0, 0)
            """)
            print("✓ 사용자 진행도 초기화 (Level 1, 0 XP)")

        # 기본 업적 정의 (Phase 3: 6개 → 20개 확장)
        default_achievements = [
            # 기존 업적 (6개)
            {
                "name": "첫 걸음",
                "description": "첫 기록을 남기셨습니다!",
                "condition_type": "any_record",
                "condition_value": json.dumps({"count": 1}),
                "exp_reward": 10,
                "icon": "🎯"
            },
            {
                "name": "아침형 인간",
                "description": "7일 연속 7시간 이상 수면",
                "condition_type": "sleep_streak",
                "condition_value": json.dumps({"days": 7, "min_hours": 7}),
                "exp_reward": 100,
                "icon": "🌅"
            },
            {
                "name": "운동 마스터",
                "description": "30일 연속 운동 기록",
                "condition_type": "workout_streak",
                "condition_value": json.dumps({"days": 30}),
                "exp_reward": 200,
                "icon": "💪"
            },
            {
                "name": "철인",
                "description": "할일 100개 완료",
                "condition_type": "task_complete",
                "condition_value": json.dumps({"count": 100}),
                "exp_reward": 150,
                "icon": "🏆"
            },
            {
                "name": "완벽주의자",
                "description": "모든 목표 달성 7일 연속",
                "condition_type": "perfect_week",
                "condition_value": json.dumps({"days": 7}),
                "exp_reward": 300,
                "icon": "⭐"
            },
            {
                "name": "끈기의 힘",
                "description": "습관 30일 연속 유지",
                "condition_type": "habit_streak",
                "condition_value": json.dumps({"days": 30}),
                "exp_reward": 250,
                "icon": "🔥"
            },

            # 수면 관련 신규 업적 (2개)
            {
                "name": "수면 챔피언",
                "description": "30일 연속 7시간 이상 수면",
                "condition_type": "sleep_streak",
                "condition_value": json.dumps({"days": 30, "min_hours": 7}),
                "exp_reward": 200,
                "icon": "🛌"
            },
            {
                "name": "회복의 달인",
                "description": "7일 연속 5시간 미만 수면 없이",
                "condition_type": "sleep_no_bad_days",
                "condition_value": json.dumps({"days": 7, "min_hours": 5}),
                "exp_reward": 80,
                "icon": "😴"
            },

            # 운동 관련 신규 업적 (4개)
            {
                "name": "운동 스트릭",
                "description": "60일 연속 운동 기록",
                "condition_type": "workout_streak",
                "condition_value": json.dumps({"days": 60}),
                "exp_reward": 300,
                "icon": "🔥"
            },
            {
                "name": "100분 클럽",
                "description": "하루 100분 이상 운동",
                "condition_type": "workout_single_day",
                "condition_value": json.dumps({"minutes": 100}),
                "exp_reward": 50,
                "icon": "💯"
            },
            {
                "name": "월간 1000분",
                "description": "한 달 총 1000분 이상 운동",
                "condition_type": "workout_monthly_total",
                "condition_value": json.dumps({"minutes": 1000}),
                "exp_reward": 150,
                "icon": "📅"
            },
            {
                "name": "주말 워리어",
                "description": "4주 연속 주말마다 운동",
                "condition_type": "workout_weekend_streak",
                "condition_value": json.dumps({"weeks": 4}),
                "exp_reward": 120,
                "icon": "🏃"
            },

            # 영양 관련 신규 업적 (1개)
            {
                "name": "단백질 마스터",
                "description": "30일 연속 단백질 목표 달성",
                "condition_type": "protein_streak",
                "condition_value": json.dumps({"days": 30, "min_grams": 100}),
                "exp_reward": 150,
                "icon": "🥩"
            },

            # 할일 관련 신규 업적 (3개)
            {
                "name": "생산성 킹",
                "description": "하루 10개 할일 완료",
                "condition_type": "task_single_day",
                "condition_value": json.dumps({"count": 10}),
                "exp_reward": 80,
                "icon": "⚡"
            },
            {
                "name": "마감 지킴이",
                "description": "마감 전 할일 30개 완료",
                "condition_type": "task_before_due",
                "condition_value": json.dumps({"count": 30}),
                "exp_reward": 100,
                "icon": "⏰"
            },
            {
                "name": "우선순위 마스터",
                "description": "긴급 할일 10개 완료",
                "condition_type": "task_priority",
                "condition_value": json.dumps({"priority": "urgent", "count": 10}),
                "exp_reward": 120,
                "icon": "🎯"
            },

            # 습관 관련 신규 업적 (2개)
            {
                "name": "습관의 시작",
                "description": "7일 연속 습관 유지",
                "condition_type": "habit_streak",
                "condition_value": json.dumps({"days": 7}),
                "exp_reward": 50,
                "icon": "🌱"
            },
            {
                "name": "습관 마스터",
                "description": "60일 연속 습관 유지",
                "condition_type": "habit_streak",
                "condition_value": json.dumps({"days": 60}),
                "exp_reward": 400,
                "icon": "🔱"
            },

            # 종합 업적 (2개)
            {
                "name": "레벨 5 달성",
                "description": "레벨 5에 도달하셨습니다",
                "condition_type": "level_reached",
                "condition_value": json.dumps({"level": 5}),
                "exp_reward": 100,
                "icon": "🎖️"
            },
            {
                "name": "레벨 10 달성",
                "description": "레벨 10에 도달하셨습니다",
                "condition_type": "level_reached",
                "condition_value": json.dumps({"level": 10}),
                "exp_reward": 250,
                "icon": "🏅"
            },
        ]

        for achievement in default_achievements:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements
                    (name, description, condition_type, condition_value, exp_reward, icon)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    achievement["name"],
                    achievement["description"],
                    achievement["condition_type"],
                    achievement["condition_value"],
                    achievement["exp_reward"],
                    achievement["icon"]
                ))
            except sqlite3.IntegrityError:
                pass  # 이미 존재하는 업적은 무시

        self.conn.commit()
        cursor.execute("SELECT COUNT(*) FROM achievements")
        count = cursor.fetchone()[0]
        print(f"✓ 기본 업적 {count}개 로드 완료")

    def reset_database(self):
        """데이터베이스 초기화 (개발용)"""
        if not self.conn:
            raise RuntimeError("데이터베이스가 연결되지 않았습니다.")

        cursor = self.conn.cursor()

        # 모든 테이블 삭제
        tables = [
            "achievement_logs", "achievements", "exp_logs", "user_progress",
            "tasks", "habit_logs", "habits", "custom_metrics", "daily_health"
        ]

        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

        self.conn.commit()
        print("✓ 데이터베이스 초기화 완료")


def main():
    """데이터베이스 초기화 실행"""
    db = Database()
    db.connect()

    print("=== LifeBot 데이터베이스 초기화 ===\n")

    # 스키마 생성
    db.init_schema()

    # 초기 데이터 삽입
    db.seed_initial_data()

    print("\n=== 초기화 완료 ===")

    db.close()


if __name__ == "__main__":
    main()
