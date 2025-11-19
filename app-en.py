import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import matplotlib.pyplot as plt
import calendar
import numpy as np

# ================= Page Config ==================
st.set_page_config(
    page_title="Everest Inventory Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= Ingredient Database ==================
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
.card-header {display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center;}
.metric-card {background:#1f2937; padding:12px 18px; border-radius:10px; border:1px solid #4b5563;}
</style>
""", unsafe_allow_html=True)

# ================= Data Files ==================
INV_FILE = "inventory_data.csv"
HIS_FILE = "history_data.csv"

# ================= Load Functions ==================
def load_inventory():
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE)
        expected = ["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
        for c in expected:
            if c not in df.columns:
                df[c] = ""
        return df
    return pd.DataFrame(columns=expected)

def save_inventory(df):
    df.to_csv(INV_FILE, index=False, encoding="utf-8-sig")

def load_history():
    if os.path.exists(HIS_FILE):
        df = pd.read_csv(HIS_FILE)
        expected = ["Date","Branch","Item","Type","Qty"]
        for c in expected:
            if c not in df.columns:
                df[c] = ""
        return df
    return pd.DataFrame(columns=["Date","Branch","Item","Type","Qty"])

def save_history(df):
    df.to_csv(HIS_FILE, index=False, encoding="utf-8-sig")

# ================= Init Session ==================
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

if "history" not in st.session_state:
    st.session_state.history = load_history()

branches = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]

# ================= Header ==================
st.markdown(f"""
<div class="card-header">
    <div>
        <h1>Everest Inventory Management System</h1>
        <p>Full stock system with date input, IN/OUT log, and calendar visualization.</p>
    </div>
    <div class="metric-card">
        Total registered items: <b>{len(st.session_state.inventory)}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= Tabs ==================
tab1, tab2, tab3, tab4 = st.tabs([
    "✏ Register / Edit Inventory", 
    "📊 View / Print Inventory",
    "📦 Stock IN / OUT Log",
    "📅 Monthly Calendar Heatmap"
])

# ============================================================
# TAB 1 — Register / Edit Inventory
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
        input_type = st.radio("Item Input", ["Select from list", "Type manually"])
        if input_type == "Select from list":
            items = sorted([i["item"] for i in ingredient_list if i["category"] == category])
            item = st.selectbox("Item", items)
        else:
            item = st.text_input("Item")
        unit = st.text_input("Unit (kg, pcs, box)")

    with col3:
        qty = st.number_input("Current Qty", min_value=0.0, step=1.0)
        min_qty = st.number_input("Minimum Required", min_value=0.0, step=1.0)
        note = st.text_input("Note")

    if st.button("💾 Save Inventory"):
        df = st.session_state.inventory.copy()
        df.loc[len(df)] = [branch, item, category, unit, qty, min_qty, note, str(selected_date)]
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Saved successfully!")

# ============================================================
# TAB 2 — View / Print Inventory
# ============================================================
with tab2:
    st.subheader("Search Inventory")

    df = st.session_state.inventory.copy()

    date_filter = st.date_input("Filter by Date")
    df = df[df["Date"] == str(date_filter)]

    cat_filter = st.selectbox("Category", ["All"] + sorted(set(df["Category"])))
    if cat_filter != "All":
        df = df[df["Category"] == cat_filter]

    item_filter = st.selectbox("Item", ["All"] + sorted(set(df["Item"])))
    if item_filter != "All":
        df = df[df["Item"] == item_filter]

    st.dataframe(df, use_container_width=True)

    printable_html = df.to_html(index=False)
    st.download_button("🖨 Download Printable HTML",
                       data=f"<html><body>{printable_html}</body></html>",
                       file_name="inventory_print.html",
                       mime="text/html")

# ============================================================
# TAB 3 — Stock IN / OUT Log
# ============================================================
with tab3:
    st.subheader("Stock IN / OUT Logging")

    col1, col2, col3 = st.columns(3)

    with col1:
        log_date = st.date_input("Date", value=date.today())
        log_branch = st.selectbox("Branch", branches)

    with col2:
        log_item = st.selectbox("Item", sorted(set(i["item"] for i in ingredient_list)))
        log_type = st.selectbox("Type", ["IN", "OUT"])

    with col3:
        log_qty = st.number_input("Quantity", min_value=0.0, step=1.0)

    if st.button("📥 Log Stock Movement"):
        df = st.session_state.history.copy()
        df.loc[len(df)] = [str(log_date), log_branch, log_item, log_type, log_qty]
        st.session_state.history = df
        save_history(df)
        st.success("Recorded successfully!")

    st.markdown("### Stock Movement History")
    st.dataframe(st.session_state.history, use_container_width=True)

# ============================================================
# TAB 4 — Monthly Calendar Heatmap
# ============================================================
with tab4:
    st.subheader("Monthly Calendar Heatmap (Stock Activity)")

    df = st.session_state.history.copy()

    month = st.selectbox("Select Month", range(1, 13), index=datetime.now().month - 1)
    year = st.selectbox("Select Year", range(2022, 2031), index=3)

    # Extract selected month data
    df["d"] = pd.to_datetime(df["Date"])
    df = df[(df["d"].dt.month == month) & (df["d"].dt.year == year)]

    # Count movements per day
    day_activity = df["d"].dt.day.value_counts().sort_index()

    # Build heatmap grid (5 rows, 7 columns)
    cal = calendar.monthcalendar(year, month)
    heatmap = np.zeros((len(cal), 7))

    for week_index, week in enumerate(cal):
        for day_index, day in enumerate(week):
            if day != 0 and day in day_activity.index:
                heatmap[week_index][day_index] = day_activity[day]

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(heatmap, cmap='YlOrRd')

    ax.set_title(f"Stock Movements for {year}-{month}")
    ax.set_xticks(range(7))
    ax.set_xticklabels(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])

    ax.set_yticks(range(len(cal)))
    ax.set_yticklabels([f"Week {i+1}" for i in range(len(cal))])

    plt.colorbar(im)
    st.pyplot(fig)

