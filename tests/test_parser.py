#!/usr/bin/env python3
"""파서 테스트"""

from agents.conversation import ConversationAgent

# 테스트
conv = ConversationAgent()

test_inputs = [
    "어제 7시간 잤어",
    "30분 운동했어",
    "카드비 계산해야 해",
    "오늘 요약",
    "레벨"
]

print("=== 파서 테스트 ===\n")

for text in test_inputs:
    result = conv.parse_input(text)
    print(f"입력: {text}")
    print(f"결과: {result}")
    print()
