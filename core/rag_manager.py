"""
RAG (Retrieval-Augmented Generation) Manager
Handles conversation memory storage and retrieval with vector embeddings
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from core.database import Database
from core.embeddings import EmbeddingService


class RAGManager:
    """RAG 시스템 관리자 - 대화 저장 및 검색"""

    def __init__(self, database: Database):
        """
        Initialize RAG manager

        Args:
            database: Connected Database instance
        """
        self.db = database
        self.embedding_service = EmbeddingService()
        self.session_id = str(uuid.uuid4())  # Unique session ID

    def save_conversation(
        self,
        role: str,
        content: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Save conversation with automatic embedding generation

        Args:
            role: 'user' or 'assistant'
            content: Conversation content
            context: Optional context information
            session_id: Optional session ID (uses default if not provided)

        Returns:
            ID of inserted conversation record

        Raises:
            ValueError: If role is invalid or content is empty
        """
        if role not in ['user', 'assistant']:
            raise ValueError("Role must be 'user' or 'assistant'")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        # Use provided session_id or default
        sid = session_id or self.session_id

        # Generate embedding
        try:
            embedding = self.embedding_service.generate_embedding(content)
        except Exception as e:
            print(f"⚠️  Failed to generate embedding: {e}")
            embedding = None

        # Save to database
        cursor = self.db.conn.cursor()

        if self.db.db_type == 'postgres':
            # PostgreSQL with vector type
            if embedding:
                cursor.execute("""
                    INSERT INTO conversation_memory
                    (session_id, role, content, context, embedding, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (sid, role, content, context, embedding, datetime.now()))
            else:
                cursor.execute("""
                    INSERT INTO conversation_memory
                    (session_id, role, content, context, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (sid, role, content, context, datetime.now()))

            result = cursor.fetchone()
            record_id = result['id'] if result else None

        else:
            # SQLite (embedding stored as JSON text for compatibility)
            import json
            embedding_json = json.dumps(embedding) if embedding else None

            cursor.execute("""
                INSERT INTO conversation_memory
                (session_id, role, content, context, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (sid, role, content, context, datetime.now()))

            record_id = cursor.lastrowid

        self.db.conn.commit()
        return record_id

    def search_similar_conversations(
        self,
        query: str,
        top_k: int = 5,
        role_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar conversations using vector similarity

        Args:
            query: Search query text
            top_k: Number of results to return (default: 5)
            role_filter: Optional filter by role ('user' or 'assistant')

        Returns:
            List of conversation records with similarity scores

        Note:
            Only works with PostgreSQL + pgvector. Returns empty list for SQLite.
        """
        if self.db.db_type != 'postgres':
            print("⚠️  Vector search requires PostgreSQL + pgvector. Using fallback text search.")
            return self._fallback_text_search(query, top_k, role_filter)

        # Generate query embedding
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
        except Exception as e:
            print(f"❌ Failed to generate query embedding: {e}")
            return []

        # Vector similarity search using cosine distance
        cursor = self.db.conn.cursor()

        role_clause = "AND role = %s" if role_filter else ""
        role_param = (query_embedding, role_filter, top_k) if role_filter else (query_embedding, top_k)

        cursor.execute(f"""
            SELECT
                id,
                session_id,
                role,
                content,
                context,
                timestamp,
                1 - (embedding <=> %s) AS similarity
            FROM conversation_memory
            WHERE embedding IS NOT NULL
            {role_clause}
            ORDER BY embedding <=> %s
            LIMIT %s
        """, role_param)

        results = cursor.fetchall()

        return [
            {
                'id': row['id'],
                'session_id': row['session_id'],
                'role': row['role'],
                'content': row['content'],
                'context': row['context'],
                'timestamp': row['timestamp'],
                'similarity': float(row['similarity'])
            }
            for row in results
        ]

    def _fallback_text_search(
        self,
        query: str,
        top_k: int = 5,
        role_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Fallback text search for SQLite (no vector support)

        Uses simple SQL LIKE for keyword matching
        """
        cursor = self.db.conn.cursor()

        role_clause = "AND role = ?" if role_filter else ""
        params = (f"%{query}%", role_filter, top_k) if role_filter else (f"%{query}%", top_k)

        cursor.execute(f"""
            SELECT
                id, session_id, role, content, context, timestamp
            FROM conversation_memory
            WHERE content LIKE ?
            {role_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """, params)

        results = cursor.fetchall()

        return [
            {
                'id': dict(row)['id'] if hasattr(row, 'keys') else row[0],
                'session_id': dict(row)['session_id'] if hasattr(row, 'keys') else row[1],
                'role': dict(row)['role'] if hasattr(row, 'keys') else row[2],
                'content': dict(row)['content'] if hasattr(row, 'keys') else row[3],
                'context': dict(row)['context'] if hasattr(row, 'keys') else row[4],
                'timestamp': dict(row)['timestamp'] if hasattr(row, 'keys') else row[5],
                'similarity': 0.5  # Dummy similarity score
            }
            for row in results
        ]

    def batch_generate_embeddings(self) -> int:
        """
        Generate embeddings for all conversations that don't have them yet

        Returns:
            Number of embeddings generated

        Note:
            Only works with PostgreSQL + pgvector
        """
        if self.db.db_type != 'postgres':
            print("⚠️  Batch embedding generation requires PostgreSQL")
            return 0

        # Get conversations without embeddings
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, content
            FROM conversation_memory
            WHERE embedding IS NULL
            ORDER BY timestamp ASC
        """)

        rows = cursor.fetchall()
        if not rows:
            print("✓ All conversations already have embeddings")
            return 0

        print(f"📝 Generating embeddings for {len(rows)} conversations...")

        # Generate embeddings in batch
        contents = [row['content'] for row in rows]
        ids = [row['id'] for row in rows]

        try:
            embeddings = self.embedding_service.generate_embeddings_batch(contents)

            # Update database
            for record_id, embedding in zip(ids, embeddings):
                cursor.execute("""
                    UPDATE conversation_memory
                    SET embedding = %s
                    WHERE id = %s
                """, (embedding, record_id))

            self.db.conn.commit()
            print(f"✅ Generated {len(embeddings)} embeddings")
            return len(embeddings)

        except Exception as e:
            print(f"❌ Failed to generate batch embeddings: {e}")
            self.db.conn.rollback()
            return 0

    def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get conversation history for a session

        Args:
            session_id: Session ID (uses default if not provided)
            limit: Maximum number of messages to return

        Returns:
            List of conversation records ordered by timestamp
        """
        sid = session_id or self.session_id
        cursor = self.db.conn.cursor()

        if self.db.db_type == 'postgres':
            cursor.execute("""
                SELECT id, session_id, role, content, context, timestamp
                FROM conversation_memory
                WHERE session_id = %s
                ORDER BY timestamp ASC
                LIMIT %s
            """, (sid, limit))
        else:
            cursor.execute("""
                SELECT id, session_id, role, content, context, timestamp
                FROM conversation_memory
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (sid, limit))

        results = cursor.fetchall()

        return [
            {
                'id': dict(row)['id'] if hasattr(row, 'keys') else row[0],
                'session_id': dict(row)['session_id'] if hasattr(row, 'keys') else row[1],
                'role': dict(row)['role'] if hasattr(row, 'keys') else row[2],
                'content': dict(row)['content'] if hasattr(row, 'keys') else row[3],
                'context': dict(row)['context'] if hasattr(row, 'keys') else row[4],
                'timestamp': dict(row)['timestamp'] if hasattr(row, 'keys') else row[5]
            }
            for row in results
        ]


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from dotenv import load_dotenv
    load_dotenv()

    # Test RAG manager
    db = Database()
    db.connect()

    # Ensure schema exists
    try:
        db.init_schema()
    except:
        pass

    rag = RAGManager(db)

    print("=== Testing RAG Manager ===\n")

    # Test 1: Save conversations
    print("1. Saving conversations...")
    rag.save_conversation('user', '어제 7시간 잤고 30분 운동했어')
    rag.save_conversation('assistant', '좋습니다! 건강 데이터를 기록했습니다.')
    rag.save_conversation('user', '이창하는 대학교 때 친해진 형이야')
    rag.save_conversation('assistant', '이창하님 정보를 저장했습니다.')
    print("✓ Saved 4 conversations\n")

    # Test 2: Search similar conversations
    print("2. Searching similar conversations...")
    results = rag.search_similar_conversations('운동', top_k=3)
    print(f"Found {len(results)} results for '운동':")
    for r in results:
        print(f"  - [{r['role']}] {r['content'][:50]}... (similarity: {r['similarity']:.3f})")
    print()

    # Test 3: Get conversation history
    print("3. Getting conversation history...")
    history = rag.get_conversation_history(limit=10)
    print(f"Found {len(history)} messages in current session")

    db.close()
