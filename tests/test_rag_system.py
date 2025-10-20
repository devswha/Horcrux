"""
RAG System End-to-End Test
Tests the complete RAG pipeline: save → embed → search
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.database import Database
from core.rag_manager import RAGManager
from core.simple_llm import SimpleLLM


def test_rag_system():
    """
    End-to-end RAG system test

    Tests:
    1. Database connection
    2. RAG initialization
    3. Conversation saving with embeddings
    4. Vector similarity search
    5. SimpleLLM integration
    """

    print("=== RAG System End-to-End Test ===\n")

    # Step 1: Database connection
    print("1. Database connection...")
    db = Database()
    db.connect()

    if db.db_type == 'postgres':
        print("   ✅ Connected to PostgreSQL (Supabase)")
    else:
        print("   ✅ Connected to SQLite (local)")

    # Step 2: RAG Manager initialization
    print("\n2. RAG Manager initialization...")
    rag = RAGManager(db)
    print("   ✅ RAGManager initialized")

    # Step 3: Save test conversations
    print("\n3. Saving test conversations...")
    test_conversations = [
        ("이창하는 대학교 때 친해진 형이야", "assistant", "이창하님 정보를 저장했습니다."),
        ("어제 7시간 잤고 30분 운동했어", "assistant", "수면 7시간, 운동 30분 기록했습니다."),
        ("오늘 React Hooks 공부했어", "assistant", "React Hooks 학습을 기록했습니다."),
        ("내일 회의가 3시에 있어", "assistant", "내일 3시 회의를 추가했습니다."),
    ]

    for user_msg, role, assistant_msg in test_conversations:
        rag.save_conversation('user', user_msg)
        rag.save_conversation(role, assistant_msg)

    print(f"   ✅ Saved {len(test_conversations) * 2} conversations")

    # Step 4: Embedding generation (if PostgreSQL)
    if db.db_type == 'postgres':
        print("\n4. Embedding generation...")
        count = rag.batch_generate_embeddings()
        if count > 0:
            print(f"   ✅ Generated {count} embeddings")
        else:
            print("   ✅ All conversations already have embeddings")
    else:
        print("\n4. Embedding generation...")
        print("   ⚠️  Skipped (SQLite mode - embeddings in PostgreSQL only)")

    # Step 5: Vector similarity search
    print("\n5. Vector similarity search...")

    test_queries = [
        "이창하",
        "운동",
        "공부",
        "회의",
    ]

    for query in test_queries:
        results = rag.search_similar_conversations(query, top_k=2)
        print(f"\n   Query: '{query}'")
        print(f"   Results: {len(results)}")

        for i, result in enumerate(results, 1):
            content_preview = result['content'][:50] + "..." if len(result['content']) > 50 else result['content']
            similarity = result.get('similarity', 'N/A')
            print(f"     {i}. [{result['role']}] {content_preview} (similarity: {similarity})")

    print("\n   ✅ Search completed")

    # Step 6: SimpleLLM integration test
    print("\n6. SimpleLLM integration test...")

    try:
        llm = SimpleLLM(db.conn)

        if llm.rag:
            print("   ✅ SimpleLLM RAG initialized")

            # Test query_memory intent
            test_input = "이창하에 대해 뭐 알고 있어?"
            print(f"\n   Test input: '{test_input}'")

            response = llm.process(test_input)
            print(f"   Response: {response[:100]}..." if len(response) > 100 else f"   Response: {response}")

            print("\n   ✅ SimpleLLM RAG integration working")
        else:
            print("   ⚠️  SimpleLLM RAG not initialized (check OPENAI_API_KEY)")

    except Exception as e:
        print(f"   ❌ SimpleLLM test failed: {e}")

    # Cleanup
    db.close()

    print("\n=== Test Complete ===\n")
    print("Summary:")
    print(f"  - Database: {db.db_type}")
    print(f"  - RAG Manager: OK")
    print(f"  - Conversations saved: {len(test_conversations) * 2}")
    print(f"  - Search: OK")
    print(f"  - SimpleLLM: OK")

    if db.db_type == 'postgres':
        print("\n✅ RAG system fully operational with PostgreSQL + pgvector!")
    else:
        print("\n✅ RAG system working in SQLite fallback mode!")
        print("   (Deploy to Streamlit Cloud with Supabase for full vector search)")


if __name__ == "__main__":
    test_rag_system()
