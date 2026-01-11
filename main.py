import flet as ft
from datetime import date
import logic
from drive_utils import upload_file_to_drive
import uuid
import json

def main(page: ft.Page):
    # --- Page Config ---
    page.title = "Everest Inventory"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = ft.ScrollMode.ADAPTIVE
    # Mobile friendly settings
    page.window_width = 400 
    page.window_height = 800

    # --- State Containers ---
    # We use page.session for simple state sharing across tabs if needed
    if not page.session.contains("cart"):
        page.session.set("cart", {}) # {(cat, item): qty}

    # --- UI Components Generators ---

    def create_splash():
        return ft.Container(
            content=ft.Column([
                ft.Text("Everest Inventory", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Professional Stock Management", size=16, color=ft.colors.GREY_400),
                ft.ProgressRing(),
                ft.Text("Loading...", size=12)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )

    # --- Tab 3: Purchase Implementation ---
    class PurchaseTab(ft.UserControl):
        def __init__(self):
            super().__init__()
            self.vendor_map = logic.load_vendor_mapping()
            self.all_items = logic.load_item_db(logic.PUR_DB)
            self.categories = ["All"] + logic.get_all_categories(logic.PUR_DB)
            self.selected_category = "All"
            self.cart = page.session.get("cart")
            self.grid_container = ft.Column()
            self.summary_container = ft.Column()

        def build(self):
            # 1. Header Inputs
            self.date_picker = ft.DatePicker(on_change=self.on_date_change)
            self.date_btn = ft.ElevatedButton(
                f"Date: {date.today()}",
                icon=ft.icons.CALENDAR_TODAY,
                on_click=lambda _: self.date_picker.pick_date(),
            )
            page.overlay.append(self.date_picker)
            
            self.branch_dropdown = ft.Dropdown(
                label="Branch",
                options=[ft.dropdown.Option(b) for b in logic.BRANCHES],
                value=logic.BRANCHES[0]
            )

            # 2. Item Filter
            self.cat_dropdown = ft.Dropdown(
                label="Category",
                options=[ft.dropdown.Option(c) for c in self.categories],
                value="All",
                on_change=self.on_category_change
            )

            # 3. Build UI
            self.render_grid()
            self.render_summary()
            self.status_col = ft.Column()
            self.render_status_section()

            # Initialize FilePicker with upload handler
            self.file_picker = ft.FilePicker(
                on_result=self.on_file_picker_result,
                on_upload=self.on_upload_complete
            )
            page.overlay.append(self.file_picker)
            self.current_upload_oid = None # Track which order is being uploaded

            return ft.Column([
                ft.Row([self.date_btn, self.branch_dropdown], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Text("1. Select Items", size=20, weight=ft.FontWeight.BOLD),
                self.cat_dropdown,
                self.grid_container,
                ft.Divider(),
                ft.Text("2. Purchase Summary", size=20, weight=ft.FontWeight.BOLD),
                self.summary_container,
                ft.Divider(),
                ft.Text("3. Order Status & Receipt", size=20, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("🔄 Refresh Status", on_click=lambda _: self.render_status_section()),
                self.status_col
            ], scroll=ft.ScrollMode.NEVER) # Parent scrolls

        def on_date_change(self, e):
            self.date_btn.text = f"Date: {self.date_picker.value.date()}"
            self.date_btn.update()

        def on_category_change(self, e):
            self.selected_category = self.cat_dropdown.value
            self.render_grid()
            self.grid_container.update()

        def render_grid(self):
            self.grid_container.controls.clear()
            
            filtered = self.all_items
            if self.selected_category != "All":
                filtered = [i for i in self.all_items if i["category"] == self.selected_category]

            for item in filtered:
                ikey = (item["category"], item["item"])
                qty_val = self.cart.get(ikey, 0.0)
                
                # Unit Text
                t_title = ft.Text(f"{item['item']} ({item['unit']})", size=16, expand=True)
                
                # Qty Input (TextField)
                t_qty = ft.TextField(
                    value=str(qty_val) if qty_val > 0 else "",
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=80,
                    text_align=ft.TextAlign.RIGHT,
                    hint_text="0",
                    on_change=lambda e, k=ikey: self.update_cart(k, e.control.value)
                )

                row = ft.Row([t_title, t_qty], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                self.grid_container.controls.append(row)
        
        def update_cart(self, key, value):
            try:
                val = float(value)
                if val > 0:
                    self.cart[key] = val
                else:
                    if key in self.cart: del self.cart[key]
            except ValueError:
                if key in self.cart: del self.cart[key] # Handle empty string
            
            page.session.set("cart", self.cart)
            self.render_summary()
            self.summary_container.update()

        def render_summary(self):
            self.summary_container.controls.clear()
            grouped = logic.group_cart_by_vendor(self.cart, self.vendor_map)
            
            if not grouped:
                self.summary_container.controls.append(ft.Text("No items selected."))
                return

            for v_name, v_data in grouped.items():
                # Card for each vendor
                items_str = "\n".join([f"- {i['item']} ({i['qty']}{i['unit']})" for i in v_data['items']])
                
                # SMS logic
                # For Flet we can use page.launch_url("sms:...")
                # Note: SMS body encoding logic is same as before
                sms_body = f"[Everest 구매요청]\n지점: {self.branch_dropdown.value}\n날짜: {self.date_btn.text}\n\n{items_str}"
                import urllib.parse
                encoded = urllib.parse.quote(sms_body)
                sms_link = f"sms:{v_data['phone']}?body={encoded}"

                def on_save_click(e, vn=v_name, vd=v_data, sl=sms_link):
                    # Save DB
                    orders_df = logic.load_orders()
                    new_order = {
                        "OrderId": str(uuid.uuid4()),
                        "Date": str(self.date_btn.text.replace("Date: ", "")), 
                        "Branch": self.branch_dropdown.value,
                        "Vendor": vn,
                        "Items": json.dumps(vd["items"], ensure_ascii=False),
                        "Status": "Pending",
                        "CreatedDate": str(datetime.now())
                    }
                    orders_df = pd.concat([orders_df, pd.DataFrame([new_order])], ignore_index=True)
                    logic.save_orders(orders_df)
                    
                    page.snack_bar = ft.SnackBar(ft.Text(f"Saved order for {vn}! Opening SMS..."))
                    page.snack_bar.open = True
                    page.update()
                    page.launch_url(sl)
                    
                    # Refresh Status Section to show new pending order
                    self.render_status_section()
                
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.Text(f"🏢 {v_name}", weight=ft.FontWeight.BOLD, size=18),
                            ft.Text(items_str, size=14),
                            ft.ElevatedButton("📲 Save & Send SMS", on_click=on_save_click)
                        ])
                    )
                )
                self.summary_container.controls.append(card)

        # --- Order Status Section ---
        def render_status_section(self):
            self.status_col.controls.clear()
            orders_df = logic.load_orders()
            if orders_df.empty:
                self.status_col.controls.append(ft.Text("No orders found."))
                self.status_col.update()
                return

            # Filter Pending (or recently completed if we want to show history brief)
            # For this MVP, let's show Pending + Completed sorted by date
            orders_df = orders_df.sort_values("CreatedDate", ascending=False)
            
            for index, row in orders_df.iterrows():
                if row["Status"] not in ["Pending", "Completed"]: continue
                
                oid = row["OrderId"]
                status = row["Status"]
                items = json.loads(row["Items"])
                
                # Create a card for this order
                
                # --- Editable Items Logic ---
                # We need to store edits. 
                # Flet is stateful, so we can just create Controls and read their values when button clicked!
                
                item_controls = []
                for i_data in items:
                    # Each item row: Name | Qty Input | Unit
                    tf_qty = ft.TextField(
                        value=str(i_data['qty']), 
                        width=70, 
                        keyboard_type=ft.KeyboardType.NUMBER,
                        text_align=ft.TextAlign.RIGHT,
                        data=i_data # Store original data in control
                    )
                    row_ui = ft.Row([
                        ft.Text(f"{i_data['item']}", expand=True),
                        tf_qty,
                        ft.Text(f"{i_data['unit']}")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    item_controls.append(row_ui)
                
                # --- Confirm Button Logic ---
                def on_confirm_click(e, passed_oid=oid, passed_controls=item_controls):
                    # Reads values from textfields
                    confirmed_list = []
                    for c_row in passed_controls:
                        # c_row is Row. controls[1] is TextField
                        tf = c_row.controls[1]
                        orig_data = tf.data
                        new_qty = float(tf.value or 0)
                        
                        item_copy = orig_data.copy()
                        item_copy['qty'] = new_qty
                        confirmed_list.append(item_copy)
                    
                    success, msg = logic.confirm_receipt(passed_oid, confirmed_list)
                    if success:
                        page.snack_bar = ft.SnackBar(ft.Text("✅ Receipt Confirmed & Inventory Updated!"))
                        page.snack_bar.open = True
                        page.update()
                        self.render_status_section() # Refresh UI
                    else:
                        page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error: {msg}"))
                        page.snack_bar.open = True
                        page.update()

                # --- Photo Upload Logic ---
                def on_upload_click(e, passed_oid=oid):
                    self.current_upload_oid = passed_oid
                    # Trigger File Picker (Photos)
                    self.file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

                # Card Content
                status_color = ft.colors.GREEN if status == "Completed" else ft.colors.ORANGE
                content_col = [
                    ft.Text(f"{row['Date']} | {row['Vendor']}", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(status, color=ft.colors.WHITE, size=12),
                        bgcolor=status_color, padding=5, border_radius=5
                    ),
                    ft.Divider(),
                    ft.Text("Items (Edit Qty for Receipt):"),
                    ft.Column(item_controls),
                    ft.Divider()
                ]
                
                if status == "Pending":
                    content_col.append(
                        ft.ElevatedButton("📥 Confirm Receipt", on_click=on_confirm_click)
                    )
                else:
                    content_col.append(ft.Text("✅ Confirmed", color=ft.colors.GREEN))
                
                # Upload Button (Always Visible or just below)
                content_col.append(
                    ft.ElevatedButton("📸 Upload Receipt Photo", 
                                      icon=ft.icons.CAMERA_ALT, 
                                      on_click=on_upload_click)
                )

                card = ft.Card(
                    content=ft.Container(
                        padding=15,
                        content=ft.Column(content_col)
                    )
                )
                self.status_col.controls.append(card)
            
            self.status_col.update()

        def on_file_picker_result(self, e: ft.FilePickerResultEvent):
            if not e.files or not self.current_upload_oid:
                return
            
                # We catch the file from the upload directory.
                
                fname = e.file_name
                # If running locally, page.get_upload_url maps to a local temp file? 
                # Actually Flet's default native uploader saves to a temp dir.
                
                # To keep it simple and robust for THIS user who runs locally or remotely:
                # We will just implement the drive upload here if we can find the file.
                
                # Flet 0.21+ upload stores in temp folder.
                # Let's try to locate it. Or, since we are rushing, let's use a simpler hack for Local Desktop fallback.
                pass

    # --- Refined Upload Logic ---
    # We need to attach on_upload callback to file_picker in build()
    
    # ... In build():
    # self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result, on_upload=self.on_upload_complete)
    
    # ... New Method:
        def on_upload_complete(self, e: ft.FilePickerUploadEvent):
             # This event triggers when client finishes sending file to Flet Server.
             # BUT Flet Server default handler doesn't automatically save files to disk unless we handle it?
             # Actually, for standard `flet run`, it might not.
             
             # CORRECT APPROACH:
             # If f.path exists (Desktop), use it.
             # If NOT, we are on Web. Flet Web uploads need a backend handler.
             # Since we are using `flet run` (internal server), we can Configure `page.upload_dir`.
             pass


    # --- App Layout ---
    
    t = ft.Tabs(
        selected_index=2, # Start at Tab 3 for demo
        animation_duration=300,
        tabs=[
            ft.Tab(text="Edit", icon=ft.icons.EDIT),
            ft.Tab(text="View", icon=ft.icons.LIST),
            ft.Tab(text="Purchase", icon=ft.icons.SHOPPING_CART, content=PurchaseTab()),
            ft.Tab(text="Logs", icon=ft.icons.HISTORY),
        ],
        expand=True,
    )

    page.add(t)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
