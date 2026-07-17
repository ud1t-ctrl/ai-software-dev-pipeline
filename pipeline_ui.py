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
    page_title="AI Dev Pipeline",
    page_icon="\u2699\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

STEP_LABELS = ["Requirements", "Schema", "API Docs", "Backend", "Frontend", "Review", "Tests", "Docs"]
STEP_ICONS = ["\U0001F4CB", "\U0001F5C3\ufe0f", "\U0001F4D8", "\u2699\ufe0f", "\U0001F5A5\ufe0f", "\U0001F50D", "\u2705", "\U0001F4C4"]

# ── Styling ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500&display=swap');

:root {
    --ink: #0F1419;
    --panel: #171E29;
    --panel-2: #1D2635;
    --line: #2A3345;
    --brass: #E8A33D;
    --teal: #4FD1C5;
    --green: #6FCF97;
    --text: #E8E6E1;
    --muted: #8B93A0;
}

.stApp { background: var(--ink); }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); }

/* ── Header ───────────────────────────────────────────────── */
.hero-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--brass);
    margin-bottom: 6px;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.5rem;
    line-height: 1.15;
    margin: 0 0 8px 0;
    color: var(--text);
}
.hero-sub {
    font-family: 'Inter', sans-serif;
    color: var(--muted);
    font-size: 1rem;
    max-width: 720px;
    margin-bottom: 1.8rem;
}

/* ── Pipeline stepper (the signature element) ───────────────── */
.stepper { display: flex; gap: 6px; margin-bottom: 1.6rem; }
.step {
    flex: 1;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
    transition: all 0.25s ease;
}
.step-icon { font-size: 1.05rem; display: block; margin-bottom: 4px; opacity: 0.55; }
.step-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.02em;
    color: var(--muted);
    text-transform: uppercase;
}
.step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: var(--muted);
    opacity: 0.6;
}
.step.done { border-color: var(--green); background: rgba(111, 207, 151, 0.08); }
.step.done .step-icon, .step.done .step-label { color: var(--green); opacity: 1; }
.step.active {
    border-color: var(--brass);
    background: rgba(232, 163, 61, 0.10);
    box-shadow: 0 0 0 1px var(--brass);
}
.step.active .step-icon, .step.active .step-label { color: var(--brass); opacity: 1; }

/* ── Sidebar agent roster ────────────────────────────────────── */
section[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
.sidebar-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 14px;
}
.agent-card {
    background: var(--panel-2);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    border-left: 2px solid var(--brass);
}
.agent-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: var(--brass);
    letter-spacing: 0.05em;
}
.agent-name { font-family: 'Space Grotesk', sans-serif; font-weight: 500; font-size: 0.92rem; margin-top: 2px; }
.agent-desc { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }

/* ── Inputs / buttons ─────────────────────────────────────────── */
div[data-testid="stTextInput"] input {
    background: var(--panel) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.92rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--brass) !important;
    box-shadow: 0 0 0 1px var(--brass) !important;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: var(--brass) !important;
    color: #0F1419 !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover { filter: brightness(1.08); }

/* ── Status/log box ───────────────────────────────────────────── */
div[data-testid="stExpander"] { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }

/* ── Metrics ─────────────────────────────────────────────────── */
div[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px 14px; }
div[data-testid="stMetricValue"] { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; }
div[data-testid="stMetricLabel"] { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; text-transform: uppercase; color: var(--muted); }

.status-ok { color: var(--green); font-weight: 600; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }
.status-warn { color: var(--brass); font-weight: 600; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }
.status-skip { color: var(--muted); font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)

LANGUAGE_MAP = {".py": "python", ".html": "html", ".md": "markdown", ".sql": "sql"}


def lang_for(filename: str) -> str:
    for ext, lang in LANGUAGE_MAP.items():
        if filename.endswith(ext):
            return lang
    return "text"


