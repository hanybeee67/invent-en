"""
Configuration module for Everest Inventory System
Centralizes all constants, settings, and configurations
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== Application Settings ====================
APP_NAME = "Everest Inventory Management System"
APP_VERSION = "2.0.0"
APP_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ==================== Branch Configuration ====================
BRANCHES = [
    "동대문",
    "굿모닝시티",
    "양재",
    "수원영통",
    "동탄",
    "영등포",
    "룸비니"
]

# ==================== Storage Configuration ====================
# Check for Render Persistent Disk or use local data folder
if os.path.exists("/data"):
    BASE_DIR = "/data"
    STORAGE_MODE = "Persistent 🟢"
    STORAGE_MESSAGE = "Data is saved to Persistent Disk (/data)."
else:
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    STORAGE_MODE = "Temporary ⚠️"
    STORAGE_MESSAGE = "Data is saved locally (Temporary). Data may be lost on restart if on cloud."

# Ensure data directory exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)

# ==================== File Paths ====================
# Main data files
DATA_FILE = os.path.join(BASE_DIR, "inventory_data.csv")          # Current inventory snapshot
HISTORY_FILE = os.path.join(BASE_DIR, "stock_history.csv")        # IN/OUT transaction log
ORDERS_FILE = os.path.join(BASE_DIR, "orders_db.csv")             # Purchase orders

# Database files
INV_DB = os.path.join(BASE_DIR, "inventory_db.csv")               # Inventory items master
PUR_DB = os.path.join(BASE_DIR, "purchase_db.csv")                # Purchase items master
VENDOR_FILE = os.path.join(BASE_DIR, "vendor_mapping.csv")        # Vendor contact info

# Legacy/backup files
ITEM_FILE = os.path.join(BASE_DIR, "food ingredients.txt")        # Original format backup

# ==================== Security Settings ====================
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "1800"))       # 30 minutes default
PASSWORD_SALT = os.getenv("PASSWORD_SALT", "everest_inventory_salt_2026")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD", None)            # None = use fallback

# ==================== Backup Settings ====================
ENABLE_AUTO_BACKUP = os.getenv("ENABLE_AUTO_BACKUP", "true").lower() == "true"
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

# ==================== Google Drive Settings ====================
GOOGLE_KEY_JSON = os.getenv("GOOGLE_KEY_JSON", None)
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "1go58wzFXi172SRRXJ0TGa71WKfyrwOi2")

# ==================== UI Settings ====================
# Mobile detection threshold
MOBILE_BREAKPOINT = 768  # pixels

# Tab names (responsive)
TAB_NAMES_DESKTOP = [
    "✏ Register / Edit",
    "📊 View / Print",
    "🛒 Purchase",
    "📦 IN / OUT Log",
    "📈 Usage Analysis",
    "📄 Monthly Report",
    "💾 Data Management",
    "❓ Help Manual",
    "🍽 Sales"
]

TAB_NAMES_MOBILE = ["✏️", "📊", "🛒", "📦", "📈", "📄", "💾", "❓", "🍽"]

# ==================== Data Schema ====================
INVENTORY_COLUMNS = ["Branch", "Item", "Category", "Unit", "CurrentQty", "MinQty", "Note", "Date"]
HISTORY_COLUMNS = ["Date", "Branch", "Category", "Item", "Unit", "Type", "Qty"]
ORDERS_COLUMNS = ["OrderId", "Date", "Branch", "Vendor", "Items", "Status", "CreatedDate"]

# ==================== Feature Flags ====================
ENABLE_MOBILE_MODE = os.getenv("ENABLE_MOBILE_MODE", "true").lower() == "true"
ENABLE_SESSION_TIMEOUT = MANAGER_PASSWORD is not None  # Only if .env configured

# ==================== Helper Functions ====================
def get_all_file_paths():
    """Return list of all critical data files for backup"""
    return [
        DATA_FILE,
        HISTORY_FILE,
        ORDERS_FILE,
        INV_DB,
        PUR_DB,
        VENDOR_FILE
    ]

def get_config_summary():
    """Return configuration summary for debugging"""
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENVIRONMENT,
        "storage": {
            "base_dir": BASE_DIR,
            "mode": STORAGE_MODE,
            "exists": os.path.exists(BASE_DIR)
        },
        "features": {
            "mobile_mode": ENABLE_MOBILE_MODE,
            "session_timeout": ENABLE_SESSION_TIMEOUT,
            "auto_backup": ENABLE_AUTO_BACKUP
        },
        "branches": len(BRANCHES)
    }

# For testing
if __name__ == "__main__":
    import json
    summary = get_config_summary()
    print("Configuration Summary:")
    print(json.dumps(summary, indent=2))
    print(f"\nFile paths exist:")
    for path in get_all_file_paths():
        print(f"  {os.path.basename(path)}: {os.path.exists(path)}")
