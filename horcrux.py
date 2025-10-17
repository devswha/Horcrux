#!/usr/bin/env python3
"""
Horcrux - Main Entry Point
건강/할일 관리 에이전트 시스템
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """메인 실행 함수"""
    print("🤖 Horcrux 시작 옵션:")
    print("1. 자연어 대화 모드 (추천)")
    print("2. 명령어 모드")
    print("3. 웹 대시보드")
    print("0. 종료")

    choice = input("\n선택하세요 (1-3): ").strip()

    if choice == "1":
        from interfaces.main_natural import main as natural_main
        natural_main()
    elif choice == "2":
        from interfaces.main import main as cli_main
        cli_main()
    elif choice == "3":
        print("\n웹 대시보드를 시작합니다...")
        print("브라우저에서 http://localhost:8501 을 여세요")
        os.system("streamlit run interfaces/app.py")
    elif choice == "0":
        print("종료합니다.")
        sys.exit(0)
    else:
        print("잘못된 선택입니다.")
        main()

if __name__ == "__main__":
    main()