def render_stepper(active_index: int) -> str:
    """active_index: -1 = nothing started, 0-7 = that stage is in progress, 8 = all done."""
    html = '<div class="stepper">'
    for i, (label, icon) in enumerate(zip(STEP_LABELS, STEP_ICONS)):
        if i < active_index:
            state = "done"
        elif i == active_index:
            state = "active"
        else:
            state = ""
        html += (
            f'<div class="step {state}">'
            f'<span class="step-icon">{icon}</span>'
            f'<span class="step-label">{label}</span><br>'
            f'<span class="step-num">{i + 1}/8</span>'
            f'</div>'
        )
    html += "</div>"
    return html


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">\U0001F9D1\u200d\U0001F4BB The Crew</div>', unsafe_allow_html=True)
    for i, (name, desc) in enumerate(AGENT_TEAM, start=1):
        st.markdown(
            f'<div class="agent-card">'
            f'<div class="agent-num">AGENT {i:02d}</div>'
            f'<div class="agent-name">{name}</div>'
            f'<div class="agent-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown('<span style="font-family:\'IBM Plex Mono\',monospace; font-size:0.8rem; color:var(--muted);">MODEL</span>', unsafe_allow_html=True)
    st.markdown('<span style="font-family:\'IBM Plex Mono\',monospace; font-size:0.85rem;">qwen2.5-coder:7b <span style="color:var(--muted);">via Ollama</span></span>', unsafe_allow_html=True)

    ollama_up = check_ollama_available()
    st.markdown("")
    if ollama_up:
        st.markdown('<span class="status-ok">\u25cf OLLAMA REACHABLE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-warn">\u25cf OLLAMA NOT REACHABLE</span>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Reset session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="hero-eyebrow">MULTI-AGENT SOFTWARE PIPELINE</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">One idea in. A working app out.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Describe an app idea below. Seven AI agents run it through requirements, '
    'design, backend, frontend, review, tests, and docs \u2014 in order, each building on the last, '
    'with automatic bug detection and repair along the way.</div>',
    unsafe_allow_html=True,
)

# ── Session state ────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
    st.session_state.run_folder = None
    st.session_state.elapsed = None

stepper_placeholder = st.empty()
stepper_placeholder.markdown(render_stepper(-1), unsafe_allow_html=True)

# ── Input form ────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    idea = st.text_input(
        "App idea",
        placeholder="> Create a Library Management System",
        label_visibility="collapsed",
    )
with col2:
    run_clicked = st.button("\u25b6 Run Pipeline", type="primary", use_container_width=True, disabled=not ollama_up)

skip_debug = st.checkbox("\u26a1 Skip debug/repair loops (much faster, files may still have bugs)", value=False)

if not ollama_up:
    st.warning("Start Ollama first (`ollama serve`), then refresh this page.")

# ── Run the pipeline ─────────────────────────────────────────────────────
if run_clicked and idea.strip():
    log_container = st.status("Starting pipeline...", expanded=True)
    log_lines = []
    stage_index = {"i": -1}

    def progress(msg: str):
        log_lines.append(msg)
        log_container.write(msg)
        if msg.startswith("\u2713"):
            stage_index["i"] += 1
            stepper_placeholder.markdown(render_stepper(stage_index["i"]), unsafe_allow_html=True)

    start = time.time()
    try:
        run_folder, results = run_pipeline(idea.strip(), progress=progress, skip_debug_loops=skip_debug)
        elapsed = time.time() - start
        log_container.update(label=f"Pipeline complete in {elapsed:.0f}s", state="complete")
        stepper_placeholder.markdown(render_stepper(8), unsafe_allow_html=True)
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
    st.markdown(f'<div style="font-family:\'Space Grotesk\',sans-serif; font-weight:700; font-size:1.3rem; margin-bottom:10px;">\U0001F4E6 outputs/{run_folder}/</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Files", len(results))
    m2.metric("Size", f"{sum(len(r['content'] or '') for r in results):,} chars")
    m3.metric("Time", f"{elapsed:.0f}s")
    checked = [r for r in results if r["ok"] is not None]
    m4.metric("Validated", f"{sum(1 for r in checked if r['ok'])}/{len(checked)}" if checked else "skipped")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            zf.writestr(r["filename"], r["content"] or "")
    st.download_button(
        "\u2b07 Download all (.zip)",
        data=zip_buffer.getvalue(),
        file_name=f"{run_folder}.zip",
        mime="application/zip",
    )

    st.markdown("#### Files")
    for r in results:
        if r["ok"] is None:
            status_html = '<span class="status-skip">\u2014 validation skipped</span>'
        elif r["ok"]:
            status_html = '<span class="status-ok">\u2713 passed validation</span>'
        else:
            status_html = '<span class="status-warn">\u26a0 needs review</span>'
        with st.expander(f"{r['filename']}  \u2014  {len(r['content'] or ''):,} chars"):
            st.markdown(status_html, unsafe_allow_html=True)
            st.code(r["content"] or "(empty)", language=lang_for(r["filename"]))
            st.download_button("Download this file", data=r["content"] or "", file_name=r["filename"], key=f"dl_{r['filename']}")