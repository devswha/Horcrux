"""
데이터베이스 스키마 정의 및 초기화
7개 테이블: daily_health, custom_metrics, habits, habit_logs, tasks,
            user_progress, exp_logs
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class Database:
    """SQLite 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "horcrux.db"):
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

        # 8. 학습 기록 (Learning Logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                category TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 인덱스 생성
        self._create_indexes(cursor)

        self.conn.commit()
        print("✓ 데이터베이스 스키마 초기화 완료 (8개 테이블)")

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
            "CREATE INDEX IF NOT EXISTS idx_learning_logs_date ON learning_logs(date)",
            "CREATE INDEX IF NOT EXISTS idx_learning_logs_category ON learning_logs(category)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

    def seed_initial_data(self):
        """초기 데이터 삽입 (사용자 진행도)"""
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
    def reset_database(self):
        """데이터베이스 초기화 (개발용)"""
        if not self.conn:
            raise RuntimeError("데이터베이스가 연결되지 않았습니다.")

        cursor = self.conn.cursor()

        # 모든 테이블 삭제
        tables = [
            "learning_logs", "exp_logs", "user_progress",
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

    print("=== Horcrux 데이터베이스 초기화 ===\n")

    # 스키마 생성
    db.init_schema()

    # 초기 데이터 삽입
    db.seed_initial_data()

    print("\n=== 초기화 완료 ===")

    db.close()


if __name__ == "__main__":
    main()
