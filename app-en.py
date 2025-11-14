
import streamlit as st
import pandas as pd
import os
import base64

# ---------------- Basic page config ----------------
st.set_page_config(
    page_title="Everest Inventory Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Global CSS ----------------
CUSTOM_CSS = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #1f2937 0, #020617 45%, #020617 100%);
    color: #e5e7eb;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 2.5rem;
    max-width: 1200px;
}
h1, h2, h3, h4 {
    color: #e5e7eb;
    letter-spacing: 0.02em;
}
p, .stMarkdown {
    color: #cbd5f5;
}
.card {
    background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(15,23,42,0.9));
    padding: 1.6rem 1.8rem;
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.4);
    box-shadow: 0 22px 55px rgba(15,23,42,0.95);
    margin-bottom: 1.8rem;
}
.metric-card {
    background: radial-gradient(circle at top left, rgba(30,64,175,0.35), rgba(15,23,42,0.98));
    padding: 1.0rem 1.2rem;
    border-radius: 14px;
    border: 1px solid rgba(129,140,248,0.6);
    box-shadow: 0 16px 40px rgba(15,23,42,0.9);
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0.2rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 999px;
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020617);
    border-right: 1px solid rgba(30,64,175,0.7);
}
section[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
label, .stSelectbox, .stTextInput, .stNumberInput {
    font-size: 0.9rem;
}
[data-testid="stDataFrame"] {
    background-color: rgba(15,23,42,0.9);
    border-radius: 14px;
    border: 1px solid rgba(148,163,184,0.35);
}
.stCheckbox label {
    color: #e5e7eb;
}
.stDownloadButton button, .stButton button {
    border-radius: 999px;
    padding: 0.45rem 1.0rem;
    border: 1px solid rgba(148,163,184,0.7);
    background: radial-gradient(circle at top left, #1d4ed8, #1e293b);
    color: #e5e7eb;
    font-weight: 500;
}
.stDownloadButton button:hover, .stButton button:hover {
    border-color: #a5b4fc;
    box-shadow: 0 0 0 1px rgba(129,140,248,0.9);
}
div[data-testid="stAlert"] {
    background-color: rgba(15,23,42,0.85);
    border-radius: 12px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------- Config ----------------
DATA_FILE = "inventory_data.csv"
LOGO_FILE = "everest_logo.png"

branches = ["동대문", "굿모닝시티", "양재", "수원영통", "동탄", "영등포", "룸비니"]
categories = [
    "Meat", "Vegetable", "Seafood", "Spice",
    "Sauce", "Grain/Noodle", "Beverage", "Packaging", "Other"
]

# ---------------- Logo loader ----------------
def load_logo_base64():
    if os.path.exists(LOGO_FILE):
        try:
            with open(LOGO_FILE, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

logo_b64 = load_logo_base64()

# ---------------- Data helpers ----------------
def load_inventory():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            expected_cols = ["지점", "품목명", "카테고리", "단위", "현재수량", "최소수량", "비고"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            return df
        except Exception:
            return pd.DataFrame(columns=["지점", "품목명", "카테고리", "단위", "현재수량", "최소수량", "비고"])
    else:
        return pd.DataFrame(columns=["지점", "품목명", "카테고리", "단위", "현재수량", "최소수량", "비고"])

def save_inventory(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# ---------------- Session init ----------------
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

# ---------------- Header ----------------
logo_block_html = ""
if logo_b64:
    logo_block_html = f"""
    <div style="display:flex; align-items:center; justify-content:center; margi

