#!/usr/bin/env python3
"""LLM 실제 테스트"""

import sys
import ollama

print("=== Ollama Direct Test ===\n")

# 직접 Ollama로 테스트
test_input = "어제 11시에 잤다가 새벽 3시에 일어나서 밥먹고 다시 오전 8시쯤 잤다가 2시에 일어났어"

prompt = f"""사용자 입력을 분석하여 JSON으로 응답하세요.

사용자 입력: "{test_input}"

이 입력에서 수면 정보를 추출하세요.
- 첫 번째 수면: 11시 ~ 3시 (몇 시간?)
- 두 번째 수면: 8시 ~ 14시 (몇 시간?)
- 총 수면 시간?

JSON 형식으로 응답:
[{{"intent": "sleep", "entities": {{"sleep_hours": 총시간, "description": "설명"}}, "confidence": 0.95}}]
"""

try:
    response = ollama.chat(
        model='llama3.2:3b',
        messages=[
            {'role': 'system', 'content': 'JSON만 응답하는 파서입니다.'},
            {'role': 'user', 'content': prompt}
        ],
        options={'temperature': 0.3}
    )

    print(f"응답:\n{response['message']['content']}")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50 + "\n")

# LLMClient로도 테스트
print("=== LLMClient Test ===\n")

try:
    from core.llm_client import LLMClientFactory

    llm = LLMClientFactory.create()
    if llm:
        result = llm.parse_intent(test_input)
        print(f"LLM 결과: {result}")
    else:
        print("LLM 클라이언트 생성 실패")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()