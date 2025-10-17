#!/usr/bin/env python3
"""
Horcrux 웹 대시보드 (Streamlit)
"""
import os
import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가 (import 경로 해결)
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# .env 파일 자동 로드
load_dotenv()

import streamlit as st
import pandas as pd
from datetime import datetime
from core.database import Database
from core.llm_client import LLMClientFactory
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent


# 페이지 설정
st.set_page_config(
    page_title="Horcrux - 건강/할일 관리",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'db' not in st.session_state:
    st.session_state.db = Database()
    st.session_state.db.connect()

    # 데이터베이스 스키마 확인 및 초기화
    try:
        cursor = st.session_state.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_progress'")
        if not cursor.fetchone():
            # 테이블이 없으면 스키마 초기화
            st.session_state.db.init_schema()
            st.session_state.db.seed_initial_data()
    except Exception as e:
        st.error(f"데이터베이스 초기화 중 오류: {e}")

if 'orchestrator' not in st.session_state:
    # LLM 클라이언트 초기화
    try:
        llm_client = LLMClientFactory.create()
        if llm_client:
            st.session_state.llm_status = "✅ LLM 활성화"
        else:
            st.session_state.llm_status = "⚠️ LLM 비활성화"
    except Exception as e:
        llm_client = None
        st.session_state.llm_status = f"⚠️ LLM 오류: {str(e)}"

    # 에이전트 초기화 (LLM 클라이언트 전달)
    conversation = ConversationAgent(llm_client=llm_client)
    data_manager = DataManagerAgent(st.session_state.db.conn)
    gamification = GamificationAgent(st.session_state.db.conn)
    coaching = CoachingAgent(st.session_state.db.conn)
    st.session_state.orchestrator = OrchestratorAgent(
        conversation, data_manager, gamification, coaching, llm_client=llm_client
    )
    st.session_state.data_manager = data_manager
    st.session_state.gamification = gamification

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# 사이드바
with st.sidebar:
    st.title("🤖 Horcrux")
    st.caption("건강/할일 관리 시스템")
    st.markdown("---")

    # LLM 상태 표시
    if 'llm_status' in st.session_state:
        st.info(st.session_state.llm_status)

    st.markdown("---")

    # 메뉴
    menu = st.radio(
        "메뉴",
        ["💬 채팅", "📊 데이터 보기"],
        label_visibility="collapsed"
    )


# 메인 컨텐츠
if menu == "💬 채팅":
    st.header("💬 대화형 입력")

    # 채팅 히스토리 표시
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.chat_message("user").write(message['content'])
            else:
                st.chat_message("assistant").write(message['content'])

    # 입력창
    user_input = st.chat_input("무엇을 도와드릴까요? (예: 어제 7시간 잤어)")

    if user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        # 처리
        result = st.session_state.orchestrator.handle_user_input(user_input)

        # 응답 메시지 추가
        response = result.get('message', '처리 완료')
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })

        st.rerun()


elif menu == "📊 데이터 보기":
    st.header("📊 저장된 데이터")

    # 데이터 테이블 탭
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💤 건강 데이터",
        "📝 할일",
        "🎯 습관",
        "💎 경험치",
        "📊 기타"
    ])

    cursor = st.session_state.db.conn.cursor()

    with tab1:
        st.subheader("💤 일일 건강 기록 (daily_health)")
        cursor.execute("SELECT * FROM daily_health ORDER BY date DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

    with tab2:
        st.subheader("📝 할일 목록 (tasks)")
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

    with tab3:
        st.subheader("🎯 습관 목록 (habits)")
        cursor.execute("SELECT * FROM habits")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

        st.markdown("---")

        st.subheader("📅 습관 로그 (habit_logs)")
        cursor.execute("SELECT * FROM habit_logs ORDER BY date DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

    with tab4:
        st.subheader("💎 경험치 로그 (exp_logs)")
        cursor.execute("SELECT * FROM exp_logs ORDER BY created_at DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

        st.markdown("---")

        st.subheader("📈 레벨 진행도 (user_progress)")
        cursor.execute("SELECT * FROM user_progress")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

    with tab5:
        st.subheader("📊 커스텀 메트릭 (custom_metrics)")
        cursor.execute("SELECT * FROM custom_metrics ORDER BY date DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")


# Footer
st.markdown("---")
st.caption("Horcrux v2.0 - Phase 4 (Web UI)")
