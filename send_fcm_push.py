#!/usr/bin/env python3
"""
Send 100 different test push notifications to all FCM tokens saved in fcm_tokens.json
"""
import json
import requests
import random
from datetime import datetime

# TODO: Fill in your FCM server key here
FCM_SERVER_KEY = "YOUR_FCM_SERVER_KEY_HERE"

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"

# 100 different marketing messages for entrance automation company
MARKETING_MESSAGES = [
    {
        "title": "🚪 Smart Gate Solutions",
        "body": "Transform your entrance with our cutting-edge automated gate systems!"
    },
    {
        "title": "🔒 Security Upgrade Alert",
        "body": "Upgrade your security with our advanced access control systems!"
    },
    {
        "title": "📹 CCTV Installation Special",
        "body": "Get 20% off on professional CCTV surveillance installation this month!"
    },
    {
        "title": "⚡ Quick Access Solutions",
        "body": "Say goodbye to manual gates! Experience seamless automated entry."
    },
    {
        "title": "🏠 Apartment Security",
        "body": "Secure your apartment complex with our boom barrier access control!"
    },
    {
        "title": "🎯 Smart Home Integration",
        "body": "Control your gates from anywhere with our smart home automation!"
    },
    {
        "title": "💰 Limited Time Offer",
        "body": "Free consultation + 15% discount on all gate automation packages!"
    },
    {
        "title": "🔔 Maintenance Reminder",
        "body": "Your gate system is due for maintenance. Book your service now!"
    },
    {
        "title": "🚀 New Technology Alert",
        "body": "Experience the future with our AI-powered access control systems!"
    },
    {
        "title": "📱 Mobile App Update",
        "body": "New features added! Control your gates with voice commands now!"
    },
    {
        "title": "🎉 Welcome Bonus",
        "body": "New customer? Get free installation worth ₹5,000 on any automation package!"
    },
    {
        "title": "🚨 Emergency Support",
        "body": "24/7 technical support available for all our automation systems!"
    },
    {
        "title": "💳 Payment Plans Available",
        "body": "0% EMI available on all gate automation and CCTV packages!"
    },
    {
        "title": "🏆 Customer Satisfaction",
        "body": "Join 10,000+ satisfied customers with our automation solutions!"
    },
    {
        "title": "📊 Security Analytics",
        "body": "Track your property's security with our advanced analytics dashboard!"
    },
    {
        "title": "🎁 Referral Rewards",
        "body": "Refer friends and earn ₹2,000 for each successful installation!"
    },
    {
        "title": "🔋 Battery Backup Alert",
        "body": "Ensure uninterrupted security with our backup power solutions!"
    },
    {
        "title": "🚀 Express Installation",
        "body": "Get your automation system installed within 24 hours!"
    },
    {
        "title": "📈 ROI Calculator",
        "body": "See how much you can save with automated security systems!"
    },
    {
        "title": "🎯 Personalized Quote",
        "body": "Get a customized quote for your specific automation needs!"
    },
    {
        "title": "🔔 Service Update",
        "body": "New remote monitoring features added to all our systems!"
    },
    {
        "title": "💰 Cashback Alert",
        "body": "10% cashback credited for your recent automation purchase!"
    },
    {
        "title": "🚗 Vehicle Access Control",
        "body": "Automate your parking with our smart vehicle detection systems!"
    },
    {
        "title": "📱 Smart Features",
        "body": "Control your gates with fingerprint, card, or mobile app!"
    },
    {
        "title": "🎊 Festival Special",
        "body": "Diwali special: Zero installation charges on all automation packages!"
    },
    {
        "title": "🔒 Security Alert",
        "body": "New anti-tampering features added to protect your automation systems!"
    },
    {
        "title": "📋 Free Assessment",
        "body": "Get a free security assessment for your property today!"
    },
    {
        "title": "🌟 Premium Support",
        "body": "Upgrade to Premium for 24/7 priority support and maintenance!"
    },
    {
        "title": "🎯 Smart Recommendations",
        "body": "Based on your property, we recommend our sliding gate automation!"
    },
    {
        "title": "🚪 Swing Gate Solutions",
        "body": "Perfect for residential properties! Automated swing gates with safety sensors."
    },
    {
        "title": "🔄 Folding Gate Automation",
        "body": "Space-saving folding gates with smooth automation for commercial use!"
    },
    {
        "title": "📹 HD CCTV Systems",
        "body": "Crystal clear 4K surveillance with night vision and motion detection!"
    },
    {
        "title": "🏢 Commercial Solutions",
        "body": "Secure your business with our commercial-grade automation systems!"
    },
    {
        "title": "🏠 Residential Packages",
        "body": "Complete home security with automated gates and CCTV surveillance!"
    },
    {
        "title": "⚡ Quick Response",
        "body": "Our team responds within 2 hours for all emergency service calls!"
    },
    {
        "title": "🎯 Energy Efficient",
        "body": "Save up to 40% on energy costs with our smart automation systems!"
    },
    {
        "title": "🔔 Smart Alerts",
        "body": "Get instant notifications when someone enters your property!"
    },
    {
        "title": "💰 Cost Effective",
        "body": "Reduce security costs by 60% with automated systems!"
    },
    {
        "title": "🚗 Parking Automation",
        "body": "Automate your parking with our smart barrier and access control!"
    },
    {
        "title": "📱 Remote Control",
        "body": "Control your gates from anywhere in the world with our mobile app!"
    },
    {
        "title": "🎊 Anniversary Special",
        "body": "Celebrating 10 years! Get 25% off on all automation packages!"
    },
    {
        "title": "🔒 Advanced Security",
        "body": "Multi-layer security with biometric access and CCTV monitoring!"
    },
    {
        "title": "📋 Free Demo",
        "body": "Experience our automation systems with a free demonstration!"
    },
    {
        "title": "🌟 VIP Support",
        "body": "Exclusive VIP support for premium customers with dedicated hotline!"
    },
    {
        "title": "🎯 Custom Solutions",
        "body": "Tailored automation solutions for your specific requirements!"
    },
    {
        "title": "🚪 Sliding Gate Magic",
        "body": "Smooth sliding gates with silent operation and safety features!"
    },
    {
        "title": "🔄 Bi-fold Excellence",
        "body": "Space-efficient bi-fold gates perfect for limited driveway space!"
    },
    {
        "title": "📹 PTZ Camera Systems",
        "body": "Pan-tilt-zoom cameras with 360° coverage for complete surveillance!"
    },
    {
        "title": "🏢 Industrial Grade",
        "body": "Heavy-duty automation systems for industrial and commercial use!"
    },
    {
        "title": "🏠 Smart Homes",
        "body": "Integrate your gates with Alexa and Google Home for voice control!"
    },
    {
        "title": "⚡ Lightning Fast",
        "body": "Gates that respond in milliseconds for ultimate convenience!"
    },
    {
        "title": "🎯 Weather Resistant",
        "body": "All our systems are weather-proof and built to last!"
    },
    {
        "title": "🔔 24/7 Monitoring",
        "body": "Round-the-clock monitoring with instant alert systems!"
    },
    {
        "title": "💰 Investment Protection",
        "body": "Protect your property investment with advanced security automation!"
    },
    {
        "title": "🚗 RFID Access",
        "body": "Quick vehicle access with RFID tags and automatic recognition!"
    },
    {
        "title": "📱 App Integration",
        "body": "Seamless integration with your existing smart home ecosystem!"
    },
    {
        "title": "🎊 New Year Special",
        "body": "Start 2024 secure! 30% off on all automation installations!"
    },
    {
        "title": "🔒 Military Grade",
        "body": "Military-grade security systems for maximum protection!"
    },
    {
        "title": "📋 Free Quote",
        "body": "Get a detailed quote for your automation needs within 24 hours!"
    },
    {
        "title": "🌟 Platinum Service",
        "body": "Platinum service with dedicated account manager and priority support!"
    },
    {
        "title": "🎯 Expert Consultation",
        "body": "Free consultation with our automation experts to find the perfect solution!"
    },
    {
        "title": "🚪 Automatic Gates",
        "body": "Experience the luxury of automatic gates with safety sensors!"
    },
    {
        "title": "🔄 Folding Excellence",
        "body": "Premium folding gates with smooth automation and elegant design!"
    },
    {
        "title": "📹 Night Vision CCTV",
        "body": "Crystal clear surveillance even in complete darkness!"
    },
    {
        "title": "🏢 Corporate Security",
        "body": "Enterprise-grade security solutions for corporate environments!"
    },
    {
        "title": "🏠 Home Automation",
        "body": "Complete home automation with gates, CCTV, and smart controls!"
    },
    {
        "title": "⚡ Instant Response",
        "body": "Gates that respond instantly to your commands!"
    },
    {
        "title": "🎯 Energy Smart",
        "body": "Solar-powered automation systems for eco-friendly security!"
    },
    {
        "title": "🔔 Smart Notifications",
        "body": "Get notified instantly when gates are accessed!"
    },
    {
        "title": "💰 Money Saving",
        "body": "Save on security personnel costs with automated systems!"
    },
    {
        "title": "🚗 Vehicle Recognition",
        "body": "Automatic vehicle recognition for seamless access!"
    },
    {
        "title": "📱 Cloud Control",
        "body": "Control your gates from the cloud with our advanced app!"
    },
    {
        "title": "🎊 Holiday Special",
        "body": "Holiday special: Free maintenance for 1 year on all packages!"
    },
    {
        "title": "🔒 Bulletproof Security",
        "body": "Bulletproof security systems for maximum protection!"
    },
    {
        "title": "📋 Site Survey",
        "body": "Free site survey to assess your automation requirements!"
    },
    {
        "title": "🌟 Gold Support",
        "body": "Gold support package with 4-hour response time guarantee!"
    },
    {
        "title": "🎯 Perfect Fit",
        "body": "Custom automation solutions that fit your exact needs!"
    },
    {
        "title": "🚪 Silent Operation",
        "body": "Whisper-quiet gate automation for peaceful environments!"
    },
    {
        "title": "🔄 Space Saver",
        "body": "Space-saving folding gates perfect for narrow driveways!"
    },
    {
        "title": "📹 HD Surveillance",
        "body": "High-definition surveillance with advanced recording features!"
    },
    {
        "title": "🏢 Business Security",
        "body": "Secure your business with professional automation systems!"
    },
    {
        "title": "🏠 Family Safety",
        "body": "Keep your family safe with automated security systems!"
    },
    {
        "title": "⚡ Power Backup",
        "body": "Uninterrupted security with automatic power backup systems!"
    },
    {
        "title": "🎯 Climate Control",
        "body": "All systems designed to work in extreme weather conditions!"
    },
    {
        "title": "🔔 Real-time Alerts",
        "body": "Real-time security alerts sent directly to your phone!"
    },
    {
        "title": "💰 Value for Money",
        "body": "Premium automation systems at competitive prices!"
    },
    {
        "title": "🚗 Automatic Parking",
        "body": "Automated parking solutions with barrier control!"
    },
    {
        "title": "📱 Smart Integration",
        "body": "Integrate with your existing smart home devices!"
    },
    {
        "title": "🎊 Season Sale",
        "body": "Season sale: Up to 40% off on all automation packages!"
    },
    {
        "title": "🔒 Maximum Security",
        "body": "Maximum security with multi-layer protection systems!"
    },
    {
        "title": "📋 Expert Advice",
        "body": "Free expert advice on choosing the right automation system!"
    },
    {
        "title": "🌟 Elite Service",
        "body": "Elite service with dedicated support team and fast response!"
    },
    {
        "title": "🎯 Tailored Solutions",
        "body": "Tailored automation solutions for your unique requirements!"
    },
    {
        "title": "🚪 Luxury Gates",
        "body": "Luxury automatic gates with premium finishes and features!"
    },
    {
        "title": "🔄 Compact Design",
        "body": "Compact folding gates for space-constrained properties!"
    },
    {
        "title": "📹 Advanced CCTV",
        "body": "Advanced CCTV systems with AI-powered motion detection!"
    },
    {
        "title": "🏢 Industrial Security",
        "body": "Heavy-duty security solutions for industrial facilities!"
    },
    {
        "title": "🏠 Residential Security",
        "body": "Complete residential security with automated systems!"
    },
    {
        "title": "⚡ High Speed",
        "body": "High-speed gate automation for busy environments!"
    },
    {
        "title": "🎯 Durability",
        "body": "Built to last with premium materials and engineering!"
    },
    {
        "title": "🔔 Instant Updates",
        "body": "Instant updates on all security events and activities!"
    },
    {
        "title": "💰 Cost Efficient",
        "body": "Cost-efficient automation that pays for itself!"
    },
    {
        "title": "🚗 Smart Parking",
        "body": "Smart parking solutions with automated access control!"
    },
    {
        "title": "📱 Easy Control",
        "body": "Easy-to-use mobile app for controlling all your systems!"
    },
    {
        "title": "🎊 Special Offer",
        "body": "Special offer: Free upgrade to premium features!"
    },
    {
        "title": "🔒 Ultimate Protection",
        "body": "Ultimate protection with state-of-the-art security systems!"
    },
    {
        "title": "📋 Free Assessment",
        "body": "Free security assessment for your property!"
    },
    {
        "title": "🌟 Premium Care",
        "body": "Premium care with extended warranty and support!"
    },
    {
        "title": "🎯 Expert Installation",
        "body": "Expert installation by certified technicians!"
    },
    {
        "title": "🚪 Automatic Entry",
        "body": "Automatic entry systems for ultimate convenience!"
    },
    {
        "title": "🔄 Smart Folding",
        "body": "Smart folding gates with intelligent automation!"
    },
    {
        "title": "📹 Crystal Clear",
        "body": "Crystal clear surveillance with advanced camera systems!"
    },
    {
        "title": "🏢 Corporate Grade",
        "body": "Corporate-grade security for professional environments!"
    },
    {
        "title": "🏠 Home Protection",
        "body": "Complete home protection with automated security!"
    },
    {
        "title": "⚡ Quick Access",
        "body": "Quick access with fast-response automation systems!"
    },
    {
        "title": "🎯 All Weather",
        "body": "All-weather automation systems for any climate!"
    },
    {
        "title": "🔔 Smart Monitoring",
        "body": "Smart monitoring with intelligent alert systems!"
    },
    {
        "title": "💰 Investment Value",
        "body": "Increase your property value with security automation!"
    },
    {
        "title": "🚗 Vehicle Security",
        "body": "Vehicle security with automated access control!"
    },
    {
        "title": "📱 Remote Access",
        "body": "Remote access to all your security systems!"
    },
    {
        "title": "🎊 Limited Time",
        "body": "Limited time offer: Free consultation and assessment!"
    },
    {
        "title": "🔒 Fortress Security",
        "body": "Fortress-level security for maximum protection!"
    },
    {
        "title": "📋 Professional Survey",
        "body": "Professional security survey for your property!"
    },
    {
        "title": "🌟 VIP Treatment",
        "body": "VIP treatment with dedicated support and priority service!"
    },
    {
        "title": "🎯 Perfect Match",
        "body": "Find the perfect automation solution for your needs!"
    }
]

