#!/usr/bin/env python3
"""LLM 파싱 테스트"""

from core.llm_client import LLMClientFactory

print("=== LLM 클라이언트 테스트 ===\n")

try:
    # LLM 클라이언트 생성
    llm = LLMClientFactory.create()

    if llm:
        print("✅ LLM 클라이언트 생성 성공")
        print(f"Provider: Ollama (llama3.2:3b)\n")

        # 테스트 케이스
        test_cases = [
            "새벽3시부터 12시까지 잤어",
            "밤 11시부터 아침 7시까지 수면",
            "1시간 30분 운동했어",
            "오늘 단백질 120g 먹었어"
        ]

        for text in test_cases:
            print(f"입력: {text}")
            result = llm.parse_intent(text)
            print(f"결과: {result}")
            print()

    else:
        print("⚠️  LLM 비활성화됨 (config.yaml 확인)")

except Exception as e:
    print(f"❌ 오류: {str(e)}")
    import traceback
    traceback.print_exc()
