#!/usr/bin/env python3

"""
Debug script for Fastag application
Run this to test the application and identify issues
"""

import os
import sys
import traceback
from fastag import create_app

def test_app():
    """Test the application creation and basic functionality"""
    print("🔍 Testing Fastag Application...")
    print("=" * 50)
    
    try:
        # Test app creation
        print("1. Creating application...")
        app = create_app()
        print("✅ Application created successfully")
        
        # Test database connection
        print("\n2. Testing database connection...")
        with app.app_context():
            from fastag.utils.db import get_db
            db = get_db()
            print("✅ Database connection successful")
            
            # Test basic query
            try:
                locations = db.execute('SELECT * FROM locations').fetchall()
                print(f"✅ Database query successful - Found {len(locations)} locations")
            except Exception as e:
                print(f"❌ Database query failed: {e}")
                return False
        
        # Test template rendering
        print("\n3. Testing template rendering...")
        with app.app_context():
            from flask import render_template
            try:
                # Test locations template
                locations = db.execute('SELECT * FROM locations').fetchall()
                rendered = render_template('locations.html', locations=locations)
                print("✅ Locations template renders successfully")
            except Exception as e:
                print(f"❌ Template rendering failed: {e}")
                print(f"Error details: {traceback.format_exc()}")
                return False
        
        # Test static files
        print("\n4. Testing static files...")
        static_dir = os.path.join(os.path.dirname(__file__), 'fastag', 'static')
        if os.path.exists(static_dir):
            print(f"✅ Static directory exists: {static_dir}")
            files = os.listdir(static_dir)
            print(f"   Found files: {files}")
        else:
            print(f"❌ Static directory not found: {static_dir}")
        
        # Test configuration
        print("\n5. Testing configuration...")
        print(f"   SECRET_KEY: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        print(f"   DATABASE: {app.config.get('DATABASE', 'Not set')}")
        print(f"   LOG_DIR: {app.config.get('LOG_DIR', 'Not set')}")
        
        print("\n✅ All tests passed! Application should work correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Application test failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False

def test_login_flow():
    """Test the login flow specifically"""
    print("\n🔐 Testing Login Flow...")
    print("=" * 30)
    
    try:
        app = create_app()
        with app.test_client() as client:
            # Test login page
            print("1. Testing login page...")
            response = client.get('/login')
            if response.status_code == 200:
                print("✅ Login page loads successfully")
            else:
                print(f"❌ Login page failed: {response.status_code}")
                return False
            
            # Test login with admin credentials
            print("2. Testing login with admin credentials...")
            response = client.post('/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Login successful")
                # Check if redirected to locations page
                if '/locations' in response.request.url:
                    print("✅ Redirected to locations page")
                else:
                    print(f"⚠️ Redirected to: {response.request.url}")
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
            
            print("✅ Login flow test passed!")
            return True
            
    except Exception as e:
        print(f"❌ Login flow test failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    print("🚀 Fastag Application Debug Tool")
    print("=" * 40)
    
    # Test basic app functionality
    if test_app():
        # Test login flow
        test_login_flow()
    else:
        print("\n❌ Basic app test failed. Please fix the issues above.")
        sys.exit(1) 