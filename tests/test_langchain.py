#!/usr/bin/env python3
"""LangChain 테스트"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 확인
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your-api-key-here":
    print("⚠️  OpenAI API 키를 .env 파일에 입력해주세요!")
    print("nano .env")
    exit(1)

print("✅ API 키 확인됨")
print(f"키 시작: {api_key[:10]}...")

# LangChain LLM 테스트
from core.langchain_llm import LangChainLLM

llm = LangChainLLM()

test_inputs = [
    "어제 11시에 잤다가 새벽 3시에 일어나서 밥먹고 다시 오전 8시쯤 잤다가 2시에 일어났어 ㅋㅋ",
    "오늘 약속은 저녁 8시반에 영화보는거 있고, 잠은 어제 새벽3시부터 12시까지 잤어",
    "안녕! 오늘 날씨 어때?",
]

print("\n=== LangChain 테스트 ===\n")

for text in test_inputs:
    print(f"입력: {text}")
    result = llm.parse_intent(text)

    if result.get("multiple"):
        print(f"복합 명령: {len(result.get('intents', []))}개")
        for i, intent in enumerate(result.get('intents', []), 1):
            print(f"  {i}. {intent.get('intent')}: {intent.get('entities')}")
    else:
        print(f"단일 명령: {result.get('intent')}")
        print(f"엔티티: {result.get('entities')}")

    # 일반 대화인 경우
    if result.get("intent") == "chat":
        response = llm.chat(text)
        print(f"AI 응답: {response}")

    print()