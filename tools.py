"""
Output-saving helpers.

We no longer rely on the LLM calling a "tool" to save files — local models
over Ollama don't reliably trigger CrewAI's native tool-calling, even when
asked to. Instead, agents just write their answer as plain text, and these
functions save that text to disk AFTER the crew finishes (called from
main.py). This is more reliable across different local models.
"""

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

BASE_OUTPUT_DIR = "outputs"
_current_run_folder = "default"


def set_run_folder(project_idea: str) -> str:
    """
    Turns the project idea into a safe folder name (e.g.
    'Create a Library Management System' -> 'create-a-library-management-system')
    and stores it for write_output_file to use.
    """
    global _current_run_folder
    slug = re.sub(r"[^a-z0-9]+", "-", project_idea.lower()).strip("-")
    _current_run_folder = slug or "default"
    os.makedirs(os.path.join(BASE_OUTPUT_DIR, _current_run_folder), exist_ok=True)
    return _current_run_folder


def _strip_code_fence(content: str) -> str:
    """
    Extracts the FIRST ```lang ... ``` code block anywhere in the content,
    discarding anything before or after it. Local models often add trailing
    commentary after the code (e.g. "Note: install X first...") even when
    told to respond with ONLY code — this ensures that extra text never
    leaks into the saved file.
    """
    content = content.strip()
    match = re.search(r"```[a-zA-Z]*\n(.*?)\n```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    # No fence found at all — fall back to the raw content as-is.
    return content


def write_output_file(filename: str, content: str, strip_fence: bool = False) -> str:
    """
    Saves content to outputs/<run_folder>/<filename>.
    Set strip_fence=True for code files (app.py, index.html, test_app.py)
    where the model likely wrapped the code in a markdown fence.
    """
    run_dir = os.path.join(BASE_OUTPUT_DIR, _current_run_folder)
    os.makedirs(run_dir, exist_ok=True)
    if strip_fence:
        content = _strip_code_fence(content)
    path = os.path.join(run_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or "")
    return path


def debug_fix_python_code(code: str, filename: str, llm, max_attempts: int = 5) -> str:
    """
    Syntax-checks Python code using ast.parse (no execution, just parsing —
    fast and doesn't risk running a Flask server or hitting missing packages).
    If it's broken, sends the exact error back to the LLM and asks for a fix,
    repeating up to max_attempts times. This is what makes the pipeline
    "self-debugging" instead of one-shot generation.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            ast.parse(code)
            print(f"  [{filename}] Syntax OK on attempt {attempt}")
            return code
        except SyntaxError as e:
            print(f"  [{filename}] Syntax error on attempt {attempt}: {e}")
            if attempt == max_attempts:
                print(f"  [{filename}] Max attempts reached — saving as-is (still has errors).")
                return code

            fix_prompt = (
                f"The following Python code has a syntax error that must be fixed.\n\n"
                f"ERROR: {e}\n\n"
                f"CODE:\n```python\n{code}\n```\n\n"
                f"Return ONLY the complete corrected Python code in a single "
                f"```python code block. Do not include any explanation, notes, "
                f"or text before or after the code block."
            )
            response = llm.call([{"role": "user", "content": fix_prompt}])
            code = _strip_code_fence(response)
    return code


def check_db_initialization(app_code: str, timeout: int = 30) -> str | None:
    """
    Actually imports the given Flask app code in an isolated subprocess and
    calls db.create_all() inside an app context — WITHOUT starting the server
    (app.run() is never reached since it's imported, not run as __main__).

    This catches real structural bugs that ast.parse can't see: missing
    primary keys, bad foreign key references, missing imports, undefined
    names used at import time, etc. Runs in a throwaway temp directory so it
    never touches your real project files or database.

    Returns None if it initialized cleanly, or the error output (string) if
    something failed.
    """
    tmp_dir = tempfile.mkdtemp(prefix="pipeline_check_")
    try:
        app_path = os.path.join(tmp_dir, "app_under_test.py")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(app_code)

        harness = textwrap.dedent(f"""
            import sys, traceback
            sys.path.insert(0, {tmp_dir!r})
            try:
                import app_under_test as m
                with m.app.app_context():
                    m.db.create_all()
                print("DB_CHECK_OK")
            except Exception:
                print("DB_CHECK_FAILED")
                traceback.print_exc()
                sys.exit(1)
        """)
        harness_path = os.path.join(tmp_dir, "_harness.py")
        with open(harness_path, "w", encoding="utf-8") as f:
            f.write(harness)

        try:
            result = subprocess.run(
                [sys.executable, harness_path],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return (
                f"Timed out after {timeout}s — likely a blocking call (e.g. "
                f"app.run()) that isn't properly guarded by "
                f"`if __name__ == '__main__':`."
            )

        if result.returncode == 0 and "DB_CHECK_OK" in result.stdout:
            return None
        return (result.stdout + result.stderr).strip()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def debug_fix_backend_code(code: str, llm, max_attempts: int = 5) -> str:
    """
    Full repair loop for app.py: first fixes syntax errors (ast.parse), THEN
    fixes structural/schema errors by actually initializing the database
    (check_db_initialization). This is what catches things like a missing
    primary key or a bad foreign key reference — real execution feedback,
    not just an LLM's opinion.
    """
    # Stage 1: syntax
    code = debug_fix_python_code(code, "app.py", llm, max_attempts=max_attempts)

    # Stage 2: does it actually initialize a real database correctly?
    for attempt in range(1, max_attempts + 1):
        error = check_db_initialization(code)
        if error is None:
            print(f"  [app.py] Database initialization OK on attempt {attempt}")
            return code

        print(f"  [app.py] DB init error on attempt {attempt}:\n{error[:500]}")
        if attempt == max_attempts:
            print(f"  [app.py] Max attempts reached — saving as-is (may still have structural bugs).")
            return code

        fix_prompt = (
            f"The following Flask + SQLAlchemy code fails when actually "
            f"initializing the database (db.create_all()). This usually means "
            f"a missing primary key, a bad db.ForeignKey() reference (wrong "
            f"table/column name), a missing import, or a similar structural "
            f"issue — not a syntax error.\n\n"
            f"ERROR OUTPUT:\n{error}\n\n"
            f"CODE:\n```python\n{code}\n```\n\n"
            f"Return ONLY the complete corrected Python code in a single "
            f"```python code block. Do not include any explanation, notes, "
            f"or text before or after the code block."
        )
        response = llm.call([{"role": "user", "content": fix_prompt}])
        code = _strip_code_fence(response)
        # Re-check syntax after the fix, in case the model introduced a new one
        code = debug_fix_python_code(code, "app.py", llm, max_attempts=2)
    return code