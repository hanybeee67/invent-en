import os
import pandas as pd
from datetime import date, datetime
import json

# ================= Files (Absolute Paths for Persistence) ==================
# Render Persistent Disk (/data) 확인, 없으면 현재 디렉토리 사용
if os.path.exists("/data"):
    BASE_DIR = "/data"
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "inventory_data.csv")          # 재고 스냅샷
HISTORY_FILE = os.path.join(BASE_DIR, "stock_history.csv")        # 입출고 로그
ITEM_FILE = os.path.join(BASE_DIR, "food ingredients.txt")        # 원본 (백업용)
INV_DB = os.path.join(BASE_DIR, "inventory_db.csv")             # 재고용 DB
PUR_DB = os.path.join(BASE_DIR, "purchase_db.csv")              # 구매용 DB
VENDOR_FILE = os.path.join(BASE_DIR, "vendor_mapping.csv")      # 구매처 매핑 DB
ORDERS_FILE = os.path.join(BASE_DIR, "orders_db.csv")           # 발주(주문) 내역 DB

BRANCHES = ["동대문","굿모닝시티","양재","수원영통","동탄","영등포","룸비니"]

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
        print(f"Error parsing items in {file_path}: {e}")
        
    return items

def save_item_db(file_path, items):
    """
    아이템 DB 저장 (items: list of dicts)
    """
    try:
        # Convert list of dicts back to DataFrame
        df = pd.DataFrame(items)
        # Ensure column order matches standard if possible, otherwise just save
        if not df.empty:
            # Standardize columns for saving: Category, Item, Unit
            # Map back to standard names if needed, or just save keys as headers
            # keys are 'category', 'item', 'unit'
            df = df[['category', 'item', 'unit']] 
        
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        return True, "Success"
    except Exception as e:
        return False, str(e)

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
            print(f"Error parsing vendors: {e}")
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

# Helper to get purchase logic helpers
def get_vendor_for_item(mapping, category, item):
    """
    Vendor mapping logic from map: (cat, item) -> (cat, "") -> default
    """
    key = (category, item)
    if key in mapping:
        return mapping[key]
    key_broad = (category, "")
    if key_broad in mapping:
        return mapping[key_broad]
    return {"vendor": "Unknown", "phone": ""}

def group_cart_by_vendor(cart_items, vendor_map):
    """
    cart_items: { (cat, item): qty, ... }
    Returns: { vendor_name: { 'phone': str, 'items': [ {item, qty, unit, cat}, ... ] } }
    """
    grouped = {}
    
    for (cat, item_name), qty in cart_items.items():
        if qty <= 0: continue
        
        info = get_vendor_for_item(vendor_map, cat, item_name)
        v_name = info["vendor"]
        v_phone = info["phone"]
        
        if v_name not in grouped:
            grouped[v_name] = {"phone": v_phone, "items": []}
            
        # Unit lookup (could pass DB or just assume known - simplified below, might need unit lookup)
        # In logic.py we can just call helper. For efficiency, maybe load once. 
        # But for valid unit we need db.
        unit = get_unit_for_item(PUR_DB, cat, item_name)
        
        grouped[v_name]["items"].append({
            "cat": cat,
            "item": item_name,
            "qty": qty,
            "unit": unit
        })
    return grouped

def confirm_receipt(order_id, confirmed_items_list):
    """
    Handles the confirmation of an order receipt.
    1. Updates Inventory (CurrentQty += ReceivedQty)
    2. Logs to History
    3. Updates Order Status to 'Completed'
    
    confirmed_items_list: List of dicts [{'cat', 'item', 'qty', 'unit'}, ...] (Modified quantities)
    """
    try:
        inv_df = load_inventory()
        hist_df = load_history()
        orders_df = load_orders()
        
        # Get Order Info for History
        order_row = orders_df[orders_df["OrderId"] == order_id]
        if order_row.empty:
            return False, "Order not found"
        
        o_branch = order_row.iloc[0]["Branch"]
        today_str = str(date.today())
        
        # 1. Update Inventory & History
        for item_data in confirmed_items_list:
            cat = item_data['cat']
            i_name = item_data['item']
            qty = float(item_data['qty'])
            unit = item_data['unit']
            
            if qty > 0:
                # History
                hist_df.loc[len(hist_df)] = [
                    today_str, o_branch, cat, i_name, unit, "IN", qty
                ]
                
                # Inventory
                mask = (inv_df["Branch"] == o_branch) & (inv_df["Item"] == i_name) & (inv_df["Category"] == cat)
                if mask.any():
                    current_qty = float(inv_df.loc[mask, "CurrentQty"].values[0])
                    inv_df.loc[mask, "CurrentQty"] = current_qty + qty
                else:
                    # New Item
                    new_row = pd.DataFrame(
                        [[o_branch, i_name, cat, unit, qty, 0, "", today_str]],
                        columns=["Branch","Item","Category","Unit","CurrentQty","MinQty","Note","Date"]
                    )
                    inv_df = pd.concat([inv_df, new_row], ignore_index=True)
        
        # 2. Update Order
        orders_df.loc[orders_df["OrderId"] == order_id, "Items"] = json.dumps(confirmed_items_list, ensure_ascii=False)
        orders_df.loc[orders_df["OrderId"] == order_id, "Status"] = "Completed"
        
        # 3. Save All
        save_inventory(inv_df)
        save_history(hist_df)
        save_orders(orders_df)
        
        return True, "Inventory Updated Successfully"
        
    except Exception as e:
        return False, str(e)
