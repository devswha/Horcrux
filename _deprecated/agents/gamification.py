"""
게임화 에이전트
- 경험치 부여
- 레벨 계산
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

        return {
            "level": current_level,
            "current_exp": current_exp,
            "total_exp": total_exp,
            "next_level_exp": next_level_exp,
            "progress_percent": round((current_exp / next_level_exp) * 100, 1) if next_level_exp > 0 else 0
        }
