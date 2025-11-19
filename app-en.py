import streamlit as st
import pandas as pd
import os
from datetime import date

# ================= Page Config ==================
st.set_page_config(
    page_title="Everest Inventory Management System",
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

# ================= Global CSS ==================
st.markdown("""
<style>
.stApp {background-color:#111827; color:#e5e7eb;}
h1 {word-break:keep-all;}
.card-header {display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center;}
.metric-card {background:#1f2937; padding:12px 18px; border-radius:10px; border:1px solid #4b5563;}
</style>
""", unsafe_allow_html=True)

# ================= Data Load / Save ==================
DATA_FILE = "inventory_data.csv"

def load_inventory():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        expected = ["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
        for col in expected:
            if col not in df.columns:
                df[col] = ""
        return df[expected]
    else:
        return pd.DataFrame(columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"])

def save_inventory(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

branches = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]

# ================= Header ==================
st.markdown(f"""
<div class="card-header">
    <div>
        <h1>Everest Inventory Management System</h1>
        <p>Manage stock by branch, date, category, and auto-classified items.</p>
    </div>
    <div class="metric-card">
        Total items stored: <b>{len(st.session_state.inventory)}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= Tabs ==================
tab1, tab2 = st.tabs(["✏ Register / Edit Inventory", "📊 View / Print Inventory"])

# ================= TAB 1: Register ==================
with tab1:
    st.subheader("Register / Edit Inventory")
    
    col0, col1, col2, col3 = st.columns(4)
    
    with col0:
        selected_date = st.date_input("📅 Date", value=date.today())
    
    with col1:
        branch = st.selectbox("Branch", branches)
        category = st.selectbox("Category", sorted(set([i["category"] for i in ingredient_list])))
    
    with col2:
        input_type = st.radio("Item Input", ["Select from list", "Type manually"])
        if input_type == "Select from list":
            items = sorted([i["item"] for i in ingredient_list if i["category"] == category])
            item = st.selectbox("Item name", items)
        else:
            item = st.text_input("Item name")
        unit = st.text_input("Unit (kg, pcs, box)")
    
    with col3:
        qty = st.number_input("Current Quantity", min_value=0.0, step=1.0)
        min_qty = st.number_input("Minimum Required", min_value=0.0, step=1.0)
        note = st.text_input("Note")

    if st.button("💾 Save / Update"):
        df = st.session_state.inventory.copy()
        new_row = pd.DataFrame([[branch, item, category, unit, qty, min_qty, note, str(selected_date)]],
                               columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"])
        df = pd.concat([df,new_row], ignore_index=True)
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Saved Successfully!")

# ================= TAB 2: View ==================
with tab2:
    st.subheader("View / Print Inventory")
    
    df = st.session_state.inventory.copy()
    
    date_filter = st.date_input("Filter by Date", value=None)
    if date_filter:
        df = df[df["Date"] == str(date_filter)]
    
    category_filter = st.selectbox("Category", ["All"] + sorted(set(df["Category"])))
    if category_filter != "All":
        df = df[df["Category"] == category_filter]
    
    item_filter = st.selectbox("Item", ["All"] + sorted(set(df["Item"])))
    if item_filter != "All":
        df = df[df["Item"] == item_filter]
    
    st.dataframe(df, use_container_width=True)
    
    printable_html = df.to_html(index=False)
    st.download_button("🖨 Download Printable HTML",
                       data=f"<html><body>{printable_html}</body></html>",
                       file_name="inventory_print.html",
                       mime="text/html")
