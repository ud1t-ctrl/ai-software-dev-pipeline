# AI Software Development Team — Multi-Agent Dev Pipeline

A multi-agent AI pipeline built with **CrewAI** and **Ollama** that takes a one-line product idea and generates a full software project: requirements, database schema, API docs, backend code, frontend, tests, and documentation — with a multi-stage self-debugging system that actually runs the generated code to catch and fix real bugs before you ever see them.

## What it does

Give it a prompt like `"Create a Library Management System"`, and it runs that idea through a team of 7 AI agents, each specialized like a real dev team role, producing 8 output files — either from the command line or a web UI.

## The agent team

| # | Agent | Role |
|---|---|---|
| 1 | Requirement Analyst | Writes the SRS (Software Requirements Specification) |
| 2 | System Designer | Designs the database schema and REST API contract |
| 3 | Backend Developer | Implements the Flask backend |
| 4 | Frontend Developer | Builds an HTML/CSS/JS frontend |
| 5 | Code Reviewer | Reviews backend + frontend for bugs, documents findings |
| 6 | QA Tester | Writes pytest unit tests |
| 7 | Documentation Writer | Writes the final README for the generated app |

## Pipeline flow

```
Product idea
    │
    ▼
Requirement Analyst   →  SRS.md
    │
    ▼
System Designer       →  schema.sql, API_DOCS.md
    │
    ▼
Backend Developer      →  app.py
    │            ⤷ auto-patched + repair loop runs HERE, before Frontend starts
    ▼
Frontend Developer     →  index.html  (built against the ALREADY-FIXED backend)
    │            ⤷ frontend URLs checked against real backend routes
    ▼
Code Reviewer          →  REVIEW_REPORT.md
    │
    ▼
QA Tester               →  test_app.py
    │
    ▼
Documentation Writer     →  README.md
```

Each stage receives the previous stages' outputs as context, so decisions made early (e.g. the database schema) flow through to later stages automatically. Critically, the backend's repair loop runs **immediately after the Backend Developer finishes** — not after the whole crew is done — so the Frontend Developer always builds against the final, corrected backend rather than a draft that's about to change.

## Self-debugging system

Before any file is saved, it goes through automated checks — real execution feedback, not just an LLM's opinion of its own code.

**Deterministic auto-patches** (plain code, no AI, 100% reliable):
- Adds `flask-cors` + `CORS(app)` if missing
- Wraps `db.create_all()` in `with app.app_context():` if it isn't already
- Forces the database to SQLite and strips MySQL/Postgres driver imports (no external DB server exists in this environment)
- Adds `required` to every frontend `<input>` (skipping hidden/submit/button/checkbox/radio)

**`app.py` repair loop** (up to 5 attempts per stage, real error fed back to the model each time):
1. **Syntax** — `ast.parse()`
2. **Database initialization** — actually imports the code and runs `db.create_all()` in an isolated subprocess, catching missing primary keys, bad foreign keys, undefined names
3. **Endpoint smoke test** — spins up Flask's test client and fires a request at every registered route, flagging any that crash with a 500

**`index.html` consistency check** (up to 3 attempts) — extracts every `/api/...` URL the frontend actually calls and cross-checks it against the real routes registered in the backend (introspected directly, not guessed from docs), fixing any mismatch.

**`test_app.py`** — syntax check only.

A **"skip debug loops"** option is available (CLI prompt or UI checkbox) for a much faster run when you just need a quick draft — auto-patches still apply, only the slower LLM-retry cycles are skipped.

## Tech stack

- **CrewAI** — multi-agent orchestration framework
- **Ollama** — runs the LLM locally (`qwen2.5-coder:7b`), free, no API key
- **Streamlit** — the web UI
- **Flask + Flask-SQLAlchemy** — generated backend stack
- **Python 3.12**

## Setup

See [`SETUP.md`](./SETUP.md) for full installation and run instructions.

