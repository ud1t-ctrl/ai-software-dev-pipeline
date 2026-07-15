"""
Core pipeline execution logic — shared by main.py (CLI) and pipeline_ui.py
(Streamlit UI), so both entry points run the exact same code with no
duplication.
"""

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
    auto_patch_backend_code,
    auto_patch_frontend_code,
    check_db_initialization,
    check_endpoint_smoke_test,
    _strip_code_fence,
)
import ast

pipeline_crew = Crew(
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


def check_ollama_available(base_url: str = "http://localhost:11434") -> bool:
    """Quick reachability check — used by the UI to warn before running."""
    try:
        urllib.request.urlopen(base_url, timeout=3)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def run_pipeline(project_idea: str, folder_name: str = None, progress=print):
    """
    Runs the full 8-stage pipeline for the given idea: kicks off the crew,
    then saves + auto-patches + debug-loops each file.
    """
    # If no folder_name is provided (like when running the Streamlit UI), 
    # automatically generate a short one from the project idea to prevent Windows crashes.
    if not folder_name:
        folder_name = project_idea[:40].strip()

    run_folder = set_run_folder(folder_name)
    
    progress(f"Starting pipeline for: \u201c{folder_name}\u201d")
    progress(f"Output folder: outputs/{run_folder}/")

    progress("Running the 8-agent crew (this is the slow part)...")
    
    # Pass the massive, detailed project_idea to the CrewAI agents
    pipeline_crew.kickoff(inputs={"project_idea": project_idea})
    
    progress("Crew finished. Saving, auto-patching, and debugging files...")

    results = []
    for task, filename, strip_fence in FILE_MAP:
        raw = task.output.raw if task.output else ""
        content = _strip_code_fence(raw) if strip_fence else raw
        ok = True

        if filename == "app.py":
            progress(f"[{filename}] Applying auto-patches (CORS, app context)...")
            content = auto_patch_backend_code(content)
            progress(f"[{filename}] Running syntax + DB-init + endpoint-smoke-test loop...")
            content = debug_fix_backend_code(content, ollama_llm, max_attempts=5)
            # Final validation pass
            try:
                ast.parse(content)
                ok = check_db_initialization(content) is None and check_endpoint_smoke_test(content) is None
            except SyntaxError:
                ok = False
        elif filename.endswith(".py"):
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

        path = write_output_file(filename, content, strip_fence=False)
        progress(f"Saved {path} ({len(content or '')} chars)")
        results.append({"filename": filename, "path": path, "content": content, "ok": ok})

    progress("Pipeline complete.")
    return run_folder, results
