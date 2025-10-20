"""
MemoryAgent - Phase 5A: Personal Memory System
개인 정보 저장 및 검색 (사람, 상호작용, 지식, 회고)
"""
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    """개인 메모리 관리 에이전트"""

    def __init__(self, db_conn: sqlite3.Connection):
        super().__init__("MemoryAgent")
        self.conn = db_conn

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        메시지 처리 - 메모리 관련 작업 수행

        message format:
        {
            "action": "store_person" | "get_person" | "store_interaction" | "store_knowledge" | "query_memory",
            "data": {...}
        }
        """
        action = message.get("action")
        data = message.get("data", {})

        if action == "store_person":
            return self.store_person(data)
        elif action == "get_person":
            return self.get_person(data.get("name"))
        elif action == "store_interaction":
            return self.store_interaction(data)
        elif action == "store_knowledge":
            return self.store_knowledge(data)
        elif action == "store_reflection":
            return self.store_reflection(data)
        elif action == "query_memory":
            return self.query_memory(data.get("query"), data.get("type"))
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    # === People Management ===

    def store_person(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사람 정보 저장 또는 업데이트

        Args:
            data: {
                "name": str (required),
                "relationship_type": str (optional),
                "first_met_date": str (optional),
                "tags": list (optional),
                "personality_notes": str (optional),
                "contact_info": str (optional),
                "importance_score": int (optional, 1-10)
            }
        """
        try:
            name = data.get("name")
            if not name:
                return {"success": False, "error": "Name is required"}

            cursor = self.conn.cursor()

            # Check if person exists
            cursor.execute("SELECT id FROM people WHERE name = ?", (name,))
            existing = cursor.fetchone()

            if existing:
                # Update existing person
                person_id = existing[0]
                update_fields = []
                params = []

                for field in ["relationship_type", "first_met_date", "personality_notes",
                             "contact_info", "importance_score"]:
                    if field in data:
                        update_fields.append(f"{field} = ?")
                        params.append(data[field])

                if "tags" in data:
                    update_fields.append("tags = ?")
                    params.append(json.dumps(data["tags"]))

                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(name)

                    sql = f"UPDATE people SET {', '.join(update_fields)} WHERE name = ?"
                    cursor.execute(sql, params)
                    self.conn.commit()

                return {
                    "success": True,
                    "person_id": person_id,
                    "action": "updated",
                    "message": f"'{name}' 정보가 업데이트되었습니다."
                }
            else:
                # Insert new person
                tags_json = json.dumps(data.get("tags", []))

                cursor.execute("""
                    INSERT INTO people
                    (name, relationship_type, first_met_date, tags, personality_notes,
                     contact_info, importance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    data.get("relationship_type"),
                    data.get("first_met_date"),
                    tags_json,
                    data.get("personality_notes"),
                    data.get("contact_info"),
                    data.get("importance_score", 5)
                ))

                self.conn.commit()
                person_id = cursor.lastrowid

                return {
                    "success": True,
                    "person_id": person_id,
                    "action": "created",
                    "message": f"'{name}'가 기억되었습니다."
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_person(self, name: str) -> Dict[str, Any]:
        """사람 정보 조회"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, name, relationship_type, first_met_date, tags,
                       personality_notes, contact_info, importance_score,
                       created_at, updated_at
                FROM people WHERE name = ?
            """, (name,))

            row = cursor.fetchone()
            if not row:
                return {
                    "success": False,
                    "error": f"'{name}'에 대한 정보가 없습니다."
                }

            person = {
                "id": row[0],
                "name": row[1],
                "relationship_type": row[2],
                "first_met_date": row[3],
                "tags": json.loads(row[4]) if row[4] else [],
                "personality_notes": row[5],
                "contact_info": row[6],
                "importance_score": row[7],
                "created_at": row[8],
                "updated_at": row[9]
            }

            # Get recent interactions
            cursor.execute("""
                SELECT date, type, summary, sentiment
                FROM interactions
                WHERE person_id = ?
                ORDER BY date DESC
                LIMIT 5
            """, (person["id"],))

            interactions = []
            for int_row in cursor.fetchall():
                interactions.append({
                    "date": int_row[0],
                    "type": int_row[1],
                    "summary": int_row[2],
                    "sentiment": int_row[3]
                })

            person["recent_interactions"] = interactions

            return {
                "success": True,
                "person": person
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # === Interaction Logging ===

    def store_interaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        상호작용 로그 저장

        Args:
            data: {
                "person_name": str (required),
                "date": str (optional, defaults to today),
                "type": str (meeting/call/message/other),
                "summary": str (optional),
                "sentiment": str (positive/neutral/negative),
                "topics": list (optional),
                "location": str (optional),
                "duration_min": int (optional)
            }
        """
        try:
            person_name = data.get("person_name")
            if not person_name:
                return {"success": False, "error": "person_name is required"}

            # Get or create person
            person_result = self.get_person(person_name)
            if not person_result["success"]:
                # Create person first
                self.store_person({"name": person_name})
                person_result = self.get_person(person_name)

            person_id = person_result["person"]["id"]

            cursor = self.conn.cursor()
            date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            topics_json = json.dumps(data.get("topics", []))

            cursor.execute("""
                INSERT INTO interactions
                (person_id, date, type, summary, sentiment, topics, location, duration_min)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                date,
                data.get("type", "other"),
                data.get("summary"),
                data.get("sentiment", "neutral"),
                topics_json,
                data.get("location"),
                data.get("duration_min")
            ))

            self.conn.commit()
            interaction_id = cursor.lastrowid

            return {
                "success": True,
                "interaction_id": interaction_id,
                "message": f"'{person_name}'와의 상호작용이 기록되었습니다."
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # === Knowledge Management ===

    def store_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        지식 저장

        Args:
            data: {
                "title": str (required),
                "content": str (required),
                "source": str (optional),
                "category": str (optional),
                "tags": list (optional),
                "learned_date": str (optional, defaults to today),
                "confidence": int (optional, 1-5)
            }
        """
        try:
            title = data.get("title")
            content = data.get("content")

            if not title or not content:
                return {"success": False, "error": "title and content are required"}

            cursor = self.conn.cursor()
            learned_date = data.get("learned_date", datetime.now().strftime("%Y-%m-%d"))
            tags_json = json.dumps(data.get("tags", []))

            cursor.execute("""
                INSERT INTO knowledge_entries
                (title, content, source, category, tags, learned_date, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                content,
                data.get("source"),
                data.get("category"),
                tags_json,
                learned_date,
                data.get("confidence", 3)
            ))

            self.conn.commit()
            knowledge_id = cursor.lastrowid

            return {
                "success": True,
                "knowledge_id": knowledge_id,
                "message": f"'{title}'가 지식 저장소에 추가되었습니다."
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # === Reflection Management ===

    def store_reflection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        회고/성찰 저장

        Args:
            data: {
                "content": str (required),
                "date": str (optional, defaults to today),
                "topic": str (optional),
                "mood": str (optional),
                "insights": list (optional),
                "related_events": list (optional)
            }
        """
        try:
            content = data.get("content")
            if not content:
                return {"success": False, "error": "content is required"}

            cursor = self.conn.cursor()
            date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            insights_json = json.dumps(data.get("insights", []))
            related_json = json.dumps(data.get("related_events", []))

            cursor.execute("""
                INSERT INTO reflections
                (date, topic, content, mood, insights, related_events)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                date,
                data.get("topic"),
                content,
                data.get("mood"),
                insights_json,
                related_json
            ))

            self.conn.commit()
            reflection_id = cursor.lastrowid

            return {
                "success": True,
                "reflection_id": reflection_id,
                "message": "회고가 기록되었습니다."
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # === Memory Query ===

    def query_memory(self, query: str, memory_type: Optional[str] = None) -> Dict[str, Any]:
        """
        메모리 검색 (키워드 기반)

        Args:
            query: 검색 키워드
            memory_type: "people" | "knowledge" | "interactions" | "reflections" | None (all)

        Returns:
            검색 결과
        """
        try:
            results = {}

            if not memory_type or memory_type == "people":
                results["people"] = self._search_people(query)

            if not memory_type or memory_type == "knowledge":
                results["knowledge"] = self._search_knowledge(query)

            if not memory_type or memory_type == "interactions":
                results["interactions"] = self._search_interactions(query)

            if not memory_type or memory_type == "reflections":
                results["reflections"] = self._search_reflections(query)

            return {
                "success": True,
                "query": query,
                "results": results
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search_people(self, query: str) -> List[Dict[str, Any]]:
        """사람 검색"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, relationship_type, tags, personality_notes
            FROM people
            WHERE name LIKE ? OR personality_notes LIKE ? OR tags LIKE ?
            LIMIT 10
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        people = []
        for row in cursor.fetchall():
            people.append({
                "id": row[0],
                "name": row[1],
                "relationship_type": row[2],
                "tags": json.loads(row[3]) if row[3] else [],
                "personality_notes": row[4]
            })
        return people

    def _search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """지식 검색"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, content, source, category, learned_date
            FROM knowledge_entries
            WHERE title LIKE ? OR content LIKE ? OR category LIKE ?
            ORDER BY learned_date DESC
            LIMIT 10
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        knowledge = []
        for row in cursor.fetchall():
            knowledge.append({
                "id": row[0],
                "title": row[1],
                "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                "source": row[3],
                "category": row[4],
                "learned_date": row[5]
            })
        return knowledge

    def _search_interactions(self, query: str) -> List[Dict[str, Any]]:
        """상호작용 검색"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.id, p.name, i.date, i.type, i.summary, i.sentiment
            FROM interactions i
            JOIN people p ON i.person_id = p.id
            WHERE i.summary LIKE ? OR i.topics LIKE ?
            ORDER BY i.date DESC
            LIMIT 10
        """, (f"%{query}%", f"%{query}%"))

        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                "id": row[0],
                "person_name": row[1],
                "date": row[2],
                "type": row[3],
                "summary": row[4],
                "sentiment": row[5]
            })
        return interactions

    def _search_reflections(self, query: str) -> List[Dict[str, Any]]:
        """회고 검색"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, date, topic, content, mood
            FROM reflections
            WHERE topic LIKE ? OR content LIKE ?
            ORDER BY date DESC
            LIMIT 10
        """, (f"%{query}%", f"%{query}%"))

        reflections = []
        for row in cursor.fetchall():
            reflections.append({
                "id": row[0],
                "date": row[1],
                "topic": row[2],
                "content": row[3][:200] + "..." if len(row[3]) > 200 else row[3],
                "mood": row[4]
            })
        return reflections
