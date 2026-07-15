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


def auto_patch_backend_code(code: str) -> str:
    """
    Deterministic fixes applied with plain string/regex operations — NOT the
    LLM. These guarantee specific known gaps are fixed every single time,
    regardless of whether the model remembered to do them:
      1. Adds `from flask_cors import CORS` + `CORS(app)` if missing.
      2. Wraps a bare `db.create_all()` call in `with app.app_context():`
         if it isn't already inside one.
    """
    patched = code

    # 1. Ensure CORS is imported and enabled
    if "flask_cors" not in patched:
        if "from flask_sqlalchemy import SQLAlchemy" in patched:
            patched = patched.replace(
                "from flask_sqlalchemy import SQLAlchemy",
                "from flask_sqlalchemy import SQLAlchemy\nfrom flask_cors import CORS",
                1,
            )
        else:
            patched = "from flask_cors import CORS\n" + patched

    if re.search(r"CORS\s*\(\s*app\s*\)", patched) is None:
        patched = re.sub(
            r"(app\s*=\s*Flask\([^\)]*\)\s*\n)",
            r"\1CORS(app)\n",
            patched,
            count=1,
        )

    # 2. Ensure db.create_all() is wrapped in an app context
    lines = patched.split("\n")
    new_lines = []
    for line in lines:
        m = re.match(r"^(\s*)db\.create_all\(\)\s*$", line)
        if m:
            indent = m.group(1)
            prev = new_lines[-1].strip() if new_lines else ""
            if "app.app_context()" not in prev:
                new_lines.append(f"{indent}with app.app_context():")
                new_lines.append(f"{indent}    db.create_all()")
                continue
        new_lines.append(line)
    patched = "\n".join(new_lines)

    return patched


def auto_patch_frontend_code(html: str) -> str:
    """
    Deterministic fix: adds the `required` attribute to every <input> that
    doesn't already have it (skipping hidden/submit/button/checkbox/radio,
    where it either does nothing or could misbehave). This is what stops
    empty form submissions from reaching the backend at all — guaranteed,
    not dependent on the model remembering to add it.
    """
    def process(match):
        tag = match.group(0)
        if "required" in tag:
            return tag
        type_match = re.search(r"""type=["'](\w+)["']""", tag)
        input_type = type_match.group(1).lower() if type_match else "text"
        if input_type in ("hidden", "submit", "button", "checkbox", "radio"):
            return tag
        stripped = tag.rstrip()
        if stripped.endswith("/>"):
            return stripped[:-2].rstrip() + " required />"
        return stripped[:-1].rstrip() + " required>"

    return re.sub(r"<input\b[^>]*>", process, html)


