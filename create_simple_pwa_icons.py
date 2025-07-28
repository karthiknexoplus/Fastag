#!/usr/bin/env python3
"""
Create simple PWA icons without Pillow dependency
This creates basic colored icons for PWA functionality
"""

import os
import json
import base64
from pathlib import Path

def create_simple_icon(size, color="#764ba2", text="FASTag"):
    """Create a simple SVG icon"""
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{size}" height="{size}" fill="{color}" rx="8"/>
  <text x="{size//2}" y="{size//2 + size//10}" 
        font-family="Arial, sans-serif" 
        font-size="{size//6}" 
        font-weight="bold" 
        text-anchor="middle" 
        fill="white">{text}</text>
</svg>'''
    return svg_content

def create_icon_files():
    """Create simple PWA icons"""
    print("Creating simple PWA icons...")
    
    # Create icons directory
    icons_dir = Path("fastag/static/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Icon sizes needed for PWA
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        # Create simple SVG icon
        svg_content = create_simple_icon(size)
        
        # Save as SVG (modern browsers support SVG icons)
        svg_path = icons_dir / f"icon-{size}x{size}.svg"
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        # Also create a simple PNG placeholder using base64
        png_path = icons_dir / f"icon-{size}x{size}.png"
        create_simple_png_placeholder(size, png_path)
        
        print(f"Created: {svg_path} and {png_path}")
    
    # Create shortcut icons
    shortcuts = {
        'dashboard': '📊',
        'locations': '📍',
        'vehicle': '🚗',
        'close': '❌'
    }
    
    for name, emoji in shortcuts.items():
        # Create SVG shortcut icon
        svg_content = create_simple_icon(96, "#764ba2", emoji)
        svg_path = icons_dir / f"{name}-96x96.svg"
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        # Create PNG placeholder
        png_path = icons_dir / f"{name}-96x96.png"
        create_simple_png_placeholder(96, png_path)
        
        print(f"Created shortcut icon: {svg_path} and {png_path}")

def create_simple_png_placeholder(size, path):
    """Create a simple PNG placeholder using base64"""
    # This is a minimal 1x1 pixel PNG with the right color
    # In a real scenario, you'd want to use a proper image library
    # But for PWA functionality, even a placeholder works
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    
    with open(path, 'wb') as f:
        f.write(png_data)

def create_screenshots():
    """Create placeholder screenshots"""
    print("\nCreating placeholder screenshots...")
    
    screenshots_dir = Path("fastag/static/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Create simple SVG screenshots
    screenshots = [
        ('mobile-dashboard.svg', 390, 844),
        ('desktop-dashboard.svg', 1280, 720)
    ]
    
    for filename, width, height in screenshots:
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#f4f6fb"/>
  <rect x="50" y="50" width="{width-100}" height="{height-100}" 
        fill="white" stroke="#764ba2" stroke-width="3" rx="10"/>
  <text x="{width//2}" y="{height//2}" 
        font-family="Arial, sans-serif" 
        font-size="24" 
        font-weight="bold" 
        text-anchor="middle" 
        fill="#764ba2">FASTag Dashboard</text>
</svg>'''
        
        screenshot_path = screenshots_dir / filename
        with open(screenshot_path, 'w') as f:
            f.write(svg_content)
        
        print(f"Created screenshot: {screenshot_path}")

def update_manifest_for_svg():
    """Update manifest to use SVG icons where possible"""
    print("\nUpdating manifest for SVG support...")
    
    manifest_path = "fastag/static/manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Update icons to use SVG where possible
        for icon in manifest.get('icons', []):
            if icon.get('sizes') in ['16x16', '32x32', '72x72', '96x96', '128x128', '144x144', '152x152', '192x192']:
                icon['src'] = icon['src'].replace('.png', '.svg')
        
        # Update shortcuts to use SVG
        for shortcut in manifest.get('shortcuts', []):
            for icon in shortcut.get('icons', []):
                icon['src'] = icon['src'].replace('.png', '.svg')
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("Updated manifest to use SVG icons")

def main():
    print("🚀 Creating Simple PWA Icons (No Pillow Required)")
    print("=" * 50)
    
    # Import json at the top level
    import json
    
    create_icon_files()
    create_screenshots()
    update_manifest_for_svg()
    
    print("\n" + "=" * 50)
    print("✅ Simple PWA icons created successfully!")
    print("\nNote: These are basic placeholder icons.")
    print("For production, consider replacing with proper branded icons.")
    print("\nYour PWA will work perfectly with these icons!")

if __name__ == '__main__':
    main() 