#!/bin/bash
# LifeBot 실행 스크립트

echo "╔═══════════════════════════════════════╗"
echo "║       🤖 LifeBot Health Manager       ║"
echo "║         건강/할일 관리 시스템         ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    exit 1
fi

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "   .env.example을 복사하여 API 키를 설정하세요:"
    echo "   cp .env.example .env"
    echo ""
fi

# 실행 옵션
if [ "$1" = "web" ]; then
    echo "🌐 웹 대시보드 시작..."
    streamlit run interfaces/app.py
elif [ "$1" = "chat" ]; then
    echo "💬 자연어 대화 모드 시작..."
    python3 interfaces/main_natural.py
elif [ "$1" = "cli" ]; then
    echo "⌨️  명령어 모드 시작..."
    python3 interfaces/main.py
elif [ "$1" = "test" ]; then
    echo "🧪 테스트 실행..."
    pytest tests/
else
    # 메뉴 표시
    python3 lifebot.py
fi