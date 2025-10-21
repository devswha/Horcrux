"""
SimpleLLM - 100% LLM 기반 올인원 시스템
- 파싱: LLM (GPT-4o-mini)
- 실행: DB 헬퍼 메서드
- 응답: LLM (GPT-4o-mini)
"""
import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.database import Database
from core.rag_manager import RAGManager


class SimpleLLM:
    """간단하고 유연한 LLM 기반 시스템"""

    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn

        # 데이터베이스 타입 감지
        self.db_type = 'postgres' if os.getenv("SUPABASE_URL") else 'sqlite'

        # SQL placeholder 설정 (SQLite: ?, PostgreSQL: %s)
        self.placeholder = '%s' if self.db_type == 'postgres' else '?'

        # OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        # LLM 초기화 (파싱 + 응답 생성)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=api_key
        )

        # RAG 초기화 (대화 메모리 + 벡터 검색)
        try:
            db_wrapper = Database()
            db_wrapper.conn = db_conn
            db_wrapper.db_type = self.db_type
            self.rag = RAGManager(db_wrapper)
        except Exception as e:
            print(f"⚠️  RAG 초기화 실패: {e}")
            self.rag = None

    def process(self, user_input: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        사용자 입력 처리

        Args:
            user_input: 사용자 입력
            chat_history: 대화 이력 (선택)

        Returns:
            응답 메시지
        """
        try:
            # 1단계: LLM 파싱
            parsed = self._parse_with_llm(user_input)

            if not parsed.get("success"):
                return parsed.get("error", "처리 중 오류가 발생했습니다.")

            # 2단계: 실행
            results = self._execute(parsed)

            # 3단계: LLM 응답 생성
            response = self._generate_response(user_input, results, parsed)

            # 4단계: 대화 저장 (RAG)
            if self.rag:
                try:
                    self.rag.save_conversation('user', user_input)
                    self.rag.save_conversation('assistant', response)
                except Exception as e:
                    print(f"⚠️  대화 저장 실패: {e}")

            return response

        except Exception as e:
            return f"처리 중 오류 발생: {str(e)}"

    # ========================================
    # 1단계: LLM 파싱
    # ========================================

    def _parse_with_llm(self, user_input: str) -> Dict[str, Any]:
        """LLM으로 입력 파싱"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_hour = datetime.now().hour

        system_prompt = f"""당신은 한국어 건강/할일/메모리 관리 데이터 파서입니다.

**현재 시간**: {current_time} (오후 {current_hour}시)

**역할**: 사용자 입력을 분석하여 의도(intent)와 엔티티를 JSON으로 추출

**가능한 의도**:
- sleep: 수면 기록
- workout: 운동 기록
- study: 공부/학습 시간 기록
- protein: 단백질 섭취
- weight: 체중 기록
- task_add: 할일 추가
- task_complete: 할일 완료
- learning_log: 학습 내용 기록
- remember_person: 사람 정보 저장
- remember_interaction: 상호작용 기록
- remember_knowledge: 지식 저장
- query_memory: 메모리 검색
- reflect: 회고/성찰
- summary: 요약 조회
- chat: 일반 대화

**중요**:
- "지금", "현재", "지금까지"는 위의 현재 시간 기준으로 계산
- 예: "오후 3시부터 지금까지" (현재 {current_hour}시) = {current_hour - 15}시간
- 여러 의도가 있으면 배열로 반환

**응답 형식** (순수 JSON만):
```json
{{"intent": "sleep", "entities": {{"sleep_hours": 7, "date": "2025-10-17"}}, "confidence": 0.95}}
```
또는 복합:
```json
[
  {{"intent": "sleep", "entities": {{"sleep_hours": 7}}}},
  {{"intent": "workout", "entities": {{"workout_minutes": 30}}}}
]
```

**엔티티 키 이름**:
- sleep: sleep_hours (숫자)
- workout: workout_minutes (숫자)
- study: study_hours (숫자)
- protein: protein_grams (숫자)
- weight: weight_kg (숫자)
- task_add: task_title (문자열), due_date (선택), priority (선택, 값: 'low'/'normal'/'high'/'urgent')
- remember_person: name, relationship_type, tags (리스트), notes
- remember_interaction: person_name, type, summary, date
- remember_knowledge: title, content, category
- query_memory: query, type (people/knowledge/interactions)
- learning_log: title, content
- reflect: content, topic, mood

**중요 제약**:
- priority는 반드시 'low', 'normal', 'high', 'urgent' 중 하나
- 약속/이벤트도 task_add로 처리, priority는 생략하거나 'normal' 사용
"""

        user_prompt = f"""사용자 입력: "{user_input}"

이 입력을 분석하여 JSON으로 응답하세요. 순수 JSON만 출력하세요."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            content = response.content.strip()

            # JSON 파싱
            # 마크다운 코드 블록 제거
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            parsed = json.loads(content)

            # 단일 또는 복합 명령 정규화
            if isinstance(parsed, dict):
                return {
                    "success": True,
                    "multiple": False,
                    "intents": [parsed]
                }
            elif isinstance(parsed, list):
                return {
                    "success": True,
                    "multiple": True,
                    "intents": parsed
                }
            else:
                return {"success": False, "error": "잘못된 파싱 결과"}

        except json.JSONDecodeError as e:
            # 일반 대화로 처리
            return {
                "success": True,
                "multiple": False,
                "intents": [{
                    "intent": "chat",
                    "entities": {"message": user_input}
                }]
            }
        except Exception as e:
            return {"success": False, "error": f"파싱 오류: {str(e)}"}

    # ========================================
    # 2단계: 실행 (DB 헬퍼 메서드)
    # ========================================

    def _execute(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """파싱 결과 실행"""
        results = []
        intents = parsed.get("intents", [])

        for intent_data in intents:
            intent = intent_data.get("intent")
            entities = intent_data.get("entities", {})

            try:
                if intent == "sleep":
                    result = self._store_sleep(entities)
                elif intent == "workout":
                    result = self._store_workout(entities)
                elif intent == "study":
                    result = self._store_study(entities)
                elif intent == "protein":
                    result = self._store_protein(entities)
                elif intent == "weight":
                    result = self._store_weight(entities)
                elif intent == "task_add":
                    result = self._add_task(entities)
                elif intent == "task_complete":
                    result = self._complete_task(entities)
                elif intent == "learning_log":
                    result = self._store_learning_log(entities)
                elif intent == "remember_person":
                    result = self._store_person(entities)
                elif intent == "remember_interaction":
                    result = self._store_interaction(entities)
                elif intent == "remember_knowledge":
                    result = self._store_knowledge(entities)
                elif intent == "query_memory":
                    result = self._query_memory(entities)
                elif intent == "reflect":
                    result = self._store_reflection(entities)
                elif intent == "summary":
                    result = self._get_summary(entities)
                elif intent == "chat":
                    result = {"success": True, "message": "대화"}
                else:
                    result = {"success": False, "error": f"알 수 없는 의도: {intent}"}

                results.append({
                    "intent": intent,
                    "result": result
                })

            except Exception as e:
                results.append({
                    "intent": intent,
                    "result": {"success": False, "error": str(e)}
                })

        return results

    # === DB 헬퍼 메서드 ===

    def _store_sleep(self, entities: Dict) -> Dict:
        """수면 기록"""
        hours = entities.get("sleep_hours")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not hours:
            return {"success": False, "error": "수면 시간이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO daily_health (date, sleep_h)
            VALUES ({self.placeholder}, {self.placeholder})
            ON CONFLICT(date) DO UPDATE SET sleep_h = excluded.sleep_h
        """, (date, hours))
        self.conn.commit()

        return {
            "success": True,
            "message": f"수면 {hours}시간 기록",
            "data": {"hours": hours, "date": date, "target": 7}
        }

    def _store_workout(self, entities: Dict) -> Dict:
        """운동 기록"""
        minutes = entities.get("workout_minutes")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not minutes:
            return {"success": False, "error": "운동 시간이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO daily_health (date, workout_min)
            VALUES ({self.placeholder}, {self.placeholder})
            ON CONFLICT(date) DO UPDATE SET workout_min = excluded.workout_min
        """, (date, minutes))
        self.conn.commit()

        return {
            "success": True,
            "message": f"운동 {minutes}분 기록",
            "data": {"minutes": minutes, "date": date, "target": 30}
        }

    def _store_study(self, entities: Dict) -> Dict:
        """공부 기록"""
        hours = entities.get("study_hours")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not hours:
            return {"success": False, "error": "공부 시간이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO custom_metrics (date, metric_name, value, unit, category)
            VALUES ({self.placeholder}, 'study', {self.placeholder}, 'hours', 'learning')
        """, (date, hours))
        self.conn.commit()

        return {
            "success": True,
            "message": f"공부 {hours}시간 기록",
            "data": {"hours": hours, "date": date}
        }

    def _store_protein(self, entities: Dict) -> Dict:
        """단백질 기록"""
        grams = entities.get("protein_grams")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not grams:
            return {"success": False, "error": "단백질 양이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO daily_health (date, protein_g)
            VALUES ({self.placeholder}, {self.placeholder})
            ON CONFLICT(date) DO UPDATE SET protein_g = excluded.protein_g
        """, (date, grams))
        self.conn.commit()

        return {
            "success": True,
            "message": f"단백질 {grams}g 기록",
            "data": {"grams": grams, "date": date, "target": 100}
        }

    def _store_weight(self, entities: Dict) -> Dict:
        """체중 기록"""
        kg = entities.get("weight_kg")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not kg:
            return {"success": False, "error": "체중이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO daily_health (date, weight_kg)
            VALUES ({self.placeholder}, {self.placeholder})
            ON CONFLICT(date) DO UPDATE SET weight_kg = excluded.weight_kg
        """, (date, kg))
        self.conn.commit()

        return {
            "success": True,
            "message": f"체중 {kg}kg 기록",
            "data": {"kg": kg, "date": date}
        }

    def _add_task(self, entities: Dict) -> Dict:
        """할일 추가"""
        title = entities.get("task_title")
        due_date = entities.get("due_date")
        priority = entities.get("priority", "normal")

        if not title:
            return {"success": False, "error": "할일 제목이 필요합니다"}

        # priority 값 검증 및 정규화
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            priority = "normal"  # 유효하지 않으면 기본값

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO tasks (title, due, priority, status)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, 'pending')
        """, (title, due_date, priority))
        self.conn.commit()

        return {
            "success": True,
            "message": f"할일 추가: {title}",
            "data": {"title": title, "due": due_date, "priority": priority}
        }

    def _complete_task(self, entities: Dict) -> Dict:
        """할일 완료"""
        title = entities.get("task_title") or entities.get("task_id")

        if not title:
            return {"success": False, "error": "할일 제목이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT id FROM tasks
            WHERE title LIKE {self.placeholder} AND status = 'pending'
            LIMIT 1
        """, (f"%{title}%",))

        task = cursor.fetchone()
        if not task:
            return {"success": False, "error": f"'{title}' 할일을 찾을 수 없습니다"}

        task_id = task["id"] if self.db_type == 'postgres' else task[0]

        cursor.execute(f"""
            UPDATE tasks
            SET status = 'done', completed_at = CURRENT_TIMESTAMP
            WHERE id = {self.placeholder}
        """, (task_id,))
        self.conn.commit()

        return {
            "success": True,
            "message": f"할일 완료: {title}",
            "data": {"title": title}
        }

    def _store_learning_log(self, entities: Dict) -> Dict:
        """학습 기록"""
        title = entities.get("title")
        content = entities.get("content", "")
        category = entities.get("category")
        date = datetime.now().strftime("%Y-%m-%d")

        if not title:
            return {"success": False, "error": "학습 제목이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO learning_logs (date, title, content, category)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
        """, (date, title, content, category))
        self.conn.commit()

        return {
            "success": True,
            "message": f"학습 기록: {title}",
            "data": {"title": title, "content": content}
        }

    def _store_person(self, entities: Dict) -> Dict:
        """사람 정보 저장"""
        name = entities.get("name")
        relationship_type = entities.get("relationship_type")
        tags = entities.get("tags", [])
        notes = entities.get("notes") or entities.get("personality_notes")

        if not name:
            return {"success": False, "error": "이름이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO people (name, relationship_type, tags, personality_notes)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
            ON CONFLICT(name) DO UPDATE SET
                relationship_type = excluded.relationship_type,
                tags = excluded.tags,
                personality_notes = excluded.personality_notes,
                updated_at = CURRENT_TIMESTAMP
        """, (name, relationship_type, json.dumps(tags), notes))
        self.conn.commit()

        return {
            "success": True,
            "message": f"'{name}' 정보 저장",
            "data": {"name": name, "relationship": relationship_type}
        }

    def _store_interaction(self, entities: Dict) -> Dict:
        """상호작용 기록"""
        person_name = entities.get("person_name")
        interaction_type = entities.get("type", "other")
        summary = entities.get("summary", "")
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not person_name:
            return {"success": False, "error": "사람 이름이 필요합니다"}

        cursor = self.conn.cursor()

        # 사람 ID 조회 또는 생성
        cursor.execute(f"SELECT id FROM people WHERE name = {self.placeholder}", (person_name,))
        person = cursor.fetchone()

        if not person:
            cursor.execute(f"INSERT INTO people (name) VALUES ({self.placeholder})", (person_name,))
            if self.db_type == 'postgres':
                cursor.execute("SELECT lastval()")
                person_id = cursor.fetchone()[0]
            else:
                person_id = cursor.lastrowid
        else:
            person_id = person["id"] if self.db_type == 'postgres' else person[0]

        # 상호작용 기록
        cursor.execute(f"""
            INSERT INTO interactions (person_id, date, type, summary)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
        """, (person_id, date, interaction_type, summary))
        self.conn.commit()

        return {
            "success": True,
            "message": f"'{person_name}'와의 상호작용 기록",
            "data": {"person": person_name, "summary": summary}
        }

    def _store_knowledge(self, entities: Dict) -> Dict:
        """지식 저장"""
        title = entities.get("title")
        content = entities.get("content")
        category = entities.get("category")
        date = datetime.now().strftime("%Y-%m-%d")

        if not title or not content:
            return {"success": False, "error": "제목과 내용이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO knowledge_entries (title, content, category, learned_date)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
        """, (title, content, category, date))
        self.conn.commit()

        return {
            "success": True,
            "message": f"지식 저장: {title}",
            "data": {"title": title, "content": content}
        }

    def _query_memory(self, entities: Dict) -> Dict:
        """메모리 검색 (RAG 기반)"""
        query = entities.get("query")
        memory_type = entities.get("type")

        if not query:
            return {"success": False, "error": "검색어가 필요합니다"}

        cursor = self.conn.cursor()
        results = {}

        # RAG 기반 대화 검색 (최우선)
        if self.rag:
            try:
                conversations = self.rag.search_similar_conversations(query, top_k=5)
                if conversations:
                    results["conversations"] = [
                        {
                            "role": conv["role"],
                            "content": conv["content"][:200],
                            "timestamp": str(conv["timestamp"]),
                            "similarity": round(conv["similarity"], 3)
                        }
                        for conv in conversations
                    ]
            except Exception as e:
                print(f"⚠️  RAG 검색 실패: {e}")

        # 사람 검색
        if not memory_type or memory_type == "people":
            cursor.execute(f"""
                SELECT name, relationship_type, personality_notes
                FROM people
                WHERE name LIKE {self.placeholder} OR personality_notes LIKE {self.placeholder}
                LIMIT 5
            """, (f"%{query}%", f"%{query}%"))

            rows = cursor.fetchall()
            results["people"] = [
                {
                    "name": row["name"] if self.db_type == 'postgres' else row[0],
                    "relationship": row["relationship_type"] if self.db_type == 'postgres' else row[1],
                    "notes": row["personality_notes"] if self.db_type == 'postgres' else row[2]
                }
                for row in rows
            ]

        # 지식 검색
        if not memory_type or memory_type == "knowledge":
            cursor.execute(f"""
                SELECT title, content
                FROM knowledge_entries
                WHERE title LIKE {self.placeholder} OR content LIKE {self.placeholder}
                LIMIT 5
            """, (f"%{query}%", f"%{query}%"))

            rows = cursor.fetchall()
            results["knowledge"] = [
                {
                    "title": row["title"] if self.db_type == 'postgres' else row[0],
                    "content": (row["content"] if self.db_type == 'postgres' else row[1])[:100] + "..."
                              if len(row["content"] if self.db_type == 'postgres' else row[1]) > 100
                              else (row["content"] if self.db_type == 'postgres' else row[1])
                }
                for row in rows
            ]

        return {
            "success": True,
            "message": f"'{query}' 검색 결과",
            "data": results
        }

    def _store_reflection(self, entities: Dict) -> Dict:
        """회고 저장"""
        content = entities.get("content")
        topic = entities.get("topic")
        mood = entities.get("mood")
        date = datetime.now().strftime("%Y-%m-%d")

        if not content:
            return {"success": False, "error": "회고 내용이 필요합니다"}

        cursor = self.conn.cursor()
        cursor.execute(f"""
            INSERT INTO reflections (date, topic, content, mood)
            VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
        """, (date, topic, content, mood))
        self.conn.commit()

        return {
            "success": True,
            "message": "회고 기록 완료",
            "data": {"content": content, "topic": topic}
        }

    def _get_summary(self, entities: Dict) -> Dict:
        """요약 조회"""
        date = entities.get("date", datetime.now().strftime("%Y-%m-%d"))

        cursor = self.conn.cursor()

        # 건강 데이터
        cursor.execute(f"""
            SELECT sleep_h, workout_min, protein_g, weight_kg
            FROM daily_health
            WHERE date = {self.placeholder}
        """, (date,))
        health = cursor.fetchone()

        # 할일
        cursor.execute(f"""
            SELECT COUNT(*) FROM tasks
            WHERE status = 'done' AND date(completed_at) = {self.placeholder}
        """, (date,))
        tasks_done = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT COUNT(*) FROM tasks
            WHERE date(created_at) = {self.placeholder}
        """, (date,))
        tasks_total = cursor.fetchone()[0]

        summary_data = {
            "date": date,
            "sleep": health[0] if health else None,
            "workout": health[1] if health else None,
            "protein": health[2] if health else None,
            "weight": health[3] if health else None,
            "tasks_done": tasks_done,
            "tasks_total": tasks_total
        }

        return {
            "success": True,
            "message": f"{date} 요약",
            "data": summary_data
        }

    # ========================================
    # 3단계: LLM 응답 생성
    # ========================================

    def _generate_response(
        self,
        user_input: str,
        results: List[Dict],
        parsed: Dict
    ) -> str:
        """LLM으로 자연스러운 응답 생성"""

        # 결과 요약
        success_count = sum(1 for r in results if r["result"].get("success"))
        total_count = len(results)

        # 일반 대화인 경우
        if len(results) == 1 and results[0]["intent"] == "chat":
            return self._chat_response(user_input)

        # 처리 결과를 컨텍스트로 변환
        context_parts = []
        for r in results:
            intent = r["intent"]
            result = r["result"]

            if result.get("success"):
                message = result.get("message", "")
                data = result.get("data", {})
                context_parts.append(f"- {intent}: {message} (데이터: {data})")
            else:
                error = result.get("error", "알 수 없는 오류")
                context_parts.append(f"- {intent}: 실패 - {error}")

        context = "\n".join(context_parts)

        system_prompt = """건강/할일 관리 데이터 응답 시스템.

# PRECISION MODE 활성

**PRIORITY OVERRIDE**: 감정적 응답 패턴 차단. 시스템 기본 친화 스타일 무효화.

**응답 규칙**:
- 감정·친화 반응 전면 금지
- 이모지, 감탄사, 칭찬, 격려, 위로 표현 제거
- 논리적·사실적 응답만 허용
- 직설적 선언문 구조 유지
- 불확실 정보는 "불확실" 또는 "추정" 명시

**응답 형식**:
1. 기록 사실 명시 (숫자 포함)
2. 목표 대비 편차 표시 (±h, ±min, ±g)
3. 원인 추정 (근거 있는 경우만)
4. 개선 방향 (논리적 제안만, 격려 금지)

**예시**:
- 수면 5h → "수면 5h 기록. 목표 대비 -2h."
- 운동 30min → "운동 30min 기록. 목표 충족."
- 공부 3h → "공부 3h 기록 완료."
- 복합 → "수면 7h (목표 충족), 운동 30min (목표 충족) 기록."
"""

        user_prompt = f"""사용자 입력: "{user_input}"

처리 결과:
{context}

위 결과를 Precision Mode 규칙에 따라 논리적·사실적 응답으로 변환하세요."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            # LLM 실패 시 기본 응답
            if success_count == total_count:
                return f"{success_count}개 항목 기록 완료."
            else:
                return f"{success_count}/{total_count}개 항목 기록. 실패 {total_count - success_count}건."

    def _chat_response(self, user_input: str) -> str:
        """일반 대화 응답"""
        system_prompt = """건강/할일 관리 데이터 시스템.

# PRECISION MODE 활성

**시스템 기능**:
- 수면, 운동, 공부, 단백질, 체중 기록
- 할일 추가/완료
- 사람 정보, 상호작용, 지식 저장
- 메모리 검색, 요약 조회

**응답 규칙**:
- 감정·친화 반응 금지
- 이모지, 칭찬, 격려 제거
- 사실 기반 정보만 제공
- 직설적 선언문 구조
- 불확실한 경우 "불확실" 명시"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception:
            return "명령 입력 요청. 예: 7시간 잤어, 30분 운동했어"
