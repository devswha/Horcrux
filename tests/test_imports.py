#!/usr/bin/env python3
"""
Import 테스트 - 모든 모듈이 정상적으로 import 되는지 확인
"""
import sys
from pathlib import Path

print("=== Import 테스트 ===\n")

# 1. Core 모듈 테스트
try:
    from core.database import Database
    print("✅ core.database import 성공")
except ImportError as e:
    print(f"❌ core.database import 실패: {e}")

try:
    from core.llm_client import LLMClientFactory
    print("✅ core.llm_client import 성공")
except ImportError as e:
    print(f"❌ core.llm_client import 실패: {e}")

try:
    from core.config import Config
    print("✅ core.config import 성공")
except ImportError as e:
    print(f"❌ core.config import 실패: {e}")

# 2. Agents 모듈 테스트
try:
    from agents.conversation import ConversationAgent
    from agents.data_manager import DataManagerAgent
    from agents.gamification import GamificationAgent
    from agents.coaching import CoachingAgent
    from agents.orchestrator import OrchestratorAgent
    print("✅ 모든 agents import 성공")
except ImportError as e:
    print(f"❌ agents import 실패: {e}")

# 3. Parsers 모듈 테스트
try:
    from parsers.korean_patterns import KoreanPatterns
    from parsers.date_parser import DateParser
    from parsers.number_parser import NumberParser
    print("✅ 모든 parsers import 성공")
except ImportError as e:
    print(f"❌ parsers import 실패: {e}")

# 4. Interfaces 테스트
print("\n--- Interfaces 테스트 ---")

# interfaces 폴더 내부에서 실행될 때
sys.path.insert(0, str(Path("interfaces").resolve().parent))

try:
    exec(open('interfaces/app.py').read(), {'__file__': 'interfaces/app.py', '__name__': '__main__'})
    print("✅ interfaces/app.py import 성공")
except ImportError as e:
    print(f"⚠️ interfaces/app.py import 문제: {e}")
except Exception as e:
    print(f"⚠️ interfaces/app.py 실행 시 다른 오류: {e}")

print("\n모든 import 테스트 완료!")