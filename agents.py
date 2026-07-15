"""
Agent definitions.

Each Agent = an LLM configured with a role, a goal, and a backstory.
The backstory isn't decoration — it steers the tone/quality of output
(a "senior backend developer" writes differently than a generic bot).

llm: we point every agent at a local Ollama model instead of a paid API.
Make sure `ollama serve` is running and you've pulled a model, e.g.:
    ollama pull llama3.1

NOTE: Agents no longer have a "Save File Tool" — local models over Ollama
don't reliably trigger CrewAI's tool-calling, so saving happens in Python
after the crew finishes (see main.py + tools.py). Agents just focus on
writing the best possible content as their answer.
"""

from crewai import Agent, LLM

# qwen2.5-coder is fine-tuned specifically for code (vs llama3.1's general-purpose
# training), so it tends to produce fewer syntax errors and less stray commentary
# mixed into code output. Pull it first: ollama pull qwen2.5-coder:7b
ollama_llm = LLM(
    model="ollama/qwen2.5-coder:7b",
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # dummy value — Ollama ignores it, but the OpenAI-compatible client requires something here
)

requirement_analyst = Agent(
    role="Requirement Analyst",
    goal="Convert a one-line product idea into a clear, structured Software Requirements Specification (SRS)",
    backstory=(
        "You are a senior business analyst with 10 years of experience gathering "
        "software requirements. You write precise, unambiguous SRS documents covering "
        "functional requirements, non-functional requirements, user roles, and constraints."
    ),
    llm=ollama_llm,
    verbose=True,
)

system_designer = Agent(
    role="System Designer",
    goal="Design a normalized database schema and a REST API contract based on the SRS",
    backstory=(
        "You are a software architect who specializes in relational database design "
        "and RESTful API design. You produce clean schemas (tables, columns, types, keys, "
        "relationships) and clear API endpoint documentation (method, path, request/response bodies)."
    ),
    llm=ollama_llm,
    verbose=True,
)

backend_developer = Agent(
    role="Backend Developer",
    goal="Implement working backend code that matches the database schema and API contract",
    backstory=(
        "You are a senior Python backend developer. You write clean, runnable Flask code "
        "implementing the endpoints exactly as specified, including basic error handling. "
        "You respond with ONLY the code, wrapped in a single markdown code block."
    ),
    llm=ollama_llm,
    verbose=True,
)

frontend_developer = Agent(
    role="Frontend Developer",
    goal="Build a simple frontend that consumes the backend API",
    backstory=(
        "You are a frontend developer who builds clean, functional UIs with HTML/CSS/JavaScript "
        "that call the given API endpoints correctly. You respond with ONLY the code, wrapped in "
        "a single markdown code block."
    ),
    llm=ollama_llm,
    verbose=True,
)

code_reviewer = Agent(
    role="Code Reviewer",
    goal="Review the backend and frontend code for bugs, security issues, and mismatches with the API contract",
    backstory=(
        "You are a strict senior code reviewer. You carefully check code against the "
        "original design (schema and API contract) for: bugs, missing error handling, "
        "security issues (e.g. SQL injection, missing input validation), and inconsistencies "
        "between backend and frontend. You write a clear report listing every issue found "
        "and exactly how to fix it."
    ),
    llm=ollama_llm,
    verbose=True,
)

qa_tester = Agent(
    role="QA Tester",
    goal="Write unit tests that verify the backend code behaves as specified",
    backstory=(
        "You are a meticulous QA engineer who writes Python unit tests (using pytest) "
        "covering normal cases, edge cases, and error cases for each API endpoint. "
        "You respond with ONLY the code, wrapped in a single markdown code block."
    ),
    llm=ollama_llm,
    verbose=True,
)

documentation_writer = Agent(
    role="Documentation Writer",
    goal="Write a clear README that ties together the whole project",
    backstory=(
        "You are a technical writer who produces concise, well-structured README files: "
        "project overview, setup instructions, API summary, and how to run tests."
    ),
    llm=ollama_llm,
    verbose=True,
)