#!/usr/bin/env python3
"""
챗봇 기록 기능 전체 테스트
"""
import os
from dotenv import load_dotenv
load_dotenv()

import sqlite3
from datetime import datetime, date
from agents.orchestrator import OrchestratorAgent
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from core.llm_client import LLMClientFactory

# DB 연결
db_conn = sqlite3.connect('lifebot.db')
db_conn.row_factory = sqlite3.Row

# 에이전트 초기화
llm_client = LLMClientFactory.create()
conversation = ConversationAgent(llm_client=llm_client)
data_manager = DataManagerAgent(db_conn)
gamification = GamificationAgent(db_conn)
coaching = CoachingAgent(db_conn)
orchestrator = OrchestratorAgent(
    conversation, data_manager, gamification, coaching, llm_client=llm_client
)

print("=== 🤖 LifeBot 기록 기능 테스트 ===\n")

# 테스트 케이스
test_cases = [
    ("7시간 잤어", "수면 기록"),
    ("30분 운동했어", "운동 기록"),
    ("단백질 80그램 먹었어", "단백질 기록"),
    ("카드비 납부하기", "할일 추가"),
    ("어제 8시간 자고 1시간 운동했어", "복합 명령"),
    ("오늘 요약 보여줘", "요약 조회"),
    ("진행도 확인", "진행도 확인"),
]

def check_db(query: str, params: tuple = ()) -> list:
    """DB 조회 헬퍼"""
    cursor = db_conn.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()

for user_input, description in test_cases:
    print(f"📝 테스트: {description}")
    print(f"👤 입력: {user_input}")

    try:
        # 명령 처리
        result = orchestrator.handle_user_input(user_input)

        # 응답 출력
        if result.get('success'):
            print(f"✅ 성공: {result.get('message', '처리 완료')[:100]}...")

            # DB 확인
            if "잤" in user_input or "수면" in description:
                today = date.today().isoformat()
                sleep_data = check_db(
                    "SELECT sleep_h FROM daily_health WHERE date = ?",
                    (today,)
                )
                if sleep_data:
                    print(f"   💾 DB 기록: 수면 {sleep_data[0]['sleep_h']}시간")

            elif "운동" in user_input:
                today = date.today().isoformat()
                workout_data = check_db(
                    "SELECT workout_min FROM daily_health WHERE date = ?",
                    (today,)
                )
                if workout_data:
                    print(f"   💾 DB 기록: 운동 {workout_data[0]['workout_min']}분")

            elif "단백질" in user_input:
                today = date.today().isoformat()
                protein_data = check_db(
                    "SELECT protein_g FROM daily_health WHERE date = ?",
                    (today,)
                )
                if protein_data:
                    print(f"   💾 DB 기록: 단백질 {protein_data[0]['protein_g']}g")

            elif "납부" in user_input or "할일" in description:
                tasks = check_db(
                    "SELECT id, title, status FROM tasks ORDER BY id DESC LIMIT 1"
                )
                if tasks:
                    print(f"   💾 DB 기록: 할일 #{tasks[0]['id']} '{tasks[0]['title']}' ({tasks[0]['status']})")

        else:
            print(f"❌ 실패: {result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

    print("-" * 60)
    print()

# 현재 상태 확인
print("\n=== 📊 최종 DB 상태 확인 ===\n")

# 오늘 건강 데이터
today = date.today().isoformat()
health = check_db("SELECT * FROM daily_health WHERE date = ?", (today,))
if health:
    h = health[0]
    print(f"오늘의 건강 기록 ({today}):")
    print(f"  💤 수면: {h['sleep_h']}시간")
    print(f"  💪 운동: {h['workout_min']}분")
    print(f"  🍗 단백질: {h['protein_g']}g")
    print(f"  ⚖️ 체중: {h['weight_kg']}kg" if h['weight_kg'] else "  ⚖️ 체중: 미기록")
else:
    print("오늘 건강 기록이 없습니다.")

print()

# 미완료 할일
pending_tasks = check_db(
    "SELECT id, title, priority FROM tasks WHERE status = 'pending' LIMIT 5"
)
if pending_tasks:
    print("📝 미완료 할일:")
    for task in pending_tasks:
        priority_emoji = {"urgent": "🔴", "high": "🟠", "normal": "🟡", "low": "🟢"}
        emoji = priority_emoji.get(task['priority'], "⚪")
        print(f"  {emoji} #{task['id']}: {task['title']}")
else:
    print("📝 미완료 할일이 없습니다.")

print()

# 레벨/XP
progress = check_db("SELECT * FROM user_progress LIMIT 1")
if progress:
    p = progress[0]
    print(f"🎮 레벨/경험치:")
    print(f"  Level {p['level']} ({p['current_exp']} XP)")
    print(f"  총 {p['total_exp']} XP 획득")

db_conn.close()
print("\n테스트 완료! ✨")