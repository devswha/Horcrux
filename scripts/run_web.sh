#!/bin/bash
# Horcrux 웹 대시보드 실행 스크립트

echo "🤖 Horcrux 웹 대시보드 시작..."
echo ""
echo "브라우저에서 http://localhost:8501 을 여세요"
echo ""

streamlit run interfaces/app.py
