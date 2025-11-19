import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import plotly.express as px
import calendar
import numpy as np
import io

# ================= Page Config ==================
st.set_page_config(
    page_title="Everest Inventory Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= Ingredient List ==================
ingredient_list = [
    {"item": "Onion", "category": "Vegetable"},
    {"item": "Potato", "category": "Vegetable"},
    {"item": "Carrot", "category": "Vegetable"},
    {"item": "Tomato", "category": "Vegetable"},
    {"item": "Cabbage", "category": "Vegetable"},
    {"item": "Capsicum", "category": "Vegetable"},
    {"item": "Garlic", "category": "Vegetable"},
    {"item": "Chicken breast", "category": "Meat / Poultry"},
    {"item": "Chicken drumstick", "category": "Meat / Poultry"},
    {"item": "Prawn", "category": "Seafood"},
    {"item": "Mixed seafood", "category": "Seafood"},
    {"item": "Flour", "category": "Grain / Flour"},
    {"item": "Rice", "category": "Grain / Rice"},
    {"item": "Dal", "category": "Grain / Pulse"},
    {"item": "Chick peas", "category": "Grain / Pulse"},
    {"item": "Tomato ketchup", "category": "Sauce / Dressing"},
    {"item": "Soy sauce", "category": "Sauce / Dressing"},
    {"item": "Milk", "category": "Dairy"},
    {"item": "Cooking cream", "category": "Dairy"},
    {"item": "Ghee", "category": "Dairy"},
]

# ================= CSS ==================
st.markdown("""
<style>
.stApp {background-color:#111827; color:#e5e7eb;}
.metric-card {background:#1f2937; padding:12px 18px; border-radius:10px; border:1px solid #374151;}
</style>
""", unsafe_allow_html=True)

# ================= File Paths ==================
INV_FILE = "inventory_data.csv"
HIS_FILE = "history_data.csv"

# ================= Load Inventory ==================
def load_inventory():
    cols = ["Branch", "Item", "Category", "Unit",
            "CurrentQty", "MinQty", "Note", "Date"]

    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df[cols]

    return pd.DataFrame(columns=cols)

# ================= Save Inventory ==================
def save_inventory(df):
    df.to_csv(INV_FILE, index=False, encoding="utf-8-sig")

# ================= Load History ==================
def load_history():
    cols = ["Date", "Branch", "Item", "Type", "Qty"]

    if os.path.exists(HIS_FILE):
        df = pd.read_csv(HIS_FILE)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df[cols]

    return pd.DataFrame(columns=cols)

# ================= Save History ==================
def save_history(df):
    df.to_csv(HIS_FILE, index=False, encoding="utf-8-sig")

# ================= Init State ==================
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

if "history" not in st.session_state:
    st.session_state.history = load_history()

branches = ["동대문", "굿모닝시티", "양재", "수원영통", "동탄", "영등포", "룸비니"]

# ================= Header ==================
st.markdown("""
<h1>Everest Inventory Management System</h1>
<p>Advanced stock system with auto updates, heatmap, and reporting</p>
""", unsafe_allow_html=True)

# ================= Tabs ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✏ Register Inventory",
    "📊 View Inventory",
    "📦 Stock IN / OUT Log",
    "📅 Heatmap Visualization",
    "📄 Monthly Report"
])

# ============================================================
# TAB 1 — Register Inventory
# ============================================================
with tab1:
    st.subheader("Register New Inventory")

    col0, col1, col2, col3 = st.columns(4)

    with col0:
        selected_date = st.date_input("📅 Date", value=date.today())

    with col1:
        branch = st.selectbox("Branch", branches)
        category = st.selectbox("Category", sorted(set(i["category"] for i in ingredient_list)))

    with col2:
        mode = st.radio("Item Input", ["Select from list", "Type manually"])
        if mode == "Select from list":
            items = sorted([i["item"] for i in ingredient_list if i["category"] == category])
            item = st.selectbox("Item", items)
        else:
            item = st.text_input("Item")

        unit = st.text_input("Unit (kg, pcs, box)")

    with col3:
        qty = st.number_input("Current Qty", min_value=0.0, step=1.0)
        min_qty = st.number_input("Minimum Qty", min_value=0.0, step=1.0)
        note = st.text_input("Note")

    if st.button("💾 Save Inventory"):
        df = st.session_state.inventory.copy()
        df.loc[len(df)] = [
            branch, item, category, unit, qty, min_qty, note, str(selected_date)
        ]
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Saved")