# Load tokens
try:
    with open('fcm_tokens.json', 'r') as f:
        tokens = json.load(f)
except FileNotFoundError:
    print("fcm_tokens.json not found. Please enable push notifications in your PWA first.")
    exit(1)

if not tokens:
    print("No FCM tokens found. Please enable push notifications in your PWA first.")
    exit(1)

print(f"Found {len(tokens)} FCM token(s)")
print(f"Sending {len(MARKETING_MESSAGES)} different notifications...")

# Send each message
for i, message in enumerate(MARKETING_MESSAGES, 1):
    print(f"\n--- Sending Message {i}/{len(MARKETING_MESSAGES)} ---")
    print(f"Title: {message['title']}")
    print(f"Body: {message['body']}")
    
    # Prepare notification payload
    payload = {
        "registration_ids": tokens,
        "notification": {
            "title": message['title'],
            "body": message['body'],
            "icon": "/static/icons/icon-192x192.png",
            "badge": "1",
            "sound": "default",
            "click_action": "FLUTTER_NOTIFICATION_CLICK"
        },
        "data": {
            "message_id": f"msg_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": str(datetime.now().timestamp()),
            "type": "marketing"
        }
    }

    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(FCM_ENDPOINT, headers=headers, json=payload, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success', 0) > 0:
                print(f"✅ Successfully sent to {result.get('success', 0)} device(s)")
            if result.get('failure', 0) > 0:
                print(f"❌ Failed to send to {result.get('failure', 0)} device(s)")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    
    # Small delay between messages to avoid rate limiting
    import time
    time.sleep(0.5)

print(f"\n🎉 Completed sending {len(MARKETING_MESSAGES)} different notifications!") 