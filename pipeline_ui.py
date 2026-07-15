"""
Streamlit UI for the AI Software Development Pipeline.

Run with:  streamlit run pipeline_ui.py
"""

import io
import time
import zipfile

import streamlit as st

from pipeline_runner import run_pipeline, check_ollama_available, AGENT_TEAM

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Dev Team",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom styling ───────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .sub-header {
        color: #888;
        font-size: 1.05rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background: rgba(120, 120, 120, 0.08);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-left: 3px solid #6c63ff;
    }
    .agent-name {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .agent-desc {
        font-size: 0.82rem;
        color: #999;
    }
    .status-ok {
        color: #2ecc71;
        font-weight: 600;
    }
    .status-warn {
        color: #f39c12;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
</style>
""", unsafe_allow_html=True)

LANGUAGE_MAP = {
    ".py": "python",
    ".html": "html",
    ".md": "markdown",
    ".sql": "sql",
}


def lang_for(filename: str) -> str:
    for ext, lang in LANGUAGE_MAP.items():
        if filename.endswith(ext):
            return lang
    return "text"


# ── Sidebar: agent team + info ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧑‍💻 The Agent Team")
    for name, desc in AGENT_TEAM:
        st.markdown(
            f'<div class="agent-card">'
            f'<div class="agent-name">{name}</div>'
            f'<div class="agent-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### ⚙️ Model")
    st.caption("Running locally via Ollama — `qwen2.5-coder:7b`")

    ollama_up = check_ollama_available()
    if ollama_up:
        st.success("Ollama is reachable")
    else:
        st.error("Ollama not reachable at localhost:11434")

    st.markdown("---")
    if st.button("🔄 Reset session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">🤖 AI Software Development Pipeline</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Describe an app idea. A 7-agent AI team will generate requirements, '
    'a database schema, API docs, backend code, a frontend, tests, and documentation — '
    'with automatic bug detection and repair.</p>',
    unsafe_allow_html=True,
)

# ── Session state defaults ──────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.run_folder = None
    st.session_state.elapsed = None

# ── Input form ────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    idea = st.text_input(
        "App idea",
        placeholder="e.g. Create a Library Management System",
        label_visibility="collapsed",
    )
with col2:
    run_clicked = st.button(
        "▶ Run Pipeline",
        type="primary",
        use_container_width=True,
        disabled=not ollama_up,
    )

if not ollama_up:
    st.warning("Start Ollama first (`ollama serve`), then refresh this page.")

# ── Run the pipeline ─────────────────────────────────────────────────────
if run_clicked and idea.strip():
    log_container = st.status("Starting pipeline...", expanded=True)
    log_lines = []

    def progress(msg: str):
        log_lines.append(msg)
        log_container.write(msg)

    start = time.time()
    try:
        run_folder, results = run_pipeline(idea.strip(), progress=progress)
        elapsed = time.time() - start
        log_container.update(label=f"Pipeline complete in {elapsed:.0f}s", state="complete")
        st.session_state.results = results
        st.session_state.run_folder = run_folder
        st.session_state.elapsed = elapsed
        st.balloons()
    except Exception as e:
        log_container.update(label="Pipeline failed", state="error")
        st.error(f"Something went wrong: {e}")

elif run_clicked and not idea.strip():
    st.warning("Type an app idea first.")

# ── Results ──────────────────────────────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results
    run_folder = st.session_state.run_folder
    elapsed = st.session_state.elapsed

    st.markdown("---")
    st.markdown(f"### 📦 Generated: `{run_folder}`")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Files generated", len(results))
    m2.metric("Total size", f"{sum(len(r['content'] or '') for r in results):,} chars")
    m3.metric("Time taken", f"{elapsed:.0f}s")
    m4.metric("Passed validation", f"{sum(1 for r in results if r['ok'])}/{len(results)}")

    # Zip download for everything at once
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            zf.writestr(r["filename"], r["content"] or "")
    st.download_button(
        "⬇ Download all files (.zip)",
        data=zip_buffer.getvalue(),
        file_name=f"{run_folder}.zip",
        mime="application/zip",
        use_container_width=False,
    )

    st.markdown("#### Files")
    for r in results:
        status_html = (
            '<span class="status-ok">✓ passed validation</span>' if r["ok"]
            else '<span class="status-warn">⚠ needs review</span>'
        )
        with st.expander(f"📄 {r['filename']}  —  {len(r['content'] or ''):,} chars"):
            st.markdown(status_html, unsafe_allow_html=True)
            st.code(r["content"] or "(empty)", language=lang_for(r["filename"]))
            st.download_button(
                "Download this file",
                data=r["content"] or "",
                file_name=r["filename"],
                key=f"dl_{r['filename']}",
            )
