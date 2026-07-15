"""
Task definitions.

Each Task is one unit of work for one agent, and maps to exactly ONE
output file (see the FILE_MAP at the bottom, used by main.py to save
everything after the crew finishes).

The `context` field is the pipeline-chaining mechanism: passing
[task_a, task_b] as context means this task automatically receives
task_a's and task_b's outputs as input.

{project_idea} is a template variable, filled in at runtime via
crew.kickoff(inputs={"project_idea": ...}) in main.py.
"""

from crewai import Task
from agents import (
    requirement_analyst,
    system_designer,
    backend_developer,
    frontend_developer,
    code_reviewer,
    qa_tester,
    documentation_writer,
)

# 1. Requirements -> SRS.md
task_srs = Task(
    description=(
        "The product idea is: '{project_idea}'. Write a complete SRS document covering: "
        "purpose, scope, functional requirements (identify the core entities and actions "
        "this app needs based on the idea), non-functional requirements, and user roles "
        "relevant to this specific app. Respond with ONLY the SRS content in markdown."
    ),
    expected_output="The full SRS document in markdown, nothing else.",
    agent=requirement_analyst,
)

# 2. Database schema -> schema.sql
task_schema = Task(
    description=(
        "Using the SRS above, design a normalized relational database schema (tables, "
        "columns, types, keys, relationships) for this app. Respond with ONLY valid SQL "
        "CREATE TABLE statements, wrapped in a single ```sql code block."
    ),
    expected_output="SQL CREATE TABLE statements in one code block, nothing else.",
    agent=system_designer,
    context=[task_srs],
)

# 3. API contract -> API_DOCS.md
task_api_docs = Task(
    description=(
        "Using the SRS and database schema above, write a REST API contract listing every "
        "endpoint needed for this app: method, path, request body, response body. "
        "Respond with ONLY the API documentation in markdown."
    ),
    expected_output="The full API documentation in markdown, nothing else.",
    agent=system_designer,
    context=[task_srs, task_schema],
)

# 4. Backend -> app.py
task_backend = Task(
    description=(
        "Using the database schema and API contract above, implement the backend in "
        "Python using Flask: app setup, database models/connection, and every endpoint "
        "from the API contract with basic error handling. Respond with ONLY the code, "
        "wrapped in a single ```python code block."
    ),
    expected_output="Complete Flask app code in one code block, nothing else.",
    agent=backend_developer,
    context=[task_schema, task_api_docs],
)

# 5. Frontend -> index.html
task_frontend = Task(
    description=(
        "Using the API contract and backend code above, build a simple frontend "
        "(single HTML file with embedded CSS/JS) that lets a user interact with every "
        "core feature of this app by calling the backend API endpoints. Respond with "
        "ONLY the code, wrapped in a single ```html code block."
    ),
    expected_output="Complete HTML/CSS/JS code in one code block, nothing else.",
    agent=frontend_developer,
    context=[task_api_docs, task_backend],
)

# 6. Review -> REVIEW_REPORT.md (a report, not a code rewrite - simpler & more reliable)
task_review = Task(
    description=(
        "Review the backend code and frontend code above against the database schema and "
        "API contract. List every issue found: bugs, missing error handling, security "
        "issues (e.g. SQL injection, unvalidated input), and mismatches between backend "
        "and frontend. For each issue, explain exactly how to fix it. Respond with ONLY "
        "this review report in markdown."
    ),
    expected_output="A markdown review report listing issues and fixes, nothing else.",
    agent=code_reviewer,
    context=[task_schema, task_api_docs, task_backend, task_frontend],
)

# 7. QA -> test_app.py
task_qa = Task(
    description=(
        "Using the backend code and review report above, write pytest unit tests covering "
        "each API endpoint: normal case, edge case, and error case. Respond with ONLY the "
        "code, wrapped in a single ```python code block."
    ),
    expected_output="Complete pytest test code in one code block, nothing else.",
    agent=qa_tester,
    context=[task_backend, task_review],
)

# 8. Docs -> README.md
task_readme = Task(
    description=(
        "Using the SRS, schema, API docs, backend, frontend, review report, and tests "
        "above, write a README.md covering: project overview (what is '{project_idea}'), "
        "tech stack, setup/installation steps, how to run the backend, how to run the "
        "tests, a summary of the API endpoints, and a short 'Known Issues' section based "
        "on the review report. Respond with ONLY the README content in markdown."
    ),
    expected_output="The full README in markdown, nothing else.",
    agent=documentation_writer,
    context=[task_srs, task_api_docs, task_review, task_qa],
)

# Maps each task to its output filename and whether to strip a code fence.
# Used by main.py after the crew finishes.
FILE_MAP = [
    (task_srs, "SRS.md", False),
    (task_schema, "schema.sql", True),
    (task_api_docs, "API_DOCS.md", False),
    (task_backend, "app.py", True),
    (task_frontend, "index.html", True),
    (task_review, "REVIEW_REPORT.md", False),
    (task_qa, "test_app.py", True),
    (task_readme, "README.md", False),
]
