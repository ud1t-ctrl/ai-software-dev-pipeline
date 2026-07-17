"""
Core pipeline execution logic — shared by main.py (CLI) and pipeline_ui.py
(Streamlit UI), so both entry points run the exact same code with no
duplication.
"""

import ast
import urllib.request
import urllib.error

from crewai import Crew, Process
from agents import (
    requirement_analyst,
    system_designer,
    backend_developer,
    frontend_developer,
    code_reviewer,
    qa_tester,
    documentation_writer,
    ollama_llm,
)
from tasks import (
    task_srs,
    task_schema,
    task_api_docs,
    task_backend,
    task_frontend,
    task_review,
    task_qa,
    task_readme,
    FILE_MAP,
)
from tools import (
    set_run_folder,
    write_output_file,
    debug_fix_python_code,
    debug_fix_backend_code,
    debug_fix_frontend_consistency,
    auto_patch_backend_code,
    auto_patch_frontend_code,
    check_db_initialization,
    check_endpoint_smoke_test,
    _strip_code_fence,
)

# Agent list exposed for the UI to display (role -> one-line description)
AGENT_TEAM = [
    ("Requirement Analyst", "Writes the SRS from your one-line idea"),
    ("System Designer", "Designs the database schema and API contract"),
    ("Backend Developer", "Implements the Flask backend"),
    ("Frontend Developer", "Builds the HTML/CSS/JS frontend"),
    ("Code Reviewer", "Reviews and corrects backend + frontend bugs"),
    ("QA Tester", "Writes pytest unit tests"),
    ("Documentation Writer", "Writes the generated app's README"),
]

# Order matches the tasks list below — used to label each task_callback firing
# and to detect exactly when the Backend Developer's task (index 3) finishes.
STAGE_LABELS = [
    "Requirement Analyst finished — SRS written",
    "System Designer finished — database schema designed",
    "System Designer finished — API docs written",
    "Backend Developer finished — Flask backend written",
    "Frontend Developer finished — frontend built",
    "Code Reviewer finished — bugs reviewed & corrected",
    "QA Tester finished — unit tests written",
    "Documentation Writer finished — README written",
]
BACKEND_STAGE_INDEX = 3


def check_ollama_available(base_url: str = "http://localhost:11434") -> bool:
    """Quick reachability check — used by the UI to warn before running."""
    try:
        urllib.request.urlopen(base_url, timeout=3)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def run_pipeline(project_idea: str, progress=print, skip_debug_loops: bool = False):
    """
    Runs the full 8-stage pipeline for the given idea.

    Key design point: the backend's auto-patch + syntax/DB-init/endpoint
    repair loop runs INSIDE a task_callback, immediately after the Backend
    Developer's task finishes and BEFORE the Frontend Developer's task
    starts. This means the frontend is always built against the corrected,
    final backend code — not a draft that's about to change. (Previously
    this repair loop ran only after the whole crew finished, so the
    frontend was coding against a version of the backend that hadn't been
    fixed yet.)

    `progress` is called with each high-level status line as the pipeline
    advances — pass `print` for the CLI, or a UI-aware callback for the
    web UI. Detailed per-attempt retry logs from the debug loops still
    print to the console regardless, since those are very high-volume for
    a UI to display live.

    `skip_debug_loops`: if True, all LLM-based repair loops (backend AND
    the frontend-backend consistency check) are skipped — files are saved
    right after the instant, free deterministic auto-patches.

    Returns (run_folder, results) where results is a list of dicts:
        {"filename": str, "path": str, "content": str, "ok": bool | None}
    `ok` is None when validation was skipped or not applicable.
    """
    run_folder = set_run_folder(project_idea)
    progress(f"Starting pipeline for: \u201c{project_idea}\u201d")
    progress(f"Output folder: outputs/{run_folder}/")
    if skip_debug_loops:
        progress("Debug/repair loops are SKIPPED — files will save as generated (auto-patches still apply).")

    stage_counter = {"i": 0}

    def on_task_complete(task_output):
        i = stage_counter["i"]
        if i < len(STAGE_LABELS):
            progress(f"\u2713 {STAGE_LABELS[i]}")

        if i == BACKEND_STAGE_INDEX and not skip_debug_loops:
            progress("[app.py] Backend finished \u2014 patching + repairing NOW, before the frontend starts...")
            raw = task_backend.output.raw if task_backend.output else ""
            fixed = _strip_code_fence(raw)
            fixed = auto_patch_backend_code(fixed)
            fixed = debug_fix_backend_code(fixed, ollama_llm, max_attempts=5)
            task_backend.output.raw = fixed
            progress("[app.py] Backend corrected \u2014 Frontend Developer will now see the fixed version.")

        stage_counter["i"] += 1

    crew = Crew(
        agents=[
            requirement_analyst,
            system_designer,
            backend_developer,
            frontend_developer,
            code_reviewer,
            qa_tester,
            documentation_writer,
        ],
        tasks=[
            task_srs,
            task_schema,
            task_api_docs,
            task_backend,
            task_frontend,
            task_review,
            task_qa,
            task_readme,
        ],
        process=Process.sequential,
        verbose=True,
        task_callback=on_task_complete,
    )

    progress("Running the 8-agent crew (this is the slow part)...")
    crew.kickoff(inputs={"project_idea": project_idea})
    progress("Crew finished. Saving files...")

    results = []
    backend_final_content = None  # captured while processing app.py, reused for index.html's consistency check

    for task, filename, strip_fence in FILE_MAP:
        raw = task.output.raw if task.output else ""
        content = _strip_code_fence(raw) if strip_fence else raw
        ok = None if skip_debug_loops else True

        if filename == "app.py":
            if skip_debug_loops:
                progress(f"[{filename}] Applying auto-patches (CORS, app context, SQLite)...")
                content = auto_patch_backend_code(content)
            else:
                # Already patched + repaired inside the task_callback above —
                # just do a final check to set the UI's status badge.
                try:
                    ast.parse(content)
                    ok = check_db_initialization(content) is None and check_endpoint_smoke_test(content) is None
                except SyntaxError:
                    ok = False
            backend_final_content = content

        elif filename.endswith(".py"):
            if not skip_debug_loops:
                progress(f"[{filename}] Running syntax-check-and-repair loop...")
                content = debug_fix_python_code(content, filename, ollama_llm, max_attempts=5)
                try:
                    ast.parse(content)
                    ok = True
                except SyntaxError:
                    ok = False

        elif filename == "index.html":
            progress(f"[{filename}] Applying auto-patch (required fields)...")
            content = auto_patch_frontend_code(content)
            if not skip_debug_loops and backend_final_content:
                progress(f"[{filename}] Checking frontend URLs match real backend routes...")
                content = debug_fix_frontend_consistency(content, backend_final_content, ollama_llm, max_attempts=3)

        path = write_output_file(filename, content, strip_fence=False)
        progress(f"Saved {path} ({len(content or '')} chars)")
        results.append({"filename": filename, "path": path, "content": content, "ok": ok})

    progress("Pipeline complete.")
    return run_folder, results