#!/usr/bin/env python3
"""
할일 파싱 테스트
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.langchain_llm import LangChainLLM
from agents.conversation import ConversationAgent
from agents.orchestrator import OrchestratorAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from core.database import Database

print("=== 🧪 할일 파싱 및 처리 테스트 ===\n")

# 초기화
db = Database(db_path=":memory:")  # 인메모리 DB
data_manager = DataManagerAgent(db.connect())
gamification = GamificationAgent(db.connect())
coaching = CoachingAgent(db.connect())
llm_client = LangChainLLM()
conversation = ConversationAgent(llm_client=llm_client)
orchestrator = OrchestratorAgent(
    conversation_agent=conversation,
    data_manager=data_manager,
    gamification=gamification,
    coaching=coaching,
    llm_client=llm_client
)

# 테스트 케이스
test_cases = [
    "내일 일본여행갈때 짐 챙겨야해",
    "카드비 납부하기",
    "프로젝트 문서 작성해야 함",
    "내일까지 보고서 제출",
]

print("1️⃣ LLM 파싱 테스트\n")
for i, user_input in enumerate(test_cases, 1):
    print(f"[{i}] 입력: {user_input}")

    # 파싱
    parse_result = conversation.parse_input(user_input)
    print(f"   파싱: {parse_result}")

    if parse_result.get("success"):
        intent = parse_result.get("intent")
        entities = parse_result.get("entities", {})
        print(f"   ✅ Intent: {intent}")
        print(f"   📦 Entities: {entities}")

        # task_title 키 확인
        if intent == "task_add":
            if "task_title" in entities:
                print(f"   ✅ task_title 키 존재")
            else:
                print(f"   ❌ task_title 키 없음!")
    else:
        print(f"   ❌ 파싱 실패")

    print()

print("\n2️⃣ Orchestrator 처리 테스트\n")
for i, user_input in enumerate(test_cases, 1):
    print(f"[{i}] 입력: {user_input}")

    # Orchestrator 처리
    result = orchestrator.handle_user_input(user_input)

    if result.get("success"):
        print(f"   ✅ 성공: {result.get('message')}")
    else:
        print(f"   ❌ 실패: {result.get('message')}")

    print()

print("\n3️⃣ 저장된 할일 확인\n")
tasks = data_manager.list_tasks(status="pending")
print(f"총 {len(tasks)}개 할일:")
for task in tasks:
    print(f"  - [{task['id']}] {task['title']}")

print("\n✅ 테스트 완료!")
