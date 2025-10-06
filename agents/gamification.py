"""
게임화 에이전트
- 경험치 부여
- 레벨 계산
- 업적 달성 체크
"""
import sqlite3
import yaml
from datetime import datetime
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent


class GamificationAgent(BaseAgent):
    """레벨업 시스템 에이전트"""

    def __init__(self, db_connection: sqlite3.Connection, config_path: str = "config.yaml"):
        super().__init__("Gamification")
        self.conn = db_connection
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 기본 설정
            return {
                "exp_rules": {
                    "task_complete": 20,
                    "task_priority_multiplier": {"low": 0.5, "normal": 1.0, "high": 1.5, "urgent": 2.5},
                    "sleep_goal": 15,
                    "workout_base": 10,
                    "protein_goal": 10,
                    "habit_streak": 5,
                    "study_per_hour": 30,
                    "consecutive_bonus": 100
                }
            }

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        action = message.get("action")

        if action == "award_exp":
            return self.award_exp(**message.get("data", {}))
        elif action == "check_level_up":
            return self.check_level_up()
        elif action == "get_progress":
            return self.get_progress_summary()
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    # ===== 경험치 부여 =====

    def award_exp(self, action_type: str, value: Any, description: str = "") -> Dict[str, Any]:
        """
        행동에 따른 경험치 부여

        Args:
            action_type: 행동 유형 ('task_complete', 'sleep_goal', 'workout', etc.)
            value: 행동 값 (우선순위, 시간 등)
            description: 설명

        Returns:
            경험치 부여 결과 및 레벨업 여부
        """
        exp_gained = self._calculate_exp(action_type, value)

        if exp_gained <= 0:
            return {"success": False, "error": "No XP gained"}

        cursor = self.conn.cursor()

        try:
            # 경험치 로그 기록
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO exp_logs (date, action_type, exp_gained, description)
                VALUES (?, ?, ?, ?)
            """, (today, action_type, exp_gained, description))

            # 사용자 진행도 업데이트
            cursor.execute("SELECT * FROM user_progress ORDER BY id DESC LIMIT 1")
            progress = cursor.fetchone()

            if progress:
                new_current_exp = progress["current_exp"] + exp_gained
                new_total_exp = progress["total_exp"] + exp_gained

                cursor.execute("""
                    UPDATE user_progress
                    SET current_exp = ?, total_exp = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_current_exp, new_total_exp, progress["id"]))

            self.conn.commit()

            # 레벨업 체크
            level_up_result = self.check_level_up()

            return {
                "success": True,
                "exp_gained": exp_gained,
                "action_type": action_type,
                "level_up": level_up_result.get("leveled_up", False),
                "new_level": level_up_result.get("new_level", progress["level"] if progress else 1)
            }

        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}

    def _calculate_exp(self, action_type: str, value: Any) -> int:
        """
        경험치 계산

        Args:
            action_type: 행동 유형
            value: 행동 값

        Returns:
            경험치
        """
        exp_rules = self.config.get("exp_rules", {})

        if action_type == "task_complete":
            base_exp = exp_rules.get("task_complete", 20)
            priority = value if isinstance(value, str) else "normal"
            multiplier = exp_rules.get("task_priority_multiplier", {}).get(priority, 1.0)
            return int(base_exp * multiplier)

        elif action_type == "sleep_goal":
            return exp_rules.get("sleep_goal", 15)

        elif action_type == "workout":
            minutes = value if isinstance(value, (int, float)) else 0
            base = exp_rules.get("workout_base", 10)
            # 30분 기준으로 비례
            return int(base * (minutes / 30))

        elif action_type == "protein_goal":
            return exp_rules.get("protein_goal", 10)

        elif action_type == "habit_streak":
            streak_days = value if isinstance(value, int) else 1
            base = exp_rules.get("habit_streak", 5)
            # Streak 길이에 따라 보너스
            return base + (streak_days // 7) * 5

        elif action_type == "study":
            hours = value if isinstance(value, (int, float)) else 0
            per_hour = exp_rules.get("study_per_hour", 30)
            return int(per_hour * hours)

        elif action_type == "consecutive_bonus":
            return exp_rules.get("consecutive_bonus", 100)

        else:
            return 0

    # ===== 레벨 시스템 =====

    def check_level_up(self) -> Dict[str, Any]:
        """레벨업 체크"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_progress ORDER BY id DESC LIMIT 1")
        progress = cursor.fetchone()

        if not progress:
            return {"leveled_up": False, "current_level": 1}

        current_level = progress["level"]
        current_exp = progress["current_exp"]

        # 다음 레벨 필요 경험치 계산
        next_level = current_level + 1
        required_exp = self._exp_for_level(next_level)

        if current_exp >= required_exp:
            # 레벨업!
            remaining_exp = current_exp - required_exp

            cursor.execute("""
                UPDATE user_progress
                SET level = ?, current_exp = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (next_level, remaining_exp, progress["id"]))
            self.conn.commit()

            return {
                "leveled_up": True,
                "old_level": current_level,
                "new_level": next_level,
                "remaining_exp": remaining_exp,
                "next_level_exp": self._exp_for_level(next_level + 1)
            }
        else:
            return {
                "leveled_up": False,
                "current_level": current_level,
                "current_exp": current_exp,
                "required_exp": required_exp,
                "progress_percent": round((current_exp / required_exp) * 100, 1)
            }

    def _exp_for_level(self, level: int) -> int:
        """
        특정 레벨 도달에 필요한 경험치 (누적이 아닌 현재 레벨에서 필요한 양)

        Level 1 → 2: 100 XP
        Level 2 → 3: 150 XP
        Level 3 → 4: 200 XP
        ...
        Level N → N+1: 100 + (N-1) * 50 XP
        """
        if level <= 1:
            return 0
        return 100 + (level - 2) * 50

    def get_progress_summary(self) -> Dict[str, Any]:
        """진행도 요약"""
        cursor = self.conn.cursor()

        # 사용자 진행도
        cursor.execute("SELECT * FROM user_progress ORDER BY id DESC LIMIT 1")
        progress = cursor.fetchone()

        if not progress:
            return {"level": 1, "current_exp": 0, "total_exp": 0}

        current_level = progress["level"]
        current_exp = progress["current_exp"]
        total_exp = progress["total_exp"]

        # 다음 레벨 경험치
        next_level_exp = self._exp_for_level(current_level + 1)

        # 달성한 업적 수
        cursor.execute("SELECT COUNT(*) as count FROM achievement_logs")
        achieved_count = cursor.fetchone()["count"]

        # 전체 업적 수
        cursor.execute("SELECT COUNT(*) as count FROM achievements")
        total_achievements = cursor.fetchone()["count"]

        return {
            "level": current_level,
            "current_exp": current_exp,
            "total_exp": total_exp,
            "next_level_exp": next_level_exp,
            "progress_percent": round((current_exp / next_level_exp) * 100, 1) if next_level_exp > 0 else 0,
            "achievements": f"{achieved_count}/{total_achievements}"
        }

    # ===== 업적 시스템 =====

    def check_achievements(self, action_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        업적 달성 체크

        Args:
            action_context: 행동 컨텍스트 (예: {'tasks_completed': 100})

        Returns:
            달성한 업적 목록
        """
        cursor = self.conn.cursor()

        # 모든 업적 가져오기
        cursor.execute("SELECT * FROM achievements")
        all_achievements = cursor.fetchall()

        newly_achieved = []

        for achievement in all_achievements:
            # 이미 달성했는지 확인
            cursor.execute("""
                SELECT COUNT(*) as count FROM achievement_logs
                WHERE achievement_id = ?
            """, (achievement["id"],))

            if cursor.fetchone()["count"] > 0:
                continue  # 이미 달성

            # 조건 체크
            if self._check_achievement_condition(achievement, action_context):
                # 업적 달성 기록
                cursor.execute("""
                    INSERT INTO achievement_logs (achievement_id)
                    VALUES (?)
                """, (achievement["id"],))

                # 경험치 보상
                if achievement["exp_reward"] > 0:
                    self.award_exp(
                        "achievement",
                        achievement["exp_reward"],
                        f"업적 달성: {achievement['name']}"
                    )

                newly_achieved.append({
                    "name": achievement["name"],
                    "description": achievement["description"],
                    "exp_reward": achievement["exp_reward"],
                    "icon": achievement["icon"]
                })

        if newly_achieved:
            self.conn.commit()

        return newly_achieved

    def _check_achievement_condition(self, achievement: sqlite3.Row, context: Dict[str, Any]) -> bool:
        """
        업적 조건 체크 (Phase 3: 전체 구현)

        Args:
            achievement: 업적 정보
            context: 행동 컨텍스트

        Returns:
            달성 여부
        """
        condition_type = achievement["condition_type"]
        condition_value = json.loads(achievement["condition_value"]) if achievement["condition_value"] else {}
        cursor = self.conn.cursor()

        # 1. 첫 기록
        if condition_type == "any_record":
            return True

        # 2. 수면 관련
        elif condition_type == "sleep_streak":
            days = condition_value.get("days", 7)
            min_hours = condition_value.get("min_hours", 7)
            return self._check_sleep_streak(days, min_hours)

        elif condition_type == "sleep_no_bad_days":
            days = condition_value.get("days", 7)
            min_hours = condition_value.get("min_hours", 5)
            return self._check_no_bad_sleep_days(days, min_hours)

        # 3. 운동 관련
        elif condition_type == "workout_streak":
            days = condition_value.get("days", 30)
            return self._check_workout_streak(days)

        elif condition_type == "workout_single_day":
            minutes = condition_value.get("minutes", 100)
            return context.get("workout_minutes", 0) >= minutes

        elif condition_type == "workout_monthly_total":
            minutes = condition_value.get("minutes", 1000)
            return self._check_monthly_workout_total(minutes)

        elif condition_type == "workout_weekend_streak":
            weeks = condition_value.get("weeks", 4)
            return self._check_weekend_workout_streak(weeks)

        # 4. 영양 관련
        elif condition_type == "protein_streak":
            days = condition_value.get("days", 30)
            min_grams = condition_value.get("min_grams", 100)
            return self._check_protein_streak(days, min_grams)

        # 5. 할일 관련
        elif condition_type == "task_complete":
            count = condition_value.get("count", 100)
            return self._check_total_tasks_completed(count)

        elif condition_type == "task_single_day":
            count = condition_value.get("count", 10)
            return context.get("tasks_completed_today", 0) >= count

        elif condition_type == "task_before_due":
            count = condition_value.get("count", 30)
            return self._check_tasks_completed_before_due(count)

        elif condition_type == "task_priority":
            priority = condition_value.get("priority", "urgent")
            count = condition_value.get("count", 10)
            return self._check_priority_tasks_completed(priority, count)

        # 6. 습관 관련
        elif condition_type == "habit_streak":
            days = condition_value.get("days", 7)
            return self._check_habit_streak(days)

        # 7. 완벽한 주
        elif condition_type == "perfect_week":
            days = condition_value.get("days", 7)
            return self._check_perfect_week(days)

        # 8. 레벨 달성
        elif condition_type == "level_reached":
            level = condition_value.get("level", 5)
            cursor.execute("SELECT level FROM user_progress ORDER BY id DESC LIMIT 1")
            progress = cursor.fetchone()
            return progress and progress["level"] >= level

        return False

    # ===== 업적 체크 헬퍼 메서드 (Phase 3) =====

    def _check_sleep_streak(self, days: int, min_hours: float) -> bool:
        """수면 연속 기록 체크"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ? AND sleep_h >= ?
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), min_hours))

        result = cursor.fetchone()
        return result and result["count"] >= days

    def _check_no_bad_sleep_days(self, days: int, min_hours: float) -> bool:
        """나쁜 수면 없이 연속 기록"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ? AND (sleep_h IS NULL OR sleep_h < ?)
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), min_hours))

        result = cursor.fetchone()
        return result and result["count"] == 0

    def _check_workout_streak(self, days: int) -> bool:
        """운동 연속 기록 체크"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ? AND workout_min > 0
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))

        result = cursor.fetchone()
        return result and result["count"] >= days

    def _check_monthly_workout_total(self, minutes: int) -> bool:
        """월간 총 운동 시간 체크"""
        cursor = self.conn.cursor()
        from datetime import datetime

        # 현재 월의 1일부터
        today = datetime.now()
        month_start = today.replace(day=1).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT SUM(workout_min) as total
            FROM daily_health
            WHERE date >= ?
        """, (month_start,))

        result = cursor.fetchone()
        return result and (result["total"] or 0) >= minutes

    def _check_weekend_workout_streak(self, weeks: int) -> bool:
        """주말 연속 운동 체크"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        # 최근 N주 주말 체크
        weekend_count = 0
        today = datetime.now().date()

        for w in range(weeks):
            # 각 주의 토요일/일요일 찾기
            week_start = today - timedelta(weeks=w, days=today.weekday())
            saturday = week_start + timedelta(days=5)
            sunday = week_start + timedelta(days=6)

            cursor.execute("""
                SELECT COUNT(*) as count
                FROM daily_health
                WHERE date IN (?, ?) AND workout_min > 0
            """, (saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")))

            result = cursor.fetchone()
            if result and result["count"] >= 1:
                weekend_count += 1

        return weekend_count >= weeks

    def _check_protein_streak(self, days: int, min_grams: float) -> bool:
        """단백질 연속 기록 체크"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ? AND protein_g >= ?
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), min_grams))

        result = cursor.fetchone()
        return result and result["count"] >= days

    def _check_total_tasks_completed(self, count: int) -> bool:
        """총 완료한 할일 수 체크"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'done'
        """)

        result = cursor.fetchone()
        return result and result["count"] >= count

    def _check_tasks_completed_before_due(self, count: int) -> bool:
        """마감 전 완료한 할일 수 체크"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'done' AND due IS NOT NULL
            AND completed_at < due
        """)

        result = cursor.fetchone()
        return result and result["count"] >= count

    def _check_priority_tasks_completed(self, priority: str, count: int) -> bool:
        """특정 우선순위 할일 완료 수 체크"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE status = 'done' AND priority = ?
        """, (priority,))

        result = cursor.fetchone()
        return result and result["count"] >= count

    def _check_habit_streak(self, days: int) -> bool:
        """습관 연속 기록 체크"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        # 가장 긴 streak를 가진 습관 찾기
        cursor.execute("SELECT id, current_streak FROM habits")
        habits = cursor.fetchall()

        for habit in habits:
            if habit["current_streak"] >= days:
                return True

        return False

    def _check_perfect_week(self, days: int) -> bool:
        """완벽한 주 체크 (모든 목표 달성)"""
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        targets = self.config.get("health_targets", {})
        sleep_target = targets.get("sleep_hours", 7)
        workout_target = targets.get("workout_minutes", 30)
        protein_target = targets.get("protein_grams", 100)

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ?
            AND sleep_h >= ?
            AND workout_min >= ?
            AND protein_g >= ?
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"),
              sleep_target, workout_target, protein_target))

        result = cursor.fetchone()
        return result and result["count"] >= days
