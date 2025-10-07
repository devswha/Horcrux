#!/usr/bin/env python3
"""웹 챗봇 기능 테스트"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from agents.orchestrator import OrchestratorAgent
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from core.llm_client import LLMClientFactory
import sqlite3

# DB 연결
db_conn = sqlite3.connect('lifebot.db')
db_conn.row_factory = sqlite3.Row  # dictionary-like access 활성화

# 에이전트 초기화
llm_client = LLMClientFactory.create()
conversation = ConversationAgent(llm_client=llm_client)
data_manager = DataManagerAgent(db_conn)
gamification = GamificationAgent(db_conn)
coaching = CoachingAgent(db_conn)
orchestrator = OrchestratorAgent(
    conversation, data_manager, gamification, coaching, llm_client=llm_client
)

# 테스트 케이스
test_inputs = [
    "안녕",
    "안녕하세요",
    "오늘 날씨 어때?",
    "7시간 잤어",
    "어제 11시에 잤다가 새벽 3시에 일어나서 밥먹고 다시 오전 8시쯤 잤다가 2시에 일어났어",
]

print("=== 웹 챗봇 테스트 ===\n")

for user_input in test_inputs:
    print(f"👤 사용자: {user_input}")

    try:
        result = orchestrator.handle_user_input(user_input)
        response = result.get('message', '처리 완료')
        print(f"🤖 봇: {response}")

        if result.get('success'):
            print(f"✅ 성공: {result.get('intent', 'unknown')}")
        else:
            print(f"❌ 실패: {result.get('error', 'Unknown error')}")

    except Exception as e:
        import traceback
        print(f"❌ 오류: {e}")
        traceback.print_exc()

    print("-" * 50)