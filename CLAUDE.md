# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Horcrux is a Korean-language health and task management agent system with gamification (level-up system). It uses a multi-agent architecture with LangChain/GPT-4o-mini for natural language processing of Korean input.

## Commands

### Running the Application

```bash
# Main menu (interactive)
python3 horcrux.py

# Direct execution
./run.sh web     # Web dashboard (Streamlit)
./run.sh chat    # Natural language chat mode
./run.sh cli     # Command-line mode
./run.sh test    # Run tests
```

### Development Commands

```bash
# Database initialization
python3 core/database.py

# Run tests
pytest                                    # All tests
pytest tests/test_agents/                 # Agent tests only
pytest tests/test_parsers/                # Parser tests only
pytest --cov=agents --cov=parsers         # With coverage

# Web dashboard
streamlit run interfaces/app.py           # Access at http://localhost:8501
```

### Environment Setup

```bash
# Required: Create .env file with API keys
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Multi-Agent System

The system uses 5 specialized agents that communicate through the OrchestratorAgent:

1. **OrchestratorAgent** (`agents/orchestrator.py`)
   - Routes user input to appropriate agents
   - Coordinates agent communication
   - Combines responses for user
   - Error handling and fallback logic

2. **ConversationAgent** (`agents/conversation.py`)
   - **LLM-only parsing** - No regex fallback
   - Uses LangChain + GPT-4o-mini for Korean NLU
   - Handles complex multi-intent commands (e.g., "어제 5시간 자고 30분 운동했어")
   - Supports learning logs, sleep pattern calculations, task extraction
   - Maintains conversation history for context

3. **DataManagerAgent** (`agents/data_manager.py`)
   - SQLite database CRUD operations
   - Data validation and integrity checks
   - Statistics aggregation (daily/weekly/monthly)
   - Manages 9 tables: daily_health, custom_metrics, habits, habit_logs, tasks, user_progress, exp_logs, achievements, achievement_logs

4. **CoachingAgent** (`agents/coaching.py`)
   - Health pattern analysis and monitoring
   - Alert rule checking (sleep < 6h, 3-day streaks, etc.)
   - Personalized advice and encouragement
   - Milestone celebrations

5. **GamificationAgent** (`agents/gamification.py`)
   - XP calculation and awarding
   - Level-up system (quadratic formula: 100 * N * (N-1) / 2)
   - Achievement tracking (20 achievements)
   - Progress summaries and motivation messages

### Message Flow Example

```
User: "어제 5시간 자고 30분 운동했어"
  ↓
OrchestratorAgent (routes)
  ↓
ConversationAgent (LLM parses)
  → Returns: [
      {intent: "sleep", entities: {sleep_hours: 5, date: "어제"}},
      {intent: "workout", entities: {workout_minutes: 30, date: "어제"}}
    ]
  ↓
DataManagerAgent (stores to DB)
  ↓
CoachingAgent (generates alerts)
  → Sleep: "⚠️ 목표보다 2시간 부족"
  → Workout: "✓ 목표 달성!"
  ↓
GamificationAgent (awards XP)
  → Sleep: 0 XP (below target)
  → Workout: +10 XP
  ↓
OrchestratorAgent (combines response)
```

### LLM Integration

**LangChain + OpenAI** (`core/langchain_llm.py`)
- Model: GPT-4o-mini (cost-effective)
- JSON output parsing with structured prompts
- Handles complex Korean expressions and time calculations
- No regex fallback - LLM is primary parser

**Key prompts:**
- Intent classification: sleep, workout, protein, weight, task_add, task_complete, study, learning_log, summary, progress, chat
- Complex sleep pattern calculation (e.g., "11시에 잤다가 3시에 깨서 다시 8시에 자서 2시에 일어났어" → 10 hours total)
- Entity extraction with strict key naming (task_title, sleep_hours, workout_minutes, etc.)

### Database Schema

9 tables in SQLite (`horcrux.db`):
- `daily_health`: Core health metrics (sleep_h, workout_min, protein_g, weight_kg)
- `custom_metrics`: Flexible metrics (BMI, blood pressure, etc.)
- `habits` / `habit_logs`: Habit tracking with streak counts
- `tasks`: Task management with status/priority
- `user_progress`: Level and XP tracking
- `exp_logs`: XP transaction history
- `achievements` / `achievement_logs`: 20 achievements with conditions

### Configuration

**config.yaml:**
- Health targets (sleep: 7h, workout: 30min, protein: 100g)
- XP rules with priority multipliers
- LLM settings (provider: "langchain", strategy: "fallback")
- Alert thresholds

**Environment variables (.env):**
- `OPENAI_API_KEY`: Required for LangChain integration
- `ANTHROPIC_API_KEY`: Optional (if switching to Claude)

## Development Guidelines

### Testing Strategy

- **Unit tests**: Individual agent functionality
- **Parser tests**: 100+ Korean expression examples
- **Integration tests**: Full flow from input → parse → store → alert → XP → response

### Adding New Intents

1. Update LangChain prompt in `core/langchain_llm.py` (line 59-99)
2. Add handler in `OrchestratorAgent.process()`
3. Implement entity extraction logic
4. Add test cases in `tests/test_parsers/`

### Adding New Achievements

1. Define achievement in `core/database.py` seed data (20 achievements)
2. Implement check logic in `agents/gamification.py`
3. Set condition_type and condition_value (JSON)

### Korean NLP Patterns

The system understands:
- **Time expressions**: "어제", "그제", "3일 전", "내일", "모레"
- **Verb conjugations**: "잤어", "잤다", "잤음" (past), "해야해", "할 것" (future)
- **Quantity expressions**: "5시간", "다섯시간", "5h", "30분", "반시간", "100그램"
- **Complex sleep patterns**: Multi-segment sleep periods with automatic calculation

### Common Pitfalls

1. **LLM dependency**: The system requires OPENAI_API_KEY. Without it, ConversationAgent will fail.
2. **Entity key names**: Must match exactly (task_title not title, sleep_hours not hours)
3. **Database state**: Run `python3 core/database.py` to reset/initialize DB with seed data
4. **Streamlit caching**: May need to clear cache when testing web UI changes

### File Organization

```
Horcrux/
├── agents/          # 5 agents + base_agent.py
├── core/            # database.py, langchain_llm.py, llm_client.py, config.py
├── parsers/         # Legacy regex parsers (not actively used)
├── interfaces/      # main.py (CLI), main_natural.py (chat), app.py (Streamlit)
├── tests/           # Unit and integration tests
├── docs/            # Additional documentation (PROMPTS.md, WEB_UI_GUIDE.md, etc.)
├── config.yaml      # Configuration
├── .env.example     # Environment template
├── horcrux.py       # Main entry point
└── run.sh           # Execution script
```

## Phase Status

✅ **Phase 1**: MVP (DB, DataManagerAgent, GamificationAgent, basic CLI)
✅ **Phase 2**: Korean NLP (ConversationAgent, CoachingAgent, OrchestratorAgent, natural CLI)
✅ **Phase 3**: LLM integration (LangChain + GPT-4o-mini, 20 achievements)
✅ **Phase 4**: Web UI (Streamlit dashboard, charts with Plotly, achievement gallery)

Current state: All phases complete. System is production-ready for personal use.
