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
    # URL 쿼리 파라미터 확인 (브라우저 새로고침 대응)
    if st.query_params.get("skip_splash") == "true":
        st.session_state["splash_shown"] = True
    else:
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

    bg_img_path = "assets/everest_splash_bg.jpg"
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
        st.query_params["skip_splash"] = "true"  # 새로고침 시에도 스킵되도록 설정
        st.rerun()
            
    st.stop() # Stop execution here so the rest of the app doesn't load

# ================= Normal App Logic Starts Here ==================

# ================= Ingredient Database (기본 하드코딩 백업) ==================
# ================= Ingredient Database (기본 하드코딩 백업) ==================
# ================= Ingredient Database (빈 상태로 시작) ==================
ingredient_list = []

# ================= Files (Absolute Paths for Persistence) ==================
# Render Persistent Disk (/data) 확인, 없으면 현재 디렉토리의 data 폴더 사용
if os.path.exists("/data"):
    BASE_DIR = "/data"
else:
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)

DATA_FILE = os.path.join(BASE_DIR, "inventory_data.csv")          # 재고 스냅샷
HISTORY_FILE = os.path.join(BASE_DIR, "stock_history.csv")        # 입출고 로그
ITEM_FILE = os.path.join(BASE_DIR, "food ingredients.txt")        # 원본 (백업용)
INV_DB = os.path.join(BASE_DIR, "inventory_db.csv")             # 재고용 DB
PUR_DB = os.path.join(BASE_DIR, "purchase_db.csv")              # 구매용 DB
VENDOR_FILE = os.path.join(BASE_DIR, "vendor_mapping.csv")      # 구매처 매핑 DB
ORDERS_FILE = os.path.join(BASE_DIR, "orders_db.csv")           # 발주(주문) 내역 DB

# ================= Login Logic ==================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Import security utilities (optional - graceful fallback)
try:
    from utils.security import verify_password, check_session_timeout, get_session_remaining_time, format_session_time
    SECURITY_MODULE_AVAILABLE = True
except ImportError:
    SECURITY_MODULE_AVAILABLE = False

def check_login(key_suffix):
    """
    Returns True if logged in, False if not (and shows login form).
    key_suffix: unique string for widget keys (e.g., "tab4")
    """
    # Check session timeout if security module is available
    if SECURITY_MODULE_AVAILABLE and st.session_state.get("logged_in", False):
        is_valid, message = check_session_timeout(st.session_state)
        if not is_valid:
            st.warning(f"⏰ {message}")
            st.session_state["logged_in"] = False
            st.rerun()
        else:
            # Show remaining session time in sidebar (optional)
            remaining = get_session_remaining_time(st.session_state)
            if remaining < 300:  # Less than 5 minutes
                st.sidebar.info(f"⏱️ Session: {format_session_time(remaining)}")
    
    if st.session_state["logged_in"]:
        return True

    st.warning("🔒 Manager Login Required")
    password = st.text_input("Password", type="password", key=f"login_pw_{key_suffix}")
    
    if st.button("Login", key=f"login_btn_{key_suffix}"):
        # Try new security module first, fallback to hardcoded
        if SECURITY_MODULE_AVAILABLE:
            if verify_password(password):
                st.session_state["logged_in"] = True
                st.session_state["last_activity"] = __import__('time').time()
                st.rerun()
            else:
                st.error("Incorrect Password")
        else:
            # Original logic (backward compatibility)
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
    word-break: keep-all; /* Prevent awkward breaks */
    white-space: nowrap; /* Keep on one line if possible */
}
.subtitle-text {
    font-size: 0.8rem; /* Smaller subtitle */
    color: #94a3b8;
    margin-top: 2px;
    word-break: keep-all;
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

def robust_read_csv(file_path, **kwargs):
    """
    다양한 인코딩 및 형식을 지원하는 강건한 CSV 읽기 함수.
    """
    if not os.path.exists(file_path):
        return pd.DataFrame()
        
    encodings = ['utf-8-sig', 'utf-16', 'cp949', 'latin-1']
    for enc in encodings:
        try:
            # sep=None, engine='python'은 구분자 자동 감지를 위해 사용
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc, **kwargs)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            # 인코딩 외의 에러(예: 빈 파일)일 경우 다음으로 넘어가거나 빈 DF 반환
            continue
            
    # 모든 인코딩 실패 시 최후의 방법 (바이트 무시)
    try:
        return pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8', errors='ignore', **kwargs)
    except:
        return pd.DataFrame()

def load_item_db(file_path):
    """
    아이템 DB 로드 (robust_read_csv 사용)
    """
    items = []
    df = robust_read_csv(file_path)
    
    if df.empty or len(df.columns) < 2:
        return items
        
    try:
        col_map = {c.lower().strip(): c for c in df.columns}
        cat_col = next((col_map[k] for k in ["category", "cat", "카테고리"] if k in col_map), df.columns[0])
        item_col = next((col_map[k] for k in ["item", "name", "아이템", "품목"] if k in col_map), df.columns[1] if len(df.columns) > 1 else None)
        unit_col = next((col_map[k] for k in ["unit", "단위"] if k in col_map), df.columns[2] if len(df.columns) > 2 else None)
        
        for _, row in df.iterrows():
            cat = str(row[cat_col]).strip() if cat_col and cat_col in df.columns else ""
            name = str(row[item_col]).strip() if item_col and item_col in df.columns else ""
            unit = str(row[unit_col]).strip() if unit_col and unit_col in df.columns else ""
            if cat and name and cat.lower() not in ["category", "카테고리"]:
                items.append({"category": cat, "item": name, "unit": unit})
    except Exception as e:
        st.error(f"Error parsing items in {file_path}: {e}")
        
    return items

