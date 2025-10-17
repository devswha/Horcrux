#!/bin/bash
# Ollama 설치 및 설정 스크립트

echo "=== Ollama 설치 ==="
curl -fsSL https://ollama.com/install.sh | sh

echo ""
echo "=== Ollama 서버 시작 ==="
ollama serve &
sleep 5

echo ""
echo "=== llama3.2:3b 모델 다운로드 ==="
ollama pull llama3.2:3b

echo ""
echo "✅ Ollama 설치 완료!"
echo "이제 Horcrux에서 LLM 기능을 사용할 수 있습니다."
