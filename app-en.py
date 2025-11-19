import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import plotly.express as px
import calendar
import io

# ================= Page Config ==================
st.set_page_config(page_title="Everest Inventory Management", layout="wide")

# ================= Ingredient List ==================
ingredient_list = [
    {"item": "Onion", "category": "Vegetable"},
    {"item": "Potato", "category": "Vegetable"},
    {"item": "Carrot", "category": "Vegetable"},
    {"item": "Tomato", "category": "Vegetable"},
    {"item": "Chicken breast", "category": "Meat / Poultry"},
    {"item": "Prawn", "category": "Seafood"},
    {"item": "Flour", "category": "Grain / Flour"},
    {"item": "Rice", "category": "Grain / Rice"},
    {"item": "Milk", "category": "Dairy"},
]

# ================= File Paths ==================
INV_FILE = "inventory_data.csv"
HIS_FILE = "history_data.csv"

# ================= Load / Save Functions ==================
def load_inventory():
    cols = ["Branch", "Item", "Category", "Unit", "CurrentQty", "MinQty", "Note", "Date"]
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        return df.reindex(columns=cols, fill_value="")
    return pd.DataFrame(columns=cols)

def save_inventory(df):
    df.to_csv(INV_FILE, index=False, encoding="utf-8-sig")

def load_history():
    cols = ["Date", "Branch", "Item", "Type", "Qty"]
    if os.path.exists(HIS_FILE):
        df = pd.read_csv(HIS_FILE)
        return df.reindex(columns=cols, fill_value="")
    return pd.DataFrame(columns=cols)

def save_history(df):
    df.to_csv(HIS_FILE, index=False, encoding="utf-8-sig")

# ================= Init Session ==================
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

if "history" not in st.session_state:
    st.session_state.history = load_history()

branches = ["동대문", "굿모닝시티", "양재", "수원영통", "동탄", "영등포", "룸비니"]

# ================= Tabs ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✏ Register Inventory",
    "📊 View Inventory",
    "📦 Stock IN / OUT",
    "📅 Heatmap Calendar",
    "📄 Monthly Report"
])

# ============================================================
# TAB 1 — Register Inventory
# ============================================================
with tab1:
    st.subheader("Register New Inventory")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        reg_date = st.date_input("📅 Date", value=date.today(), key="reg_date")
        reg_branch = st.selectbox("Branch", branches, key="reg_branch")

    with col2:
        reg_category = st.selectbox("Category", sorted({i["category"] for i in ingredient_list}), key="reg_cat")
        mode = st.radio("Item Input", ["Select from list", "Type manually"], key="reg_itemmode")

        if mode == "Select from list":
            items = sorted([i["item"] for i in ingredient_list if i["category"] == reg_category])
            reg_item = st.selectbox("Item", items, key="reg_itemlist")
        else:
            reg_item = st.text_input("Item", key="reg_itemtext")

    with col3:
        reg_unit = st.text_input("Unit", key="reg_unit")
        reg_qty = st.number_input("Current Qty", min_value=0.0, step=1.0, key="reg_qty")
        reg_min = st.number_input("Min Required", min_value=0.0, step=1.0, key="reg_min")

    with col4:
        reg_note = st.text_input("Note", key="reg_note")

    if st.button("💾 Save Inventory", key="save_inv_btn"):
        df = st.session_state.inventory.copy()
        df.loc[len(df)] = [reg_branch, reg_item, reg_category, reg_unit, reg_qty, reg_min, reg_note, str(reg_date)]
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Inventory registered!")

# ============================================================
# TAB 2 — View Inventory
# ============================================================
with tab2:
    st.subheader("View & Filter Inventory")

    df = st.session_state.inventory.copy()

    view_date = st.date_input("Filter Date", value=None, key="view_date")
    if view_date:
        df = df[df["Date"] == str(view_date)]

    view_cat = st.selectbox("Category", ["All"] + sorted(df["Category"].unique()), key="view_cat")
    if view_cat != "All":
        df = df[df["Category"] == view_cat]

    view_item = st.selectbox("Item", ["All"] + sorted(df["Item"].unique()), key="view_item")
    if view_item != "All":
        df = df[df["Item"] == view_item]

    st.dataframe(df, use_container_width=True)