Quick version:
```
ollama pull qwen2.5-coder:7b
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

**Run it — two ways:**
```
python main.py                  # command line
streamlit run pipeline_ui.py     # web UI (recommended) — opens at localhost:8501
```

Output is saved to `outputs/<slugified-idea>/`, one subfolder per idea you've tried.

## Project structure

```
AI_Software_Dev_Team/
├── main.py                # CLI entry point — thin wrapper around pipeline_runner.py
├── pipeline_ui.py           # Streamlit web UI — live pipeline stepper, file browser, downloads
├── pipeline_runner.py        # shared core logic used by BOTH main.py and pipeline_ui.py
├── agents.py                  # the 7 agents (roles, backstories, LLM config)
├── tasks.py                    # the 8 pipeline tasks and their context chaining
├── tools.py                     # auto-patching, syntax/DB-init/endpoint/consistency repair loops
├── requirements.txt
├── SETUP.md                      # detailed setup + troubleshooting + course concept mapping
├── PROJECT_OVERVIEW.md             # plain-language explainer for group members
└── outputs/                         # generated projects, one subfolder per idea
```

`pipeline_runner.py` is the important one to understand — both entry points call the same `run_pipeline()` function, so the CLI and the UI always behave identically.

## Known limitations

- The self-debugging system catches syntax, database-structure, runtime-crash, and frontend/backend URL-mismatch bugs — but not logic bugs where code runs fine but does the wrong thing (e.g. an endpoint returning the wrong field), or mismatched JSON response shapes.
- Output quality depends on the local model's capability; results will vary with different Ollama models.
- Each repair stage is capped at a fixed number of attempts (not an unlimited loop), so a very unusual bug can still slip through.
- Endpoint/consistency checks use dummy data — they verify routes don't crash and URLs exist, not that business logic is correct.

## Course context

Built as a course project demonstrating: multi-agent orchestration, tool calling, code generation, and file management using CrewAI and Ollama.

## Contributors

# AI Software Development Team — Multi-Agent Dev Pipeline

A multi-agent AI pipeline built with **CrewAI** and **Ollama** that takes a one-line product idea and generates a full software project: requirements, database schema, API docs, backend code, frontend, tests, and documentation — with a multi-stage self-debugging system that actually runs the generated code to catch and fix real bugs before you ever see them.

## What it does

Give it a prompt like `"Create a Library Management System"`, and it runs that idea through a team of 7 AI agents, each specialized like a real dev team role, producing 8 output files — either from the command line or a web UI.

## The agent team

| # | Agent | Role |
|---|---|---|
| 1 | Requirement Analyst | Writes the SRS (Software Requirements Specification) |
| 2 | System Designer | Designs the database schema and REST API contract |
| 3 | Backend Developer | Implements the Flask backend |
| 4 | Frontend Developer | Builds an HTML/CSS/JS frontend |
| 5 | Code Reviewer | Reviews backend + frontend for bugs, documents findings |
| 6 | QA Tester | Writes pytest unit tests |
| 7 | Documentation Writer | Writes the final README for the generated app |

## Pipeline flow

```
Product idea
    │
    ▼
Requirement Analyst   →  SRS.md
    │
    ▼
System Designer       →  schema.sql, API_DOCS.md
    │
    ▼
Backend Developer      →  app.py
    │            ⤷ auto-patched + repair loop runs HERE, before Frontend starts
    ▼
Frontend Developer     →  index.html  (built against the ALREADY-FIXED backend)
    │            ⤷ frontend URLs checked against real backend routes
    ▼
Code Reviewer          →  REVIEW_REPORT.md
    │
    ▼
QA Tester               →  test_app.py
    │
    ▼
