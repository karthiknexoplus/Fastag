#!/usr/bin/env python3
"""
Generate PWA icons from existing logo
This script creates various icon sizes required for PWA functionality
"""

import os
from PIL import Image, ImageDraw
import math

def create_icon_sizes():
    """Create PWA icons in various sizes"""
    
    # Icon sizes needed for PWA
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    
    # Source logo path
    logo_path = 'fastag/static/logo.png'
    
    if not os.path.exists(logo_path):
        print(f"Logo not found at {logo_path}")
        return
    
    # Create icons directory
    icons_dir = 'fastag/static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Load the source logo
    try:
        logo = Image.open(logo_path)
        print(f"Loaded logo: {logo.size}")
    except Exception as e:
        print(f"Error loading logo: {e}")
        return
    
    # Create each icon size
    for size in sizes:
        # Resize logo to target size
        resized = logo.resize((size, size), Image.Resampling.LANCZOS)
        
        # Create a new image with the target size and background
        icon = Image.new('RGBA', (size, size), (118, 75, 162, 255))  # Purple background
        icon.paste(resized, (0, 0), resized if resized.mode == 'RGBA' else None)
        
        # Save the icon
        icon_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
        icon.save(icon_path, 'PNG')
        print(f"Created: {icon_path}")
    
    # Create shortcut icons for manifest
    shortcut_icons = {
        'dashboard': '📊',
        'locations': '📍', 
        'vehicle': '🚗',
        'close': '❌'
    }
    
    for name, emoji in shortcut_icons.items():
        # Create a simple icon with emoji
        icon = Image.new('RGBA', (96, 96), (118, 75, 162, 255))
        draw = ImageDraw.Draw(icon)
        
        # Add emoji (simplified - in practice you'd use proper icon fonts)
        # For now, we'll create a colored circle with text
        draw.ellipse([20, 20, 76, 76], fill=(255, 255, 255, 255))
        draw.text((48, 48), emoji, fill=(118, 75, 162, 255), anchor="mm")
        
        icon_path = os.path.join(icons_dir, f'{name}-96x96.png')
        icon.save(icon_path, 'PNG')
        print(f"Created shortcut icon: {icon_path}")

def create_screenshots():
    """Create placeholder screenshots for PWA manifest"""
    
    screenshots_dir = 'fastag/static/screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Create placeholder screenshots
    screenshots = [
        ('mobile-dashboard.png', 390, 844),
        ('desktop-dashboard.png', 1280, 720)
    ]
    
    for filename, width, height in screenshots:
        # Create a placeholder image
        img = Image.new('RGB', (width, height), (244, 246, 251))  # Light background
        
        # Add some placeholder content
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, width-50, height-50], outline=(118, 75, 162, 255), width=3)
        draw.text((width//2, height//2), 'FASTag Dashboard', fill=(118, 75, 162, 255), anchor="mm")
        
        screenshot_path = os.path.join(screenshots_dir, filename)
        img.save(screenshot_path, 'PNG')
        print(f"Created screenshot: {screenshot_path}")

if __name__ == '__main__':
    print("Generating PWA icons...")
    create_icon_sizes()
    print("\nGenerating screenshots...")
    create_screenshots()
    print("\nPWA assets generation complete!") 