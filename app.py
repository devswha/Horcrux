#!/usr/bin/env python3
"""
LifeBot 웹 대시보드 (Streamlit)
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from core.database import Database
from agents.conversation import ConversationAgent
from agents.data_manager import DataManagerAgent
from agents.gamification import GamificationAgent
from agents.coaching import CoachingAgent
from agents.orchestrator import OrchestratorAgent


# 페이지 설정
st.set_page_config(
    page_title="LifeBot - 건강/할일 관리",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'db' not in st.session_state:
    st.session_state.db = Database()
    st.session_state.db.connect()

if 'orchestrator' not in st.session_state:
    conversation = ConversationAgent()
    data_manager = DataManagerAgent(st.session_state.db.conn)
    gamification = GamificationAgent(st.session_state.db.conn)
    coaching = CoachingAgent(st.session_state.db.conn)
    st.session_state.orchestrator = OrchestratorAgent(
        conversation, data_manager, gamification, coaching
    )
    st.session_state.data_manager = data_manager
    st.session_state.gamification = gamification

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# 사이드바
with st.sidebar:
    st.title("🤖 LifeBot")
    st.markdown("---")

    # 진행도 표시
    progress = st.session_state.gamification.get_progress_summary()

    st.metric("레벨", f"Level {progress['level']}")
    st.metric("경험치", f"{progress['current_exp']}/{progress['next_level_exp']} XP")

    # 프로그레스 바
    progress_percent = progress['progress_percent'] / 100
    st.progress(progress_percent, text=f"{progress['progress_percent']:.1f}%")

    st.metric("업적", progress['achievements'])

    st.markdown("---")

    # 메뉴
    menu = st.radio(
        "메뉴",
        ["💬 채팅", "📊 대시보드", "📈 분석", "🏆 업적"],
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

    # 예시 버튼들
    st.markdown("---")
    st.subheader("빠른 입력")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💤 수면 기록"):
            st.session_state.quick_input = "7시간 잤어"
    with col2:
        if st.button("💪 운동 기록"):
            st.session_state.quick_input = "30분 운동했어"
    with col3:
        if st.button("📝 할일 추가"):
            st.session_state.quick_input = "새 할일"
    with col4:
        if st.button("📊 오늘 요약"):
            st.session_state.quick_input = "오늘 요약"


elif menu == "📊 대시보드":
    st.header("📊 대시보드")

    # 오늘 요약
    today = datetime.now().strftime("%Y-%m-%d")
    summary = st.session_state.data_manager.get_summary(today)

    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sleep = summary['health'].get('sleep_h')
        st.metric(
            "💤 수면",
            f"{sleep}시간" if sleep else "기록 없음",
            f"{sleep - 7:.1f}h" if sleep else None,
            delta_color="normal"
        )

    with col2:
        workout = summary['health'].get('workout_min')
        st.metric(
            "💪 운동",
            f"{workout}분" if workout else "기록 없음",
            f"{workout - 30}분" if workout else None,
            delta_color="normal"
        )

    with col3:
        protein = summary['health'].get('protein_g')
        st.metric(
            "🍗 단백질",
            f"{protein}g" if protein else "기록 없음",
            f"{protein - 100:.0f}g" if protein else None,
            delta_color="normal"
        )

    with col4:
        tasks = summary['tasks']
        st.metric(
            "📝 할일",
            f"{tasks['done']}/{tasks['total']}",
            f"{tasks['done']}개 완료"
        )

    st.markdown("---")

    # 주간 차트
    st.subheader("📈 주간 트렌드")

    # 최근 7일 데이터 가져오기
    cursor = st.session_state.db.conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT date, sleep_h, workout_min, protein_g
        FROM daily_health
        WHERE date >= ?
        ORDER BY date
    """, (week_ago,))

    rows = cursor.fetchall()

    if rows:
        df = pd.DataFrame([{
            'date': row['date'],
            'sleep': row['sleep_h'] or 0,
            'workout': row['workout_min'] or 0,
            'protein': row['protein_g'] or 0
        } for row in rows])

        # 수면 차트
        fig_sleep = go.Figure()
        fig_sleep.add_trace(go.Scatter(
            x=df['date'],
            y=df['sleep'],
            mode='lines+markers',
            name='수면',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        fig_sleep.add_hline(y=7, line_dash="dash", line_color="green",
                           annotation_text="목표: 7시간")
        fig_sleep.update_layout(
            title="수면 시간 (시간)",
            xaxis_title="날짜",
            yaxis_title="시간",
            height=300
        )

        # 운동 차트
        fig_workout = go.Figure()
        fig_workout.add_trace(go.Bar(
            x=df['date'],
            y=df['workout'],
            name='운동',
            marker_color='#ff7f0e'
        ))
        fig_workout.add_hline(y=30, line_dash="dash", line_color="green",
                             annotation_text="목표: 30분")
        fig_workout.update_layout(
            title="운동 시간 (분)",
            xaxis_title="날짜",
            yaxis_title="분",
            height=300
        )

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_sleep, use_container_width=True)
        with col2:
            st.plotly_chart(fig_workout, use_container_width=True)
    else:
        st.info("아직 데이터가 없습니다. 건강 기록을 시작해보세요!")

    st.markdown("---")

    # 할일 목록
    st.subheader("📝 할일 목록")

    tasks = st.session_state.data_manager.get_pending_tasks()

    if tasks:
        for task in tasks:
            priority_emoji = {
                "urgent": "🔴",
                "high": "🟠",
                "normal": "🟢",
                "low": "🔵"
            }.get(task['priority'], "⚪")

            col1, col2, col3 = st.columns([0.5, 4, 1])

            with col1:
                st.write(priority_emoji)
            with col2:
                st.write(f"**{task['title']}**")
                if task['due']:
                    st.caption(f"마감: {task['due']}")
            with col3:
                if st.button("완료", key=f"task_{task['id']}"):
                    result = st.session_state.data_manager.complete_task(task['id'])
                    if result.get('success'):
                        st.success("완료!")
                        st.rerun()
    else:
        st.info("할일이 없습니다!")


elif menu == "📈 분석":
    st.header("📈 고급 분석")

    # 주간 통계
    st.subheader("📊 주간 통계")

    stats = st.session_state.data_manager.get_weekly_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("평균 수면", f"{stats['avg_sleep']}시간")
    with col2:
        st.metric("총 운동 시간", f"{stats['total_workout']}분")
    with col3:
        st.metric("완료한 할일", f"{stats['completed_tasks']}개")

    st.markdown("---")

    # 경험치 로그
    st.subheader("💎 경험치 획득 내역")

    cursor = st.session_state.db.conn.cursor()
    cursor.execute("""
        SELECT date, action_type, exp_gained, description
        FROM exp_logs
        ORDER BY created_at DESC
        LIMIT 10
    """)

    exp_logs = cursor.fetchall()

    if exp_logs:
        df_exp = pd.DataFrame([{
            '날짜': row['date'],
            '행동': row['action_type'],
            'XP': row['exp_gained'],
            '설명': row['description']
        } for row in exp_logs])

        st.dataframe(df_exp, use_container_width=True, hide_index=True)

        # XP 타입별 차트
        fig_exp = px.pie(
            df_exp,
            names='행동',
            values='XP',
            title='경험치 획득 비율'
        )
        st.plotly_chart(fig_exp, use_container_width=True)
    else:
        st.info("아직 경험치 획득 내역이 없습니다.")


elif menu == "🏆 업적":
    st.header("🏆 업적 갤러리")

    # 모든 업적 가져오기
    cursor = st.session_state.db.conn.cursor()
    cursor.execute("SELECT * FROM achievements")
    achievements = cursor.fetchall()

    # 달성한 업적
    cursor.execute("""
        SELECT achievement_id, achieved_at
        FROM achievement_logs
    """)
    achieved = {row['achievement_id']: row['achieved_at'] for row in cursor.fetchall()}

    # 진행도
    achieved_count = len(achieved)
    total_count = len(achievements)

    st.progress(
        achieved_count / total_count if total_count > 0 else 0,
        text=f"{achieved_count}/{total_count} 업적 달성 ({achieved_count/total_count*100:.0f}%)"
    )

    st.markdown("---")

    # 업적 카드
    cols = st.columns(3)

    for idx, achievement in enumerate(achievements):
        with cols[idx % 3]:
            is_achieved = achievement['id'] in achieved

            # 카드 스타일
            if is_achieved:
                st.success(f"{achievement['icon']} **{achievement['name']}**")
                st.caption(achievement['description'])
                st.caption(f"✓ 달성: {achieved[achievement['id']]}")
                st.caption(f"보상: +{achievement['exp_reward']} XP")
            else:
                st.info(f"🔒 **{achievement['name']}**")
                st.caption(achievement['description'])
                st.caption(f"보상: +{achievement['exp_reward']} XP")

            st.markdown("---")


# Footer
st.markdown("---")
st.caption("LifeBot v2.0 - Phase 4 (Web UI)")
