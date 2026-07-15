# AI Software Development Team — Multi-Agent Dev Pipeline

A multi-agent AI pipeline built with **CrewAI** and **Ollama** that takes a one-line product idea and generates a full software project: requirements, database schema, API docs, backend code, frontend, tests, and documentation — with a built-in self-debugging loop.

## What it does

Give it a prompt like `"Create a Library Management System"`, and it runs that idea through a team of 7 AI agents, each specialized like a real dev team role, producing 8 output files.

## The agent team

| Agent | Role |
|---|---|
| Requirement Analyst | Writes the SRS (Software Requirements Specification) |
| System Designer | Designs the database schema and REST API contract |
| Backend Developer | Implements the Flask backend |
| Frontend Developer | Builds an HTML/CSS/JS frontend |
| Code Reviewer | Reviews backend + frontend for bugs, rewrites corrected versions |
| QA Tester | Writes pytest unit tests |
| Documentation Writer | Writes the final README for the generated app |

## Pipeline flow

```
Product idea
    │
    ▼
Requirement Analyst  →  SRS.md
    │
    ▼
System Designer  →  schema.sql, API_DOCS.md
    │
    ▼
Backend Developer  →  app.py
    │
    ▼
Frontend Developer  →  index.html
    │
    ▼
Code Reviewer  →  REVIEW_REPORT.md (+ corrected app.py / index.html)
    │
    ▼
QA Tester  →  test_app.py
    │
    ▼
Documentation Writer  →  README.md
```

Each stage receives the previous stages' outputs as context, so decisions made early (e.g. the database schema) flow through to later stages (e.g. the backend code) automatically.

## Self-debugging loop

After the crew finishes generating text, `app.py` goes through an automated repair loop **before** it's saved:

1. **Syntax check** — `ast.parse()` catches broken Python. If it fails, the exact error is sent back to the model for a fix.
2. **Database initialization check** — the generated code is actually imported and `db.create_all()` is run in an isolated subprocess, catching real structural bugs (missing primary keys, bad foreign keys, undefined names) that a syntax check alone can't see.

Each check retries with the model up to 5 times, feeding back the real error each time — this is genuine execution feedback, not just an LLM's opinion of its own code.

`test_app.py` goes through the syntax check only.

## Tech stack

- **CrewAI** — multi-agent orchestration framework
- **Ollama** — runs the LLM locally (`qwen2.5-coder:7b`), free, no API key
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
python main.py
```

You'll be prompted for a project idea — output is saved to `outputs/<slugified-idea>/`.

## Project structure

```
AI_Software_Dev_Team/
├── main.py              # entry point — runs the crew, then the debug loop, then saves files
├── agents.py             # the 7 agents (roles, backstories, LLM config)
├── tasks.py               # the 8 pipeline tasks and their context chaining
├── tools.py                # file saving, run folders, syntax + DB-init repair loops
├── requirements.txt
├── SETUP.md               # detailed setup + troubleshooting + course concept mapping
└── outputs/                # generated projects, one subfolder per idea
```

## Known limitations

- The self-debugging loop catches syntax and database-initialization errors, but not logic bugs (e.g. an endpoint returning the wrong data) — those still need manual review or the Code Reviewer agent's judgment.
- Output quality depends on the local model's capability; results will vary with different Ollama models.
- This is a one-shot review/fix pass per stage, not an unlimited iterative loop.

## Course context

Built as a course project demonstrating: multi-agent orchestration, tool calling, code generation, and file management using CrewAI and Ollama.

## Contributors

- Udit Hasan 
- Sovan Mukherjee
- Trisha De
- Trini Hazra
- Upama Chakraborty
- Supratim Biswas

