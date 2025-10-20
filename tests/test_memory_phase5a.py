#!/usr/bin/env python3
"""
Phase 5A Memory System - Integration Test
Tests memory storage and retrieval through the full agent pipeline
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.database import Database
from core.llm_client import LLMClientFactory
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.memory import MemoryAgent
from agents.orchestrator import OrchestratorAgent


def test_memory_system():
    """Test Phase 5A memory features"""

    print("=== Phase 5A Memory System Test ===\n")

    # Initialize database
    db = Database("test_memory.db")
    db.connect()
    db.init_schema()
    db.seed_initial_data()

    # Initialize agents
    llm_client = LLMClientFactory.create()
    conversation = ConversationAgent(llm_client=llm_client)
    data_manager = DataManagerAgent(db.conn)
    gamification = GamificationAgent(db.conn)
    coaching = CoachingAgent(db.conn)
    memory_agent = MemoryAgent(db.conn)

    orchestrator = OrchestratorAgent(
        conversation, data_manager, gamification, coaching,
        memory_agent=memory_agent,
        llm_client=llm_client
    )

    # Test cases
    test_cases = [
        {
            "name": "Store Person",
            "input": "민수는 내 대학 친구야. 개발자고 커피를 좋아해",
            "expected_intent": "remember_person"
        },
        {
            "name": "Store Interaction",
            "input": "어제 지수랑 카페에서 커피 마셨어",
            "expected_intent": "remember_interaction"
        },
        {
            "name": "Store Knowledge",
            "input": "React의 useEffect는 사이드 이펙트를 처리하는 훅이야",
            "expected_intent": "remember_knowledge"
        },
        {
            "name": "Query Memory (Person)",
            "input": "민수에 대해 뭐 알고 있어?",
            "expected_intent": "query_memory"
        },
        {
            "name": "Store Reflection",
            "input": "오늘 개발에 대해 많이 배웠다. 특히 프롬프트 엔지니어링이 중요하다는 걸 깨달았어",
            "expected_intent": "reflect"
        },
    ]

    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"입력: {test['input']}")

        try:
            result = orchestrator.handle_user_input(test['input'])
            print(f"\n결과:")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Message: {result.get('message', 'No message')}")

            # Check if response contains expected data
            if result.get('success'):
                print(f"  ✅ {test['name']} 성공!")
            else:
                print(f"  ❌ {test['name']} 실패: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

    # Verify database
    print(f"\n{'='*60}")
    print("Database Verification")
    print(f"{'='*60}")

    cursor = db.conn.cursor()

    # Check people table
    cursor.execute("SELECT COUNT(*) FROM people")
    people_count = cursor.fetchone()[0]
    print(f"People stored: {people_count}")

    # Check interactions table
    cursor.execute("SELECT COUNT(*) FROM interactions")
    interactions_count = cursor.fetchone()[0]
    print(f"Interactions stored: {interactions_count}")

    # Check knowledge_entries table
    cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
    knowledge_count = cursor.fetchone()[0]
    print(f"Knowledge entries stored: {knowledge_count}")

    # Check reflections table
    cursor.execute("SELECT COUNT(*) FROM reflections")
    reflections_count = cursor.fetchone()[0]
    print(f"Reflections stored: {reflections_count}")

    # Detailed checks
    if people_count > 0:
        print("\n인물 정보:")
        cursor.execute("SELECT name, relationship_type, tags FROM people")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} (tags: {row[2]})")

    if knowledge_count > 0:
        print("\n지식 저장소:")
        cursor.execute("SELECT title, content FROM knowledge_entries")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1][:50]}...")

    # Cleanup
    db.close()

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_memory_system()
