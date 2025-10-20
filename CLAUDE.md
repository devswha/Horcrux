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

### SimpleLLM System

**SimpleLLM** (`core/simple_llm.py`) is the core of Horcrux - a single, clean orchestrator that uses LLM for everything:

**Design Philosophy**:
- ✅ **100% LLM-driven**: Both parsing AND response generation use GPT-4o-mini
- ✅ **No rule-based logic**: Flexible, natural language understanding
- ✅ **All-in-one**: Single class with DB helper methods (~700 lines)
- ✅ **No gamification**: Removed XP/levels for simplicity

**Architecture**:
```python
class SimpleLLM:
    def process(user_input) -> str:
        # 1. LLM Parsing (with current time context)
        parsed = _parse_with_llm(user_input)

        # 2. Execute DB operations
        results = _execute(parsed)  # Routes to helper methods

        # 3. LLM Response Generation
        response = _generate_response(user_input, results)

        return response
```

**Key Features**:
1. **Time-aware parsing**: Includes current time for accurate "지금" (now) calculations
2. **Multi-intent**: Handles compound commands (e.g., "7시간 자고 30분 운동")
3. **15+ DB helpers**: sleep, workout, study, person, interaction, knowledge, etc.
4. **Natural responses**: LLM generates friendly Korean responses (no templates)

### Message Flow Example

```
User: "어제 5시간 자고 30분 운동했어"
  ↓
SimpleLLM._parse_with_llm() → LLM parses to JSON:
  [
    {intent: "sleep", entities: {sleep_hours: 5, date: "2025-10-16"}},
    {intent: "workout", entities: {workout_minutes: 30, date: "2025-10-16"}}
  ]
  ↓
SimpleLLM._execute() → Calls DB helpers:
  _store_sleep() → INSERT INTO daily_health (date, sleep_h) VALUES (...)
  _store_workout() → INSERT INTO daily_health (date, workout_min) VALUES (...)
  ↓
SimpleLLM._generate_response() → LLM generates response:
  "5시간 주무셨군요. 목표인 7시간보다 2시간 부족합니다. 💤
   30분 운동하셨어요! 목표 달성입니다. 계속 이어가세요! 💪"
  ↓
Return to user
```

**Note**: No coaching rules, no XP calculation - LLM handles everything naturally!

### LLM Integration

**SimpleLLM uses LangChain + OpenAI** (`core/simple_llm.py`):
- Model: GPT-4o-mini (cost-effective, fast)
- **Dual LLM usage**: Parsing (JSON) + Response generation (natural language)
- Current time context for accurate "지금" calculations
- No regex fallback - 100% LLM

**Supported intents**:
- Health: sleep, workout, study, protein, weight
- Tasks: task_add, task_complete
- Memory: remember_person, remember_interaction, remember_knowledge, query_memory
- Other: reflect, summary, chat

**Key features**:
- Entity extraction with strict naming (sleep_hours, workout_minutes, task_title, etc.)
- Complex time calculations ("오후 3시부터 지금까지" with current_time context)
- Multi-intent parsing (handles "X하고 Y했어" compound commands)

### Database Schema

**13 tables** - supports both SQLite (local) and PostgreSQL (cloud):

**Core Tables**:
- `daily_health`: Core health metrics (sleep_h, workout_min, protein_g, weight_kg)
- `custom_metrics`: Flexible metrics (study hours, etc.)
- `habits` / `habit_logs`: Habit tracking with streak counts
- `tasks`: Task management with status/priority
- `user_progress`, `exp_logs`: Level/XP tracking (legacy support)

**Phase 5A Memory Tables**:
- `people`: Personal relationships and contacts
- `interactions`: Interaction logs with people
- `knowledge_entries`: Knowledge repository
- `learning_logs`: Learning content tracking
- `reflections`: Daily/weekly reflections
- `conversation_memory`: Chat history

**Database Support**:
- **SQLite** (`horcrux.db`): Local development, auto-created
- **PostgreSQL** (Supabase): Cloud deployment (Streamlit Cloud)
  - Auto-switches based on `SUPABASE_URL` environment variable
  - See `SUPABASE_SETUP.md` for deployment guide