# ============================================================
# TAB 2 — View Inventory
# ============================================================
with tab2:
    st.subheader("Search Inventory")

    df = st.session_state.inventory.copy()

    date_filter = st.date_input("Filter by Date")
    df = df[df["Date"] == str(date_filter)]

    cat_filter = st.selectbox("Category", ["All"] + sorted(df["Category"].unique()))
    if cat_filter != "All":
        df = df[df["Category"] == cat_filter]

    item_filter = st.selectbox("Item", ["All"] + sorted(df["Item"].unique()))
    if item_filter != "All":
        df = df[df["Item"] == item_filter]

    st.dataframe(df, use_container_width=True)

    printable = df.to_html(index=False)
    st.download_button(
        "🖨 Download Printable HTML",
        f"<html><body>{printable}</body></html>",
        "inventory_print.html",
        mime="text/html"
    )

# ============================================================
# TAB 3 — Stock IN/OUT + Auto Update
# ============================================================
with tab3:
    st.subheader("Stock IN / OUT (Auto Update Inventory)")

    col1, col2, col3 = st.columns(3)

    with col1:
        log_date = st.date_input("Date", value=date.today())
        log_branch = st.selectbox("Branch", branches)

    with col2:
        log_item = st.selectbox("Item", sorted(set(i["item"] for i in ingredient_list)))
        log_type = st.selectbox("Type", ["IN", "OUT"])

    with col3:
        log_qty = st.number_input("Quantity", min_value=0.0, step=1.0)

    if st.button("📥 Log & Update"):
        # 기록 저장
        his = st.session_state.history.copy()
        his.loc[len(his)] = [str(log_date), log_branch, log_item, log_type, log_qty]
        st.session_state.history = his
        save_history(his)

        # 재고 자동 반영
        inv = st.session_state.inventory.copy()
        mask = (inv["Branch"] == log_branch) & (inv["Item"] == log_item)

        if mask.any():
            if log_type == "IN":
                inv.loc[mask, "CurrentQty"] += log_qty
            else:
                inv.loc[mask, "CurrentQty"] -= log_qty

            if any(inv.loc[mask, "CurrentQty"] < 0):
                st.warning("⚠ Stock went below 0!")
        else:
            st.warning("Item not found in inventory. Register it first.")

        st.session_state.inventory = inv
        save_inventory(inv)

        st.success("IN/OUT recorded & inventory updated!")

    st.dataframe(st.session_state.history, use_container_width=True)

# ============================================================
# TAB 4 — Heatmap Visualization
# ============================================================
with tab4:
    st.subheader("Monthly Stock Activity Heatmap")

    df = st.session_state.history.copy()

    month = st.selectbox("Month", list(range(1, 13)), index=datetime.now().month - 1)
    year = st.selectbox("Year", list(range(2022, 2031)), index=3)

    df["d"] = pd.to_datetime(df["Date"])
    df = df[(df["d"].dt.month == month) & (df["d"].dt.year == year)]

    if len(df) == 0:
        st.info("No activity this month.")
    else:
        df["weekday"] = df["d"].dt.weekday
        df["day"] = df["d"].dt.day

        fig = px.density_heatmap(
            df,
            x="weekday",
            y="day",
            z="Qty",
            color_continuous_scale="YlOrRd",
            labels={"weekday": "Weekday", "day": "Day"},
            nbinsx=7,
            nbinsy=6
        )

        fig.update_layout(
            xaxis=dict(
                tickmode="array",
                tickvals=[0,1,2,3,4,5,6],
                ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            )
        )

        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 5 — Monthly Report (Excel)
# ============================================================
with tab5:
    st.subheader("📄 Generate Monthly Excel Report")

    rep_month = st.selectbox("Report Month", list(range(1, 13)), index=datetime.now().month - 1)
    rep_year = st.selectbox("Report Year", list(range(2022, 2031)), index=3)

    if st.button("⬇ Download Monthly Excel Report"):
        inv = st.session_state.inventory.copy()
        his = st.session_state.history.copy()

        inv["d"] = pd.to_datetime(inv["Date"])
        his["d"] = pd.to_datetime(his["Date"])

        inv_m = inv[(inv["d"].dt.month == rep_month) & (inv["d"].dt.year == rep_year)]
        his_m = his[(his["d"].dt.month == rep_month) & (his["d"].dt.year == rep_year)]

        low_stock = inv_m[inv_m["CurrentQty"] <= inv_m["MinQty"]]

        with io.BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                inv_m.to_excel(writer, sheet_name="Inventory", index=False)
                his_m.to_excel(writer, sheet_name="IN_OUT Log", index=False)
                low_stock.to_excel(writer, sheet_name="Low Stock", index=False)

            excel_binary = buffer.getvalue()

        st.download_button(
            "⬇ Download Excel",
            excel_binary,
            file_name=f"Everest_Report_{rep_year}-{rep_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Report generated!")
