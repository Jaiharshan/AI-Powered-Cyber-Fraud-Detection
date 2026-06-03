GLOBAL_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {
    --ink: #132b44;
    --ink-soft: #3b526a;
    --paper: #f6fbff;
    --panel: #ffffff;
    --border: #c8d8e9;
    --accent: #0f7598;
    --accent-strong: #095f7d;
    --sidebar-bg: #eaf3fc;
}
.stApp {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--ink);
    background: radial-gradient(circle at 10% 0%, #e7f2ff 0%, #f5fbff 48%, #fff8f0 100%);
}
.stApp p,
.stApp label,
.stApp li,
.stMarkdown,
.stCaption,
.stMetricLabel,
.stMetricValue,
.st-emotion-cache-10trblm,
.st-emotion-cache-16txtl3 {
    color: var(--ink) !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--sidebar-bg) 0%, #f1f7fe 100%);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * {
    color: var(--ink) !important;
}
.stTextArea textarea,
.stTextInput input {
    background: var(--panel) !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--panel) !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
}
div[role="listbox"] div {
    color: var(--ink) !important;
}
div[role="radiogroup"] label {
    color: var(--ink) !important;
}
div[role="tablist"] {
    gap: 10px;
    margin-bottom: 8px;
}
div[role="tablist"] button {
    background: rgba(255, 255, 255, 0.78);
    border-radius: 10px 10px 0 0;
    border: 1px solid var(--border);
    color: var(--ink-soft);
}
div[role="tablist"] button[aria-selected="true"] {
    background: #ffffff;
    color: var(--accent-strong);
    border-bottom: 2px solid var(--accent);
    font-weight: 700;
}
[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.75);
    border: 1px dashed #8fa7bf;
}
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(120deg, #0f7598 0%, #0a6280 100%);
    color: #f8fcff;
    border: none;
    border-radius: 10px;
    font-weight: 600;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background: linear-gradient(120deg, #0d6787 0%, #08556d 100%);
    color: #ffffff;
}
.hero {
    padding: 24px 28px;
    border-radius: 16px;
    background: linear-gradient(130deg, #0f3d69 0%, #1a5f82 55%, #2b7f9f 100%);
    color: #f5f8ff;
    margin-bottom: 18px;
    box-shadow: 0 18px 35px rgba(9, 45, 79, 0.22);
}
.hero h1 {
    margin: 0 0 8px 0;
    font-size: 2.05rem;
    letter-spacing: 0.2px;
}
.hero p {
    margin: 0;
    font-size: 1rem;
    opacity: 0.93;
}
.result-card {
    border-radius: 14px;
    padding: 18px 20px;
    margin-top: 6px;
    margin-bottom: 12px;
}
.result-title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
}
.result-subtitle {
    margin: 6px 0 0 0;
    font-size: 0.96rem;
    color: #1e3954;
}
.stDataFrame,
[data-testid="stDataFrame"] {
    background: rgba(255, 255, 255, 0.84);
    border: 1px solid var(--border);
    border-radius: 10px;
}
</style>
"""
