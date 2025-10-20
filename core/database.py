"""
데이터베이스 스키마 정의 및 초기화
13개 테이블: daily_health, custom_metrics, habits, habit_logs, tasks,
            learning_logs, people, interactions, knowledge_entries,
            reflections, conversation_memory, user_progress, exp_logs

지원 DB:
- SQLite (로컬 개발)
- PostgreSQL (Supabase/Cloud 배포)
"""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# PostgreSQL 지원
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class Database:
    """SQLite/PostgreSQL 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "horcrux.db"):
        self.db_path = db_path
        self.conn: Optional[Union[sqlite3.Connection, 'psycopg2.connection']] = None
        self.db_type = None  # 'sqlite' or 'postgres'

    def connect(self) -> Union[sqlite3.Connection, 'psycopg2.connection']:
        """데이터베이스 연결 (환경에 따라 SQLite 또는 PostgreSQL)"""
        # Supabase 환경 변수 체크
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if supabase_url and supabase_key and POSTGRES_AVAILABLE:
            # PostgreSQL (Supabase) 연결
            try:
                # Supabase URL 형식: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres
                self.conn = psycopg2.connect(
                    supabase_url,
                    cursor_factory=RealDictCursor
                )
                self.db_type = 'postgres'
                print("✓ PostgreSQL (Supabase) 연결 성공")
            except Exception as e:
                print(f"⚠ PostgreSQL 연결 실패, SQLite로 fallback: {e}")
                self._connect_sqlite()
        else:
            # SQLite 연결 (로컬 개발)
            self._connect_sqlite()

        return self.conn

    def _connect_sqlite(self):
        """SQLite 연결"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.db_type = 'sqlite'

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

        # SQL 문법 선택 (SQLite vs PostgreSQL)
        if self.db_type == 'postgres':
            serial = "SERIAL PRIMARY KEY"
            autoincrement = ""
        else:
            serial = "INTEGER PRIMARY KEY AUTOINCREMENT"
            autoincrement = ""

        # 1. 일일 건강 메트릭 (핵심 지표)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS daily_health (
                id {serial},
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
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS custom_metrics (
                id {serial},
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
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS habits (
                id {serial},
                name TEXT NOT NULL UNIQUE,
                goal_type TEXT,
                target_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. 습관 추적 로그
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id {serial},
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
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS tasks (
                id {serial},
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
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS user_progress (
                id {serial},
                level INTEGER DEFAULT 1,
                current_exp INTEGER DEFAULT 0,
                total_exp INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. 경험치 획득 로그
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS exp_logs (
                id {serial},
                date DATE NOT NULL,
                action_type TEXT NOT NULL,
                exp_gained INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 8. 학습 기록 (Learning Logs)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS learning_logs (
                id {serial},
                date DATE NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                category TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # === Phase 5A: Personal Memory System ===

        # 9. 인물 정보 (People)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS people (
                id {serial},
                name TEXT NOT NULL UNIQUE,
                relationship_type TEXT,
                first_met_date DATE,
                tags TEXT,
                personality_notes TEXT,
                contact_info TEXT,
                importance_score INTEGER DEFAULT 5 CHECK(importance_score BETWEEN 1 AND 10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 10. 상호작용 로그 (Interactions)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS interactions (
                id {serial},
                person_id INTEGER NOT NULL,
                date DATE NOT NULL,
                type TEXT CHECK(type IN ('meeting', 'call', 'message', 'other')),
                summary TEXT,
                sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative')),
                topics TEXT,
                location TEXT,
                duration_min INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
            )
        """)

        # 11. 지식 저장소 (Knowledge Entries)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id {serial},
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                category TEXT,
                tags TEXT,
                learned_date DATE NOT NULL,
                confidence INTEGER DEFAULT 3 CHECK(confidence BETWEEN 1 AND 5),
                last_reviewed DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 12. 회고/성찰 (Reflections)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS reflections (
                id {serial},
                date DATE NOT NULL,
                topic TEXT,
                content TEXT NOT NULL,
                mood TEXT,
                insights TEXT,
                related_events TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 13. 대화 메모리 (Conversation Memory)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id {serial},
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT
            )
        """)

        # 인덱스 생성
        self._create_indexes(cursor)

        self.conn.commit()
        print("✓ 데이터베이스 스키마 초기화 완료 (13개 테이블)")

    def _create_indexes(self, cursor):
        """성능 최적화를 위한 인덱스 생성"""
        indexes = [
            # Existing indexes
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
            # Phase 5A indexes
            "CREATE INDEX IF NOT EXISTS idx_people_name ON people(name)",
            "CREATE INDEX IF NOT EXISTS idx_people_relationship_type ON people(relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_person_id ON interactions(person_id)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_date ON interactions(date)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(type)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_entries_category ON knowledge_entries(category)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_entries_learned_date ON knowledge_entries(learned_date)",
            "CREATE INDEX IF NOT EXISTS idx_reflections_date ON reflections(date)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_memory_session_id ON conversation_memory(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_memory_timestamp ON conversation_memory(timestamp)",
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

        # 모든 테이블 삭제 (역순으로, 외래키 때문에)
        tables = [
            # Phase 5A tables
            "conversation_memory", "reflections", "knowledge_entries",
            "interactions", "people",
            # Original tables
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
