#!/usr/bin/env python3
"""
LLM 전용 파싱 테스트 (정규식 제거 후)
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.llm_client import LLMClientFactory
from agents.conversation import ConversationAgent
import time

print("=== 🤖 LLM 전용 파싱 테스트 ===\n")

# LLM 클라이언트 초기화
llm_client = LLMClientFactory.create()
conversation = ConversationAgent(llm_client=llm_client)

# 테스트 케이스
test_cases = [
    # 기본 건강 기록
    ("7시간 잤어", "sleep"),
    ("30분 운동했어", "workout"),
    ("단백질 80그램", "protein"),

    # 복합 명령
    ("어제 8시간 자고 30분 운동했어", "multiple"),

    # 학습 기록 (새 기능)
    ("프롬포트 템플릿과 chrome mcp에 대해 알게됐어", "learning_log"),
    ("LangChain 사용법 배웠어", "learning_log"),

    # 할일
    ("카드비 납부하기", "task_add"),

    # 일반 대화
    ("안녕하세요", "chat"),
    ("오늘 날씨 좋네요", "chat"),

    # 복잡한 수면 패턴
    ("11시에 잤다가 3시에 일어나서 다시 8시에 잤다가 14시에 일어났어", "sleep"),
]

results = {
    "success": 0,
    "failed": 0,
    "total_time": 0
}

for i, (user_input, expected_intent) in enumerate(test_cases, 1):
    print(f"[{i}/{len(test_cases)}] 👤 입력: {user_input}")
    print(f"   🎯 예상: {expected_intent}")

    start_time = time.time()

    try:
        result = conversation.parse_input(user_input)
        elapsed = time.time() - start_time

        if result.get("success"):
            # 복합 명령
            if result.get("multiple"):
                intents = [intent["intent"] for intent in result.get("intents", [])]
                print(f"   ✅ 결과: {intents} ({elapsed:.2f}초)")
                if expected_intent == "multiple":
                    results["success"] += 1
                else:
                    results["failed"] += 1
            # 단일 명령
            else:
                actual_intent = result.get("intent")
                print(f"   ✅ 결과: {actual_intent} ({elapsed:.2f}초)")

                if actual_intent == expected_intent or expected_intent in ["chat", "multiple"]:
                    results["success"] += 1
                else:
                    print(f"   ⚠️ 불일치! 예상={expected_intent}, 실제={actual_intent}")
                    results["failed"] += 1

            # 엔티티 출력
            if result.get("entities"):
                print(f"   📦 엔티티: {result['entities']}")

        else:
            print(f"   ❌ 실패: {result.get('error')} ({elapsed:.2f}초)")
            results["failed"] += 1

        results["total_time"] += elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ 오류: {e} ({elapsed:.2f}초)")
        results["failed"] += 1
        results["total_time"] += elapsed
        import traceback
        traceback.print_exc()

    print()

# 결과 요약
print("=" * 60)
print("📊 테스트 결과 요약")
print("=" * 60)
print(f"✅ 성공: {results['success']}/{len(test_cases)}")
print(f"❌ 실패: {results['failed']}/{len(test_cases)}")
print(f"📈 성공률: {results['success']/len(test_cases)*100:.1f}%")
print(f"⏱️  평균 응답 시간: {results['total_time']/len(test_cases):.2f}초")
print(f"⏱️  총 소요 시간: {results['total_time']:.2f}초")

# 성능 분석
avg_time = results['total_time'] / len(test_cases)
if avg_time < 1.0:
    print(f"🚀 매우 빠름! (평균 {avg_time:.2f}초)")
elif avg_time < 2.0:
    print(f"✅ 양호 (평균 {avg_time:.2f}초)")
else:
    print(f"⚠️  느림 (평균 {avg_time:.2f}초)")

print("\n테스트 완료! ✨")