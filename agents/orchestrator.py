"""
조율자 에이전트
- 사용자 입력을 적절한 에이전트로 라우팅
- 에이전트 간 메시지 전달
- 응답 조합 및 반환
"""
from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent


class OrchestratorAgent(BaseAgent):
    """중앙 조율자 에이전트"""

    def __init__(
        self,
        conversation_agent: ConversationAgent,
        data_manager: DataManagerAgent,
        gamification: GamificationAgent,
        coaching: CoachingAgent
    ):
        super().__init__("Orchestrator")

        self.conversation = conversation_agent
        self.data_manager = data_manager
        self.gamification = gamification
        self.coaching = coaching

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리 (BaseAgent 구현)"""
        user_input = message.get("text", "")
        return self.handle_user_input(user_input)

    def handle_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 입력 처리

        Args:
            user_input: 사용자 입력 텍스트

        Returns:
            처리 결과
        """
        # 1. 파싱
        parse_result = self.conversation.parse_input(user_input)

        if not parse_result.get("success"):
            return {
                "success": False,
                "error": "파싱 실패",
                "message": "입력을 이해하지 못했어요. 다시 말씀해주세요."
            }

        intent = parse_result.get("intent")
        entities = parse_result.get("entities", {})
        confidence = parse_result.get("confidence", 0)

        # 신뢰도가 낮으면 명확화 질문
        if confidence < 0.7:
            clarification = self.conversation.ask_clarification(intent, entities)
            return {
                "success": True,
                "need_clarification": True,
                "message": clarification,
                "intent": intent,
                "entities": entities
            }

        # 2. 의도별 처리
        if intent == "sleep":
            return self._handle_sleep(entities)

        elif intent == "workout":
            return self._handle_workout(entities)

        elif intent == "protein":
            return self._handle_protein(entities)

        elif intent == "weight":
            return self._handle_weight(entities)

        elif intent == "task_add":
            return self._handle_task_add(entities)

        elif intent == "task_complete":
            return self._handle_task_complete(entities)

        elif intent == "summary":
            return self._handle_summary(entities)

        elif intent == "progress":
            return self._handle_progress()

        else:
            return {
                "success": False,
                "message": "알 수 없는 명령입니다."
            }

    def _handle_sleep(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """수면 기록 처리"""
        date = entities.get("date")
        hours = entities.get("sleep_hours")

        if not hours:
            return {
                "success": False,
                "message": "수면 시간을 알 수 없습니다."
            }

        # 데이터 저장
        result = self.data_manager.store_health_metric(date, sleep_h=hours)

        if not result.get("success"):
            return {
                "success": False,
                "message": f"저장 실패: {result.get('error')}"
            }

        # 코칭 (알림)
        alert_result = self.coaching.check_alerts("sleep", hours, date)
        alerts = alert_result.get("alerts", [])

        # 경험치 부여 (목표 달성 시)
        exp_result = None
        if hours >= 7:  # 목표 달성
            exp_result = self.gamification.award_exp("sleep_goal", hours, f"수면 {hours}시간")

        # 응답 조합
        message_parts = [f"✓ 수면 기록 완료: {hours}시간"]

        # 알림 추가
        for alert in alerts:
            message_parts.append(alert.get("message", ""))

        # 경험치 정보
        if exp_result and exp_result.get("success"):
            exp_gained = exp_result.get("exp_gained", 0)
            message_parts.append(f"  +{exp_gained} XP")

            if exp_result.get("level_up"):
                old_level = exp_result.get("new_level", 1) - 1
                new_level = exp_result.get("new_level", 1)
                message_parts.append(f"\n🎉 레벨업! {old_level} → {new_level}")

        return {
            "success": True,
            "message": "\n".join(message_parts)
        }

    def _handle_workout(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """운동 기록 처리"""
        date = entities.get("date")
        minutes = entities.get("workout_minutes")

        if minutes is None:
            return {
                "success": False,
                "message": "운동 시간을 알 수 없습니다."
            }

        # 데이터 저장
        result = self.data_manager.store_health_metric(date, workout_min=minutes)

        if not result.get("success"):
            return {
                "success": False,
                "message": f"저장 실패: {result.get('error')}"
            }

        # 코칭
        alert_result = self.coaching.check_alerts("workout", minutes, date)
        alerts = alert_result.get("alerts", [])

        # 경험치
        exp_result = self.gamification.award_exp("workout", minutes, f"운동 {minutes}분")

        # 응답
        message_parts = [f"✓ 운동 기록 완료: {minutes}분"]

        for alert in alerts:
            message_parts.append(alert.get("message", ""))

        if exp_result and exp_result.get("success"):
            exp_gained = exp_result.get("exp_gained", 0)
            message_parts.append(f"  +{exp_gained} XP")

            if exp_result.get("level_up"):
                old_level = exp_result.get("new_level", 1) - 1
                new_level = exp_result.get("new_level", 1)
                message_parts.append(f"\n🎉 레벨업! {old_level} → {new_level}")

        return {
            "success": True,
            "message": "\n".join(message_parts)
        }

    def _handle_protein(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """단백질 기록 처리"""
        date = entities.get("date")
        grams = entities.get("protein_grams")

        if grams is None:
            return {
                "success": False,
                "message": "단백질 섭취량을 알 수 없습니다."
            }

        result = self.data_manager.store_health_metric(date, protein_g=grams)

        if not result.get("success"):
            return {
                "success": False,
                "message": f"저장 실패: {result.get('error')}"
            }

        # 코칭
        alert_result = self.coaching.check_alerts("protein", grams, date)
        alerts = alert_result.get("alerts", [])

        # 경험치
        exp_result = None
        if grams >= 100:  # 목표 달성
            exp_result = self.gamification.award_exp("protein_goal", grams, f"단백질 {grams}g")

        message_parts = [f"✓ 단백질 기록 완료: {grams}g"]

        for alert in alerts:
            message_parts.append(alert.get("message", ""))

        if exp_result and exp_result.get("success"):
            exp_gained = exp_result.get("exp_gained", 0)
            message_parts.append(f"  +{exp_gained} XP")

        return {
            "success": True,
            "message": "\n".join(message_parts)
        }

    def _handle_weight(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """체중 기록 처리"""
        date = entities.get("date")
        weight = entities.get("weight_kg")

        if weight is None:
            return {
                "success": False,
                "message": "체중을 알 수 없습니다."
            }

        result = self.data_manager.store_health_metric(date, weight_kg=weight)

        return {
            "success": True,
            "message": f"✓ 체중 기록 완료: {weight}kg"
        }

    def _handle_task_add(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """할일 추가 처리"""
        title = entities.get("task_title")

        if not title:
            return {
                "success": False,
                "message": "할일 제목을 알 수 없습니다."
            }

        result = self.data_manager.store_task(title)

        if result.get("success"):
            return {
                "success": True,
                "message": f"✓ 할일 추가: [{result['task_id']}] {title}"
            }
        else:
            return {
                "success": False,
                "message": f"추가 실패: {result.get('error')}"
            }

    def _handle_task_complete(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """할일 완료 처리"""
        task_id = entities.get("task_id")

        if not task_id or task_id < 0:
            return {
                "success": False,
                "message": "할일 ID를 알 수 없습니다."
            }

        result = self.data_manager.complete_task(task_id)

        if not result.get("success"):
            return {
                "success": False,
                "message": f"완료 실패: {result.get('error')}"
            }

        # 경험치
        priority = result.get("priority", "normal")
        exp_result = self.gamification.award_exp("task_complete", priority, f"할일 완료: {result.get('title')}")

        message_parts = [f"✓ 할일 완료: {result.get('title')}"]

        if exp_result and exp_result.get("success"):
            exp_gained = exp_result.get("exp_gained", 0)
            message_parts.append(f"  +{exp_gained} XP")

            if exp_result.get("level_up"):
                old_level = exp_result.get("new_level", 1) - 1
                new_level = exp_result.get("new_level", 1)
                message_parts.append(f"\n🎉 레벨업! {old_level} → {new_level}")

        return {
            "success": True,
            "message": "\n".join(message_parts)
        }

    def _handle_summary(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """요약 조회 처리"""
        date = entities.get("date")

        summary = self.data_manager.get_summary(date)

        message_parts = [f"📊 {summary['date']} 요약", ""]

        # 건강 지표
        health = summary["health"]
        sleep = health.get("sleep_h")
        workout = health.get("workout_min")
        protein = health.get("protein_g")
        weight = health.get("weight_kg")

        message_parts.append(f"💤 수면: {sleep}시간" if sleep else "💤 수면: 기록 없음")
        message_parts.append(f"💪 운동: {workout}분" if workout else "💪 운동: 기록 없음")
        message_parts.append(f"🍗 단백질: {protein}g" if protein else "🍗 단백질: 기록 없음")
        if weight:
            message_parts.append(f"⚖️ 체중: {weight}kg")

        # 할일
        tasks = summary["tasks"]
        message_parts.append(f"📝 할일: 완료 {tasks['done']}/{tasks['total']}")

        # 습관
        if summary["habits"]:
            message_parts.append("\n🔥 습관:")
            for habit in summary["habits"]:
                status_emoji = "✓" if habit["status"] == "success" else "✗"
                message_parts.append(f"  {status_emoji} {habit['name']} (streak: {habit['streak']}일)")

        return {
            "success": True,
            "message": "\n".join(message_parts)
        }

    def _handle_progress(self) -> Dict[str, Any]:
        """진행도 조회 처리"""
        progress = self.gamification.get_progress_summary()

        level = progress["level"]
        current_exp = progress["current_exp"]
        next_exp = progress["next_level_exp"]
        percent = progress["progress_percent"]
        achievements = progress["achievements"]

        bar_length = 20
        filled = int(percent // 5)
        bar = "=" * filled + " " * (bar_length - filled)

        message = f"""
📊 Level {level} ({current_exp}/{next_exp} XP) | 🏆 업적 {achievements}
진행도: [{bar}] {percent}%
""".strip()

        return {
            "success": True,
            "message": message
        }
