#!/usr/bin/env python3
"""
채팅 파싱 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.langchain_llm import LangChainLLM

# LLM 초기화
llm = LangChainLLM()

# 테스트 입력들
test_inputs = [
    "안녕",
    "안녕하세요",
    "어떻게 지내?",
    "날씨 좋네요"
]

print("=== LLM 파싱 테스트 ===\n")

for text in test_inputs:
    print(f"입력: {text}")
    result = llm.parse_intent(text)
    print(f"결과: {result}")
    print("-" * 50)
