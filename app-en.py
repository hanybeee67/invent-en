import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import plotly.express as px
import io

# ================= Page Config ==================
st.set_page_config(page_title="Everest Inventory System", layout="wide")

# ================= File Locations ==================
INV_FILE = "inventory_data.csv"
HIS_FILE = "history_data.csv"
ITEM_FILE = "food ingrediants.txt"   # 파일명은 그대로 유지

# ================= Load Items & Units ==================
def load_items_with_units():
    items = []
    if not os.path.exists(ITEM_FILE):
        return items
    
    with open(ITEM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
            if len(parts) >= 3:
                items.append({
                    "category": parts[0],
                    "item": parts[1],
                    "unit": parts[2]
                })
    return items

item_db = load_items_with_units()
categories = sorted(list(set([i["category"] for i in item_db])))

# ================= Inventory Load/Save ==================
def load_inventory():
    cols = ["Branch","Category","Item","Unit","CurrentQty","MinQty","Note","Date"]
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        return df.reindex(columns=cols, fill_value="")
    return pd.DataFrame(columns=cols)

def save_inventory(df):
    df.to_csv(INV_FILE, index=False, encoding="utf-8-sig")

def load_history():
    cols = ["Date","Branch","Category","Item","Unit","Type","Qty"]
    if os.path.exists(HIS_FILE):
        df = pd.read_csv(HIS_FILE)
        return df.reindex(columns=cols, fill_value="")
    return pd.DataFrame(columns=cols)

def save_history(df):
    df.to_csv(HIS_FILE, index=False, encoding="utf-8-sig")

# ================= Session Init ==================
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

if "history" not in st.session_state:
    st.session_state.history = load_history()

branches = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]

# ================= Tabs ==================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✏ Register Inventory",
    "📦 Stock IN / OUT",
    "📊 Inventory View",
    "📅 Stock Heatmap",
    "📄 Monthly Report"
])

# ============================================================
# TAB 1 — Register Inventory
# ============================================================
with tab1:
    st.subheader("Register New Inventory")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        reg_date = st.date_input("📅 Date", value=date.today(), key="reg_date")
        reg_branch = st.selectbox("Branch", branches, key="reg_branch")

    with c2:
        reg_category = st.selectbox("Category", categories, key="reg_category")
        filtered_items = [i for i in item_db if i["category"] == reg_category]
        reg_item = st.selectbox(
            "Item",
            sorted([i["item"] for i in filtered_items]),
            key="reg_item"
        )

    with c3:
        auto_unit = ""
        for entry in filtered_items:
            if entry["item"] == reg_item:
                auto_unit = entry["unit"]

        reg_unit = st.text_input("Unit", value=auto_unit, key="reg_unit")
        reg_qty = st.number_input("Current Qty", min_value=0.0, step=1.0, key="reg_qty")

    with c4:
        reg_min = st.number_input("Minimum Qty", min_value=0.0, step=1.0, key="reg_min")
        reg_note = st.text_input("Note", key="reg_note")

    if st.button("💾 Save Inventory", key="reg_btn"):
        df = st.session_state.inventory.copy()
        df.loc[len(df)] = [
            reg_branch, reg_category, reg_item, reg_unit,
            reg_qty, reg_min, reg_note, str(reg_date)
        ]
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Inventory saved!")

# ============================================================
# TAB 2 — Stock IN / OUT
# ============================================================
with tab2:
    st.subheader("Stock IN / OUT with Auto Update")

    c1, c2, c3 = st.columns(3)

    with c1:
        log_date = st.date_input("Date", value=date.today(), key="log_date")
        log_branch = st.selectbox("Branch", branches, key="log_branch")

    with c2:
        log_category = st.selectbox("Category", categories, key="log_category")
        log_items = [i for i in item_db if i["category"] == log_category]
        log_item = st.selectbox(
            "Item",
            sorted([i["item"] for i in log_items]),
            key="log_item"
        )

    with c3:
        auto_unit2 = ""
        for entry in log_items:
            if entry["item"] == log_item:
                auto_unit2 = entry["unit"]

        st.write(f"📦 Unit: **{auto_unit2}**")
        log_type = st.selectbox("Type", ["IN","OUT"], key="log_type")
        log_qty = st.number_input("Qty", min_value=0.0, step=1.0, key="log_qty")

    if st.button("📥 Record Movement", key="log_btn"):
        # 기록 저장
        his = st.session_state.history.copy()
        his.loc[len(his)] = [
            str(log_date), log_branch, log_category,
            log_item, auto_unit2, log_type, log_qty
        ]
        st.session_state.history = his
        save_history(his)

        # 재고 반영
        inv = st.session_state.inventory.copy()
        mask = (inv["Branch"] == log_branch) & (inv["Item"] == log_item)

        if mask.any():
            if log_type == "IN":
                inv.loc[mask, "CurrentQty"] += log_qty
            else:
                inv.loc[mask, "CurrentQty"] -= log_qty
        else:
            st.warning("⚠ This item does not exist in inventory. Register it first!")

        st.session_state.inventory = inv
        save_inventory(inv)
        st.success("Stock updated!")

# ============================================================
# TAB 3 — Inventory View
# ============================================================
with tab3:
    st.subheader("Inventory List with Filters")

    df = st.session_state.inventory.copy()

    vc1, vc2, vc3 = st.columns(3)

    with vc1:
        f_cat = st.selectbox("Category", ["All"] + categories, key="view_cat")
        if f_cat != "All"_
