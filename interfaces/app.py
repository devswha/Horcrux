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
from core.simple_llm import SimpleLLM


# 페이지 설정
st.set_page_config(
    page_title="Horcrux - 건강/할일 관리",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'db' not in st.session_state:
    # Streamlit Cloud secrets를 환경 변수로 설정
    if hasattr(st, 'secrets'):
        for key in ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]

    st.session_state.db = Database()
    st.session_state.db.connect()

    # 데이터베이스 스키마 확인 및 초기화
    try:
        cursor = st.session_state.db.conn.cursor()

        # PostgreSQL과 SQLite 모두 지원
        if st.session_state.db.db_type == 'postgres':
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'user_progress'
            """)
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_progress'")

        if not cursor.fetchone():
            # 테이블이 없으면 스키마 초기화
            print("📝 Initializing database schema...")
            st.session_state.db.init_schema()
            st.session_state.db.seed_initial_data()
            print("✅ Database schema initialized!")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        st.error(f"데이터베이스 초기화 중 오류: {e}")

if 'agent' not in st.session_state:
    # SimpleLLM 초기화
    try:
        print("🤖 Initializing SimpleLLM...")
        st.session_state.agent = SimpleLLM(st.session_state.db.conn)
        st.session_state.llm_status = "✅ SimpleLLM 활성화 (GPT-4o-mini)"
        print(f"✅ SimpleLLM initialized! RAG: {st.session_state.agent.rag is not None}")
    except Exception as e:
        print(f"❌ SimpleLLM initialization failed: {e}")
        st.error(f"SimpleLLM 초기화 실패: {str(e)}")
        st.session_state.llm_status = f"⚠️ SimpleLLM 오류: {str(e)}"
        st.stop()

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

    # 디버그 정보
    with st.expander("🔍 디버그 정보"):
        st.write(f"**DB 타입**: {st.session_state.db.db_type}")
        st.write(f"**RAG 활성화**: {st.session_state.agent.rag is not None if 'agent' in st.session_state else 'N/A'}")

        # 환경 변수 확인
        env_status = {
            "OPENAI_API_KEY": "✅" if os.getenv("OPENAI_API_KEY") else "❌",
            "SUPABASE_URL": "✅" if os.getenv("SUPABASE_URL") else "❌",
            "SUPABASE_KEY": "✅" if os.getenv("SUPABASE_KEY") else "❌",
        }
        st.write("**환경 변수**:")
        for key, status in env_status.items():
            st.write(f"  {status} {key}")

        # Streamlit secrets 확인
        if hasattr(st, 'secrets'):
            secrets_status = {
                "OPENAI_API_KEY": "✅" if "OPENAI_API_KEY" in st.secrets else "❌",
                "SUPABASE_URL": "✅" if "SUPABASE_URL" in st.secrets else "❌",
                "SUPABASE_KEY": "✅" if "SUPABASE_KEY" in st.secrets else "❌",
            }
            st.write("**Streamlit Secrets**:")
            for key, status in secrets_status.items():
                st.write(f"  {status} {key}")

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

        # SimpleLLM 처리
        with st.spinner('처리 중...'):
            response = st.session_state.agent.process(user_input, st.session_state.chat_history)
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })

        st.rerun()


elif menu == "📊 데이터 보기":
    st.header("📊 저장된 데이터")

    # 데이터 테이블 탭
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💤 건강 데이터",
        "📝 할일",
        "🎯 습관",
        "💎 경험치",
        "📊 기타",
        "👥 인물 정보",
        "🤝 상호작용",
        "📚 지식/회고"
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

    with tab6:
        st.subheader("👥 인물 정보 (people)")
        cursor.execute("SELECT * FROM people ORDER BY importance_score DESC, name")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

    with tab7:
        st.subheader("🤝 상호작용 로그 (interactions)")
        cursor.execute("""
            SELECT i.id, p.name as person_name, i.date, i.type,
                   i.summary, i.sentiment, i.location, i.duration_min
            FROM interactions i
            JOIN people p ON i.person_id = p.id
            ORDER BY i.date DESC
        """)
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

    with tab8:
        st.subheader("📚 지식 저장소 (knowledge_entries)")
        cursor.execute("SELECT * FROM knowledge_entries ORDER BY learned_date DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")

        st.markdown("---")

        st.subheader("💭 회고/성찰 (reflections)")
        cursor.execute("SELECT * FROM reflections ORDER BY date DESC")
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame([{key: row[key] for key in row.keys()} for row in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 없습니다.")


# Footer
st.markdown("---")
st.caption("Horcrux v2.0 - Phase 5A (Memory System)")
