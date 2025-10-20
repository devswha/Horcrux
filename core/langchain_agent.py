"""
LangChain Agent + Tools 기반 시스템
LLM이 모든 결정을 내리고 도구를 호출
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage


class HorcruxAgent:
    """LangChain Agent 기반 Horcrux 시스템"""

    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn

        # OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=api_key
        )

        # Tools 정의
        self.tools = self._create_tools()

        # Agent 프롬프트
        self.prompt = self._create_prompt()

        # Agent Executor 생성
        agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )

    def _create_tools(self) -> List[Tool]:
        """사용 가능한 도구들 정의"""

        tools = [
            Tool(
                name="store_sleep",
                func=self._store_sleep,
                description="수면 시간을 기록합니다. 입력: sleep_hours (시간), date (선택, 기본값 오늘). 예: store_sleep(7, '2025-10-17')"
            ),
            Tool(
                name="store_workout",
                func=self._store_workout,
                description="운동 시간을 기록합니다. 입력: workout_minutes (분), date (선택, 기본값 오늘). 예: store_workout(30, '2025-10-17')"
            ),
            Tool(
                name="store_study",
                func=self._store_study,
                description="공부/학습 시간을 기록합니다. 입력: study_hours (시간), date (선택, 기본값 오늘). 예: store_study(3, '2025-10-17')"
            ),
            Tool(
                name="store_protein",
                func=self._store_protein,
                description="단백질 섭취량을 기록합니다. 입력: protein_grams (그램), date (선택, 기본값 오늘). 예: store_protein(100, '2025-10-17')"
            ),
            Tool(
                name="store_weight",
                func=self._store_weight,
                description="체중을 기록합니다. 입력: weight_kg (킬로그램), date (선택, 기본값 오늘). 예: store_weight(70.5, '2025-10-17')"
            ),
            Tool(
                name="add_task",
                func=self._add_task,
                description="할일을 추가합니다. 입력: title (제목), due_date (선택, 마감일), priority (선택, low/normal/high/urgent). 예: add_task('프로젝트 완료', '2025-10-20', 'high')"
            ),
            Tool(
                name="complete_task",
                func=self._complete_task,
                description="할일을 완료 처리합니다. 입력: task_id (할일 ID) 또는 title (제목). 예: complete_task('프로젝트 완료')"
            ),
            Tool(
                name="store_person",
                func=self._store_person,
                description="사람 정보를 저장합니다. 입력: name (이름), relationship_type (관계), tags (특성 리스트), notes (메모). 예: store_person('민수', '친구', ['개발자', '커피'], '커피를 좋아함')"
            ),
            Tool(
                name="store_interaction",
                func=self._store_interaction,
                description="사람과의 상호작용을 기록합니다. 입력: person_name (이름), type (meeting/call/message), summary (요약), date (선택). 예: store_interaction('민수', 'meeting', '카페에서 커피', '2025-10-17')"
            ),
            Tool(
                name="store_knowledge",
                func=self._store_knowledge,
                description="새로운 지식을 저장합니다. 입력: title (제목), content (내용), category (선택, 카테고리). 예: store_knowledge('React Hooks', 'useState와 useEffect 사용법', '프로그래밍')"
            ),
            Tool(
                name="store_learning_log",
                func=self._store_learning_log,
                description="학습 기록을 저장합니다. 입력: title (제목), content (내용), category (선택). 예: store_learning_log('프롬프트 엔지니어링', '프롬프트 최적화 방법 학습')"
            ),
            Tool(
                name="query_memory",
                func=self._query_memory,
                description="저장된 정보를 검색합니다. 입력: query (검색어), type (선택, people/knowledge/interactions). 예: query_memory('민수', 'people')"
            ),
            Tool(
                name="get_summary",
                func=self._get_summary,
                description="특정 기간의 요약을 조회합니다. 입력: date (날짜, 기본값 오늘). 예: get_summary('2025-10-17')"
            ),
            Tool(
                name="get_progress",
                func=self._get_progress,
                description="현재 레벨과 경험치를 조회합니다. 입력: 없음. 예: get_progress()"
            ),
        ]

        return tools

    def _create_prompt(self) -> ChatPromptTemplate:
        """Agent 프롬프트 생성"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_hour = datetime.now().hour

        system_message = f"""당신은 Horcrux - 건강/할일 관리 시스템의 AI 어시스턴트입니다.

**현재 시간**: {current_time} (오후 {current_hour}시)

**당신의 역할**:
1. 사용자의 한국어 입력을 이해
2. 적절한 도구(Tool)를 선택하여 실행
3. 실행 결과를 바탕으로 명확하고 유용한 응답 생성

**중요 규칙**:
- "지금", "현재", "지금까지"는 위의 현재 시간을 기준으로 계산
- 시간 계산 예: "오후 3시부터 지금까지" (현재 {current_hour}시) = {current_hour - 15}시간
- 여러 도구를 순차적으로 사용 가능 (예: 수면 기록 → 경험치 확인)
- 불확실하면 사용자에게 명확화 질문
- 응답은 간결하고 정확하게 (이모지 사용 가능)

**응답 스타일**:
- 저장 성공: "✓ [항목] 기록 완료"
- 검색 결과: 간결한 리스트 형식
- 오류 발생: 명확한 오류 메시지와 해결 방법 제시"""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        return prompt

    def process(self, user_input: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """사용자 입력 처리"""
        try:
            # Agent 실행
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history or []
            })

            return {
                "success": True,
                "message": result["output"]
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"처리 중 오류 발생: {str(e)}"
            }

    # === Tool 구현 ===

    def _store_sleep(self, params: str) -> str:
        """수면 기록 도구"""
        try:
            # 파라미터 파싱 (간단한 방식)
            parts = params.split(',')
            sleep_hours = float(parts[0].strip())
            date = parts[1].strip() if len(parts) > 1 else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO daily_health (date, sleep_h)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET sleep_h = excluded.sleep_h
            """, (date, sleep_hours))
            self.conn.commit()

            # XP 계산
            exp = 15 if sleep_hours >= 7 else 0
            if exp > 0:
                cursor.execute("""
                    INSERT INTO exp_logs (date, action_type, exp_gained, description)
                    VALUES (?, 'sleep_goal', ?, ?)
                """, (date, exp, f"수면 {sleep_hours}시간"))
                self.conn.commit()

            return f"✓ 수면 {sleep_hours}시간 기록 완료 ({date})" + (f" +{exp} XP" if exp > 0 else "")

        except Exception as e:
            return f"❌ 수면 기록 실패: {str(e)}"

    def _store_workout(self, params: str) -> str:
        """운동 기록 도구"""
        try:
            parts = params.split(',')
            workout_minutes = int(parts[0].strip())
            date = parts[1].strip() if len(parts) > 1 else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO daily_health (date, workout_min)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET workout_min = excluded.workout_min
            """, (date, workout_minutes))
            self.conn.commit()

            # XP 계산
            exp = 10 if workout_minutes >= 30 else 5 if workout_minutes >= 15 else 0
            if exp > 0:
                cursor.execute("""
                    INSERT INTO exp_logs (date, action_type, exp_gained, description)
                    VALUES (?, 'workout', ?, ?)
                """, (date, exp, f"운동 {workout_minutes}분"))
                self.conn.commit()

            return f"✓ 운동 {workout_minutes}분 기록 완료 ({date})" + (f" +{exp} XP" if exp > 0 else "")

        except Exception as e:
            return f"❌ 운동 기록 실패: {str(e)}"

    def _store_study(self, params: str) -> str:
        """공부 기록 도구"""
        try:
            parts = params.split(',')
            study_hours = float(parts[0].strip())
            date = parts[1].strip() if len(parts) > 1 else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO custom_metrics (date, metric_name, value, unit, category)
                VALUES (?, 'study', ?, 'hours', 'learning')
            """, (date, study_hours))
            self.conn.commit()

            # XP 계산 (시간당 30 XP)
            exp = int(study_hours * 30)
            cursor.execute("""
                INSERT INTO exp_logs (date, action_type, exp_gained, description)
                VALUES (?, 'study', ?, ?)
            """, (date, exp, f"공부 {study_hours}시간"))
            self.conn.commit()

            return f"✓ 공부 {study_hours}시간 기록 완료 ({date}) +{exp} XP"

        except Exception as e:
            return f"❌ 공부 기록 실패: {str(e)}"

    def _store_protein(self, params: str) -> str:
        """단백질 기록 도구"""
        try:
            parts = params.split(',')
            protein_grams = float(parts[0].strip())
            date = parts[1].strip() if len(parts) > 1 else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO daily_health (date, protein_g)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET protein_g = excluded.protein_g
            """, (date, protein_grams))
            self.conn.commit()

            exp = 10 if protein_grams >= 100 else 0
            if exp > 0:
                cursor.execute("""
                    INSERT INTO exp_logs (date, action_type, exp_gained, description)
                    VALUES (?, 'protein_goal', ?, ?)
                """, (date, exp, f"단백질 {protein_grams}g"))
                self.conn.commit()

            return f"✓ 단백질 {protein_grams}g 기록 완료 ({date})" + (f" +{exp} XP" if exp > 0 else "")

        except Exception as e:
            return f"❌ 단백질 기록 실패: {str(e)}"

    def _store_weight(self, params: str) -> str:
        """체중 기록 도구"""
        try:
            parts = params.split(',')
            weight_kg = float(parts[0].strip())
            date = parts[1].strip() if len(parts) > 1 else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO daily_health (date, weight_kg)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET weight_kg = excluded.weight_kg
            """, (date, weight_kg))
            self.conn.commit()

            return f"✓ 체중 {weight_kg}kg 기록 완료 ({date})"

        except Exception as e:
            return f"❌ 체중 기록 실패: {str(e)}"

    def _add_task(self, params: str) -> str:
        """할일 추가 도구"""
        try:
            parts = [p.strip() for p in params.split(',')]
            title = parts[0]
            due_date = parts[1] if len(parts) > 1 else None
            priority = parts[2] if len(parts) > 2 else 'normal'

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (title, due, priority, status)
                VALUES (?, ?, ?, 'pending')
            """, (title, due_date, priority))
            self.conn.commit()

            return f"✓ 할일 추가: {title}" + (f" (마감: {due_date})" if due_date else "")

        except Exception as e:
            return f"❌ 할일 추가 실패: {str(e)}"

    def _complete_task(self, params: str) -> str:
        """할일 완료 도구"""
        try:
            title_or_id = params.strip()

            cursor = self.conn.cursor()

            # 제목으로 검색
            cursor.execute("SELECT id, priority FROM tasks WHERE title LIKE ? AND status = 'pending'",
                         (f"%{title_or_id}%",))
            task = cursor.fetchone()

            if not task:
                return f"❌ '{title_or_id}' 할일을 찾을 수 없습니다"

            task_id, priority = task

            # 완료 처리
            cursor.execute("""
                UPDATE tasks SET status = 'done', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (task_id,))
            self.conn.commit()

            # XP 계산
            priority_multiplier = {'low': 0.5, 'normal': 1.0, 'high': 1.5, 'urgent': 2.5}
            exp = int(20 * priority_multiplier.get(priority, 1.0))

            cursor.execute("""
                INSERT INTO exp_logs (date, action_type, exp_gained, description)
                VALUES (date('now'), 'task_complete', ?, ?)
            """, (exp, title_or_id))
            self.conn.commit()

            return f"✓ 할일 완료: {title_or_id} +{exp} XP"

        except Exception as e:
            return f"❌ 할일 완료 실패: {str(e)}"

    def _store_person(self, params: str) -> str:
        """사람 정보 저장 도구"""
        try:
            parts = [p.strip() for p in params.split(',')]
            name = parts[0]
            relationship_type = parts[1] if len(parts) > 1 else None
            tags_str = parts[2] if len(parts) > 2 else "[]"
            notes = parts[3] if len(parts) > 3 else None

            import json
            tags = json.dumps(eval(tags_str) if tags_str.startswith('[') else [tags_str])

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO people (name, relationship_type, tags, personality_notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    relationship_type = excluded.relationship_type,
                    tags = excluded.tags,
                    personality_notes = excluded.personality_notes
            """, (name, relationship_type, tags, notes))
            self.conn.commit()

            return f"✓ '{name}' 정보 저장 완료"

        except Exception as e:
            return f"❌ 사람 정보 저장 실패: {str(e)}"

    def _store_interaction(self, params: str) -> str:
        """상호작용 기록 도구"""
        try:
            parts = [p.strip() for p in params.split(',')]
            person_name = parts[0]
            interaction_type = parts[1] if len(parts) > 1 else 'other'
            summary = parts[2] if len(parts) > 2 else ''
            date = parts[3] if len(parts) > 3 else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()

            # 사람 ID 조회 또는 생성
            cursor.execute("SELECT id FROM people WHERE name = ?", (person_name,))
            person = cursor.fetchone()

            if not person:
                cursor.execute("INSERT INTO people (name) VALUES (?)", (person_name,))
                person_id = cursor.lastrowid
            else:
                person_id = person[0]

            # 상호작용 기록
            cursor.execute("""
                INSERT INTO interactions (person_id, date, type, summary)
                VALUES (?, ?, ?, ?)
            """, (person_id, date, interaction_type, summary))
            self.conn.commit()

            return f"✓ '{person_name}'와의 상호작용 기록 완료"

        except Exception as e:
            return f"❌ 상호작용 기록 실패: {str(e)}"

    def _store_knowledge(self, params: str) -> str:
        """지식 저장 도구"""
        try:
            parts = [p.strip() for p in params.split(',')]
            title = parts[0]
            content = parts[1]
            category = parts[2] if len(parts) > 2 else None
            date = datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_entries (title, content, category, learned_date)
                VALUES (?, ?, ?, ?)
            """, (title, content, category, date))
            self.conn.commit()

            return f"✓ 지식 저장: {title}"

        except Exception as e:
            return f"❌ 지식 저장 실패: {str(e)}"

    def _store_learning_log(self, params: str) -> str:
        """학습 기록 도구"""
        try:
            parts = [p.strip() for p in params.split(',')]
            title = parts[0]
            content = parts[1] if len(parts) > 1 else ''
            category = parts[2] if len(parts) > 2 else None
            date = datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO learning_logs (date, title, content, category)
                VALUES (?, ?, ?, ?)
            """, (date, title, content, category))
            self.conn.commit()

            # XP 계산
            exp = 20
            cursor.execute("""
                INSERT INTO exp_logs (date, action_type, exp_gained, description)
                VALUES (?, 'learning', ?, ?)
            """, (date, exp, title))
            self.conn.commit()

            return f"✓ 학습 기록: {title} +{exp} XP"

        except Exception as e:
            return f"❌ 학습 기록 실패: {str(e)}"

    def _query_memory(self, params: str) -> str:
        """메모리 검색 도구"""
        try:
            parts = [p.strip() for p in params.split(',')]
            query = parts[0]
            memory_type = parts[1] if len(parts) > 1 else None

            cursor = self.conn.cursor()
            results = []

            # 사람 검색
            if not memory_type or memory_type == 'people':
                cursor.execute("""
                    SELECT name, relationship_type, personality_notes
                    FROM people
                    WHERE name LIKE ? OR personality_notes LIKE ?
                    LIMIT 5
                """, (f"%{query}%", f"%{query}%"))
                people = cursor.fetchall()
                if people:
                    results.append("👥 사람:")
                    for p in people:
                        results.append(f"  - {p[0]}" + (f" ({p[1]})" if p[1] else "") + (f": {p[2]}" if p[2] else ""))

            # 지식 검색
            if not memory_type or memory_type == 'knowledge':
                cursor.execute("""
                    SELECT title, content
                    FROM knowledge_entries
                    WHERE title LIKE ? OR content LIKE ?
                    LIMIT 5
                """, (f"%{query}%", f"%{query}%"))
                knowledge = cursor.fetchall()
                if knowledge:
                    results.append("\n📚 지식:")
                    for k in knowledge:
                        content_preview = k[1][:50] + "..." if len(k[1]) > 50 else k[1]
                        results.append(f"  - {k[0]}: {content_preview}")

            if not results:
                return f"'{query}'에 대한 검색 결과가 없습니다"

            return "\n".join(results)

        except Exception as e:
            return f"❌ 검색 실패: {str(e)}"

    def _get_summary(self, params: str) -> str:
        """요약 조회 도구"""
        try:
            date = params.strip() if params.strip() else datetime.now().strftime("%Y-%m-%d")

            cursor = self.conn.cursor()

            # 건강 데이터
            cursor.execute("""
                SELECT sleep_h, workout_min, protein_g, weight_kg
                FROM daily_health
                WHERE date = ?
            """, (date,))
            health = cursor.fetchone()

            # 할일
            cursor.execute("""
                SELECT COUNT(*) as done,
                       (SELECT COUNT(*) FROM tasks WHERE date(created_at) = ?) as total
                FROM tasks
                WHERE status = 'done' AND date(completed_at) = ?
            """, (date, date))
            tasks = cursor.fetchone()

            # XP
            cursor.execute("""
                SELECT SUM(exp_gained) FROM exp_logs WHERE date = ?
            """, (date,))
            exp = cursor.fetchone()[0] or 0

            summary = [f"📊 {date} 요약\n"]

            if health:
                if health[0]: summary.append(f"💤 수면: {health[0]}시간")
                if health[1]: summary.append(f"💪 운동: {health[1]}분")
                if health[2]: summary.append(f"🍗 단백질: {health[2]}g")
                if health[3]: summary.append(f"⚖️ 체중: {health[3]}kg")

            if tasks:
                summary.append(f"📝 할일: {tasks[0]}/{tasks[1]} 완료")

            summary.append(f"⭐ 획득 XP: {exp}")

            return "\n".join(summary)

        except Exception as e:
            return f"❌ 요약 조회 실패: {str(e)}"

    def _get_progress(self, params: str) -> str:
        """진행도 조회 도구"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT level, current_exp, total_exp FROM user_progress")
            progress = cursor.fetchone()

            if not progress:
                return "진행도 정보가 없습니다"

            level, current_exp, total_exp = progress
            next_level_exp = 100 * level * (level + 1) // 2

            return f"📊 Level {level}\n⭐ {current_exp}/{next_level_exp} XP\n💎 총 {total_exp} XP 획득"

        except Exception as e:
            return f"❌ 진행도 조회 실패: {str(e)}"
