#!/usr/bin/env python3
"""
Copy customer.png to create all required PWA icons
This ensures the PWA icons match the customer logo exactly.
"""

import os
import shutil
from pathlib import Path

def main():
    # Source logo file - using customer.png
    source_logo = "fastag/static/customer.png"
    
    # Target directory for icons
    icons_dir = "fastag/static/icons"
    
    # Create icons directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    # Required icon sizes for PWA
    icon_sizes = [
        16, 32, 72, 96, 128, 144, 152, 192, 384, 512
    ]
    
    print("Creating PWA icons from customer.png...")
    
    # Copy customer.png to create all required icon sizes
    for size in icon_sizes:
        target_file = f"{icons_dir}/icon-{size}x{size}.png"
        
        # Copy the source logo to the target
        shutil.copy2(source_logo, target_file)
        print(f"Created: icon-{size}x{size}.png")
    
    # Also create shortcut icons
    shortcut_icons = [
        ("dashboard-96x96.png", "Dashboard"),
        ("locations-96x96.png", "Locations"),
        ("vehicle-96x96.png", "Vehicle"),
        ("close-96x96.png", "Close")
    ]
    
    for filename, name in shortcut_icons:
        target_file = f"{icons_dir}/{filename}"
        shutil.copy2(source_logo, target_file)
        print(f"Created: {filename}")
    
    print("\n✅ All PWA icons created successfully!")
    print("📱 Icons now use customer.png logo")
    print(f"📁 Icons saved in: {icons_dir}")

if __name__ == "__main__":
    main() 