import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import io

# ================= Page Config ==================
st.set_page_config(
    page_title="Everest Inventory Management System",
    layout="wide",
    initial_sidebar_state="collapsed" # Hide sidebar on splash
)

# ================= Splash Screen Logic ==================
if "splash_shown" not in st.session_state:
    st.session_state["splash_shown"] = False

if not st.session_state["splash_shown"]:
    # Splash Screen CSS
    st.markdown("""
    <style>
    .stApp {
        background-image: url("app/static/everest_splash_bg.jpg"); /* Fallback if local hosting varies */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    /* Hide default elements during splash */
    [data-testid="stSidebar"], .stDeployButton, footer, header {
        display: none !important;
    }
    .splash-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        color: #ffffff;
        z-index: 9999; /* Ensure it sits on top of everything */
        background: transparent; /* Background image is on stApp */
    }
    .splash-content-box {
        background: rgba(0, 0, 0, 0.6);
        padding: 40px 30px; /* Reduced side padding for mobile */
        border-radius: 20px;
        backdrop-filter: blur(5px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
        animation: fadeIn 1.5s ease-in-out;
        max-width: 90%;
        width: auto;
    }
    .splash-title {
        font-size: clamp(2rem, 6vw, 4rem); /* Responsive font size */
        line-height: 1.2;
        font-weight: 800;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        margin-bottom: 1rem;
        color: #f8fafc;
        word-break: keep-all; /* Prevent word breaking in Korean/English mixed */
    }
    .splash-subtitle {
        font-size: 1.3rem;
        font-weight: 500;
        color: #cbd5e1; /* Light grey for subtitle */
        margin-bottom: 2rem;
    }
    .tap-hint {
        margin-top: 30px;
        font-size: 1rem;
        color: #94a3b8;
        animation: blink 2s infinite;
        font-weight: 400;
        letter-spacing: 1px;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); scale: 0.95; }
        100% { opacity: 1; transform: translateY(0); scale: 1; }
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    /* Invisible Full-Screen Button */
    div.stButton > button:first-child {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 99999;
        opacity: 0;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Background Image Handling
    import base64
    def get_base64_of_bin_file(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()

    bg_img_path = "everest_splash_bg.jpg"
    if os.path.exists(bg_img_path):
        bin_str = get_base64_of_bin_file(bg_img_path)
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)

    st.markdown("""
        <div class="splash-container">
            <div class="splash-content-box">
                <div class="splash-title">Everest Restaurant Inventory</div>
                <div class="splash-subtitle">Professional Stock Management System</div>
                <div class="tap-hint">Tap anywhere to start</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Full screen button (invisible due to CSS above)
    if st.button("Enter System", key="splash_btn"):
        st.session_state["splash_shown"] = True
        st.rerun()
            
    st.stop() # Stop execution here so the rest of the app doesn't load

# ================= Normal App Logic Starts Here ==================

# ================= Ingredient Database (기본 하드코딩 백업) ==================
# ================= Ingredient Database (기본 하드코딩 백업) ==================
ingredient_list = [
    {"category": "Meat", "item": "Chicken", "unit": "kg"},
    {"category": "Meat", "item": "Mutton", "unit": "kg"},
    {"category": "Meat", "item": "Pork", "unit": "kg"},
    {"category": "Meat", "item": "Buffalo", "unit": "kg"},
    {"category": "Meat", "item": "Fish", "unit": "kg"},
    {"category": "Vegetable", "item": "Onion", "unit": "kg"},
    {"category": "Vegetable", "item": "Tomato", "unit": "kg"},
    {"category": "Vegetable", "item": "Potato", "unit": "kg"},
    {"category": "Vegetable", "item": "Garlic", "unit": "kg"},
    {"category": "Vegetable", "item": "Ginger", "unit": "kg"},
    {"category": "Vegetable", "item": "Cabbage", "unit": "kg"},
    {"category": "Spices", "item": "Salt", "unit": "kg"},
    {"category": "Spices", "item": "Sugar", "unit": "kg"},
    {"category": "Spices", "item": "Cumin Powder", "unit": "kg"},
    {"category": "Spices", "item": "Turmeric Powder", "unit": "kg"},
    {"category": "Spices", "item": "Chili Powder", "unit": "kg"},
    {"category": "Dairy", "item": "Milk", "unit": "L"},
    {"category": "Dairy", "item": "Yogurt", "unit": "L"},
    {"category": "Dairy", "item": "Paneer", "unit": "kg"},
    {"category": "Others", "item": "Rice", "unit": "kg"},
    {"category": "Others", "item": "Flour", "unit": "kg"},
    {"category": "Others", "item": "Cooking Oil", "unit": "L"},
]

# ================= Files ==================
DATA_FILE = "inventory_data.csv"          # 재고 스냅샷
HISTORY_FILE = "stock_history.csv"        # 입출고 로그
ITEM_FILE = "food ingredients.txt"        # 카테고리/아이템/단위 DB

# ================= Login Logic ==================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def check_login(key_suffix):
    """
    Returns True if logged in, False if not (and shows login form).
    key_suffix: unique string for widget keys (e.g., "tab4")
    """
    if st.session_state["logged_in"]:
        return True

    st.warning("🔒 Manager Login Required")
    password = st.text_input("Password", type="password", key=f"login_pw_{key_suffix}")
    
    if st.button("Login", key=f"login_btn_{key_suffix}"):
        if password == "1234":
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Incorrect Password")
    
    return False

# ================= Global CSS (Premium UI) ==================
st.markdown("""
<style>
/* 1. Fonts & Colors */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    color: #e2e8f0;
}
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

/* 2. Compact Header Area */
.header-container {
    display: flex;
    align-items: center;
    padding: 10px 0; /* Reduced padding */
    margin-bottom: 10px; /* Reduced margin */
    border-bottom: 2px solid #334155;
}
.logo-img {
    width: 40px; /* Smaller logo */
    height: 40px;
    border-radius: 50%;
    margin-right: 15px;
    border: 2px solid #38bdf8;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}
.title-text {
    font-size: 1.5rem; /* Smaller title */
    font-weight: 700;
    background: -webkit-linear-gradient(45deg, #f8fafc, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.subtitle-text {
    font-size: 0.8rem; /* Smaller subtitle */
    color: #94a3b8;
    margin-top: 2px;
}

/* 3. Card & Metrics */
.metric-container {
    display: flex;
    gap: 20px;
}
.metric-box {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 15px 25px;
    flex: 1;
    text-align: center;
}
.metric-label {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 5px;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: #38bdf8;
}

/* 4. Tabs Customization */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    border-bottom: 1px solid #334155;
}
.stTabs [data-baseweb="tab"] {
    height: 40px; /* Reduced tab height */
    border-radius: 8px 8px 0 0;
    background-color: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    font-weight: 500;
    font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-bottom: none;
    color: #38bdf8;
}

/* 5. Inputs & Buttons */
.stTextInput > div > div > input, .stSelectbox > div > div > div, .stNumberInput > div > div > input {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #475569;
    border-radius: 8px;
    min-height: 40px;
}
.stButton > button {
    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    transform: translateY(-2px);
}
/* 2. Compact Header Area (Fixed Clipping) */
.header-container {
    display: flex;
    align-items: center;
    padding: 15px 0; /* Increased padding slightly */
    margin-bottom: 20px;
    border-bottom: 2px solid #334155;
}
/* Reduce default block padding to fix top cut-off */
.block-container {
    padding-top: 3rem !important; /* Increased from 2rem to 3rem for safety */
    padding-bottom: 1rem !important;
}

.logo-img {
    width: 50px; /* Slightly larger for visibility */
    height: 50px;
    border-radius: 50%;
    margin-right: 15px;
    border: 2px solid #38bdf8;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
    object-fit: cover; /* Ensure image fits well */
}
</style>
""", unsafe_allow_html=True)

# ================= Load item DB from file ==================
def load_item_db():
    """
    food ingredients.txt 형식:
    Category<TAB>Item<TAB>Unit
    
    기본 ingredient_list와 파일 내용을 병합하여 반환함.
    """
    items = []
    
    # 1. 파일 로드
    if os.path.exists(ITEM_FILE):
        try:
            with open(ITEM_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) >= 2:
                        cat = parts[0]
                        item = parts[1]
                        unit = parts[2] if len(parts) >= 3 else ""
                        items.append({"category": cat, "item": item, "unit": unit})
        except Exception as e:
            st.error(f"Error reading {ITEM_FILE}: {e}")
    
    # 2. 기본 리스트(ingredient_list) 병합 (중복 방지)
    existing_keys = set((i["category"].lower(), i["item"].lower()) for i in items)
    
    for default in ingredient_list:
        if (default["category"].lower(), default["item"].lower()) not in existing_keys:
            items.append({
                "category": default["category"], 
                "item": default["item"], 
                "unit": default.get("unit", "") 
            })
            
    return items

def get_all_categories():
    db = load_item_db()
    return sorted(set([i["category"] for i in db]))

def get_all_units():
    db = load_item_db()
    return sorted(set([i["unit"] for i in db if i["unit"]]))

def get_items_by_category(category):
    db = load_item_db()
    return sorted([i["item"] for i in db if i["category"] == category])

def get_unit_for_item(category, item):
    db = load_item_db()
    for i in db:
        if i["category"] == category and i["item"] == item:
            return i["unit"]
    return ""

# ================= Data Load / Save ==================
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

def load_history():
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        expected = ["Date","Branch","Category","Item","Unit","Type","Qty"]
        for col in expected:
            if col not in df.columns:
                df[col] = ""
        return df[expected]
    else:
        return pd.DataFrame(columns=["Date","Branch","Category","Item","Unit","Type","Qty"])

def save_history(df):
    df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

# ================= Session Init ==================
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

if "history" not in st.session_state:
    st.session_state.history = load_history()

# Default role: Staff (REMOVED)
# ...

branches = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]

