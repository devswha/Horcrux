# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LifeBot is a health and task management agent system with gamification (level-up system) that tracks health metrics (sleep, exercise, protein intake), tasks, and habits through a conversational interface. Users gain XP and level up as they complete tasks and achieve health goals.

## Current Status: Phase 1 MVP Complete ✅

### Implemented (Phase 1)
- ✅ Database schema (9 tables)
- ✅ DataManagerAgent with full CRUD operations
- ✅ GamificationAgent with XP/level system
- ✅ Basic CLI interface
- ✅ Initial achievements system (6 achievements)

### Next: Phase 2 (Natural Language Parsing)
- [ ] Korean language parser (regex-based patterns)
- [ ] ConversationAgent for intent classification
- [ ] CoachingAgent for alerts and insights
- [ ] OrchestratorAgent for agent coordination
- [ ] Natural language CLI

## Architecture

### 5 Agent System
1. **OrchestratorAgent** (조율자) - Routes messages between agents [Phase 2]
2. **ConversationAgent** (대화형 파싱) - Parses Korean natural language input [Phase 2]
3. **DataManagerAgent** (데이터 관리) - CRUD operations, statistics ✅
4. **CoachingAgent** (알림/인사이트) - Health monitoring, pattern analysis [Phase 2]
5. **GamificationAgent** (레벨업 시스템) - XP, levels, achievements ✅

### Database Schema (9 Tables)
- `daily_health`: Core daily health metrics (sleep, workout, protein, weight)
- `custom_metrics`: Flexible metrics (BMI, blood pressure, etc.)
- `habits`: Habit definitions
- `habit_logs`: Habit tracking with streak counts
- `tasks`: Todo items with priority and category
- `user_progress`: Level and XP
- `exp_logs`: XP gain history
- `achievements`: Achievement definitions
- `achievement_logs`: Achieved milestones

### XP System
- Task complete: +20 XP (multiplied by priority)
- Sleep goal (7h): +15 XP
- Workout: +10 XP (proportional to minutes)
- Protein goal: +10 XP
- Habit streak: +5 XP/day (bonus for longer streaks)
- Study/career: +30 XP/hour
- 7-day streak bonus: +100 XP

### Level Formula
Level N → N+1 requires: 100 + (N-2) * 50 XP
- Level 1 → 2: 100 XP
- Level 2 → 3: 150 XP
- Level 3 → 4: 200 XP

## Development Workflow

### Running the Application
```bash
# Initialize database (first time only)
python3 core/database.py

# Run CLI
python3 main.py
```

### Testing
```bash
# Install test dependencies
pip3 install pytest pytest-cov

# Run tests (Phase 2)
pytest

# Run with coverage
pytest --cov=agents --cov=parsers
```

### Project Structure
```
LifeBot/
├── agents/           # Agent implementations
│   ├── base_agent.py
│   ├── data_manager.py ✅
│   └── gamification.py ✅
├── core/             # Core modules
│   ├── database.py ✅
│   └── config.py (to be added)
├── parsers/          # Korean language parsers (Phase 2)
├── rules/            # Alert and XP rules (Phase 2)
├── interfaces/       # User interfaces
└── tests/            # Test suites

## Conversational Interface Examples (Phase 2)

The system will understand Korean natural language inputs like:
- "어제 5시간 잤어" → daily_health.sleep_h = 5, date = yesterday
- "30분 운동했어" → daily_health.workout_min = 30, +10 XP
- "카드비 계산해야 해" → tasks.title = "카드비 계산", status = pending
- "할일 [ID] 완료했어" → tasks.status = done, +20 XP
- "오늘 요약 보여줘" → get_summary(today)

## Implementation Notes for Phase 2

### Korean Language Parsing
Focus on extracting:
- **Temporal info**: "어제", "오늘", "3일 전"
- **Health metrics**: "5시간", "30분", "100g"
- **Task attributes**: "해야 해", "완료했어"
- **Intent**: log_health, add_task, complete_task, get_summary

### Pattern Examples
```python
# Sleep: r'(\d+)\s*시간\s*(잤|수면)'
# Workout: r'(\d+)\s*분\s*(운동|헬스|러닝)'
# Date: r'(어제|오늘|내일|그제)'
```

### Agent Communication (Phase 2)
Use message-based architecture:
```python
message = {
    "sender": "Conversation",
    "receiver": "DataManager",
    "action": "store_health",
    "data": {"date": "2025-10-01", "sleep_h": 5}
}
```

## Configuration

Settings in `config.yaml`:
- Health targets (sleep: 7h, workout: 30min, protein: 100g)
- Alert thresholds (sleep warning: 6h, consecutive days: 3)
- XP rules (task: 20, sleep: 15, workout: 10, etc.)
- Level formula: quadratic
- LLM settings (optional, for Phase 3)

## Key Files

- `core/database.py`: DB schema and initialization
- `agents/data_manager.py`: CRUD operations for all data types
- `agents/gamification.py`: XP calculation, level-up logic, achievements
- `main.py`: CLI entry point
- `config.yaml`: Application settings
- `claude.md`: Detailed project plan (Korean)
- `README.md`: User documentation
