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
```
python main.py
```

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
7. **Syntax + database-initialization repair loop** → after the crew finishes, `app.py` goes through `debug_fix_backend_code()` in `tools.py`, which runs TWO checks:
   - **Syntax**: `ast.parse()` — catches broken Python (mismatched brackets, etc.)
   - **Structural/schema**: actually imports the code in an isolated subprocess and calls `db.create_all()` inside an app context — catches missing primary keys, bad foreign key references, undefined names, and similar real bugs that only surface when the code actually runs. `test_app.py` gets syntax-checking only.

   Each failure gets fed back to the model as an exact error message, and it retries (up to 5 times per stage). This is the closest thing to genuine self-debugging in the pipeline: real execution feedback, not just an LLM's opinion of its own code.

Note: this still doesn't catch every possible bug (e.g. an endpoint that runs fine but returns the wrong data, or a frontend/backend mismatch) — those need the Code Reviewer's judgment or your own testing. But it now catches the exact category of bugs you ran into by hand (missing primary key, `db.create_all()` needing an app context) automatically, before the files even get saved.
