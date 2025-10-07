"""
데이터 관리 에이전트
- DB CRUD 작업
- 데이터 검증
- 통계 집계
"""
import sqlite3
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from agents.base_agent import BaseAgent


class DataManagerAgent(BaseAgent):
    """데이터 관리 에이전트"""

    def __init__(self, db_connection: sqlite3.Connection):
        super().__init__("DataManager")
        self.conn = db_connection

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리 (BaseAgent 구현)"""
        action = message.get("action")

        if action == "store_health":
            return self.store_health_metric(**message.get("data", {}))
        elif action == "store_task":
            return self.store_task(**message.get("data", {}))
        elif action == "get_summary":
            return self.get_summary(**message.get("data", {}))
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    # ===== 건강 지표 CRUD =====

    def store_health_metric(
        self,
        date_str: str,
        sleep_h: Optional[float] = None,
        workout_min: Optional[int] = None,
        protein_g: Optional[float] = None,
        weight_kg: Optional[float] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        일일 건강 지표 저장

        Args:
            date_str: 날짜 (YYYY-MM-DD)
            sleep_h: 수면 시간
            workout_min: 운동 시간
            protein_g: 단백질 섭취량
            weight_kg: 체중
            note: 메모

        Returns:
            저장 결과
        """
        cursor = self.conn.cursor()

        try:
            # 기존 데이터 확인
            cursor.execute("SELECT * FROM daily_health WHERE date = ?", (date_str,))
            existing = cursor.fetchone()

            if existing:
                # 업데이트
                update_fields = []
                params = []

                if sleep_h is not None:
                    update_fields.append("sleep_h = ?")
                    params.append(sleep_h)
                if workout_min is not None:
                    update_fields.append("workout_min = ?")
                    params.append(workout_min)
                if protein_g is not None:
                    update_fields.append("protein_g = ?")
                    params.append(protein_g)
                if weight_kg is not None:
                    update_fields.append("weight_kg = ?")
                    params.append(weight_kg)
                if note is not None:
                    update_fields.append("note = ?")
                    params.append(note)

                if update_fields:
                    params.append(date_str)
                    sql = f"UPDATE daily_health SET {', '.join(update_fields)} WHERE date = ?"
                    cursor.execute(sql, params)
                    self.conn.commit()
                    return {"success": True, "action": "updated", "date": date_str}
            else:
                # 새로 삽입
                cursor.execute("""
                    INSERT INTO daily_health (date, sleep_h, workout_min, protein_g, weight_kg, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date_str, sleep_h, workout_min, protein_g, weight_kg, note))
                self.conn.commit()
                return {"success": True, "action": "inserted", "date": date_str}

        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def store_custom_metric(
        self,
        date_str: str,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        category: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """커스텀 메트릭 저장 (BMI, 혈압 등)"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO custom_metrics (date, metric_name, value, unit, category, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date_str, metric_name, value, unit, category, note))
            self.conn.commit()
            return {"success": True, "metric": metric_name, "value": value}
        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    # ===== 할일 CRUD =====

    def store_task(
        self,
        title: str,
        due: Optional[str] = None,
        priority: str = "normal",
        category: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """할일 추가"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO tasks (title, due, priority, category, note)
                VALUES (?, ?, ?, ?, ?)
            """, (title, due, priority, category, note))
            self.conn.commit()
            task_id = cursor.lastrowid
            return {"success": True, "task_id": task_id, "title": title}
        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def complete_task(self, task_id: int) -> Dict[str, Any]:
        """할일 완료 처리"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                UPDATE tasks
                SET status = 'done', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (task_id,))
            self.conn.commit()

            if cursor.rowcount > 0:
                # 할일 정보 가져오기
                cursor.execute("SELECT title, priority FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                return {
                    "success": True,
                    "task_id": task_id,
                    "title": row["title"] if row else "",
                    "priority": row["priority"] if row else "normal"
                }
            else:
                return {"success": False, "error": "Task not found"}

        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def get_pending_tasks(self) -> List[Dict]:
        """미완료 할일 목록"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, due, priority, category
            FROM tasks
            WHERE status != 'done'
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                due ASC
        """)

        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                "id": row["id"],
                "title": row["title"],
                "due": row["due"],
                "priority": row["priority"],
                "category": row["category"]
            })

        return tasks

    # ===== 습관 관리 =====

    def create_habit(self, name: str, goal_type: Optional[str] = None, target_value: Optional[float] = None) -> Dict[str, Any]:
        """습관 생성"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO habits (name, goal_type, target_value)
                VALUES (?, ?, ?)
            """, (name, goal_type, target_value))
            self.conn.commit()
            habit_id = cursor.lastrowid
            return {"success": True, "habit_id": habit_id, "name": name}
        except sqlite3.IntegrityError:
            return {"success": False, "error": "Habit already exists"}
        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def log_habit(self, habit_name: str, date_str: str, status: str, note: Optional[str] = None) -> Dict[str, Any]:
        """습관 기록"""
        cursor = self.conn.cursor()

        try:
            # 습관 ID 찾기
            cursor.execute("SELECT id FROM habits WHERE name = ?", (habit_name,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Habit not found"}

            habit_id = row["id"]

            # Streak 계산
            streak_count = self._calculate_streak(habit_id, date_str, status)

            # 기록
            cursor.execute("""
                INSERT OR REPLACE INTO habit_logs (habit_id, date, status, streak_count, note)
                VALUES (?, ?, ?, ?, ?)
            """, (habit_id, date_str, status, streak_count, note))
            self.conn.commit()

            return {"success": True, "habit": habit_name, "status": status, "streak": streak_count}

        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def _calculate_streak(self, habit_id: int, current_date_str: str, current_status: str) -> int:
        """습관 streak 계산"""
        if current_status != "success":
            return 0

        cursor = self.conn.cursor()
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()

        # 어제 날짜
        yesterday = current_date - timedelta(days=1)

        # 어제 기록 확인
        cursor.execute("""
            SELECT streak_count FROM habit_logs
            WHERE habit_id = ? AND date = ? AND status = 'success'
        """, (habit_id, yesterday.strftime("%Y-%m-%d")))

        row = cursor.fetchone()
        if row:
            return row["streak_count"] + 1
        else:
            return 1

    def get_streak(self, habit_name: str) -> int:
        """현재 습관 streak 가져오기"""
        cursor = self.conn.cursor()

        # 습관 ID 찾기
        cursor.execute("SELECT id FROM habits WHERE name = ?", (habit_name,))
        row = cursor.fetchone()
        if not row:
            return 0

        habit_id = row["id"]

        # 최근 성공 기록의 streak
        cursor.execute("""
            SELECT streak_count FROM habit_logs
            WHERE habit_id = ? AND status = 'success'
            ORDER BY date DESC
            LIMIT 1
        """, (habit_id,))

        row = cursor.fetchone()
        return row["streak_count"] if row else 0

    # ===== 통계 및 요약 =====

    def get_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """일일 요약"""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        cursor = self.conn.cursor()

        # 건강 지표
        cursor.execute("SELECT * FROM daily_health WHERE date = ?", (date_str,))
        health_row = cursor.fetchone()

        health = {
            "sleep_h": health_row["sleep_h"] if health_row else None,
            "workout_min": health_row["workout_min"] if health_row else None,
            "protein_g": health_row["protein_g"] if health_row else None,
            "weight_kg": health_row["weight_kg"] if health_row else None,
        }

        # 할일 통계
        cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE date(created_at) = ?", (date_str,))
        total_tasks = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as done FROM tasks WHERE date(completed_at) = ?", (date_str,))
        done_tasks = cursor.fetchone()["done"]

        tasks = {
            "total": total_tasks,
            "done": done_tasks,
            "pending": total_tasks - done_tasks
        }

        # 습관 기록
        cursor.execute("""
            SELECT h.name, hl.status, hl.streak_count
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE hl.date = ?
        """, (date_str,))

        habits = []
        for row in cursor.fetchall():
            habits.append({
                "name": row["name"],
                "status": row["status"],
                "streak": row["streak_count"]
            })

        return {
            "date": date_str,
            "health": health,
            "tasks": tasks,
            "habits": habits
        }

    def get_weekly_stats(self) -> Dict[str, Any]:
        """주간 통계"""
        cursor = self.conn.cursor()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # 평균 수면 시간
        cursor.execute("""
            SELECT AVG(sleep_h) as avg_sleep
            FROM daily_health
            WHERE date >= ? AND date <= ?
        """, (week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))
        avg_sleep = cursor.fetchone()["avg_sleep"]

        # 총 운동 시간
        cursor.execute("""
            SELECT SUM(workout_min) as total_workout
            FROM daily_health
            WHERE date >= ? AND date <= ?
        """, (week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))
        total_workout = cursor.fetchone()["total_workout"]

        # 완료한 할일 수
        cursor.execute("""
            SELECT COUNT(*) as completed
            FROM tasks
            WHERE completed_at >= ? AND completed_at <= ?
        """, (week_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))
        completed_tasks = cursor.fetchone()["completed"]

        return {
            "period": f"{week_ago} ~ {today}",
            "avg_sleep": round(avg_sleep, 1) if avg_sleep else 0,
            "total_workout": total_workout or 0,
            "completed_tasks": completed_tasks
        }

    # ===== 학습 기록 (Learning Logs) =====

    def add_learning_log(
        self,
        title: str,
        content: str = "",
        category: str = None,
        tags: str = None,
        date: str = None
    ) -> int:
        """
        학습 기록 추가

        Args:
            title: 학습한 내용 제목 (필수)
            content: 상세 내용
            category: 카테고리 (예: "프로그래밍", "언어", "도구")
            tags: 태그 (쉼표로 구분, 예: "Python,LangChain")
            date: 날짜 (기본: 오늘)

        Returns:
            생성된 학습 기록 ID
        """
        if not title:
            raise ValueError("학습 내용 제목은 필수입니다.")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO learning_logs (date, title, content, category, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (date, title, content, category, tags))

        self.conn.commit()
        return cursor.lastrowid

    def get_learning_logs(
        self,
        date: str = None,
        category: str = None,
        limit: int = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        학습 기록 조회

        Args:
            date: 특정 날짜 (None이면 전체)
            category: 카테고리 필터
            limit: 최대 개수
            offset: 시작 위치

        Returns:
            학습 기록 리스트
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM learning_logs WHERE 1=1"
        params = []

        if date:
            query += " AND date = ?"
            params.append(date)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY date DESC, created_at DESC"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)

        logs = []
        for row in cursor.fetchall():
            logs.append({
                "id": row["id"],
                "date": row["date"],
                "title": row["title"],
                "content": row["content"],
                "category": row["category"],
                "tags": row["tags"].split(",") if row["tags"] else [],
                "created_at": row["created_at"]
            })

        return logs

    def update_learning_log(
        self,
        log_id: int,
        title: str = None,
        content: str = None,
        category: str = None,
        tags: str = None
    ) -> bool:
        """
        학습 기록 수정

        Args:
            log_id: 학습 기록 ID
            title: 새 제목
            content: 새 내용
            category: 새 카테고리
            tags: 새 태그

        Returns:
            성공 여부
        """
        cursor = self.conn.cursor()

        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if category is not None:
            updates.append("category = ?")
            params.append(category)

        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)

        if not updates:
            return False

        params.append(log_id)
        query = f"UPDATE learning_logs SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        self.conn.commit()

        return cursor.rowcount > 0

    def delete_learning_log(self, log_id: int) -> bool:
        """
        학습 기록 삭제

        Args:
            log_id: 학습 기록 ID

        Returns:
            성공 여부
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM learning_logs WHERE id = ?", (log_id,))
        self.conn.commit()

        return cursor.rowcount > 0

    def get_learning_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        학습 통계

        Args:
            days: 최근 며칠

        Returns:
            학습 통계 정보
        """
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # 총 학습 기록 수
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM learning_logs
            WHERE date >= ?
        """, (start_date,))
        total_logs = cursor.fetchone()["total"]

        # 카테고리별 통계
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM learning_logs
            WHERE date >= ? AND category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """, (start_date,))
        categories = [{"category": row["category"], "count": row["count"]} for row in cursor.fetchall()]

        # 최근 학습 기록
        recent_logs = self.get_learning_logs(limit=5)

        return {
            "total_logs": total_logs,
            "categories": categories,
            "recent": recent_logs,
            "period_days": days
        }
