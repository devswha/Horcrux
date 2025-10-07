"""
코칭 에이전트
- 건강 지표 모니터링
- 알림 규칙 체크
- 개인화된 조언 생성
- LLM 기반 인사이트 (Phase 3)
"""
import sqlite3
import yaml
from datetime import datetime, timedelta
from typing import Any, Dict, List
from agents.base_agent import BaseAgent


class CoachingAgent(BaseAgent):
    """알림 및 인사이트 제공 에이전트"""

    def __init__(self, db_connection: sqlite3.Connection, llm_client=None, config_path: str = "config.yaml"):
        super().__init__("Coaching")
        self.conn = db_connection
        self.llm = llm_client
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 기본 설정
            return {
                "health_targets": {
                    "sleep_hours": 7,
                    "workout_minutes": 30,
                    "protein_grams": 100
                },
                "alerts": {
                    "sleep_warning": 6,
                    "consecutive_days_check": 3
                }
            }

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        action = message.get("action")

        if action == "check_alerts":
            return self.check_alerts(**message.get("data", {}))
        elif action == "analyze_patterns":
            return self.analyze_patterns()
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def check_alerts(self, metric_type: str = None, value: Any = None, date: str = None) -> Dict[str, Any]:
        """
        알림 체크

        Args:
            metric_type: 메트릭 유형 ('sleep', 'workout', 'protein')
            value: 메트릭 값
            date: 날짜

        Returns:
            알림 결과
        """
        alerts = []

        # 개별 메트릭 체크
        if metric_type == "sleep" and value is not None:
            alert = self._check_sleep_alert(value)
            if alert:
                alerts.append(alert)

        elif metric_type == "workout" and value is not None:
            alert = self._check_workout_alert(value)
            if alert:
                alerts.append(alert)

        elif metric_type == "protein" and value is not None:
            alert = self._check_protein_alert(value)
            if alert:
                alerts.append(alert)

        # 패턴 기반 알림 (연속 일수 등)
        pattern_alerts = self._check_pattern_alerts()
        alerts.extend(pattern_alerts)

        return {
            "success": True,
            "alerts": alerts
        }

    def _check_sleep_alert(self, hours: float) -> Dict[str, str]:
        """수면 알림 체크"""
        target = self.config.get("health_targets", {}).get("sleep_hours", 7)
        warning_threshold = self.config.get("alerts", {}).get("sleep_warning", 6)

        if hours < warning_threshold:
            diff = target - hours
            return {
                "type": "warning",
                "category": "sleep",
                "message": f"⚠️ 목표({target}시간)보다 {diff:.1f}시간 부족합니다. 충분한 수면이 중요해요!"
            }
        elif hours < target:
            diff = target - hours
            return {
                "type": "info",
                "category": "sleep",
                "message": f"💤 목표보다 {diff:.1f}시간 부족하네요."
            }
        else:
            return {
                "type": "success",
                "category": "sleep",
                "message": f"✓ 목표 달성! 좋은 수면이었습니다."
            }

    def _check_workout_alert(self, minutes: int) -> Dict[str, str]:
        """운동 알림 체크"""
        target = self.config.get("health_targets", {}).get("workout_minutes", 30)

        if minutes == 0:
            return {
                "type": "info",
                "category": "workout",
                "message": "💪 오늘 운동은 어떠세요? 가벼운 스트레칭도 좋아요!"
            }
        elif minutes < target:
            diff = target - minutes
            return {
                "type": "info",
                "category": "workout",
                "message": f"목표까지 {diff}분 남았어요. 조금만 더 화이팅!"
            }
        else:
            return {
                "type": "success",
                "category": "workout",
                "message": f"✓ 목표 달성! {minutes}분 운동 훌륭합니다!"
            }

    def _check_protein_alert(self, grams: float) -> Dict[str, str]:
        """단백질 알림 체크"""
        target = self.config.get("health_targets", {}).get("protein_grams", 100)

        if grams < target:
            diff = target - grams
            return {
                "type": "info",
                "category": "protein",
                "message": f"🍗 목표까지 {diff:.0f}g 남았어요."
            }
        else:
            return {
                "type": "success",
                "category": "protein",
                "message": f"✓ 단백질 목표 달성!"
            }

    def _check_pattern_alerts(self) -> List[Dict[str, str]]:
        """패턴 기반 알림 (연속 일수 등)"""
        alerts = []
        cursor = self.conn.cursor()

        # 최근 N일 수면 체크
        consecutive_days = self.config.get("alerts", {}).get("consecutive_days_check", 3)
        warning_threshold = self.config.get("alerts", {}).get("sleep_warning", 6)

        today = datetime.now().date()
        start_date = today - timedelta(days=consecutive_days - 1)

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ? AND sleep_h < ?
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), warning_threshold))

        result = cursor.fetchone()
        if result and result["count"] >= consecutive_days:
            alerts.append({
                "type": "warning",
                "category": "sleep_pattern",
                "message": f"⚠️ {consecutive_days}일 연속 수면 부족입니다. 건강을 위해 충분한 휴식을 취하세요!"
            })

        # 운동 0분 연속 체크
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_health
            WHERE date >= ? AND date <= ? AND (workout_min IS NULL OR workout_min = 0)
        """, (start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))

        result = cursor.fetchone()
        if result and result["count"] >= consecutive_days:
            alerts.append({
                "type": "info",
                "category": "workout_pattern",
                "message": f"💪 {consecutive_days}일째 운동 기록이 없네요. 오늘은 가벼운 산책 어떠세요?"
            })

        return alerts

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        건강 패턴 분석 및 인사이트 생성

        Returns:
            인사이트 딕셔너리
        """
        cursor = self.conn.cursor()
        insights = []

        # 주간 평균 수면
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT AVG(sleep_h) as avg_sleep, COUNT(*) as days
            FROM daily_health
            WHERE date >= ? AND sleep_h IS NOT NULL
        """, (week_ago,))

        result = cursor.fetchone()
        if result and result["days"] > 0:
            avg_sleep = result["avg_sleep"]
            target = self.config.get("health_targets", {}).get("sleep_hours", 7)

            if avg_sleep < target - 1:
                insights.append({
                    "type": "trend",
                    "category": "sleep",
                    "message": f"📊 주간 평균 수면: {avg_sleep:.1f}시간. 목표보다 낮습니다."
                })
            else:
                insights.append({
                    "type": "trend",
                    "category": "sleep",
                    "message": f"📊 주간 평균 수면: {avg_sleep:.1f}시간. 잘하고 계세요!"
                })

        # 주간 총 운동 시간
        cursor.execute("""
            SELECT SUM(workout_min) as total_workout
            FROM daily_health
            WHERE date >= ?
        """, (week_ago,))

        result = cursor.fetchone()
        if result:
            total_workout = result["total_workout"] or 0
            insights.append({
                "type": "trend",
                "category": "workout",
                "message": f"💪 이번 주 총 운동: {total_workout}분"
            })

        return {
            "success": True,
            "insights": insights
        }

    def celebrate_milestone(self, achievement: Dict[str, Any]) -> str:
        """
        마일스톤 축하 메시지 생성

        Args:
            achievement: 업적 정보

        Returns:
            축하 메시지
        """
        name = achievement.get("name", "")
        description = achievement.get("description", "")
        exp_reward = achievement.get("exp_reward", 0)
        icon = achievement.get("icon", "🏆")

        return f"\n{icon} 새 업적 달성!\n\"{name}\"\n{description}\n+{exp_reward} XP 보상"

    def suggest_action(self, context: Dict[str, Any]) -> str:
        """
        상황별 행동 제안

        Args:
            context: 상황 정보

        Returns:
            제안 메시지
        """
        # LLM 사용 가능하면 개인화된 제안
        if self.llm and context:
            try:
                advice = self.generate_personalized_advice(context)
                if advice:
                    return advice
            except Exception:
                pass  # LLM 실패 시 기본 제안 사용

        # 기본 제안 로직
        suggestions = [
            "💡 오늘 건강 목표를 달성해보세요!",
            "🎯 할일을 하나씩 완료하며 경험치를 모아보세요!",
            "🌟 꾸준함이 가장 중요해요. 작은 습관부터 시작하세요!",
        ]

        # 랜덤 또는 컨텍스트 기반 제안
        import random
        return random.choice(suggestions)

    def generate_personalized_advice(self, context: Dict[str, Any]) -> str:
        """
        LLM 기반 개인화된 조언 생성 (Phase 3)

        Args:
            context: 사용자 데이터 컨텍스트
                - recent_sleep: 최근 수면 데이터
                - recent_workout: 최근 운동 데이터
                - pending_tasks: 미완료 할일 수
                - level: 현재 레벨
                - achievements: 달성한 업적 수

        Returns:
            개인화된 조언 메시지
        """
        if not self.llm:
            return ""

        try:
            # 컨텍스트를 프롬프트로 변환
            prompt = self._build_advice_prompt(context)

            # LLM 호출
            advice = self.llm.generate_response(
                user_input=prompt,
                context=str(context),
                tone="encouraging"
            )

            return advice.strip()

        except Exception as e:
            print(f"LLM advice generation failed: {e}")
            return ""

    def _build_advice_prompt(self, context: Dict[str, Any]) -> str:
        """조언 생성 프롬프트 구성"""
        prompt_parts = ["사용자의 현재 상태를 보고 짧고 격려하는 조언을 한 문장으로 주세요.\n\n현재 상태:"]

        if "recent_sleep" in context:
            avg_sleep = context["recent_sleep"].get("average", 0)
            target = self.config.get("health_targets", {}).get("sleep_hours", 7)
            prompt_parts.append(f"- 최근 평균 수면: {avg_sleep:.1f}시간 (목표: {target}시간)")

        if "recent_workout" in context:
            total_workout = context["recent_workout"].get("total", 0)
            prompt_parts.append(f"- 이번 주 총 운동: {total_workout}분")

        if "pending_tasks" in context:
            pending = context["pending_tasks"]
            prompt_parts.append(f"- 미완료 할일: {pending}개")

        if "level" in context:
            level = context["level"]
            prompt_parts.append(f"- 현재 레벨: {level}")

        if "achievements" in context:
            achievements = context["achievements"]
            prompt_parts.append(f"- 달성한 업적: {achievements}개")

        return "\n".join(prompt_parts)
