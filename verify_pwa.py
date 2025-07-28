#!/usr/bin/env python3
"""
PWA Verification Script for Raspberry Pi
Checks if all PWA components are properly set up
"""

import os
import json
import requests
from pathlib import Path

def check_manifest():
    """Check if manifest.json exists and is valid"""
    print("🔍 Checking Web App Manifest...")
    
    manifest_path = "fastag/static/manifest.json"
    if not os.path.exists(manifest_path):
        print("❌ Manifest file not found!")
        return False
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        missing_fields = [field for field in required_fields if field not in manifest]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ Manifest is valid")
        print(f"   App Name: {manifest.get('name')}")
        print(f"   Short Name: {manifest.get('short_name')}")
        print(f"   Display Mode: {manifest.get('display')}")
        return True
        
    except json.JSONDecodeError:
        print("❌ Manifest is not valid JSON")
        return False

def check_service_worker():
    """Check if service worker exists"""
    print("\n🔍 Checking Service Worker...")
    
    sw_path = "fastag/static/sw.js"
    if not os.path.exists(sw_path):
        print("❌ Service worker not found!")
        return False
    
    with open(sw_path, 'r') as f:
        content = f.read()
    
    if 'addEventListener' in content and 'install' in content:
        print("✅ Service worker looks valid")
        return True
    else:
        print("❌ Service worker may be incomplete")
        return False

def check_icons():
    """Check if PWA icons exist"""
    print("\n🔍 Checking PWA Icons...")
    
    icons_dir = Path("fastag/static/icons")
    if not icons_dir.exists():
        print("❌ Icons directory not found!")
        return False
    
    required_sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]
    missing_icons = []
    
    for size in required_sizes:
        # Check for both PNG and SVG icons
        png_path = icons_dir / f"icon-{size}x{size}.png"
        svg_path = icons_dir / f"icon-{size}x{size}.svg"
        if not png_path.exists() and not svg_path.exists():
            missing_icons.append(f"{size}x{size}")
    
    if missing_icons:
        print(f"❌ Missing icons: {missing_icons}")
        print("   Run: python3 create_simple_pwa_icons.py")
        return False
    
    print("✅ All required icons found")
    return True

def check_offline_page():
    """Check if offline page exists"""
    print("\n🔍 Checking Offline Page...")
    
    offline_path = "fastag/templates/offline.html"
    if not os.path.exists(offline_path):
        print("❌ Offline page not found!")
        return False
    
    print("✅ Offline page exists")
    return True

def check_health_api():
    """Check if health API route exists"""
    print("\n🔍 Checking Health API...")
    
    health_route_path = "fastag/routes/health.py"
    if not os.path.exists(health_route_path):
        print("❌ Health API route not found!")
        return False
    
    print("✅ Health API route exists")
    return True

def check_https_setup():
    """Check if HTTPS is properly configured"""
    print("\n🔍 Checking HTTPS Setup...")
    
    # Check if Tailscale is mentioned in existing files
    tailscale_files = [
        "tailscale-funnel.service",
        "tailscale-funnel.sh", 
        "TAILSCALE_FUNNEL_README.md"
    ]
    
    found_tailscale = any(os.path.exists(f) for f in tailscale_files)
    
    if found_tailscale:
        print("✅ Tailscale HTTPS setup detected")
        return True
    else:
        print("⚠️  No Tailscale setup detected")
        print("   Make sure you have HTTPS configured")
        return False

def check_flask_integration():
    """Check if PWA components are integrated with Flask"""
    print("\n🔍 Checking Flask Integration...")
    
    # Check if new blueprints are registered
    init_path = "fastag/__init__.py"
    if not os.path.exists(init_path):
        print("❌ Flask app init file not found!")
        return False
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    required_imports = [
        "from fastag.routes.offline import offline_bp",
        "from fastag.routes.health import health_bp"
    ]
    
    missing_imports = [imp for imp in required_imports if imp not in content]
    
    if missing_imports:
        print(f"❌ Missing Flask integrations: {missing_imports}")
        return False
    
    print("✅ Flask integration looks good")
    return True

def check_base_template():
    """Check if PWA meta tags are in base template"""
    print("\n🔍 Checking Base Template...")
    
    base_path = "fastag/templates/base.html"
    if not os.path.exists(base_path):
        print("❌ Base template not found!")
        return False
    
    with open(base_path, 'r') as f:
        content = f.read()
    
    required_elements = [
        'rel="manifest"',
        'apple-mobile-web-app-capable',
        'serviceWorker.register'
    ]
    
    missing_elements = [elem for elem in required_elements if elem not in content]
    
    if missing_elements:
        print(f"❌ Missing PWA elements: {missing_elements}")
        return False
    
    print("✅ Base template has PWA elements")
    return True

def main():
    print("🚀 FASTag PWA Verification")
    print("=" * 40)
    
    checks = [
        check_manifest,
        check_service_worker,
        check_icons,
        check_offline_page,
        check_health_api,
        check_https_setup,
        check_flask_integration,
        check_base_template
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during check: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 VERIFICATION RESULTS")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        print("Your PWA should work perfectly on Android and iOS!")
        print("\nNext steps:")
        print("1. Start your Flask app: python3 wsgi.py")
        print("2. Test on mobile devices")
        print("3. Install the PWA on your phone")
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nIssues found. Please fix them before testing.")
        print("Run the setup commands mentioned in the error messages above.")
    
    return passed == total

if __name__ == '__main__':
    main() 