def load_vendor_mapping():
    mapping = {}
    df = robust_read_csv(VENDOR_FILE)
    if not df.empty:
        try:
            # 컬럼명 정규화
            col_map = {c.lower().strip(): c for c in df.columns}
            cat_col = next((col_map[k] for k in ["category", "카테고리"] if k in col_map), df.columns[0])
            item_col = next((col_map[k] for k in ["item", "name", "아이템", "품목"] if k in col_map), None) # Item 컬럼 추가
            vendor_col = next((col_map[k] for k in ["vendor", "구매처", "업체"] if k in col_map), df.columns[2] if len(df.columns) > 2 else None)
            phone_col = next((col_map[k] for k in ["phone", "전화번호", "연락처"] if k in col_map), df.columns[3] if len(df.columns) > 3 else None)
            
            for _, row in df.iterrows():
                cat = str(row[cat_col]).strip()
                item = str(row[item_col]).strip() if item_col else "" # Item 값 읽기
                vendor = str(row[vendor_col]).strip() if vendor_col else ""
                phone = str(row[phone_col]).strip() if phone_col else ""
                
                # 키를 (Category, Item)으로 변경. Item이 없으면 포괄적인 Category 룰로 쓸 수도 있겠으나,
                # 사용자 요청은 아이템별 매핑이므로 (cat, item)을 키로 잡음.
                if cat and item:
                    mapping[(cat, item)] = {"vendor": vendor, "phone": phone}
                elif cat and not item: 
                     # 혹시 Item 없이 카테고리만 있는 경우 'ALL' 키(또는 빈 문자열)로 처리하여 fallback 가능하게?
                     # 일단 명확성을 위해 (cat, "") 키로 저장
                     mapping[(cat, "")] = {"vendor": vendor, "phone": phone}
        except Exception as e:
            st.error(f"Error parsing vendors: {e}")
    return mapping

def get_all_categories(file_path):
    db = load_item_db(file_path)
    return sorted(set([i["category"] for i in db]))

def get_all_units(file_path):
    db = load_item_db(file_path)
    return sorted(set([i["unit"] for i in db if i["unit"]]))

def get_items_by_category(file_path, category):
    db = load_item_db(file_path)
    return sorted([i["item"] for i in db if i["category"] == category])

def get_unit_for_item(file_path, category, item):
    db = load_item_db(file_path)
    for i in db:
        if i["category"] == category and i["item"] == item:
            return i["unit"]
    return ""