# ============================================================
# TAB 3 — Stock IN / OUT with Auto Update
# ============================================================
with tab3:
    st.subheader("Stock IN / OUT (Auto Update Inventory)")

    col1, col2, col3 = st.columns(3)

    with col1:
        log_date = st.date_input("Date", value=date.today(), key="log_date")
        log_branch = st.selectbox("Branch", branches, key="log_branch")

    with col2:
        log_item = st.selectbox("Item", sorted({i["item"] for i in ingredient_list}), key="log_item")
        log_type = st.selectbox("Type", ["IN", "OUT"], key="log_type")

    with col3:
        log_qty = st.number_input("Qty", min_value=0.0, step=1.0, key="log_qty")

    if st.button("📥 Log Movement & Update Inventory", key="log_btn"):
        his = st.session_state.history.copy()
        his.loc[len(his)] = [str(log_date), log_branch, log_item, log_type, log_qty]
        st.session_state.history = his
        save_history(his)

        inv = st.session_state.inventory.copy()
        mask = (inv["Branch"] == log_branch) & (inv["Item"] == log_item)

        if mask.any():
            if log_type == "IN":
                inv.loc[mask, "CurrentQty"] += log_qty
            else:
                inv.loc[mask, "CurrentQty"] -= log_qty
        else:
            st.warning("⚠ Item not in inventory!")

        st.session_state.inventory = inv
        save_inventory(inv)
        st.success("Inventory updated!")

    st.dataframe(st.session_state.history, use_container_width=True)

# ============================================================
# TAB 4 — Heatmap Calendar
# ============================================================
with tab4:
    st.subheader("Monthly Stock Movement Heatmap")

    df = st.session_state.history.copy()

    heat_month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1, key="heat_month")
    heat_year = st.selectbox("Year", range(2022, 2031), index=3, key="heat_year")

    df["d"] = pd.to_datetime(df["Date"])
    df = df[(df["d"].dt.month == heat_month) & (df["d"].dt.year == heat_year)]

    if df.empty:
        st.info("No movement this month.")
    else:
        df["day"] = df["d"].dt.day
        df["weekday"] = df["d"].dt.weekday

        fig = px.density_heatmap(
            df,
            x="weekday",
            y="day",
            z="Qty",
            color_continuous_scale="YlOrRd",
            labels={"weekday": "Weekday", "day": "Day"}
        )
        fig.update_layout(
            xaxis=dict(
                tickvals=[0,1,2,3,4,5,6],
                ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            )
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 5 — Monthly Report
# ============================================================
with tab5:
    st.subheader("📄 Monthly Excel Report")

    rep_month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1, key="rep_month")
    rep_year = st.selectbox("Year", range(2022, 2031), index=3, key="rep_year")

    if st.button("⬇ Download Excel Report", key="rep_btn"):
        inv = st.session_state.inventory.copy()
        his = st.session_state.history.copy()

        inv["d"] = pd.to_datetime(inv["Date"])
        his["d"] = pd.to_datetime(his["Date"])

        inv_m = inv[(inv["d"].dt.month == rep_month) & (inv["d"].dt.year == rep_year)]
        his_m = his[(his["d"].dt.month == rep_month) & (his["d"].dt.year == rep_year)]
        low_stock = inv_m[inv_m["CurrentQty"] <= inv_m["MinQty"]]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            inv_m.to_excel(writer, sheet_name="Inventory", index=False)
            his_m.to_excel(writer, sheet_name="IN_OUT_Log", index=False)
            low_stock.to_excel(writer, sheet_name="Low Stock", index=False)
        output.seek(0)

        st.download_button(
            "⬇ Download Excel",
            data=output,
            file_name=f"Everest_Report_{rep_year}-{rep_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Report generated!")