**Schema Compatibility**:
- `core/database.py` automatically adapts SQL syntax:
  - SQLite: `INTEGER PRIMARY KEY AUTOINCREMENT`
  - PostgreSQL: `SERIAL PRIMARY KEY`

### Configuration

**Environment variables (.env):**
- `OPENAI_API_KEY`: **Required** for SimpleLLM (GPT-4o-mini)
- `SUPABASE_URL`: (Optional) PostgreSQL connection string for cloud deployment
  - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`
  - If not set, uses SQLite (`horcrux.db`)
- `SUPABASE_KEY`: (Optional) Supabase anon/public key

**Local Development**:
- Uses SQLite (`horcrux.db`) by default
- No Supabase config needed

**Cloud Deployment** (Streamlit Cloud):
- Set `SUPABASE_URL` and `SUPABASE_KEY` in Streamlit secrets
- Database auto-switches to PostgreSQL
- See `SUPABASE_SETUP.md` for step-by-step guide

## Development Guidelines

### Adding New Intents

To add a new intent to SimpleLLM:

1. **Update parsing prompt** in `core/simple_llm.py` (_parse_with_llm method):
   - Add new intent to the list (e.g., "medication: 약 복용 기록")
   - Add entity key names (e.g., "medication: medication_name, dosage, time")

2. **Add DB helper method**:
   ```python
   def _store_medication(self, entities: Dict) -> Dict:
       name = entities.get("medication_name")
       dosage = entities.get("dosage")
       # ... DB insert logic
       return {"success": True, "message": f"{name} 기록"}
   ```

3. **Add router case** in `_execute()`:
   ```python
   elif intent == "medication":
       result = self._store_medication(entities)
   ```

4. **Test**: "오늘 아스피린 100mg 먹었어" → should record medication

### Korean NLP Patterns

The system understands:
- **Time expressions**: "어제", "그제", "3일 전", "내일", "모레"
- **Verb conjugations**: "잤어", "잤다", "잤음" (past), "해야해", "할 것" (future)
- **Quantity expressions**: "5시간", "다섯시간", "5h", "30분", "반시간", "100그램"
- **Complex sleep patterns**: Multi-segment sleep periods with automatic calculation

### Common Pitfalls

1. **OPENAI_API_KEY required**: SimpleLLM will fail to initialize without this env variable
2. **Entity key naming**: Must match exactly (sleep_hours not hours, task_title not title)
3. **Time calculation**: SimpleLLM includes current time context - test "지금" expressions carefully
4. **JSON parsing**: LLM must output valid JSON. Markdown code blocks are stripped automatically
5. **Streamlit caching**: May need to clear cache or restart server after code changes

### File Organization

```
Horcrux/
├── core/
│   ├── simple_llm.py        # ⭐ Main system (SimpleLLM class)
│   ├── database.py           # DB schema and initialization
│   └── langchain_llm.py      # Legacy LLM wrapper (not actively used)
├── interfaces/
│   └── app.py                # ⭐ Streamlit web dashboard (uses SimpleLLM)
├── _deprecated/
│   └── agents/               # Old multi-agent files (backup)
├── agents/                   # Empty (deprecated)
├── tests/                    # Old tests (may need updates)
├── .env                      # OPENAI_API_KEY
├── horcrux.db                # SQLite database
└── horcrux.py                # Main entry point
```

**Active files**: `core/simple_llm.py` + `interfaces/app.py` + `core/database.py`

## Project Vision

### The True Horcrux Concept

Inspired by Harry Potter's Horcruxes - objects that preserve a piece of one's soul - **Horcrux** is designed to be a **digital repository of "you"**:

- **Complete Memory**: Store everything - learning, relationships, experiences, thoughts, insights
- **AI-Powered Recall**: Use AI to find, connect, and utilize your past knowledge
- **Digital Twin**: Build a comprehensive model of yourself that grows over time
- **Context-Aware Intelligence**: AI that understands you based on your history

**Core Philosophy**:
- Humans forget, but Horcrux remembers
- Data ownership and privacy (local-first)
- AI as a partner that knows you deeply

Current Phases 1-4 focus on health/task management. **Phase 5+ will transform Horcrux into a true "digital self" repository.**

## Phase Status

✅ **Phase 1-4**: Multi-agent system (DEPRECATED - replaced by SimpleLLM)
✅ **Phase 5A**: Personal Memory System (people, interactions, knowledge, reflections)
✅ **Phase 6**: **SimpleLLM Architecture** (2025-10-17)
   - Removed multi-agent complexity → Single SimpleLLM class
   - Removed gamification (XP/levels) for simplicity
   - 100% LLM-driven (parsing + responses)
   - Fixed time calculation bugs
   - Natural Korean responses
   - **Precision Mode** applied (logical, factual responses only)
✅ **Phase 7**: **Cloud Deployment & Database Flexibility** (2025-10-20)
   - Database adapter: SQLite (local) + PostgreSQL (cloud)
   - Supabase integration for Streamlit Cloud deployment
   - Persistent data storage on cloud
   - Auto-switching based on environment
✅ **Phase 8**: **RAG System Implementation** (2025-01-20)
   - pgvector 0.8.0 활성화 (Supabase)
   - OpenAI text-embedding-3-small 통합
   - 자동 대화 임베딩 생성 (1536차원 벡터)
   - HNSW 인덱스 기반 유사도 검색
   - SimpleLLM에 RAG 통합
   - 맥락 기반 대화 지원 ("그 사람 누구야?", "최근에 뭐 했지?")

**Current state**: RAG 시스템 100% 준비 완료. 모든 대화가 자동 저장되고 벡터 검색 가능. Streamlit Cloud 배포 후 즉시 사용 가능.

## Phase 5 Roadmap: Personal Knowledge & Memory System

### Vision
Transform Horcrux from a health/task tracker into a comprehensive "digital self" repository that stores and intelligently retrieves all personal information.

### Phase 5A: Memory Foundation (1-2 weeks)
**Goal**: Basic storage and retrieval of personal information

**New Database Tables**:
```sql
-- People & Relationships
people (
  id, name, relationship_type, first_met_date,
  tags JSON, personality_notes, contact_info,
  importance_score (1-10), created_at, updated_at
)

