#!/usr/bin/env python3
"""
Precision Mode 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from core.database import Database
from core.llm_client import LLMClientFactory
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent

# 초기화
db = Database()
db.connect()

llm_client = LLMClientFactory.create()
conversation = ConversationAgent(llm_client=llm_client)
data_manager = DataManagerAgent(db.conn)
gamification = GamificationAgent(db.conn)
coaching = CoachingAgent(db.conn, llm_client=llm_client)
orchestrator = OrchestratorAgent(
    conversation, data_manager, gamification, coaching, llm_client=llm_client
)

# 테스트
test_inputs = [
    "안녕",
    "어제 5시간 잤어",
    "30분 운동했어",
    "오늘 요약"
]

print("=" * 60)
print("Precision Mode 테스트")
print("=" * 60)

for user_input in test_inputs:
    print(f"\n입력: {user_input}")
    result = orchestrator.handle_user_input(user_input)

    if result.get('success'):
        print(f"응답:\n{result.get('message')}")
    else:
        print(f"오류: {result.get('message')}")
    print("-" * 60)

db.close()
