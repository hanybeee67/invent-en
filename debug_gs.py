import gspread
from google.oauth2.service_account import Credentials
import os

GOOGLE_KEYS_FILE = "google_keys.json"
SPREADSHEET_NAME = "Everest_Inventory_DB"

def test_connection():
    if not os.path.exists(GOOGLE_KEYS_FILE):
        print(f"ERROR: {GOOGLE_KEYS_FILE} not found.")
        return

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        creds = Credentials.from_service_account_file(GOOGLE_KEYS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        print(f"Authenticated as: {creds.service_account_email}")
        
        print("Listing all accessible spreadsheets:")
        all_sh = client.openall()
        for sh in all_sh:
            print(f" - {sh.title} (ID: {sh.id})")
        
        try:
            sh = client.open(SPREADSHEET_NAME)
            print(f"\nSuccessfully opened: {SPREADSHEET_NAME}")
            print("Tabs found:")
            worksheets = sh.worksheets()
            for ws in worksheets:
                print(f" - {ws.title}")
                # Try to get top 2 rows to see headers
                try:
                    vals = ws.get("A1:C2")
                    print(f"   Sample data: {vals}")
                except Exception as e:
                    print(f"   Error reading tab: {e}")
        except Exception as e:
            print(f"\nERROR opening '{SPREADSHEET_NAME}': {e}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_connection()