# ================= Data Load / Save ==================
def load_inventory():
    df = robust_read_csv(DATA_FILE)
    expected = ["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
    if df.empty:
        return pd.DataFrame(columns=expected)
    
    # 필요한 컬럼 보장
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    return df[expected]

def save_inventory(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

def load_history():
    df = robust_read_csv(HISTORY_FILE)
    expected = ["Date","Branch","Category","Item","Unit","Type","Qty"]
    if df.empty:
        return pd.DataFrame(columns=expected)
        
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    return df[expected]

def save_history(df):
    df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")

def load_orders():
    df = robust_read_csv(ORDERS_FILE)
    expected = ["OrderId", "Date", "Branch", "Vendor", "Items", "Status", "CreatedDate"]
    if df.empty:
        return pd.DataFrame(columns=expected)
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    return df[expected]

def save_orders(df):
    df.to_csv(ORDERS_FILE, index=False, encoding="utf-8-sig")

# ================= Session & Data Refresh ==================
# 매 리런(Rerun) 마다 최신 데이터를 파일에서 직접 읽어오도록 하여 실시간성 확보
st.session_state.inventory = load_inventory()
st.session_state.history = load_history()

# Default role: Staff (REMOVED)
# ...

branches = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]

# --- Storage Status Check ---
storage_mode = "Unknown"
if BASE_DIR == "/data":
    storage_mode = "Persistent 🟢"
    storage_msg = "Data is saved to Persistent Disk (/data)."
else:
    storage_mode = "Temporary ⚠️"
    storage_msg = "Data is saved locally (Temporary). Data may be lost on restart if on cloud."
# ----------------------------

# ================= Header (Compact) ==================
col_h1, col_h2 = st.columns([0.5, 9.5])

with col_h1:
    if os.path.exists("assets/logo_circle.png"):
        st.image("assets/logo_circle.png", width=50)       
    else:
        st.markdown("<div style='font-size:2rem; text-align:center;'>🏔</div>", unsafe_allow_html=True)

with col_h2:
    h_col1, h_col2 = st.columns([8, 2])
    with h_col1:
        st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px;">
            <h1 class="title-text" style="font-size: 1.8rem; margin: 0;">Everest Inventory</h1>
            <p class="subtitle-text" style="margin: 0; white-space: normal;">Professional Stock Management System</p>
            <span style="font-size: 0.8rem; background: #334155; padding: 2px 8px; border-radius: 4px; color: #94a3b8;">{storage_mode}</span>
        </div>
        """, unsafe_allow_html=True)
    with h_col2:
        if st.button("🔄 Sync Data", help="최신 데이터를 불러오기 위해 화면을 새로고침합니다."):
            st.rerun()

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "✏ Register / Edit",
    "📊 View / Print",
    "🛒 Purchase",
    "📦 IN / OUT Log",
    "📈 Usage Analysis",
    "📄 Monthly Report",
    "💾 Data Management",
    "❓ Help Manual"
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
            category = st.selectbox("Category", get_all_categories(INV_DB), key="category")
        
        with col2:
            input_type = st.radio("Item Input", ["Select from list", "Type manually"], key="input_type")
            if input_type == "Select from list":
                items = get_items_by_category(INV_DB, category)
                item = st.selectbox("Item name", items, key="item_name")
            else:
                item = st.text_input("Item name", key="item_name_manual")

            # ---- Unit 자동 세팅 + 선택 가능 ----
            auto_unit = get_unit_for_item(INV_DB, category, item) if input_type == "Select from list" else ""
            # unit_options = ["", "kg", "g", "pcs", "box", "L", "mL", "pack", "bag"]  # Old hardcoded
            unit_options = [""] + get_all_units(INV_DB)  # Dynamic from DB
            
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
# TAB 3: Purchase (구매) (All)
# ======================================================
with tab3:
    st.subheader("🛒 Item Purchase (품목 구매)")
    st.info("구매할 품목의 수량을 입력하면 구매처별로 정리하여 문자를 보낼 수 있습니다.")
    
    vendor_map = load_vendor_mapping()
    all_items = load_item_db(PUR_DB)
    
    # --- Date & Branch Selection (New) ---
    pb_col1, pb_col2 = st.columns(2)
    with pb_col1:
        p_date = st.date_input("날짜 (Date)", value=date.today(), key="p_date")
    with pb_col2:
        p_branch = st.selectbox("지점 (Branch)", branches, key="p_branch")
    
    st.markdown("---")
    # -------------------------------------
    
    if "purchase_cart" not in st.session_state:
        st.session_state.purchase_cart = {} # {(category, item): qty}
        
    p_col1, p_col2 = st.columns([4, 6])
    
    with p_col1:
        st.markdown("### 1. Select Items")
        p_cat = st.selectbox("Category", ["All"] + get_all_categories(PUR_DB), key="p_cat")
        
        filtered_items = []
        if p_cat == "All":
            filtered_items = all_items
        else:
            filtered_items = [i for i in all_items if i["category"] == p_cat]
            
        for idx, item_info in enumerate(filtered_items):
            ikey = (item_info["category"], item_info["item"])
            
            # 행(Row) 구성: 품목명 | 수량입력 | Done버튼
            r_col1, r_col2, r_col3 = st.columns([5, 3, 2])
            
            # Check if item is already in cart
            in_cart = ikey in st.session_state.purchase_cart
            cart_qty = st.session_state.purchase_cart.get(ikey, 0.0)

            with r_col1:
                if in_cart:
                    st.markdown(f"**{item_info['item']}** ({item_info['unit']}) <span style='color:#4ade80; font-weight:bold; background:#064e3b; padding:2px 6px; border-radius:4px;'>✅ 담김 ({cart_qty})</span>", unsafe_allow_html=True)
                else:
                    st.write(f"**{item_info['item']}** ({item_info['unit']})")
            
            with r_col2:
                # 현재 장바구니에 담긴 값이 있다면 기본값으로 보여줌
                current_val = cart_qty
                reset_key = st.session_state.get("reset_trigger", 0)
                temp_qty = st.number_input("", min_value=0.0, step=1.0, 
                                          value=float(current_val),
                                          key=f"p_input_{p_cat}_{idx}_{reset_key}", 
                                          label_visibility="collapsed")
            
            with r_col3:
                # Done 버튼 클릭 시에만 장바구니(purchase_cart)에 저장
                if st.button("Done", key=f"done_btn_{p_cat}_{idx}", use_container_width=True):
                    if temp_qty > 0:
                        st.session_state.purchase_cart[ikey] = temp_qty
                        st.toast(f"✅ {item_info['item']} {temp_qty}{item_info['unit']} Added!", icon="🛒")
                    else:
                        if ikey in st.session_state.purchase_cart:
                            del st.session_state.purchase_cart[ikey]
                            st.toast(f"🗑 {item_info['item']} removed!", icon="🗑")
                    st.rerun()

        st.write("---")
        if st.button("🗑 Reset All", key="reset_cart", use_container_width=True):
            st.session_state.purchase_cart = {}
            st.session_state["reset_trigger"] = st.session_state.get("reset_trigger", 0) + 1
            st.rerun()

    with p_col2:
        st.markdown("### 2. Purchase Summary & SMS")
        # 실제 값이 담긴 항목만 필터링 (0보다 큰 것)
        active_cart = {k: v for k, v in st.session_state.purchase_cart.items() if v > 0}
        
        if not active_cart:
            st.warning("선택된 품목이 없습니다.")
        else:
            if st.button("🗑 Clear All (전체 삭제)", key="clear_all_summary", type="primary", use_container_width=True):
                st.session_state.purchase_cart = {}
                st.rerun()

            st.write("---")

            # Group by Vendor
            vendor_groups = {}
            for (cat, item), qty in active_cart.items():
                # 1. (Category, Item)으로 직접 찾기
                v_info = vendor_map.get((cat, item))
                
                # 2. 없으면 (Category, "") 로 찾기 (Category 전체 매핑)
                if not v_info:
                    v_info = vendor_map.get((cat, ""))
                
                # 3. 그래도 없으면 미지정
                if not v_info:
                    # 매핑 정보가 없을 경우, 디버깅을 위해 카테고리를 함께표시
                    v_name = f"미지정 (Unknown) - {cat}"
                    v_phone = ""
                else:
                    v_name = v_info["vendor"]
                    v_phone = v_info["phone"]
                
                if v_name not in vendor_groups:
                    vendor_groups[v_name] = {"phone": v_phone, "items": []}
                vendor_groups[v_name]["items"].append({
                    "cat": cat,
                    "item": item,
                    "qty": qty,
                    "unit": get_unit_for_item(PUR_DB, cat, item)
                })
            
            for v_name, data in vendor_groups.items():
                with st.expander(f"📦 {v_name} ({data['phone']})", expanded=True):
                    final_items_list = []
                    
                    for i_idx, item_data in enumerate(data["items"]):
                        cat, item, qty, unit = item_data["cat"], item_data["item"], item_data["qty"], item_data["unit"]
                        ikey = (cat, item)
                        
                        e_col1, e_col2 = st.columns([8, 2])
                        with e_col1:
                            st.write(f"• **{item}**: {qty} {unit}")
                        with e_col2:
                            # 요약 섹션에서의 삭제 버튼
                            if st.button("❌", key=f"p_del_{v_name}_{item}_{i_idx}"):
                                if ikey in st.session_state.purchase_cart:
                                    del st.session_state.purchase_cart[ikey]
                                st.rerun()
                        
                        final_items_list.append(f"{item} {qty}{unit}")
                    
                    st.write("---")
                    items_str = ", ".join(final_items_list)
                    
                    # SMS Body Construction
                    sms_body_lines = [
                        f"[Everest 구매요청]",
                        f"📅 {p_date}",
                        f"🏢 {p_branch}",
                        "",
                        "✅ 주문 품목:"
                    ]
                    for item_data in data["items"]:
                         sms_body_lines.append(f"- {item_data['item']} ({item_data['qty']}{item_data['unit']})")
                    sms_body_lines.append("")
                    sms_body_lines.append("확인 부탁드립니다.")

                    sms_body_final = "\n".join(sms_body_lines)
                    
                    # SMS Link Gen
                    import urllib.parse
                    encoded_body = urllib.parse.quote(sms_body_final)
                    sms_link = f"sms:{data['phone']}?body={encoded_body}"
                    
                    # Display Copy Area
                    with st.expander("📋 Review Message (메시지 미리보기)", expanded=False):
                         st.text_area("Copy Text", value=sms_body_final, height=150, key=f"sms_txt_{v_name}")

                    # --- Consolidated: Save & Send SMS ---
                    if st.button(f"📲 Save & Send SMS (저장 및 문자보내기)", key=f"save_send_{v_name}", type="primary", use_container_width=True):
                        # 1. Save Order Logic
                        import uuid
                        import json
                        
                        orders_df = load_orders()
                        new_order = {
                            "OrderId": str(uuid.uuid4()),
                            "Date": str(p_date),
                            "Branch": p_branch,
                            "Vendor": v_name,
                            "Items": json.dumps(data["items"], ensure_ascii=False),
                            "Status": "Pending",
                            "CreatedDate": str(datetime.now())
                        }
                        
                        # pd.concat to add row
                        new_row_df = pd.DataFrame([new_order])
                        orders_df = pd.concat([orders_df, new_row_df], ignore_index=True)
                        save_orders(orders_df)
                        
                        st.toast(f"✅ Order Saved! Opening SMS...", icon="📨")
                        
                        # 2. Trigger SMS using HTML meta refresh (Instant Redirect to App)
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={sms_link}">', unsafe_allow_html=True)
                        
                        # Fallback link
                        st.markdown(f"**Click below if SMS app didn't open:**")
                        st.markdown(f'<a href="{sms_link}" target="_blank" style="background:#10b981;color:white;padding:8px 12px;border-radius:5px;text-decoration:none;">📲 Open SMS App</a>', unsafe_allow_html=True)
                    # --------------------------

            # ==========================================
            # 3. Order Status & Receiving (Pending Orders)
            # ==========================================
            st.markdown("---")
            st.subheader("3. Order Status (발주 현황 및 입고 처리)")
            st.info("발주 후 도착한 물품을 확인하고 '입고 확정' 버튼을 누르면 재고에 자동 반영됩니다.")
            
            orders_df = load_orders()
            if not orders_df.empty:
                # [Fix] Keep 'Completed' items visible if they were just confirmed, to allow photo upload.
                if "freshly_confirmed" not in st.session_state:
                    st.session_state.freshly_confirmed = []
                
                # Filter: Pending OR (Completed AND in freshly_confirmed)
                mask_pending = orders_df["Status"] == "Pending"
                mask_fresh = orders_df["OrderId"].isin(st.session_state.freshly_confirmed)
                
                visible_orders = orders_df[mask_pending | mask_fresh].sort_values("CreatedDate", ascending=False)
                
                if visible_orders.empty:
                    st.write("대기 중인 발주 내역이 없습니다.")
                else:
                    import json
                    for idx, row in visible_orders.iterrows():
                        oid = row["OrderId"]
                        o_date = row["Date"]
                        o_branch = row["Branch"]
                        o_vendor = row["Vendor"]
                        o_items = json.loads(row["Items"]) # List of dicts
                        
                        with st.status(f"📅 {o_date} | 🏢 {o_branch} | 🚚 {o_vendor}", expanded=False):
                            
                            # Convert items to DataFrame for editing
                            # Check if o_items is list of dicts. 
                            # If so, create DF. columns: Item, Qty, Unit, Category
                            p_items_df = pd.DataFrame(o_items)
                            
                            # Clean up column names for display if needed or keep keys
                            # Standard keys: 'cat', 'item', 'qty', 'unit'
                            # Renaming for better UI
                            p_items_df = p_items_df.rename(columns={"item": "Item", "qty": "Qty", "unit": "Unit", "cat": "Category"})
                            # Reorder for display
                            p_items_df = p_items_df[["Category", "Item", "Qty", "Unit"]]
                            
                            st.write("▼ 아래 표에서 실 수령 수량을 수정한 뒤 '입고 확정'을 누르세요.")
                            edited_df = st.data_editor(
                                p_items_df,
                                column_config={
                                    "Qty": st.column_config.NumberColumn("Receipt Qty", min_value=0.0, step=0.5, format="%.1f"),
                                    "Item": st.column_config.TextColumn("Item", disabled=True),
                                    "Unit": st.column_config.TextColumn("Unit", disabled=True),
                                    "Category": st.column_config.TextColumn("Category", disabled=True),
                                },
                                use_container_width=True,
                                key=f"editor_{oid}",
                                num_rows="fixed"
                            )
                            
                            
                            # 1. Confirm Receipt Button (First)
                            # If already confirmed (in freshly_confirmed or Status Completed), disable button or show State
                            is_confirmed = (row["Status"] == "Completed")
                            
                            if is_confirmed:
                                st.success("✅ 이미 입고 확정된 항목입니다. (Confirmed)")
                            else:
                                if st.button("📥 Confirm Receipt (입고 확정)", key=f"confirm_{oid}", type="primary", use_container_width=True):
                                    # ... existing logic ...
                                    # 1. Update Inventory & History based on EDITED df
                                    inv_df = st.session_state.inventory.copy()
                                    hist_df = st.session_state.history.copy()
                                    
                                    # Convert back to list of dicts to save in order history
                                    final_items = []
                                    
                                    for _, e_row in edited_df.iterrows():
                                        cat, i_name, qty, unit = e_row["Category"], e_row["Item"], float(e_row["Qty"]), e_row["Unit"]
                                        
                                        # Update final items for record
                                        final_items.append({"cat": cat, "item": i_name, "qty": qty, "unit": unit})
                                        
                                        if qty > 0:
                                            # History Log
                                            hist_df.loc[len(hist_df)] = [
                                                str(date.today()), o_branch, cat, i_name, unit, "IN", qty
                                            ]
                                            
                                            # Inventory Update
                                            mask = (inv_df["Branch"] == o_branch) & (inv_df["Item"] == i_name) & (inv_df["Category"] == cat)
                                            if mask.any():
                                                current_qty = float(inv_df.loc[mask, "CurrentQty"].values[0])
                                                inv_df.loc[mask, "CurrentQty"] = current_qty + qty
                                            else:
                                                # New Item entry
                                                new_row = pd.DataFrame(
                                                    [[o_branch, i_name, cat, unit, qty, 0, "", str(date.today())]],
                                                    columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
                                                )
                                                inv_df = pd.concat([inv_df, new_row], ignore_index=True)

                                    # 2. Update Order Status & Received Items
                                    orders_df.loc[orders_df["OrderId"] == oid, "Items"] = json.dumps(final_items, ensure_ascii=False)
                                    orders_df.loc[orders_df["OrderId"] == oid, "Status"] = "Completed"
                                    
                                    # 3. Save All
                                    st.session_state.inventory = inv_df
                                    st.session_state.history = hist_df
                                    save_inventory(inv_df)
                                    save_history(hist_df)
                                    save_orders(orders_df)
                                    
                                    # [Fix] Add to freshly_confirmed so it stays visible for photo upload
                                    st.session_state.freshly_confirmed.append(oid)
                                    
                                    st.balloons()
                                    st.success("✅ 입고가 확정되었습니다! (Inventory Updated)")
                                    
                                    # Rerun to update UI (Disable button, Show success) BUT keep item visible due to filtered logic
                                    st.rerun()
                            
                            st.info("👇 **잊지 말고 아래 버튼을 눌러 거래명세서를 전송하세요! (Please Upload Receipt)**")
                            
                            # 2. Transaction Receipt Upload (Separate)
                            st.write("---")
                            st.markdown("##### 📸 Send Transaction Statement (거래명세서 전송)")
                            
                            # Inject JS to enforce camera only when this specific uploader is clicked? 
                            # Global injection covers all file inputs.
                            
                            # Drive Settings
                            drive_folder_id = "1go58wzFXi172SRRXJ0TGa71WKfyrwOi2"
                            
                            img_file = st.file_uploader(f"📸 Click here to Take Photo (명세서 촬영)", type=['png', 'jpg', 'jpeg'], key=f"rec_up_{oid}")
                            
                            if img_file is not None:
                                # Auto Upload Logic
                                if drive_folder_id:
                                    # Avoid re-uploading loops
                                    if f"uploaded_{oid}" not in st.session_state:
                                        with st.spinner("☁️ Uploading to Base (본사 전송 중)..."):
                                            from drive_utils import upload_file_to_drive
                                            # Filename: Date_Branch_Vendor.jpg
                                            file_name = f"{o_date.replace('-', '')}_{o_branch}_{o_vendor}_{oid[:4]}.jpg"
                                            img_file.seek(0)
                                            f_id = upload_file_to_drive(img_file, file_name, drive_folder_id)
                                            if f_id:
                                                st.session_state[f"uploaded_{oid}"] = True
                                                st.success(f"✅ 전송 완료! (Sent to HQ)")
                                            else:
                                                st.error("❌ 전송 실패 (Upload Failed)")
                                    else:
                                        st.success("✅ 이미 전송된 명세서입니다.")
                                else:
                                    st.warning("⚠️ Folder ID missing.")

            # --- Completed Orders View ---
            st.markdown("---")
            with st.expander("📜 View Completed Orders (입고 완료 내역)", expanded=False):
                completed_orders = orders_df[orders_df["Status"] == "Completed"].sort_values("CreatedDate", ascending=False)
                
                if completed_orders.empty:
                    st.info("No completed orders yet.")
                else:
                    st.write(f"Total: {len(completed_orders)} orders")
                    
                    for idx, row in completed_orders.iterrows():
                        oid = row["OrderId"]
                        o_date = row["Date"]
                        o_branch = row["Branch"]
                        o_vendor = row["Vendor"]
                        o_items = json.loads(row["Items"])
                        
                        st.markdown(f"**{o_date} | {o_branch} | {o_vendor}**")
                        
                        # Simple table for items
                        c_items_df = pd.DataFrame(o_items)
                        if not c_items_df.empty:
                            c_items_df = c_items_df.rename(columns={"item": "Item", "qty": "Qty", "unit": "Unit", "cat": "Category"})
                            st.dataframe(c_items_df[["Category", "Item", "Qty", "Unit"]], use_container_width=True, hide_index=True)
                        st.divider()

# ======================================================
# TAB 4: IN/OUT Log (All)
# ======================================================
with tab4:
    st.subheader("Stock IN / OUT Log (Auto Update Inventory)")
    
    c1, c2, c3 = st.columns(3)

    with c1:
        log_date = st.date_input("Date", value=date.today(), key="log_date")
        log_branch = st.selectbox("Branch", branches, key="log_branch")
    
    with c2:
        log_category = st.selectbox("Category", get_all_categories(INV_DB), key="log_category")
        log_items = get_items_by_category(INV_DB, log_category)
        log_item = st.selectbox("Item", log_items, key="log_item")
    
    with c3:
        log_unit = get_unit_for_item(INV_DB, log_category, log_item)
        st.write(f"Unit: **{log_unit or '-'}**")
        
        # --- 실시간 재고 확인 로직 추가 ---
        inv_data = st.session_state.inventory
        current_stock_row = inv_data[
            (inv_data["Branch"] == log_branch) & 
            (inv_data["Category"] == log_category) & 
            (inv_data["Item"] == log_item)
        ]
        
        if not current_stock_row.empty:
            curr_qty = float(current_stock_row.iloc[0]["CurrentQty"])
        else:
            curr_qty = 0.0
            
        st.metric(label="Current Stock (현재 재고)", value=f"{curr_qty} {log_unit}")
        # ------------------------------

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
with tab5:
    st.subheader("Usage Analysis (by Branch / Category / Item)")
    
    if check_login("tab5"):
        history_df = st.session_state.history.copy()
        if history_df.empty:
            st.info("No history data yet.")
        else:
            history_df["DateObj"] = pd.to_datetime(history_df["Date"])

            a1, a2, a3 = st.columns(3)
            with a1:
                sel_branch = st.selectbox("Branch", ["All"] + branches, key="ana_branch")
            with a2:
                sel_cat = st.selectbox("Category", ["All"] + get_all_categories(INV_DB), key="ana_cat")
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
if tab6:
    with tab6:
        st.subheader("📄 Monthly Stock Report (Excel + PDF)")
        
        if check_login("tab6"):
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
if tab7:
    with tab7:
        st.subheader("💾 Data Management / Settings")
        
        if check_login("tab7"):
            st.markdown(f"### ⚙️ System Configuration")
            
            # Storage Status Warning
            if BASE_DIR == "/data":
                 st.success("✅ **연결 성공 (Connected)**: 보존형 디스크(/data)가 정상적으로 연결되었습니다. 이제 데이터를 업로드하면 영구적으로 저장됩니다.")
            else:
                 st.error("⚠️ **저장소 미연결 (Not Connected)**: 디스크가 연결되지 않았습니다. Render 대시보드에서 설정을 확인하세요.")
            
            st.write("---")
            
            # --- 1.5 Backup & Restore (New Feature) ---
            try:
                from utils.backup import create_backup, list_backups, restore_from_backup, cleanup_old_backups, get_backup_stats
                BACKUP_MODULE_AVAILABLE = True
            except ImportError:
                BACKUP_MODULE_AVAILABLE = False
            
            if BACKUP_MODULE_AVAILABLE:
                st.markdown("### 💾 Backup & Restore (백업 및 복원)")
                
                col_b1, col_b2 = st.columns(2)
                
                with col_b1:
                    st.markdown("**Create Backup (백업 생성)**")
                    if st.button("📦 Create Backup Now (지금 백업)", type="primary", use_container_width=True):
                        files_to_backup = [DATA_FILE, HISTORY_FILE, ORDERS_FILE, INV_DB, PUR_DB, VENDOR_FILE]
                        success, msg = create_backup(BASE_DIR, files_to_backup)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    
                    # Auto cleanup old backups
                    if st.button("🗑️ Cleanup Old Backups (오래된 백업 삭제)", use_container_width=True):
                        success, msg = cleanup_old_backups(BASE_DIR, retention_days=30)
                        if success:
                            st.info(msg)
                        else:
                            st.error(msg)
                
                with col_b2:
                    st.markdown("**Backup Statistics (백업 통계)**")
                    stats = get_backup_stats(BASE_DIR)
                    if stats["total_backups"] > 0:
                        st.metric("Total Backups", stats["total_backups"])
                        st.metric("Total Size", f"{stats['total_size_mb']} MB")
                        st.caption(f"Newest: {stats['newest_date'].strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.info("No backups yet. Create your first backup!")
                
                # Restore section
                with st.expander("🔄 Restore from Backup (백업에서 복원)"):
                    backups = list_backups(BASE_DIR)
                    if backups:
                        backup_options = {f"{b['name']} ({b['size_mb']} MB)": b['path'] for b in backups}
                        selected_backup = st.selectbox("Select Backup", list(backup_options.keys()))
                        
                        st.warning("⚠️ 복원하면 현재 데이터가 백업 데이터로 덮어씌워집니다!")
                        
                        if st.button("🔄 Restore Selected Backup", type="primary"):
                            backup_path = backup_options[selected_backup]
                            success, msg = restore_from_backup(backup_path, BASE_DIR)
                            if success:
                                st.success(msg)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.info("백업 파일이 없습니다.")
                
                st.write("---")
            
            # --- 2. Current Data Status (현재 데이터 상태 확인) ---
            st.markdown("### 📊 Current Data Status (현재 저장된 데이터)")
            
            # Inventory DB Status
            inv_count = 0
            if os.path.exists(INV_DB):
                try:
                    inv_count = len(robust_read_csv(INV_DB))
                    st.success(f"**Inventory DB**: ✅ {inv_count} items saved.")
                except:
                    st.error("**Inventory DB**: ❌ File corrupted.")
            else:
                st.warning("**Inventory DB**: ❌ Empty (Not Found). Please upload data below.")

            # Purchase DB Status
            pur_count = 0
            if os.path.exists(PUR_DB):
                try:
                    pur_count = len(robust_read_csv(PUR_DB))
                    st.success(f"**Purchase DB**: ✅ {pur_count} items saved.")
                except:
                     st.error("**Purchase DB**: ❌ File corrupted.")
            else:
                st.warning("**Purchase DB**: ❌ Empty (Not Found). Please upload data below.")

            st.write("---")

            # --- 3. Factory Reset (High Risk) ---
            with st.expander("⚠️ Factory Reset (데이터 초기화 - 주의!)"):
                st.error("이 버튼을 누르면 모든 데이터가 영구적으로 삭제됩니다. 처음부터 다시 시작할 때만 사용하세요.")
                if st.button("🧨 Delete All Data (모든 데이터 삭제)", key="init_btn", type="primary"):
                    try:
                        files_to_delete = [INV_DB, PUR_DB, VENDOR_FILE, ORDERS_FILE, DATA_FILE, HISTORY_FILE]
                        for f in files_to_delete:
                            if os.path.exists(f):
                                os.remove(f)
                        st.session_state.inventory = pd.DataFrame()
                        st.session_state.history = pd.DataFrame()
                        st.session_state.purchase_cart = {}
                        st.success("All data deleted successfully. (모든 데이터가 삭제되었습니다)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting data: {e}")
                    
            # 1. 공통 처리 함수 정의
            
            # 1. 공통 처리 함수 정의
            def apply_data_to_db(df, target_file, label):
                try:
                    col_map = {c.lower().strip(): c for c in df.columns}
                    cat_col = next((col_map[k] for k in ["category", "cat", "카테고리"] if k in col_map), None)
                    item_col = next((col_map[k] for k in ["item", "name", "아이템", "품목"] if k in col_map), None)
                    unit_col = next((col_map[k] for k in ["unit", "단위"] if k in col_map), None)

                    if not cat_col or not item_col:
                        st.error(f"[{label}] 'Category' or 'Item' columns not found. Headers: {list(df.columns)}")
                        return

                    process_df = pd.DataFrame()
                    process_df["Category"] = df[cat_col].astype(str).str.strip()
                    process_df["Item"] = df[item_col].astype(str).str.strip()
                    process_df["Unit"] = df[unit_col].astype(str).str.strip() if unit_col else ""
                    
                    process_df = process_df[process_df["Category"].notna() & (process_df["Category"] != "") & 
                                            process_df["Item"].notna() & (process_df["Item"] != "")]

                    st.write(f"Preview of {label} data:")
                    st.dataframe(process_df.head(), use_container_width=True)
                    st.write(f"Total {len(process_df)} items found in this file.")

                    if st.button(f"✅ Apply to {label} Database (적용하기)", key=f"apply_{target_file}", type="primary"):
                        process_df.to_csv(target_file, index=False, encoding="utf-8-sig")
                        st.balloons()
                        st.success(f"🎉 Successfully updated {label} database! (데이터베이스에 적용되었습니다)")
                        import time
                        time.sleep(1.5) # Wait for user to see the success message
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing {label} data: {e}")

            # 2. 템플릿 다운로드 영역
            with st.expander("📥 Download Excel Templates (엑셀 양식 다운로드)"):
                sample_df = pd.DataFrame([{"Category": "Vegetable", "Item": "Onion", "Unit": "kg"}])
                template_buffer = io.BytesIO()
                with pd.ExcelWriter(template_buffer, engine="openpyxl") as writer:
                    sample_df.to_excel(writer, index=False)
                template_buffer.seek(0)
                st.download_button("⬇ Download Template (.xlsx)", data=template_buffer, file_name="everest_template.xlsx", key="dl_tmpl")

            with st.expander("📥 Download Vendor Template (거래처 양식 다운로드)"):
                vendor_sample = pd.DataFrame([{"Category": "Vegetable", "Item": "Onion", "Vendor": "Example Mart", "Phone": "010-1234-5678"}])
                v_buffer = io.BytesIO()
                with pd.ExcelWriter(v_buffer, engine="openpyxl") as writer:
                    vendor_sample.to_excel(writer, index=False)
                v_buffer.seek(0)
                st.download_button("⬇ Download Vendor Template (.xlsx)", data=v_buffer, file_name="vendor_template.xlsx", key="dl_v_tmpl")

            st.markdown("---")

            # 3. 재고관리용 데이터 업로드 섹션
            st.markdown("### 1. Inventory Items (재고관리용 목록)")
            st.info("재고 등록 및 입출고 로그 기록 시 사용되는 품목 리스트입니다.")
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                up_inv = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="up_inv")
                if up_inv:
                    try:
                        if up_inv.name.endswith('.xlsx'):
                            df_inv = pd.read_excel(up_inv)
                        else:
                            # 템플릿용 파일이므로 robust_read_csv 대신 StringIO와 encoding 시도
                            df_inv = robust_read_csv(up_inv)
                        apply_data_to_db(df_inv, INV_DB, "Inventory")
                    except Exception as e: st.error(f"Upload error: {e}")
            with i_col2:
                paste_inv = st.text_area("Paste Data (from Excel)", key="paste_inv", height=100, help="엑셀에서 복사하여 붙여넣으세요.")
                if paste_inv:
                    try:
                        # 붙여넣기 데이터는 보통 탭 구분
                        df_inv_p = pd.read_csv(io.StringIO(paste_inv), sep="\t")
                        apply_data_to_db(df_inv_p, INV_DB, "Inventory")
                    except Exception as e:
                        # 탭 실패 시 콤마 시도
                        try:
                            df_inv_p = pd.read_csv(io.StringIO(paste_inv))
                            apply_data_to_db(df_inv_p, INV_DB, "Inventory")
                        except: st.error(f"Paste error: {e}")

            st.markdown("---")

            # 4. 구매용 데이터 업로드 섹션
            st.markdown("### 2. Purchase Items (구매/주문용 목록)")
            st.info("구매 탭에서 문자 발송을 위해 구성되는 주문 품목 리스트입니다.")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                up_pur = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"], key="up_pur")
                if up_pur:
                    try:
                        if up_pur.name.endswith('.xlsx'):
                            df_pur = pd.read_excel(up_pur)
                        else:
                            df_pur = robust_read_csv(up_pur)
                        apply_data_to_db(df_pur, PUR_DB, "Purchase")
                    except Exception as e: st.error(f"Upload error: {e}")
            with p_col2:
                paste_pur = st.text_area("Paste Data (from Excel)", key="paste_pur", height=100, help="엑셀에서 복사하여 붙여넣으세요.")
                if paste_pur:
                    try:
                        df_pur_p = pd.read_csv(io.StringIO(paste_pur), sep="\t")
                        apply_data_to_db(df_pur_p, PUR_DB, "Purchase")
                    except Exception as e:
                        try:
                            df_pur_p = pd.read_csv(io.StringIO(paste_pur))
                            apply_data_to_db(df_pur_p, PUR_DB, "Purchase")
                        except: st.error(f"Paste error: {e}")

            st.markdown("---")

            # 5. 거래처(Vendor) 데이터 업로드 섹션
            st.markdown("### 3. Vendor Mapping (구매처 전화번호 관리)")
            st.info("각 품목(Item)별 구매처와 전화번호를 관리하는 리스트입니다. (필수: Category, Item, Vendor, Phone)")
            
            def apply_vendor_to_db(df):
                try:
                    col_map = {c.lower().strip(): c for c in df.columns}
                    cat_col = next((col_map[k] for k in ["category", "cat", "카테고리"] if k in col_map), None)
                    item_col = next((col_map[k] for k in ["item", "name", "아이템", "품목"] if k in col_map), None)
                    vendor_col = next((col_map[k] for k in ["vendor", "vender", "구매처", "업체"] if k in col_map), None)
                    phone_col = next((col_map[k] for k in ["phone", "전화번호", "연락처", "contact"] if k in col_map), None)

                    if not item_col or not vendor_col:
                        st.error(f"Missing columns! Requires Item, Vendor, Phone. Found: {list(df.columns)}")
                        return

                    new_df = pd.DataFrame()
                    new_df["Category"] = df[cat_col].astype(str).str.strip() if cat_col else ""
                    new_df["Item"] = df[item_col].astype(str).str.strip()
                    new_df["Vendor"] = df[vendor_col].astype(str).str.strip()
                    new_df["Phone"] = df[phone_col].astype(str).str.strip() if phone_col else ""
                    
                    new_df = new_df[new_df["Item"].notna() & (new_df["Item"] != "")]

                    st.write("Preview of Vendor Data:")
                    st.dataframe(new_df.head(), use_container_width=True)

                    if st.button("✅ Apply to Vendor DB", key="apply_vendor"):
                        new_df.to_csv(VENDOR_FILE, index=False, encoding="utf-8-sig")
                        st.success("Successfully updated Vendor Mapping!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error processing vendor data: {e}")

            v_col1, v_col2 = st.columns(2)
            with v_col1:
                up_vend = st.file_uploader("Upload Vendor Excel/CSV", type=["xlsx", "csv"], key="up_vend")
                if up_vend:
                    try:
                        if up_vend.name.endswith('.xlsx'):
                            df_vend = pd.read_excel(up_vend)
                        else:
                            df_vend = robust_read_csv(up_vend)
                        apply_vendor_to_db(df_vend)
                    except Exception as e: st.error(f"Upload error: {e}")
            with v_col2:
                paste_vend = st.text_area("Paste Vendor Data", key="paste_vend", height=100, help="엑셀에서 복사(Category/Vendor/Phone)")
                if paste_vend:
                    try:
                        df_vend_p = pd.read_csv(io.StringIO(paste_vend), sep="\t")
                        apply_vendor_to_db(df_vend_p)
                    except Exception as e:
                         # 탭 실패 시 콤마 시도
                        try:
                            df_vend_p = pd.read_csv(io.StringIO(paste_vend))
                            apply_vendor_to_db(df_vend_p)
                        except: st.error(f"Paste error: {e}")

            st.markdown("---")
            st.markdown("### 4. Emergency Recovery")
            if st.button("🚀 Initialize with Default Data", key="init_defaults"):
                default_df = pd.DataFrame([["Vegetable", "Onion", "kg"]], columns=["Category", "Item", "Unit"])
                default_df.to_csv(INV_DB, index=False, encoding="utf-8-sig")
                default_df.to_csv(PUR_DB, index=False, encoding="utf-8-sig")
                st.success("Databases initialized! Reloading...")
                st.rerun()

# ======================================================
# TAB 8: Help Manual (All)
# ======================================================
with tab8:
    st.header("🏔 Everest Inventory System - Help Manual")
    st.subheader("एभरेस्ट इन्भेन्टरी व्यवस्थापन प्रणाली - प्रयोगकर्ता पुस्तिका")
    
    st.markdown("---")
    
    st.markdown("### 1. Introduction (परिचय)")
    st.info("""
    **KO**: 에베레스트 레스토랑의 재고를 체계적으로 관리하기 위한 시스템입니다.  
    **NE**: एभरेस्ट रेस्टुरेन्टको स्टक (सामान) व्यवस्थित रूपमा व्यवस्थापन गर्नको लागि यो एउटा प्रणाली हो।
    """)

    st.markdown("### 2. Access & Login (पहुँच र लगइन)")
    st.write("""
    - **KO**: 첫 화면에서 아무 곳이나 터치하여 진입합니다.
    - **NE**: पहिलो स्क्रिनमा जहाँसुकै थिचेर भित्र जानुहोस्।
    - **Manager Password (प्रबन्धक पासवर्ड)**: `1234`
        - **KO**: 분석, 보고서, 데이터 관리 탭은 로그인이 필요합니다.
        - **NE**: विश्लेषण (Analysis), रिपोर्ट (Report), र डाटा व्यवस्थापन (Data Management) ट्याबहरूको लागि लगइन आवश्यक छ।
    """)

    st.markdown("---")
    st.markdown("### 3. Main Features (मुख्य विशेषताहरू)")
    
    with st.expander("Tab 1: Register / Edit (재고 등록 및 수정 / दर्ता र सम्पादन)"):
        st.write("""
        **KO**: 품목을 새로 등록하거나 최소 필요 수량을 설정합니다.  
        **NE**: नयाँ सामान दर्ता गर्न वा न्यूनतम आवश्यक मात्रा सेट गर्न यहाँ जानुहोस्।
        """)

    with st.expander("Tab 2: View / Print (재고 조회 및 출력 / स्टक हेर्ने र प्रिन्ट गर्ने)"):
        st.write("""
        **KO**: 현재 재고 현황을 지점별, 카테고리별로 확인하고 인쇄용 파일로 다운로드합니다.  
        **NE**: शाखा वा श्रेणी अनुसार हालको स्टक विवरण हेर्नुहोस् र प्रिन्ट गर्नको लागि फाइल डाउनलोड गर्नुहोस्।
        """)

    with st.expander("Tab 3: IN / OUT Log (입출고 기록 / भित्र र बाहिरको रेकर्ड)"):
        st.write("""
        **KO**: 배송된 물품(IN)이나 사용한 물품(OUT)을 기록하면 재고 수량이 자동으로 업데이트됩니다.  
        **NE**: आएको सामान (IN) वा प्रयोग भएको सामान (OUT) रेकर्ड गर्नुहोस्। यसले स्टकको मात्रा आफैं मिलाउनेछ।
        """)

    with st.expander("Tabs 4, 5, 6: Management (관리 기능 / व्यवस्थापन)"):
        st.write("""
        **KO**: 사용량 분석, 월간 보고서 생성, 엑셀 대량 업로드 등의 고급 기능을 제공합니다.  
        **NE**: प्रयोग विश्लेषण, मासिक रिपोर्ट, र एक्सेल अपलोड जस्ता उन्नत सुविधाहरू यहाँ उपलब्ध छन्।
        """)

    st.markdown("---")
    st.markdown("### 4. Special Features (विशेष विशेषताहरू)")
    st.warning("""
    **Low Stock Alert (재고 부족 알림 / कम स्टकको सूचना)**:
    - **KO**: 재고가 설정된 최소 수량 이하로 떨어지면 빨간색 경고창이 뜹니다.
    - **NE**: यदि सामानको मात्रा न्यूनतम सेट गरिएको भन्दा कम भयो भने, रातो रङ्गको चेतावनी देखिनेछ।
    """)
    
    st.success("""
    **Persistence (데이터 영구 저장 / डाटा सुरक्षित)**:
    - **KO**: 데이터는 서버에 자동으로 저장되므로 앱을 꺼도 사라지지 않습니다.
    - **NE**: डाटा आफैं सुरक्षित हुनेछ, त्यसैले एप बन्द गरे पनि मेटिने छैन।
    """)

    st.markdown("---")
    st.download_button(
        label="⬇ Download Detailed Word Manual (विस्तृत पुस्तिका डाउनलोड गर्नुहोस्)",
        data=open(os.path.join(BASE_DIR, 'Everest_Manual.docx'), 'rb').read() if os.path.exists(os.path.join(BASE_DIR, 'Everest_Manual.docx')) else b"",
        file_name="Everest_Manual.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