-- Interaction Logs
interactions (
  id, person_id, date, type (meeting/call/message),
  summary, sentiment (positive/neutral/negative),
  topics JSON, location, duration_min, created_at
)

-- Knowledge Repository
knowledge_entries (
  id, title, content, source (book/article/course),
  category, tags JSON, learned_date, confidence (1-5),
  last_reviewed, created_at
)

-- Reflections & Insights
reflections (
  id, date, topic, content, mood,
  insights JSON, related_events JSON, created_at
)

-- Conversation Memory
conversation_memory (
  id, session_id, role (user/assistant), content,
  timestamp, context JSON
)
```

**New Agent**:
- `MemoryAgent`: Basic CRUD for all memory tables

**New Intents** (ConversationAgent):
- `remember_fact`: "민수는 개발자야" → people table
- `remember_learning`: "오늘 React Hooks 배웠어" → knowledge_entries
- `remember_interaction`: "어제 친구들이랑 놀았어" → interactions
- `query_memory`: "민수에 대해 뭐 알고 있어?" → search memory
- `reflect`: "이번 주 어땠어?" → generate reflection

**Usage Examples**:
```
User: "민수는 내 대학 친구야. 개발자고 커피를 좋아해"
→ MemoryAgent creates person + tags

User: "민수에 대해 뭐 알고 있어?"
→ MemoryAgent retrieves: "민수는 대학 친구이며 개발자입니다. 커피를 좋아합니다."
```

### Phase 5B: Semantic Search (2-3 weeks)
**Goal**: Find relevant memories based on context, not just keywords

**New Dependencies**:
- `chromadb`: Vector database (local)
- `openai` (embeddings): text-embedding-3-small

**New Features**:
1. Automatic embedding generation for all text content
2. Semantic search: "작년에 비슷한 문제 있었을 때 어떻게 했지?" → vector search
3. Context injection: Auto-load relevant memories at conversation start
4. Smart summaries: LLM-powered summarization of long memory chains

**Architecture**:
- SQLite: Structured data (names, dates, relationships)
- Chroma: Unstructured data (embeddings for semantic search)
- Combined queries: SQL + vector search for best results

**Cost**: ~$0.02/1M tokens for embeddings (very cheap)

### Phase 5C: Relationship Graph (2 weeks)
**Goal**: Visualize and analyze personal relationships

**New Agent**:
- `RelationshipAgent`: Manage people, interactions, relationship analysis

**New Features**:
1. Relationship network visualization (Plotly/Cytoscape)
2. Interaction timeline per person
3. Relationship insights:
   - "You haven't contacted X in 2 months"
   - "You meet Y most often on weekends"
4. People directory with rich profiles

**Web UI**:
- New tab: "👥 인간관계"
- Network graph (nodes = people, edges = interactions)
- Person detail view with timeline

### Phase 5D: Proactive Insights (3 weeks)
**Goal**: AI that understands patterns and proactively helps

**New Agent**:
- `ReflectionAgent`: Pattern analysis, insights generation, proactive suggestions

**New Features**:
1. Weekly/monthly reflection prompts
2. Pattern discovery:
   - "You tend to skip workouts on Mondays"
   - "You're most productive in the mornings"
3. Knowledge review system (Spaced Repetition)
4. Proactive reminders:
   - "Today you're meeting X. Last time you discussed Y."
5. Growth dashboard:
   - Skills learned over time
   - Relationship quality trends
   - Achievement milestones

**AI Techniques**:
- Time-series analysis for behavior patterns
- LLM-powered insight generation
- Recommendation system for learning/review

### Technical Architecture

**Extended Agent System**:
```
User Input
  ↓
