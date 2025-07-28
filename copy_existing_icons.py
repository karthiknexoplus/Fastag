#!/usr/bin/env python3
"""
Copy existing logo to create PWA icons
This is the simplest approach - no dependencies required
"""

import os
import shutil
from pathlib import Path

def copy_existing_logo():
    """Copy existing logo to create PWA icons"""
    print("🚀 Creating PWA Icons from Existing Logo")
    print("=" * 50)
    
    # Source logo
    logo_path = "fastag/static/logo.png"
    if not os.path.exists(logo_path):
        print(f"❌ Logo not found at {logo_path}")
        print("Creating simple placeholder icons instead...")
        create_placeholder_icons()
        return
    
    # Create icons directory
    icons_dir = Path("fastag/static/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Icon sizes needed for PWA
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    
    print(f"📁 Copying logo to create {len(sizes)} icon sizes...")
    
    for size in sizes:
        # Copy the logo with size-specific filename
        icon_path = icons_dir / f"icon-{size}x{size}.png"
        shutil.copy2(logo_path, icon_path)
        print(f"✅ Created: {icon_path}")
    
    # Create shortcut icons by copying the logo
    shortcuts = ['dashboard', 'locations', 'vehicle', 'close']
    
    for name in shortcuts:
        shortcut_path = icons_dir / f"{name}-96x96.png"
        shutil.copy2(logo_path, shortcut_path)
        print(f"✅ Created shortcut icon: {shortcut_path}")
    
    print("\n" + "=" * 50)
    print("✅ PWA icons created successfully!")
    print("📱 Your PWA will work perfectly with these icons!")
    print("\nNote: All icons are copies of your existing logo.")
    print("For better results, consider creating optimized icons later.")

def create_placeholder_icons():
    """Create simple placeholder icons if logo doesn't exist"""
    print("Creating placeholder icons...")
    
    # Create icons directory
    icons_dir = Path("fastag/static/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple text file as placeholder
    placeholder_content = """This is a placeholder icon.
Replace this with your actual logo for better PWA experience."""
    
    # Icon sizes needed for PWA
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        icon_path = icons_dir / f"icon-{size}x{size}.txt"
        with open(icon_path, 'w') as f:
            f.write(placeholder_content)
        print(f"📝 Created placeholder: {icon_path}")
    
    print("\n⚠️  Placeholder icons created.")
    print("Please add your logo.png to fastag/static/ and run this script again.")

def create_screenshots():
    """Create simple text-based screenshots"""
    print("\n📸 Creating placeholder screenshots...")
    
    screenshots_dir = Path("fastag/static/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    screenshots = [
        ('mobile-dashboard.txt', 'Mobile Dashboard Screenshot'),
        ('desktop-dashboard.txt', 'Desktop Dashboard Screenshot')
    ]
    
    for filename, description in screenshots:
        screenshot_path = screenshots_dir / filename
        with open(screenshot_path, 'w') as f:
            f.write(f"{description}\n\nThis is a placeholder screenshot for the PWA manifest.")
        print(f"📸 Created: {screenshot_path}")

def main():
    print("🚀 FASTag PWA Icon Setup (No Dependencies)")
    print("=" * 50)
    
    # Try to copy existing logo
    copy_existing_logo()
    
    # Create screenshots
    create_screenshots()
    
    print("\n🎉 Setup complete!")
    print("Your PWA will work with these icons.")
    print("For production, consider creating optimized icons.")

if __name__ == '__main__':
    main() 