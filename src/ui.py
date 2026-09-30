CSS = """
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 24%),
                radial-gradient(circle at top right, rgba(168, 85, 247, 0.16), transparent 18%),
                linear-gradient(180deg, #020617 0%, #0f172a 100%) !important;
    color: #e2e8f0;
}

.stApp {
    background: transparent;
}

.main-title {
    font-size: 4.5rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #22d3ee, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 20px;
}

.subtitle {
    text-align: center;
    font-size: 1.2rem;
    color: #cbd5e1;
    margin-bottom: 40px;
}

.auth-box {
    background: rgba(15, 23, 42, 0.75);
    padding: 35px;
    border-radius: 25px;
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.22);
}

textarea, .stTextArea textarea {
    background-color: rgba(15, 23, 42, 0.92) !important;
    color: #e2e8f0 !important;
    border-radius: 18px !important;
    border: 1px solid rgba(148, 163, 184, 0.18) !important;
    padding: 18px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

textarea:focus, .stTextArea textarea:focus, .stTextInput input:focus {
    outline: none !important;
    border-color: rgba(56, 189, 248, 0.85) !important;
    box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.14) !important;
}

.stButton button {
    width: 100%;
    border-radius: 14px;
    height: 3.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #6366f1, #ec4899);
    color: white;
    border: none;
    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.18);
}

.stButton button:hover {
    transform: translateY(-1px);
}

.glass {
    background: rgba(15, 23, 42, 0.74);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 32px 80px rgba(0, 0, 0, 0.24);
    backdrop-filter: blur(18px);
}

.input-field {
    width: 100%;
    border-radius: 18px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    background: rgba(15, 23, 42, 0.95);
    color: #e2e8f0;
    padding: 1rem 1.1rem;
    font-size: 1rem;
    min-height: 160px;
    resize: none;
}

.btn-primary, .btn-secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    font-weight: 700;
    transition: transform 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.btn-primary {
    background: linear-gradient(135deg, #8b5cf6, #ec4899);
    color: white;
    border: none;
    box-shadow: 0 18px 40px rgba(236, 72, 153, 0.18);
}

.btn-primary:hover {
    transform: translateY(-1px);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.06);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.45rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.status-pill.primary {
    background: rgba(99, 102, 241, 0.15);
    color: #c7d2fe;
}

.status-pill.secondary {
    background: rgba(14, 165, 233, 0.12);
    color: #bae6fd;
}

/* ─── Tabs ───────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(15, 23, 42, 0.6);
    padding: 6px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px;
    padding: 10px 20px;
    font-weight: 600;
    color: #94a3b8;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #06b6d4, #3b82f6) !important;
    color: white !important;
    border-radius: 12px !important;
}

/* ─── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.85);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

[data-testid="stSidebar"] .stButton button {
    background: rgba(255, 255, 255, 0.06);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    height: 2.8rem;
    box-shadow: none;
}

[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(56, 189, 248, 0.5);
    transform: none;
}

/* ─── Cards & containers ─────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.6);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

/* ─── Inputs & selects ───────────────────────── */
[data-baseweb="input"],
[data-baseweb="select"] > div,
[data-baseweb="base-input"] {
    background: rgba(15, 23, 42, 0.9) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
}

.stDownloadButton button, .stButton button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    height: 3.2rem;
    border-radius: 14px;
    font-weight: 600;
}

.stDownloadButton button:hover {
    border-color: rgba(56, 189, 248, 0.5) !important;
}

/* ─── Success / error / info messages ────────── */
[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* ─── Headings ───────────────────────────────── */
h1, h2, h3 {
    letter-spacing: -0.01em;
}

h2 {
    background: linear-gradient(90deg, #22d3ee, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    font-weight: 800;
}

</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def show_logo(path="assets/logo.png", width=250):
    import streamlit as st
    try:
        st.image(path, width=width)
    except Exception:
        st.info("Add your logo as assets/logo.png")


def show_title():
    import streamlit as st
    st.markdown(
        '<div class="main-title">Bámi-Sọ̀rọ̀</div>',
        unsafe_allow_html=True,
    )


def show_subtitle(text="Smart Yoruba Speech-to-Text Platform"):
    import streamlit as st
    st.markdown(
        f'<div class="subtitle">{text}</div>',
        unsafe_allow_html=True,
    )


def show_footer():
    import streamlit as st
    st.markdown("---")
    st.markdown(
        '<center style="color:#64748b;font-size:0.85rem">'
        'Bámi-Sọ̀rọ̀ · AI Yoruba Speech-to-Text & Translation · '
        'Powered by Whisper, NLLB-200 & GPT-4o<br/>'
        'Built with ❤️ by Ṣẹ̀kẹ̀rẹ̀ Communications'
        '</center>',
        unsafe_allow_html=True,
    )