def check_endpoint_smoke_test(app_code: str, timeout: int = 30) -> str | None:
    """
    Deeper than check_db_initialization: actually spins up Flask's test
    client and fires a request at EVERY registered route/method combination
    (using dummy values for path parameters and an empty JSON body for
    POST/PUT/PATCH). Catches real runtime crashes — e.g. a missing import
    used inside a route function, an unhandled IntegrityError — that only
    surface when a route actually executes, not just at import time.

    A 4xx response (bad request, not found, etc.) is considered fine — we're
    only flagging 5xx responses, since those mean the server crashed on an
    unhandled exception. Runs in an isolated temp dir/throwaway database.

    Returns None if every route responded without a 5xx, or a summary of
    which routes crashed and why.
    """
    tmp_dir = tempfile.mkdtemp(prefix="pipeline_endpoint_check_")
    try:
        app_path = os.path.join(tmp_dir, "app_under_test.py")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(app_code)

        harness = textwrap.dedent(f"""
            import sys, re, traceback
            sys.path.insert(0, {tmp_dir!r})
            try:
                import app_under_test as m
                m.app.testing = True
                with m.app.app_context():
                    m.db.create_all()
                client = m.app.test_client()

                def build_url(rule_str):
                    def repl(match):
                        conv = match.group(1)
                        return '1' if conv == 'int' else 'test'
                    return re.sub(r'<(?:(\\w+):)?(\\w+)>', repl, rule_str)

                errors = []
                tested = set()
                for rule in m.app.url_map.iter_rules():
                    methods = rule.methods - {{'HEAD', 'OPTIONS'}}
                    url = build_url(str(rule))
                    for method in methods:
                        key = (url, method)
                        if key in tested:
                            continue
                        tested.add(key)
                        try:
                            if method == 'GET':
                                resp = client.get(url)
                            elif method == 'DELETE':
                                resp = client.delete(url)
                            else:
                                resp = client.open(url, method=method, json={{}})
                            if resp.status_code >= 500:
                                body = resp.get_data(as_text=True)[:300]
                                errors.append(f"{{method}} {{url}} -> {{resp.status_code}}: {{body}}")
                        except Exception as e:
                            errors.append(f"{{method}} {{url}} -> EXCEPTION: {{e}}")

                if errors:
                    print("ENDPOINT_CHECK_FAILED")
                    print(chr(10).join(errors))
                    sys.exit(1)
                print("ENDPOINT_CHECK_OK")
            except Exception:
                print("ENDPOINT_CHECK_FAILED")
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
            return f"Timed out after {timeout}s during endpoint smoke test."

        if result.returncode == 0 and "ENDPOINT_CHECK_OK" in result.stdout:
            return None
        return (result.stdout + result.stderr).strip()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def debug_fix_backend_code(code: str, llm, max_attempts: int = 5) -> str:
    """
    Full repair loop for app.py, in three stages:
      1. Syntax (ast.parse)
      2. Database initialization (does db.create_all() actually work?)
      3. Endpoint smoke test (does every route respond without a 5xx crash
         when actually called?)
    Each stage runs after the previous one settles. This is real execution
    feedback at increasing depth, not just an LLM's opinion of its own code.
    """
    # Stage 1: syntax
    code = debug_fix_python_code(code, "app.py", llm, max_attempts=max_attempts)

    # Stage 2: does it actually initialize a real database correctly?
    for attempt in range(1, max_attempts + 1):
        error = check_db_initialization(code)
        if error is None:
            print(f"  [app.py] Database initialization OK on attempt {attempt}")
            break

        print(f"  [app.py] DB init error on attempt {attempt}:\n{error[:500]}")
        if attempt == max_attempts:
            print(f"  [app.py] Max attempts reached on DB init — moving on with current code.")
            break

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
        code = debug_fix_python_code(code, "app.py", llm, max_attempts=2)

    # Stage 3: does every registered route survive an actual request?
    for attempt in range(1, max_attempts + 1):
        error = check_endpoint_smoke_test(code)
        if error is None:
            print(f"  [app.py] Endpoint smoke test OK on attempt {attempt}")
            return code

        print(f"  [app.py] Endpoint smoke test error on attempt {attempt}:\n{error[:800]}")
        if attempt == max_attempts:
            print(f"  [app.py] Max attempts reached on endpoint test — saving as-is.")
            return code

        fix_prompt = (
            f"The following Flask code crashes with a 500 error (or an "
            f"unhandled exception) on one or more of its own routes when "
            f"actually called with a test request. This usually means: a "
            f"missing import used inside a route function, an unhandled "
            f"database exception (e.g. IntegrityError on a duplicate/invalid "
            f"value), or a bug in the route's logic.\n\n"
            f"ERROR OUTPUT:\n{error}\n\n"
            f"CODE:\n```python\n{code}\n```\n\n"
            f"Return ONLY the complete corrected Python code in a single "
            f"```python code block. Do not include any explanation, notes, "
            f"or text before or after the code block."
        )
        response = llm.call([{"role": "user", "content": fix_prompt}])
        code = _strip_code_fence(response)
        code = debug_fix_python_code(code, "app.py", llm, max_attempts=2)
    return code