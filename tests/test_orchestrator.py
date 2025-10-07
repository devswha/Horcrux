#!/usr/bin/env python3
"""Orchestrator 테스트"""

from core.database import Database
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent

# DB 연결
db = Database()
db.connect()

# 에이전트 초기화
conversation = ConversationAgent()
data_manager = DataManagerAgent(db.conn)
gamification = GamificationAgent(db.conn)
coaching = CoachingAgent(db.conn)
orchestrator = OrchestratorAgent(conversation, data_manager, gamification, coaching)

# 테스트
test_inputs = [
    "어제 7시간 잤어",
    "30분 운동했어",
    "카드비 계산해야 해",
]

print("=== Orchestrator 테스트 ===\n")

for text in test_inputs:
    result = orchestrator.handle_user_input(text)
    print(f"입력: {text}")
    print(f"결과: {result}")
    print(f"메시지: {result.get('message')}")
    print()