Documentation Writer     →  README.md
```

Each stage receives the previous stages' outputs as context, so decisions made early (e.g. the database schema) flow through to later stages automatically. Critically, the backend's repair loop runs **immediately after the Backend Developer finishes** — not after the whole crew is done — so the Frontend Developer always builds against the final, corrected backend rather than a draft that's about to change.

## Self-debugging system

Before any file is saved, it goes through automated checks — real execution feedback, not just an LLM's opinion of its own code.

**Deterministic auto-patches** (plain code, no AI, 100% reliable):
- Adds `flask-cors` + `CORS(app)` if missing
- Wraps `db.create_all()` in `with app.app_context():` if it isn't already
- Forces the database to SQLite and strips MySQL/Postgres driver imports (no external DB server exists in this environment)
- Adds `required` to every frontend `<input>` (skipping hidden/submit/button/checkbox/radio)

**`app.py` repair loop** (up to 5 attempts per stage, real error fed back to the model each time):
1. **Syntax** — `ast.parse()`
2. **Database initialization** — actually imports the code and runs `db.create_all()` in an isolated subprocess, catching missing primary keys, bad foreign keys, undefined names
3. **Endpoint smoke test** — spins up Flask's test client and fires a request at every registered route, flagging any that crash with a 500

**`index.html` consistency check** (up to 3 attempts) — extracts every `/api/...` URL the frontend actually calls and cross-checks it against the real routes registered in the backend (introspected directly, not guessed from docs), fixing any mismatch.

**`test_app.py`** — syntax check only.

A **"skip debug loops"** option is available (CLI prompt or UI checkbox) for a much faster run when you just need a quick draft — auto-patches still apply, only the slower LLM-retry cycles are skipped.

## Tech stack

- **CrewAI** — multi-agent orchestration framework
- **Ollama** — runs the LLM locally (`qwen2.5-coder:7b`), free, no API key
- **Streamlit** — the web UI
- **Flask + Flask-SQLAlchemy** — generated backend stack
- **Python 3.12**

## Setup

See [`SETUP.md`](./SETUP.md) for full installation and run instructions.

Quick version:
```
ollama pull qwen2.5-coder:7b
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

**Run it — two ways:**
```
python main.py                  # command line
streamlit run pipeline_ui.py     # web UI (recommended) — opens at localhost:8501
```

Output is saved to `outputs/<slugified-idea>/`, one subfolder per idea you've tried.

## Project structure

```
AI_Software_Dev_Team/
├── main.py                # CLI entry point — thin wrapper around pipeline_runner.py
├── pipeline_ui.py           # Streamlit web UI — live pipeline stepper, file browser, downloads
├── pipeline_runner.py        # shared core logic used by BOTH main.py and pipeline_ui.py
├── agents.py                  # the 7 agents (roles, backstories, LLM config)
├── tasks.py                    # the 8 pipeline tasks and their context chaining
├── tools.py                     # auto-patching, syntax/DB-init/endpoint/consistency repair loops
├── requirements.txt
├── SETUP.md                      # detailed setup + troubleshooting + course concept mapping
├── PROJECT_OVERVIEW.md             # plain-language explainer for group members
└── outputs/                         # generated projects, one subfolder per idea
```

`pipeline_runner.py` is the important one to understand — both entry points call the same `run_pipeline()` function, so the CLI and the UI always behave identically.

## Known limitations

- The self-debugging system catches syntax, database-structure, runtime-crash, and frontend/backend URL-mismatch bugs — but not logic bugs where code runs fine but does the wrong thing (e.g. an endpoint returning the wrong field), or mismatched JSON response shapes.
- Output quality depends on the local model's capability; results will vary with different Ollama models.
- Each repair stage is capped at a fixed number of attempts (not an unlimited loop), so a very unusual bug can still slip through.
- Endpoint/consistency checks use dummy data — they verify routes don't crash and URLs exist, not that business logic is correct.

## Course context

Built as a course project demonstrating: multi-agent orchestration, tool calling, code generation, and file management using CrewAI and Ollama.

## Contributors

Udit Hasan
Sovan Mukherjee
Trisha De
Trini Hazra
Upama Chakraborty
Supratim Biswas