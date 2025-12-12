import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import io

# ================= Page Config ==================
st.set_page_config(
    page_title="Everest Inventory Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= Ingredient Database (기본 하드코딩 백업) ==================
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

# ================= Files ==================
DATA_FILE = "inventory_data.csv"          # 재고 스냅샷
HISTORY_FILE = "stock_history.csv"        # 입출고 로그
ITEM_FILE = "food ingrediants.txt"        # 카테고리/아이템/단위 DB

# ================= Global CSS ==================
st.markdown("""
<style>
/* .stApp background is handled by config.toml now */
h1 {word-break:keep-all;}
.card-header {display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center;}
.metric-card {background:#1f2937; padding:12px 18px; border-radius:10px; border:1px solid #4b5563;}
</style>
""", unsafe_allow_html=True)

# ================= Load item DB from file ==================
def load_item_db():
    """
    food ingrediants.txt 형식:
    Category<TAB>Item<TAB>Unit
    """
    if not os.path.exists(ITEM_FILE):
        return []

    items = []
    with open(ITEM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
            if len(parts) >= 3:
                cat, item, unit = parts[0], parts[1], parts[2]
                items.append({"category": cat, "item": item, "unit": unit})
    return items

item_db = load_item_db()

def get_all_categories():
    if item_db:
        return sorted(set([i["category"] for i in item_db]))
    else:
        return sorted(set([i["category"] for i in ingredient_list]))

def get_items_by_category(category):
    if item_db:
        return sorted([i["item"] for i in item_db if i["category"] == category])
    else:
        return sorted([i["item"] for i in ingredient_list if i["category"] == category])

def get_unit_for_item(category, item):
    if item_db:
        for i in item_db:
            if i["category"] == category and i["item"] == item:
                return i["unit"]
    return ""  # 없으면 빈 문자열

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

branches = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]
categories = get_all_categories()

# ================= Header ==================
st.markdown(f"""
<div class="card-header">
    <div>
        <h1>Everest Inventory Management System</h1>
        <p>Manage stock by branch, date, category, item, and movement history.</p>
    </div>
    <div class="metric-card">
        Total inventory rows: <b>{len(st.session_state.inventory)}</b><br>
        Total history rows: <b>{len(st.session_state.history)}</b>
    </div>
</div>
""", unsafe_allow_html=True)

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
# TAB 1: Register / Edit Inventory (아이템 선택 시 Unit 자동)
# ======================================================
with tab1:
    st.subheader("Register / Edit Inventory")
    
    col0, col1, col2, col3 = st.columns(4)
    
    with col0:
        selected_date = st.date_input("📅 Date", value=date.today(), key="selected_date")
    
    with col1:
        branch = st.selectbox("Branch", branches, key="branch")
        category = st.selectbox("Category", categories, key="category")
    
    with col2:
        input_type = st.radio("Item Input", ["Select from list", "Type manually"], key="input_type")
        if input_type == "Select from list":
            items = get_items_by_category(category)
            item = st.selectbox("Item name", items, key="item_name")
        else:
            item = st.text_input("Item name", key="item_name_manual")

        # ---- Unit 자동 세팅 + 선택 가능 ----
        auto_unit = get_unit_for_item(category, item) if input_type == "Select from list" else ""
        unit_options = ["", "kg", "g", "pcs", "box", "L", "mL", "pack", "bag"]
        default_index = unit_options.index(auto_unit) if auto_unit in unit_options else 0
        unit = st.selectbox("Unit", unit_options, index=default_index, key="unit_select")

    with col3:
        qty = st.number_input("Current Quantity", min_value=0.0, step=1.0, key="qty")
        min_qty = st.number_input("Minimum Required", min_value=0.0, step=1.0, key="min_qty")
        note = st.text_input("Note", key="note")

    if st.button("💾 Save / Update", key="save_btn"):
        df = st.session_state.inventory.copy()
        new_row = pd.DataFrame(
            [[branch, item, category, unit, qty, min_qty, note, str(selected_date)]],
            columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
        )
        df = pd.concat([df, new_row], ignore_index=True)
        st.session_state.inventory = df
        save_inventory(df)
        st.success("Saved Successfully!")

# ======================================================
# TAB 2: View / Print Inventory
# ======================================================
with tab2:
    st.subheader("View / Print Inventory")
    
    df = st.session_state.inventory.copy()
    
    # 날짜 필터
    date_filter = st.date_input("Filter by Date", key="view_date")
    if date_filter:
        df = df[df["Date"] == str(date_filter)]
    
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
# TAB 3: IN/OUT Log (날짜별 입·출고 기록 + 재고 자동 반영)
# ======================================================
with tab3:
    st.subheader("Stock IN / OUT Log (Auto Update Inventory)")
    
    c1, c2, c3 = st.columns(3)

    with c1:
        log_date = st.date_input("Date", value=date.today(), key="log_date")
        log_branch = st.selectbox("Branch", branches, key="log_branch")
    
    with c2:
        log_category = st.selectbox("Category", categories, key="log_category")
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
# TAB 4: Usage Analysis (카테고리/지점별 사용량 분석)
# ======================================================
with tab4:
    st.subheader("Usage Analysis (by Branch / Category / Item)")

    history_df = st.session_state.history.copy()
    if history_df.empty:
        st.info("No history data yet.")
    else:
        history_df["DateObj"] = pd.to_datetime(history_df["Date"])

        a1, a2, a3 = st.columns(3)
        with a1:
            sel_branch = st.selectbox("Branch", ["All"] + branches, key="ana_branch")
        with a2:
            sel_cat = st.selectbox("Category", ["All"] + categories, key="ana_cat")
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
# TAB 5: Monthly Report (Excel + PDF)
# ======================================================
with tab5:
    st.subheader("📄 Monthly Stock Report (Excel + PDF)")

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
# TAB 6: Data Management (Bulk Import)
# ======================================================
with tab6:
    st.subheader("💾 Data Management / Settings")
    
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
                    st.success("Successfully updated! Please refresh the page to reflect changes.")
                    
                    # session_state 갱신 시도 (optional)
                    # item_db = load_item_db() # 전역이라 즉시 반영 안될 수 있음, rerun 권장
                    st.stop() # Rerun to reload

        except Exception as e:
            st.error(f"Error processing file: {e}")