OrchestratorAgent
  ↓
ConversationAgent (parse intent)
  ↓
┌─────────────┬──────────────┬──────────────┬───────────────┐
│MemoryAgent  │RelationAgent │KnowledgeAgent│ReflectionAgent│
│(Phase 5A)   │(Phase 5C)    │(Phase 5B)    │(Phase 5D)     │
└─────────────┴──────────────┴──────────────┴───────────────┘
  ↓
Response (with relevant context from memory)
```

**Memory Retrieval Flow**:
1. User asks question
2. MemoryAgent: Vector search for relevant memories
3. SQL queries for structured data (dates, names)
4. Combine results and inject into LLM context
5. LLM generates contextual response

**Data Privacy**:
- Local-first: SQLite + Chroma run locally
- Optional cloud backup (encrypted)
- No data leaves your machine except API calls (OpenAI)
- Export to JSON/Markdown anytime

### Implementation Priority

**Immediate (Phase 5A)**:
1. Create new database tables
2. Implement MemoryAgent basic CRUD
3. Add new intents to ConversationAgent
4. Test: "Remember X" → "What do you know about X?"

**Next (Phase 5B)**:
1. Integrate Chroma DB
2. Embedding pipeline
3. Semantic search

**Later (Phase 5C + 5D)**:
1. Relationship visualization
2. Proactive insights
3. Advanced analytics

### Success Metrics

Phase 5 is successful when:
- ✅ User can store any information naturally ("Remember that...")
- ✅ AI recalls relevant information at the right time
- ✅ System feels like "an AI that knows me"
- ✅ Privacy is maintained (local-first)
- ✅ Data grows into a comprehensive "digital self"

### Future Vision (Phase 6+)

- Voice interface (whisper + TTS)
- Mobile app (React Native + local sync)
- Multi-modal memory (images, audio, video)
- Collaborative memory (shared with family/team)
- Export to other AI systems (ChatGPT, Claude)
- Brain-computer interface integration (far future 😄)

---

**"Your life, remembered forever. Your AI, that truly knows you."**
