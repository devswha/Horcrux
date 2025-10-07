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
        coaching: CoachingAgent,
        llm_client=None
    ):
        super().__init__("Orchestrator")

        self.conversation = conversation_agent
        self.data_manager = data_manager
        self.gamification = gamification
        self.coaching = coaching
        self.llm = llm_client  # LLM 클라이언트

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

        # 복합 명령 처리
        if parse_result.get("multiple"):
            return self._handle_multiple_intents(user_input, parse_result.get("intents", []))

        # 단일 명령 처리
        intent = parse_result.get("intent")
        entities = parse_result.get("entities", {})
        confidence = parse_result.get("confidence", 0)

        # 원본 입력을 entities에 추가 (대화형 응답용)
        entities["original_text"] = user_input

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
        result = self._handle_single_intent(intent, entities)

        # 3. LLM으로 응답을 대화형으로 개선
        if result and result.get("success") and self.llm:
            result["message"] = self._make_conversational(
                user_input=user_input,
                intent=intent,
                basic_message=result.get("message", "")
            )

        return result

    def _handle_single_intent(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """단일 의도 처리"""
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

        elif intent == "study":
            return self._handle_study(entities)

        elif intent == "learning_log":
            return self._handle_learning_log(entities)

        elif intent == "summary":
            return self._handle_summary(entities)

        elif intent == "progress":
            return self._handle_progress()

        elif intent == "chat":
            return self._handle_chat(entities)

        else:
            return {
                "success": False,
                "message": "알 수 없는 명령입니다."
            }

    def _handle_multiple_intents(
        self,
        user_input: str,
        intents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """복합 명령 처리"""
        print(f"🔍 복합 명령 감지: {len(intents)}개 의도")

        results = []
        total_exp = 0

        for idx, intent_data in enumerate(intents, 1):
            intent = intent_data.get("intent")
            entities = intent_data.get("entities", {})

            print(f"  처리 중 {idx}/{len(intents)}: {intent}")

            result = self._handle_single_intent(intent, entities)

            if result.get("success"):
                results.append({
                    "intent": intent,
                    "message": result.get("message", ""),
                    "entities": entities
                })

                # XP 추출 (메시지에서 "+XX XP" 패턴 찾기)
                import re
                exp_match = re.search(r'\+(\d+)\s*XP', result.get("message", ""))
                if exp_match:
                    total_exp += int(exp_match.group(1))

        # 결과 조합
        if not results:
            return {
                "success": False,
                "message": "처리할 수 있는 명령이 없었습니다."
            }

        # 메시지 조합
        message_parts = [f"네, {len(results)}가지 기록했어요! 😊\n"]

        for idx, res in enumerate(results, 1):
            emoji = self._get_emoji_for_intent(res["intent"])
            # 메시지에서 첫 줄만 추출 (✓로 시작하는 부분)
            msg_lines = res["message"].split("\n")
            main_msg = msg_lines[0] if msg_lines else res["message"]
            message_parts.append(f"{emoji} {main_msg}")

        if total_exp > 0:
            message_parts.append(f"\n💪 총 +{total_exp} XP 획득! 계속 이렇게 꾸준히 해보세요!")

        final_message = "\n".join(message_parts)

        # LLM으로 대화형 응답 생성
        if self.llm:
            final_message = self._make_conversational(
                user_input=user_input,
                intent="multiple",
                basic_message=final_message
            )

        return {
            "success": True,
            "message": final_message,
            "multiple": True,
            "count": len(results)
        }

    def _get_emoji_for_intent(self, intent: str) -> str:
        """의도별 이모지 반환"""
        emoji_map = {
            "sleep": "💤",
            "workout": "💪",
            "protein": "🍗",
            "weight": "⚖️",
            "task_add": "📝",
            "task_complete": "✅",
            "study": "📚",
            "summary": "📊",
            "progress": "📈"
        }
        return emoji_map.get(intent, "✓")

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

    def _handle_study(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """공부 기록 처리"""
        date = entities.get("date")

        # 시간 또는 분 단위 지원
        hours = entities.get("study_hours")
        minutes = entities.get("study_minutes")

        if hours is not None:
            total_minutes = int(hours * 60)
        elif minutes is not None:
            total_minutes = minutes
        else:
            return {
                "success": False,
                "message": "공부 시간을 알 수 없습니다."
            }

        # TODO: custom_metrics에 study_minutes 저장
        # 현재는 간단히 XP만 부여
        study_hours = total_minutes / 60.0

        # 경험치 부여 (30 XP/시간)
        exp_per_hour = 30
        exp_gained = int(study_hours * exp_per_hour)

        exp_result = self.gamification.award_exp(
            "study",
            study_hours,
            f"공부 {study_hours:.1f}시간"
        )

        message_parts = [f"✓ 공부 기록 완료: {study_hours:.1f}시간 ({total_minutes}분)"]

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

    def _handle_learning_log(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """학습 기록 처리 (새로운 지식/스킬 습득)"""
        title = entities.get("title", "").strip()
        content = entities.get("content", "").strip()
        category = entities.get("category")
        tags = entities.get("tags")
        date = entities.get("date")

        if not title:
            return {
                "success": False,
                "message": "학습 내용을 알 수 없습니다."
            }

        try:
            # 학습 기록 저장
            log_id = self.data_manager.add_learning_log(
                title=title,
                content=content,
                category=category,
                tags=tags,
                date=date
            )

            # 경험치 부여 (학습 기록 1개당 10 XP)
            exp_result = self.gamification.award_exp(
                "learning",
                1,
                f"학습: {title}"
            )

            message_parts = [f"📚 학습 기록 저장: {title}"]
            if content:
                message_parts.append(f"   내용: {content[:50]}{'...' if len(content) > 50 else ''}")

            if exp_result and exp_result.get("success"):
                exp_gained = exp_result.get("exp_gained", 0)
                message_parts.append(f"  +{exp_gained} XP")

                if exp_result.get("level_up"):
                    old_level = exp_result.get("new_level", 1) - 1
                    new_level = exp_result.get("new_level", 1)
                    message_parts.append(f"\n🎉 레벨업! {old_level} → {new_level}")

            return {
                "success": True,
                "message": "\n".join(message_parts),
                "log_id": log_id
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"학습 기록 저장 실패: {e}"
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

    def _handle_chat(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """일반 대화 처리"""
        try:
            # LangChain의 chat 메서드 호출
            user_message = entities.get("message", "안녕하세요!")

            if self.llm and hasattr(self.llm, 'chat'):
                response = self.llm.chat(user_message)
            else:
                # LLM이 없으면 기본 응답
                response = "안녕하세요! 무엇을 도와드릴까요? 😊"

            return {
                "success": True,
                "message": response
            }

        except Exception as e:
            print(f"⚠️ 대화 처리 오류: {e}")
            return {
                "success": True,
                "message": "안녕하세요! 오늘 건강 기록이나 할일을 도와드릴까요?"
            }

    def _make_conversational(
        self,
        user_input: str,
        intent: str,
        basic_message: str
    ) -> str:
        """
        LLM을 사용해 응답을 대화형으로 변환

        Args:
            user_input: 사용자 원본 입력
            intent: 파악된 의도
            basic_message: 기본 응답 메시지

        Returns:
            대화형 응답
        """
        if not self.llm:
            return basic_message

        try:
            system_prompt = """당신은 친근하고 격려하는 헬스케어 어시스턴트입니다.
사용자의 건강 데이터 기록에 대해 따뜻하게 반응하고 격려해주세요.
기본 정보는 그대로 유지하되, 대화형으로 다시 작성하세요.
이모지를 적절히 사용하고, 2-3문장으로 간결하게 작성하세요."""

            prompt = f"""사용자: "{user_input}"

기본 응답: {basic_message}

위 기본 응답을 친근하고 격려하는 톤으로 다시 작성해주세요.
XP, 레벨, 시간/수치 등의 정보는 반드시 그대로 포함하되, 더 대화적으로 표현하세요."""

            conversational = self.llm.generate_response(
                user_input=basic_message,
                context=basic_message,
                tone="friendly"
            )

            return conversational.strip()

        except Exception as e:
            print(f"⚠️ 대화형 응답 생성 실패: {e}")
            return basic_message
