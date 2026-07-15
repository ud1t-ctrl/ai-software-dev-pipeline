"""
Entry point. This is what you run: `python main.py`

The Crew ties agents + tasks together and runs them.
Process.sequential = run tasks in the exact order listed, one after another.

Files are saved AFTER the crew finishes, in Python code, using each task's
raw text output (task.output.raw). This avoids relying on local models to
correctly call a "save file" tool, which is unreliable over Ollama.
"""

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
from tools import set_run_folder, write_output_file, debug_fix_python_code, debug_fix_backend_code, _strip_code_fence

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

if __name__ == "__main__":
    project_idea = input("What app should the pipeline build? (e.g. 'Create a Library Management System'): ").strip()
    if not project_idea:
        project_idea = "Create a Library Management System"
        print(f"No input given, defaulting to: {project_idea}")

    run_folder = set_run_folder(project_idea)
    pipeline_crew.kickoff(inputs={"project_idea": project_idea})

    print("\n\n===== SAVING OUTPUT FILES =====")
    for task, filename, strip_fence in FILE_MAP:
        raw = task.output.raw if task.output else ""
        content = _strip_code_fence(raw) if strip_fence else raw

        if filename == "app.py":
            print(f"\n[{filename}] Running syntax + database-initialization repair loop...")
            content = debug_fix_backend_code(content, ollama_llm, max_attempts=5)
        elif filename.endswith(".py"):
            print(f"\n[{filename}] Running syntax-check-and-repair loop...")
            content = debug_fix_python_code(content, filename, ollama_llm, max_attempts=5)

        path = write_output_file(filename, content, strip_fence=False)
        size = len(content or "")
        print(f"Saved {path} ({size} chars)")

    print(f"\n===== PIPELINE COMPLETE =====")
    print(f"Check the outputs/{run_folder}/ folder for all 8 files.")