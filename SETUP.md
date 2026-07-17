# Setup Instructions

## 1. Install Ollama (runs the LLM locally, free, no API key)
- Download from https://ollama.com and install.
- Pull qwen2.5-coder — fine-tuned specifically for code, produces cleaner output than general-purpose models for this pipeline:
  ```
  ollama pull qwen2.5-coder:7b
  ```
- Start the Ollama server (usually starts automatically after install; if not):
  ```
  ollama serve
  ```
- Leave that terminal running. It serves at http://localhost:11434 by default.

## 2. Set up the Python project
```
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Run the pipeline

**Option A — command line:**
```
python main.py
```

**Option B — web UI (recommended):**
```
streamlit run pipeline_ui.py
```
This opens a browser tab automatically at `http://localhost:8501` with a text box for your app idea, a "Run Pipeline" button, live progress, and a file browser with syntax-highlighted previews and download buttons (individually or as one .zip) once it finishes. The sidebar shows the agent team and checks whether Ollama is reachable before letting you run anything.

Both entry points run the exact same underlying logic (`pipeline_runner.py`) — pick whichever you prefer.

You'll see each agent "think" and work in the terminal (verbose=True).
When it finishes, check the `outputs/` folder for:
SRS.md, schema.sql, API_DOCS.md, app.py, index.html, test_app.py, README.md

## 4. If something goes wrong
- **Connection refused / can't reach localhost:11434** → Ollama isn't running. Run `ollama serve` in a separate terminal.
- **Model not found** → run `ollama pull llama3.1` (or whichever model you set in `agents.py`).
- **Very slow / times out** → try a smaller model like `ollama pull mistral` and update `agents.py` accordingly. Local models are much slower than cloud APIs — a full 6-agent run can take several minutes depending on your machine.
- **Agent output is low quality** → this is normal with smaller local models. Tightening the `description` in `tasks.py` (be very specific) usually helps more than switching agents.

## How to explain this in your viva/demo
1. **Orchestration** → `main.py`'s `Crew(process=Process.sequential)` runs agents in order.
2. **Tool calling** → `tools.py`'s `save_file` — agents call this instead of just printing text.
3. **Code generation** → the Backend/Frontend/QA agents' task outputs *are* the generated code.
4. **File management** → `save_file` writes everything into a real `outputs/` folder structure.
5. **Context chaining** → each `Task`'s `context=[...]` parameter is what makes this a pipeline instead of disconnected prompts.
6. **Review/debug loop** → the Code Reviewer agent runs after Backend + Frontend, checks their output against the schema/API contract, and rewrites corrected versions with fixes explained in `REVIEW_REPORT.md`.
7. **Deterministic auto-patching** → before any LLM repair loop runs, `auto_patch_backend_code()` and `auto_patch_frontend_code()` in `tools.py` apply guaranteed fixes with plain string/regex operations — no AI involved, so these never depend on the model remembering: CORS gets added to the backend, `db.create_all()` gets wrapped in an app context if it isn't already, and every frontend `<input>` gets a `required` attribute (skipping hidden/submit/button/checkbox/radio).
8. **Syntax + database-initialization + endpoint-smoke-test repair loop** → after auto-patching, `app.py` goes through THREE checks in `debug_fix_backend_code()`:
   - **Syntax**: `ast.parse()`
   - **Structural**: actually imports the code and runs `db.create_all()` inside an app context — catches missing primary keys, bad foreign keys, undefined names.
   - **Runtime/endpoint**: spins up Flask's test client and fires a request at EVERY registered route (dummy path values, empty JSON body), flagging any 500 responses — catches crashes that only surface when a route actually runs, like a missing import inside a function or an unhandled `IntegrityError`. 4xx responses are fine; only 5xx counts as a bug.

   Each failure gets fed back to the model as the exact error, retried up to 5 times per stage. `test_app.py` still gets syntax-checking only.
9. **Fixed pipeline ordering (backend repairs happen BEFORE the frontend is written)** → previously, the backend's repair loop only ran after the ENTIRE crew finished — meaning the Frontend Developer was always coding against a draft, pre-repair version of the backend. Now, `run_pipeline()` uses CrewAI's `task_callback` to intercept the moment the Backend Developer's task finishes, run the full auto-patch + repair loop right then, and overwrite that task's output — so by the time the Frontend Developer's turn comes, it's building against the actual final backend code, not one that's about to change.
10. **Frontend-backend URL consistency check** → after the frontend is generated, `debug_fix_frontend_consistency()` extracts every `/api/...` URL the frontend's JavaScript actually calls and compares it against the REAL routes registered in the (now-finalized) backend — introspected directly via Flask's `url_map`, not guessed from documentation text. Any mismatch (wrong path, missing ID segment, typo) gets fed back to the model with the real route list, retried up to 3 times.

Note: even with all of this, some things still need human judgment — logic bugs where code runs fine but does the wrong thing, or response-shape mismatches (right URL, wrong field names in the JSON) that the consistency check doesn't cover. But the specific bugs hit during manual testing (missing primary key, missing CORS, unhandled duplicate-ISBN crash, missing `func` import, empty-form crashes, MySQL-driver crashes, and frontend/backend URL drift) are now caught automatically before the files are ever saved.