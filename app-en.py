import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import plotly.express as px
import io

# ================= Page Config ==================
st.set_page_config(page_title="Everest Inventory Management", layout="wide")

# ================= File Paths ==================
INV_FILE = "inventory_data.csv"
HIS_FILE = "history_data.csv"
PRODUCT_FILE = "food ingrediants.txt"

# ================= Load Product Units from File ==================
def load_product_units():
    units = {}
    if not os.path.exists(PRODUCT_FILE):
        return units
    try:
        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.split('\t') if p.strip()]
                if len(parts) >= 2:
                    name = parts[0]
                    unit = parts[-1]
                    units[name] = unit
    except Exception:
        pass
    return units

product_units = load_product_units()

# ================= Load / Save Inventory ==================
def load_inventory():
    cols = ["Branch", "Item", "Category", "Unit", "CurrentQty", "MinQty", "Note", "Date"]
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        return df.reindex(columns=cols, fill_value="")
    return pd.DataFrame(columns=cols)

def save_inventory(df):
    df.to_csv(INV_FILE, index=False, encoding="utf-8-sig")

# ================= Load / Save History ==================
def load_history():
    cols = ["Date", "Branch", "Item", "Type", "Qty"]
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

branches = ["동대문", "굿모닝시티", "양재", "수원영통", "동탄", "영등포", "룸비니"]

# ================= Tabs ==================
tab1, tab2, tab3 = st.tabs([
    "✏ Register Inventory",
    "📦 Stock IN / OUT",
    "📄 View Inventory"
])

# ============================================================
# TAB 1 — Register Inventory with Auto Unit
# ============================================================
with tab1:
    st.subheader("Register New Inventory")

    col1, col2, col3 = st.columns(3)

    with col1:
        reg_date = st.date_input("📅 Date", value=date.today(), key="reg_date")
        reg_branch = st.selectbox("Branch", branches, key="reg_branch")

    with col2:
        reg_item = st.selectbox("Item", sorted(product_units.keys()), key="reg_item")
        reg_category = st.text_input("Category", value="General", key="reg_category")

    with col3:
        if "reg_unit_value" not in st.session_state:
            st.session_state["reg_unit_value"] = ""

        # 🔹 제품이 변경되면 자동으로 Unit 업데이트
        if st.session_state.get("last_item") != reg_item:
            st.session_state["reg_unit_value"] = product_units.get(reg_item, "")
            st.session_state["last_item"] = reg_item

        reg_unit = st.text_input("Unit", value=st.session_state["reg_unit_value"], key="reg_unit_input")
        reg_qty = st.number_input("Current Qty", min_value=0.0, step=1.0, key="reg_qty")
        reg_min = st.number_input("Minimum Qty", min_value=0.0, step=1.0, key="reg_min")
        reg_note = st.text_input("Note", key="reg_note")

    if st.button("💾 Save Inventory", key="save_btn"):
        df = st.session_state.inventory.copy()
        df.loc[len(df)] = [
            reg_branch, reg_item, reg_category, reg_unit,
            reg_qty, reg_min, reg_note, str(reg_date)
        ]
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Inventory saved successfully!")

# ============================================================
# TAB 2 — Stock IN / OUT with unit reference
# ============================================================
with tab2:
    st.subheader("Stock IN / OUT (Auto Update Inventory)")

    col1, col2, col3 = st.columns(3)

    with col1:
        log_date = st.date_input("Movement Date", value=date.today(), key="log_date")
        log_branch = st.selectbox("Branch", branches, key="log_branch")

    with col2:
        log_item = st.selectbox("Item", sorted(product_units.keys()), key="log_item")
        log_type = st.selectbox("Type", ["IN", "OUT"], key="log_type")

    with col3:
        log_unit_auto = product_units.get(log_item, "")
        st.write(f"📦 Unit: **{log_unit_auto}**")
        log_qty = st.number_input("Quantity", min_value=0.0, step=1.0, key="log_qty")

    if st.button("📥 Log Movement & Update Inventory", key="log_btn"):
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
        else:
            st.warning("⚠ Item not found in inventory!")

        st.session_state.inventory = inv
        save_inventory(inv)
        st.success("Inventory updated successfully!")

# ============================================================
# TAB 3 — View Inventory
# ============================================================
with tab3:
    st.subheader("Inventory List")
    st.dataframe(st.session_state.inventory, use_container_width=True)
