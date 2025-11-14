import streamlit as st
import pandas as pd
import os

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

# Branch names (real store names, keep Korean)
branches = ["동대문", "굿모닝시티", "양재", "수원영통", "동탄", "영등포", "룸비니"]

# Categories (English labels, but 저장은 한국어 컬럼에)
categories = [
    "Meat", "Vegetable", "Seafood", "Spice",
    "Sauce", "Grain/Noodle", "Beverage", "Packaging", "Other"
]

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
st.markdown(
    f"""
<div class="card" style="margin-bottom: 1.2rem;">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:1rem;">
    <div>
      <h1 style="margin-bottom:0.2rem;">📦 EVEREST Inventory Management System</h1>
      <p style="margin-top:0.2rem; color:#9ca3af;">
        Internal dashboard to manage stock by branch and item, and quickly identify low-stock items that require reordering.
      </p>
    </div>
    <div class="metric-card">
      <div style="font-size:0.85rem; color:#9ca3af;">Total items stored</div>
      <div style="font-size:1.4rem; font-weight:600; color:#e5e7eb; margin-top:0.1rem;">
        {len(st.session_state.inventory)} items
      </div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tab_input, tab_view = st.tabs(["✏ Input / Edit Stock", "📊 View / Print Inventory"])

# ================= TAB 1: Input / Edit =================
with tab_input:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Input / Edit Inventory")

    col1, col2, col3 = st.columns(3)

    with col1:
        branch = st.selectbox("Branch", branches, key="inv_branch")
        name = st.text_input("Item name", key="inv_name")
        category = st.selectbox("Category", categories, key="inv_cat")

    with col2:
        unit = st.text_input("Unit (e.g. kg, pcs, box)", key="inv_unit")
        qty = st.number_input("Current quantity", min_value=0.0, step=1.0, key="inv_qty")
        min_qty = st.number_input("Minimum required quantity", min_value=0.0, step=1.0, key="inv_min")

    with col3:
        note = st.text_input("Note", key="inv_note")
        save_btn = st.button("💾 Save / Update item")
        del_btn = st.button("🗑 Delete item (by branch + name)")

    if save_btn:
        if name.strip() == "":
            st.warning("Please enter the item name.")
        else:
            df = st.session_state.inventory.copy()
            mask = (df["지점"] == branch) & (df["품목명"] == name)

            new_row = {
                "지점": branch,
                "품목명": name,
                "카테고리": category,
                "단위": unit,
                "현재수량": qty,
                "최소수량": min_qty,
                "비고": note,
            }

            if mask.any():
                df.loc[mask, :] = list(new_row.values())
                st.success("Existing item has been updated.")
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("New item has been added.")

            st.session_state.inventory = df
            save_inventory(df)

    if del_btn:
        df = st.session_state.inventory.copy()
        mask = (df["지점"] == branch) & (df["품목명"] == name)
        if mask.any():
            df = df[~mask].reset_index(drop=True)
            st.session_state.inventory = df
            save_inventory(df)
            st.success(f"Item '{name}' at branch '{branch}' has been deleted.")
        else:
            st.warning("No item found for this branch + item name combination.")

    st.markdown("---")
    st.caption("※ Data is stored in inventory_data.csv, so it will persist even if the app restarts.")
    st.markdown('</div>', unsafe_allow_html=True)

# ================= TAB 2: View / Print =================
with tab_view:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("View / Print Inventory (Branch → Category → Item)")

    df = st.session_state.inventory.copy()

    if df.empty:
        st.info("No inventory data found. Please add items in the 'Input / Edit Stock' tab first.")
    else:
        for col in ["현재수량", "최소수량"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Step 1: Branch
        branch_options = ["All branches"] + sorted(df["지점"].dropna().unique().tolist())
        selected_branch = st.selectbox("Step 1: Select branch", branch_options)

        filtered = df.copy()
        if selected_branch != "All branches":
            filtered = filtered[filtered["지점"] == selected_branch]

        # Step 2: Category
        available_categories = sorted(filtered["카테고리"].dropna().unique().tolist())
        cat_options = ["All categories"] + available_categories
        selected_category = st.selectbox("Step 2: Select category", cat_options)

        if selected_category != "All categories":
            filtered = filtered[filtered["카테고리"] == selected_category]

        # Step 3: Item
        available_items = sorted(filtered["품목명"].dropna().unique().tolist())
        item_options = ["All items"] + available_items
        selected_item = st.selectbox("Step 3: Select item", item_options)

        if selected_item != "All items":
            filtered = filtered[filtered["품목명"] == selected_item]

        # Extra filter
        only_low = st.checkbox("Show only low stock items (Current ≤ Minimum)", value=False)
        if only_low:
            filtered = filtered[filtered["현재수량"] <= filtered["최소수량"]]

        st.markdown("#### Inventory List")

        if filtered.empty:
            st.info("No items match the selected conditions.")
        else:
            # Highlight low stock
            def highlight_low(row):
                if row["현재수량"] <= row["최소수량"]:
                    return ['background-color: #7f1d1d; color: #fee2e2; font-weight: 500;'] * len(row)
                else:
                    return [''] * len(row)

            styled = filtered.style.apply(highlight_low, axis=1)
            st.dataframe(styled, use_container_width=True)

            # -------- Print-friendly HTML --------
            html_table = filtered.to_html(index=False, border=1, justify="center")

            printable_html = """
            <html>
            <head>
            <meta charset="utf-8" />
            <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 24px;
                background: #ffffff;
                color: #000000;
            }}
            h2 {{
                text-align: center;
                margin-bottom: 6px;
            }}
            .meta {{
                text-align: center;
                font-size: 12px;
                color: #555;
                margin-bottom: 18px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
            }}
            th, td {{
                border: 1px solid #444;
                padding: 6px 8px;
                text-align: center;
            }}
            th {{
                background: #e5e7eb;
                font-weight: bold;
            }}
            @media print {{
                body {{ margin: 0; }}
                table {{ page-break-inside: avoid; }}
            }}
            </style>
            </head>
            <body>
            <div style="text-align:center; margin-bottom:12px;">
              <h2>Everest Inventory - Printable Report</h2>
              <div class="meta">
                Branch: {branch} | Category: {category} | Item: {item} | Only low stock: {only_low}
              </div>
            </div>
            {table}
            </body>
            </html>
            """.format(
                branch=selected_branch,
                category=selected_category,
                item=selected_item,
                only_low="Yes" if only_low else "No",
                table=html_table
            )

            st.download_button(
                label="🖨 Download Print-Friendly HTML",
                data=printable_html,
                file_name="everest_inventory_print.html",
                mime="text/html",
            )
            st.caption("Open the downloaded HTML file in a browser and press Ctrl+P to print or save as PDF.")

            # CSV download
            csv = filtered.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="⬇ Download current view as CSV",
                data=csv,
                file_name="everest_inventory_filtered.csv",
                mime="text/csv",
            )

    st.markdown('</div>', unsafe_allow_html=True)


