from PIL import Image, ImageDraw
import os

# Source path (from user metadata)
source_path = r"C:/Users/hanyb/.gemini/antigravity/brain/4423b3f2-3e85-48e8-b269-47c61ae224fe/uploaded_image_1765529613356.jpg"
# Destination path
dest_path = r"c:/everest inventory/everest invent-en/invent-en/logo_circle.png"

try:
    img = Image.open(source_path).convert("RGBA")
    
    # 1. Square Crop (Center)
    width, height = img.size
    min_dim = min(width, height)
    
    left = int((width - min_dim) / 2)
    top = int((height - min_dim) / 2)
    right = int(left + min_dim)
    bottom = int(top + min_dim)
    
    img = img.crop((left, top, right, bottom))
    
    # 2. Circle Mask
    mask = Image.new("L", (min_dim, min_dim), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, min_dim, min_dim), fill=255)
    
    # 3. Apply Mask
    result = img.copy()
    result.putalpha(mask)
    
    # Resize for web optimization (e.g. 200x200)
    result = result.resize((200, 200), Image.Resampling.LANCZOS)
    
    result.save(dest_path)
    print(f"Successfully saved circular logo to: {dest_path}")
    
except Exception as e:
    print(f"Error processing image: {e}")