# ================= Header (Compact) ==================
col_h1, col_h2 = st.columns([0.5, 9.5])

with col_h1:
    if os.path.exists("logo_circle.png"):
        st.image("logo_circle.png", width=50)       
    else:
        st.markdown("<div style='font-size:2rem; text-align:center;'>🏔</div>", unsafe_allow_html=True)

with col_h2:
    st.markdown("""
    <div style="display: flex; align-items: baseline; gap: 15px;">
        <h1 class="title-text" style="font-size: 1.8rem; margin: 0;">Everest Inventory</h1>
        <p class="subtitle-text" style="margin: 0;">Professional Stock Management System</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ================= Low Stock Alert ==================
if not st.session_state.inventory.empty:
    # Ensure numeric columns
    inv_df = st.session_state.inventory.copy()
    inv_df["CurrentQty"] = pd.to_numeric(inv_df["CurrentQty"], errors="coerce").fillna(0)
    inv_df["MinQty"] = pd.to_numeric(inv_df["MinQty"], errors="coerce").fillna(0)
    
    # Check condition: CurrentQty <= MinQty AND MinQty > 0
    low_stock = inv_df[(inv_df["CurrentQty"] <= inv_df["MinQty"]) & (inv_df["MinQty"] > 0)]
    
    if not low_stock.empty:
        st.error(f"⚠️ Warning: {len(low_stock)} items are below minimum stock level!", icon="🚨")
        with st.expander("View Low Stock Items"):
            st.dataframe(low_stock[["Branch", "Category", "Item", "CurrentQty", "MinQty", "Unit"]], use_container_width=True)

# ================= Tabs ==================

# ================= Tabs ==================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✏ Register / Edit Inventory",
    "📊 View / Print Inventory",
    "📦 IN / OUT Log",
    "📈 Usage Analysis",
    "📄 Monthly Report",
    "💾 Data Management"
])

# ======================================================
# TAB 1: Register / Edit Inventory (Manager Only)
# ======================================================
if tab1:
    with tab1:
        st.subheader("Register / Edit Inventory")
        
        col0, col1, col2, col3 = st.columns(4)
        
        with col0:
            selected_date = st.date_input("📅 Date", value=date.today(), key="selected_date")
        
        with col1:
            branch = st.selectbox("Branch", branches, key="branch")
            category = st.selectbox("Category", get_all_categories(), key="category")
        
        with col2:
            input_type = st.radio("Item Input", ["Select from list", "Type manually"], key="input_type")
            if input_type == "Select from list":
                items = get_items_by_category(category)
                item = st.selectbox("Item name", items, key="item_name")
            else:
                item = st.text_input("Item name", key="item_name_manual")

            # ---- Unit 자동 세팅 + 선택 가능 ----
            auto_unit = get_unit_for_item(category, item) if input_type == "Select from list" else ""
            # unit_options = ["", "kg", "g", "pcs", "box", "L", "mL", "pack", "bag"]  # Old hardcoded
            unit_options = [""] + get_all_units()  # Dynamic from DB
            
            # 아이템이 변경되었는지 확인하여 unit_select 강제 업데이트
            current_item_key = f"last_item_{category}_{item}"
            if "last_selected_item" not in st.session_state:
                st.session_state.last_selected_item = ""

            # 아이템이 변경되었다면 (또는 초기 진입)
            if st.session_state.last_selected_item != item:
                if auto_unit in unit_options:
                    st.session_state["unit_select"] = auto_unit
                else:
                    st.session_state["unit_select"] = unit_options[0]
                st.session_state.last_selected_item = item

            # default_index는 이제 초기 렌더링에만 영향, 실제 값은 session_state가 지배
            try:
                default_index = unit_options.index(st.session_state.get("unit_select", ""))
            except ValueError:
                default_index = 0
                
            unit = st.selectbox("Unit", unit_options, index=default_index, key="unit_select")

        # ---- 기존 데이터 확인 로직 (위젯 렌더링 전에 실행해야 함) ----
        df_curr = st.session_state.inventory
        mask = (df_curr["Branch"] == branch) & (df_curr["Category"] == category) & (df_curr["Item"] == item)
        existing_row = df_curr[mask]
        
        is_update = False
        full_key = f"{branch}_{category}_{item}"
        
        # Session State 키 초기화
        if "last_loaded_key" not in st.session_state:
            st.session_state.last_loaded_key = ""
        
        # 아이템 변경 감지 -> 데이터 로드 또는 초기화
        if st.session_state.last_loaded_key != full_key:
            if not existing_row.empty:
                # DB 값 불러오기
                st.session_state["qty"] = float(existing_row.iloc[0]["CurrentQty"])
                st.session_state["min_qty"] = float(existing_row.iloc[0]["MinQty"])
                st.session_state["note"] = str(existing_row.iloc[0]["Note"])
            else:
                # 신규 -> 초기화
                st.session_state["qty"] = 0.0
                st.session_state["min_qty"] = 0.0
                st.session_state["note"] = ""
            
            st.session_state.last_loaded_key = full_key
            # 값을 설정했으므로, 아래 위젯들이 이 값을 물고 렌더링됨.
            # 하지만 확실한 UI 갱신을 위해 rerun 할 수도 있으나, 
            # widget key가 설정된 상태에서 값 update후 렌더링이면 반영됨.

        if not existing_row.empty:
            is_update = True

        with col3:
            # key="qty" 등을 사용할 때 session_state에 값이 있으면 그 값을 초기값으로 사용
            qty = st.number_input("Current Quantity", min_value=0.0, step=1.0, key="qty")
            min_qty = st.number_input("Minimum Required", min_value=0.0, step=1.0, key="min_qty")
            note = st.text_input("Note", key="note")

        # 버튼 영역
        b_col1, b_col2 = st.columns(2)
        
        with b_col1:
            btn_label = "💾 Update Inventory" if is_update else "💾 Register New"
            if st.button(btn_label, key="save_btn"):
                df = st.session_state.inventory.copy()
                if is_update:
                    df.loc[mask, "CurrentQty"] = qty
                    df.loc[mask, "MinQty"] = min_qty
                    df.loc[mask, "Note"] = note
                    df.loc[mask, "Date"] = str(selected_date)
                    df.loc[mask, "Unit"] = unit 
                    st.success("Updated Successfully!")
                else:
                    new_row = pd.DataFrame(
                        [[branch, item, category, unit, qty, min_qty, note, str(selected_date)]],
                        columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
                    )
                    df = pd.concat([df, new_row], ignore_index=True)
                    st.success("Registered Successfully!")
                st.session_state.inventory = df
                save_inventory(df)
        
        with b_col2:
            if is_update:
                if st.button("🗑 Delete Item", key="del_btn", type="primary"):
                    df = st.session_state.inventory.copy()
                    df = df[~mask]
                    st.session_state.inventory = df
                    save_inventory(df)
                    st.warning("Item Deleted.")
                    st.session_state.last_loaded_key = ""
                    st.rerun()

# ======================================================
# TAB 2: View / Print Inventory (All)
# ======================================================
with tab2:
    st.subheader("View / Print Inventory")
    
    df = st.session_state.inventory.copy()
    
    # 날짜 필터
    date_filter = st.date_input("Filter by Date", key="view_date")
    if date_filter:
        df = df[df["Date"] == str(date_filter)]
    
    # 지점 필터 (추가됨)
    branch_filter = st.selectbox("Branch", ["All"] + branches, key="view_branch")
    if branch_filter != "All":
        df = df[df["Branch"] == branch_filter]
    
    category_filter = st.selectbox("Category", ["All"] + sorted(set(df["Category"])), key="view_cat")
    if category_filter != "All":
        df = df[df["Category"] == category_filter]
    
    item_filter = st.selectbox("Item", ["All"] + sorted(set(df["Item"])), key="view_item")
    if item_filter != "All":
        df = df[df["Item"] == item_filter]
    
    st.dataframe(df, use_container_width=True)
    
    printable_html = df.to_html(index=False)
    st.download_button(
        "🖨 Download Printable HTML",
        data=f"<html><body>{printable_html}</body></html>",
        file_name="inventory_print.html",
        mime="text/html",
        key="print_html"
    )

# ======================================================
# TAB 3: IN/OUT Log (All)
# ======================================================
with tab3:
    st.subheader("Stock IN / OUT Log (Auto Update Inventory)")
    
    c1, c2, c3 = st.columns(3)

    with c1:
        log_date = st.date_input("Date", value=date.today(), key="log_date")
        log_branch = st.selectbox("Branch", branches, key="log_branch")
    
    with c2:
        log_category = st.selectbox("Category", get_all_categories(), key="log_category")
        log_items = get_items_by_category(log_category)
        log_item = st.selectbox("Item", log_items, key="log_item")
    
    with c3:
        log_unit = get_unit_for_item(log_category, log_item)
        st.write(f"Unit: **{log_unit or '-'}**")
        log_type = st.selectbox("Type", ["IN", "OUT"], key="log_type")
        log_qty = st.number_input("Quantity", min_value=0.0, step=1.0, key="log_qty")

    if st.button("📥 Record IN / OUT", key="log_btn"):
        # 1) 히스토리 저장
        history_df = st.session_state.history.copy()
        history_df.loc[len(history_df)] = [
            str(log_date), log_branch, log_category, log_item, log_unit, log_type, log_qty
        ]
        st.session_state.history = history_df
        save_history(history_df)

        # 2) 재고 자동 반영
        inv = st.session_state.inventory.copy()
        mask = (inv["Branch"] == log_branch) & (inv["Item"] == log_item) & (inv["Category"] == log_category)
        if mask.any():
            if log_type == "IN":
                inv.loc[mask, "CurrentQty"] = inv.loc[mask, "CurrentQty"] + log_qty
            else:
                inv.loc[mask, "CurrentQty"] = inv.loc[mask, "CurrentQty"] - log_qty
        else:
            # 기존 재고 없는 상태에서 IN이면 새로 생성
            if log_type == "IN":
                new_row = pd.DataFrame(
                    [[log_branch, log_item, log_category, log_unit, log_qty, 0, "", str(log_date)]],
                    columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
                )
                inv = pd.concat([inv, new_row], ignore_index=True)
            else:
                st.warning("OUT인데 해당 재고가 없어서 수량은 반영되지 않았습니다.")

        st.session_state.inventory = inv
        save_inventory(inv)
        st.success("IN / OUT recorded and inventory updated!")

    st.markdown("### Recent Stock Movements")
    st.dataframe(st.session_state.history.tail(50), use_container_width=True)

# ======================================================
# TAB 4: Usage Analysis (All)
# ======================================================
with tab4:
    st.subheader("Usage Analysis (by Branch / Category / Item)")
    
    if check_login("tab4"):
        history_df = st.session_state.history.copy()
        if history_df.empty:
            st.info("No history data yet.")
        else:
            history_df["DateObj"] = pd.to_datetime(history_df["Date"])

            a1, a2, a3 = st.columns(3)
            with a1:
                sel_branch = st.selectbox("Branch", ["All"] + branches, key="ana_branch")
            with a2:
                sel_cat = st.selectbox("Category", ["All"] + get_all_categories(), key="ana_cat")
            with a3:
                # 기간 선택 (월 단위)
                year_options = sorted(set(history_df["DateObj"].dt.year))
                sel_year = st.selectbox("Year", year_options, index=len(year_options)-1, key="ana_year")
                sel_month = st.selectbox("Month", list(range(1,13)), index=datetime.now().month-1, key="ana_month")

            # 필터 적용
            filt = (history_df["DateObj"].dt.year == sel_year) & (history_df["DateObj"].dt.month == sel_month)
            if sel_branch != "All":
                filt &= (history_df["Branch"] == sel_branch)
            if sel_cat != "All":
                filt &= (history_df["Category"] == sel_cat)

            use_df = history_df[filt]

            if use_df.empty:
                st.info("선택한 조건에 해당하는 데이터가 없습니다.")
            else:
                # OUT 기준 사용량 계산
                out_df = use_df[use_df["Type"] == "OUT"]

                st.markdown("#### Top Used Items (by OUT Quantity)")
                item_usage = out_df.groupby(["Branch","Category","Item"])["Qty"].sum().reset_index()
                item_usage = item_usage.sort_values("Qty", ascending=False)
                st.dataframe(item_usage.head(20), use_container_width=True)

                st.markdown("#### Category Usage (OUT Quantity)")
                cat_usage = out_df.groupby(["Branch","Category"])["Qty"].sum().reset_index()
                cat_usage = cat_usage.sort_values("Qty", ascending=False)
                st.dataframe(cat_usage, use_container_width=True)

# ======================================================
# TAB 5: Monthly Report (Manager Only)
# ======================================================
if tab5:
    with tab5:
        st.subheader("📄 Monthly Stock Report (Excel + PDF)")
        
        if check_login("tab5"):
            rep_year = st.number_input("Year", min_value=2020, max_value=2100, value=datetime.now().year, step=1, key="rep_year")
            rep_month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month, step=1, key="rep_month")

            if st.button("Generate Monthly Report", key="rep_btn"):
                inv = st.session_state.inventory.copy()
                hist = st.session_state.history.copy()

                # 날짜 처리
                inv["DateObj"] = pd.to_datetime(inv["Date"], errors="coerce")
                hist["DateObj"] = pd.to_datetime(hist["Date"], errors="coerce")

                inv_m = inv[(inv["DateObj"].dt.year == rep_year) & (inv["DateObj"].dt.month == rep_month)]
                hist_m = hist[(hist["DateObj"].dt.year == rep_year) & (hist["DateObj"].dt.month == rep_month)]

                # 월간 사용량 (OUT 기준)
                usage_m = pd.DataFrame()
                if not hist_m.empty:
                    out_m = hist_m[hist_m["Type"] == "OUT"]
                    usage_m = out_m.groupby(["Branch","Category","Item"])["Qty"].sum().reset_index().sort_values("Qty", ascending=False)

                # ===== Excel 생성 =====
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    inv_m.to_excel(writer, sheet_name="Inventory", index=False)
                    hist_m.to_excel(writer, sheet_name="IN_OUT_History", index=False)
                    if not usage_m.empty:
                        usage_m.to_excel(writer, sheet_name="Usage_TOP", index=False)
                excel_buffer.seek(0)

                st.download_button(
                    "⬇ Download Excel Report",
                    data=excel_buffer,
                    file_name=f"Everest_Report_{rep_year}_{rep_month}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_dl"
                )

                # ===== PDF 생성 (간단 요약 / reportlab 필요) =====
                try:
                    from reportlab.lib.pagesizes import A4
                    from reportlab.pdfgen import canvas

                    pdf_buffer = io.BytesIO()
                    c = canvas.Canvas(pdf_buffer, pagesize=A4)
                    text = c.beginText(40, 800)
                    text.setFont("Helvetica", 11)

                    text.textLine(f"Everest Monthly Stock Report - {rep_year}-{rep_month:02d}")
                    text.textLine("")
                    text.textLine(f"Total inventory rows this month: {len(inv_m)}")
                    text.textLine(f"Total IN/OUT records this month: {len(hist_m)}")
                    text.textLine("")

                    if not usage_m.empty:
                        text.textLine("Top Used Items (OUT):")
                        for _, row in usage_m.head(10).iterrows():
                            line = f"- {row['Branch']} / {row['Category']} / {row['Item']}: {row['Qty']}"
                            text.textLine(line)
                    else:
                        text.textLine("No OUT records this month.")

                    c.drawText(text)
                    c.showPage()
                    c.save()
                    pdf_buffer.seek(0)

                    st.download_button(
                        "⬇ Download PDF Summary",
                        data=pdf_buffer,
                        file_name=f"Everest_Report_{rep_year}_{rep_month}.pdf",
                        mime="application/pdf",
                        key="pdf_dl"
                    )
                except Exception:
                    st.info("PDF 생성을 위해서는 requirements.txt 에 'reportlab' 패키지를 추가해야 합니다.")

# ======================================================
# TAB 6: Data Management (Bulk Import) (Manager Only)
# ======================================================
if tab6:
    with tab6:
        st.subheader("💾 Data Management / Settings")
        
        if check_login("tab6"):
            st.markdown("### 1. Bulk Import Ingredients")
            st.info("Upload an Excel file to register all your ingredients at once. Existing data will be overwritten/merged.")

            # 1. 템플릿 다운로드
            sample_data = [
                {"Category": "Vegetable", "Item": "Onion", "Unit": "kg"},
                {"Category": "Meat", "Item": "Chicken", "Unit": "kg"},
                {"Category": "Sauce", "Item": "Soy Sauce", "Unit": "L"},
            ]
            sample_df = pd.DataFrame(sample_data)
            
            template_buffer = io.BytesIO()
            with pd.ExcelWriter(template_buffer, engine="openpyxl") as writer:
                sample_df.to_excel(writer, index=False)
            template_buffer.seek(0)
            
            st.download_button(
                label="⬇ Download Excel Template",
                data=template_buffer,
                file_name="ingredient_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_template"
            )

            # 2. 파일 업로드 및 처리
            uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="file_uploader")
            
            if uploaded_file is not None:
                try:
                    new_df = pd.read_excel(uploaded_file)
                    st.write("Preview of uploaded data:")
                    st.dataframe(new_df.head(), use_container_width=True)
                    
                    # 유효성 검사 (Relaxed Validation)
                    # 1. 컬럼명 정규화 (공백제거, Title Case 변환)
                    # 예: " category " -> "Category", "item" -> "Item"
                    new_df.columns = [c.strip().title() for c in new_df.columns]

                    required_cols = ["Category", "Item", "Unit"]
                    missing_cols = [col for col in required_cols if col not in new_df.columns]

                    if missing_cols:
                        st.error(f"Excel file must contain columns: {required_cols}. Missing: {missing_cols}")
                    else:
                        if st.button("✅ Apply to Database", key="apply_db"):
                            # 파일로 저장 (food ingrediants.txt)
                            # 기존 형식: Category<TAB>Item<TAB>Unit
                            with open(ITEM_FILE, "w", encoding="utf-8") as f:
                                for _, row in new_df.iterrows():
                                    # 탭이나 줄바꿈 문자 제거
                                    cat = str(row["Category"]).strip()
                                    item = str(row["Item"]).strip()
                                    unit = str(row["Unit"]).strip()
                                    if cat and item:
                                        f.write(f"{cat}\t{item}\t{unit}\n")
                            
                            # 메모리 갱신
                            # item_db, categories 변수 등은 리로드 필요
                            # 가장 쉬운 방법은 캐시 날리거나, rerun.
                            # 여기서는 app 재실행 유도 또는 직접 갱신
                            st.success("Successfully updated! Reloading...")
                            st.rerun() 

                except Exception as e:
                    st.error(f"Error processing file: {e}")

            st.markdown("---")
            st.markdown("### 2. Emergency Recovery")
            st.warning("If file upload fails due to network issues, you can initialize the database with basic default ingredients.")
            if st.button("🚀 Initialize with Default Ingredients", key="init_defaults"):
                with open(ITEM_FILE, "w", encoding="utf-8") as f:
                    for d in ingredient_list:
                        f.write(f"{d['category']}\t{d['item']}\t{d['unit']}\n")
                st.success("Default database created! Reloading...")
                st.rerun()
