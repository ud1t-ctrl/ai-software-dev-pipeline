"""
Entry point for the command-line version. This is what you run: `python main.py`

All the actual logic lives in pipeline_runner.py, shared with the Streamlit
UI (pipeline_ui.py) so both entry points behave identically.
"""

from pipeline_runner import run_pipeline

if __name__ == "__main__":
    # 1. Ask for a short, safe folder name first
    folder_name = input("Enter a short name for the output folder (e.g. 'student-app'): ").strip()
    if not folder_name:
        folder_name = "default-app"

    # 2. Ask for the detailed project idea for the AI
    project_idea = input("Enter the full detailed prompt for the agents: ").strip()
    if not project_idea:
        project_idea = "Create a Library Management System"
        print(f"No input given, defaulting to: {project_idea}")

    # 3. Pass BOTH variables to the runner
    run_folder, results = run_pipeline(project_idea, folder_name, progress=print)

    print(f"\n===== PIPELINE COMPLETE =====")
    print(f"Check the outputs/{run_folder}/ folder for all 8 files.")
    failed = [r["filename"] for r in results if not r["ok"]]
    if failed:
        print(f"Note: these files didn't pass full validation and may need manual review: {', '.join(failed)}")