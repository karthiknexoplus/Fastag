#!/usr/bin/env python3
"""
Send 200 different test push notifications to all FCM tokens using the HTTP v1 API and a Google service account.
"""
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import random
from datetime import datetime

# TODO: Fill in your service account JSON file path and Firebase project ID
SERVICE_ACCOUNT_FILE = 'pwapush-4e4e4-5a979a55d9d3.json'
FIREBASE_PROJECT_ID = 'pwapush-4e4e4'

FCM_ENDPOINT = f'https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send'

# 200 different marketing messages for Onebee entrance automation
MESSAGES = [
    {
        "title": "🚪 Onebee Smart Gate Solutions",
        "body": "Transform your entrance with Onebee's cutting-edge automated gate systems! Contact us at 95008 50000 | www.onebee.in"
    },
    {
        "title": "🔒 Onebee Security Upgrade",
        "body": "Upgrade your security with Onebee's advanced access control systems! Call 95008 50000 for free consultation."
    },
    {
        "title": "📹 Onebee CCTV Installation",
        "body": "Get 20% off on professional CCTV surveillance installation this month! Visit www.onebee.in for details."
    },
    {
        "title": "⚡ Onebee Quick Access",
        "body": "Say goodbye to manual gates! Experience seamless automated entry with Onebee. Call 95008 50000."
    },
    {
        "title": "🏠 Onebee Apartment Security",
        "body": "Secure your apartment complex with Onebee's boom barrier access control! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Smart Home Integration",
        "body": "Control your gates from anywhere with Onebee's smart home automation! Visit www.onebee.in"
    },
    {
        "title": "💰 Onebee Limited Time Offer",
        "body": "Free consultation + 15% discount on all gate automation packages! Call 95008 50000 now!"
    },
    {
        "title": "🔔 Onebee Maintenance Reminder",
        "body": "Your gate system is due for maintenance. Book your service with Onebee at 95008 50000!"
    },
    {
        "title": "🚀 Onebee New Technology",
        "body": "Experience the future with Onebee's AI-powered access control systems! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Mobile App Update",
        "body": "New features added! Control your gates with voice commands now! Download from www.onebee.in"
    },
    {
        "title": "🎉 Onebee Welcome Bonus",
        "body": "New customer? Get free installation worth ₹5,000 on any automation package! Call 95008 50000."
    },
    {
        "title": "🚨 Onebee Emergency Support",
        "body": "24/7 technical support available for all Onebee automation systems! Contact 95008 50000."
    },
    {
        "title": "💳 Onebee Payment Plans",
        "body": "0% EMI available on all Onebee gate automation and CCTV packages! Visit www.onebee.in"
    },
    {
        "title": "🏆 Onebee Customer Satisfaction",
        "body": "Join 10,000+ satisfied customers with Onebee automation solutions! Call 95008 50000."
    },
    {
        "title": "📊 Onebee Security Analytics",
        "body": "Track your property's security with Onebee's advanced analytics dashboard! Visit www.onebee.in"
    },
    {
        "title": "🎁 Onebee Referral Rewards",
        "body": "Refer friends and earn ₹2,000 for each successful Onebee installation! Call 95008 50000."
    },
    {
        "title": "🔋 Onebee Battery Backup",
        "body": "Ensure uninterrupted security with Onebee's backup power solutions! Contact 95008 50000."
    },
    {
        "title": "🚀 Onebee Express Installation",
        "body": "Get your Onebee automation system installed within 24 hours! Call 95008 50000."
    },
    {
        "title": "📈 Onebee ROI Calculator",
        "body": "See how much you can save with Onebee automated security systems! Visit www.onebee.in"
    },
    {
        "title": "🎯 Onebee Personalized Quote",
        "body": "Get a customized quote for your specific automation needs from Onebee! Call 95008 50000."
    },
    {
        "title": "🔔 Onebee Service Update",
        "body": "New remote monitoring features added to all Onebee systems! Visit www.onebee.in"
    },
    {
        "title": "💰 Onebee Cashback Alert",
        "body": "10% cashback credited for your recent Onebee automation purchase! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Vehicle Access Control",
        "body": "Automate your parking with Onebee's smart vehicle detection systems! Call 95008 50000."
    },
    {
        "title": "📱 Onebee Smart Features",
        "body": "Control your gates with fingerprint, card, or mobile app from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🎊 Onebee Festival Special",
        "body": "Diwali special: Zero installation charges on all Onebee automation packages! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Security Alert",
        "body": "New anti-tampering features added to protect your Onebee automation systems! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Free Assessment",
        "body": "Get a free security assessment for your property from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Premium Support",
        "body": "Upgrade to Onebee Premium for 24/7 priority support and maintenance! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Smart Recommendations",
        "body": "Based on your property, Onebee recommends our sliding gate automation! Call 95008 50000."
    },
    {
        "title": "🚪 Onebee Swing Gate Solutions",
        "body": "Perfect for residential properties! Onebee's automated swing gates with safety sensors. Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Folding Gate Automation",
        "body": "Space-saving folding gates with smooth automation for commercial use from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee HD CCTV Systems",
        "body": "Crystal clear 4K surveillance with night vision and motion detection from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Commercial Solutions",
        "body": "Secure your business with Onebee's commercial-grade automation systems! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Residential Packages",
        "body": "Complete home security with Onebee's automated gates and CCTV surveillance! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Quick Response",
        "body": "Onebee team responds within 2 hours for all emergency service calls! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Energy Efficient",
        "body": "Save up to 40% on energy costs with Onebee's smart automation systems! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Smart Alerts",
        "body": "Get instant notifications when someone enters your property with Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Cost Effective",
        "body": "Reduce security costs by 60% with Onebee's automated systems! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Parking Automation",
        "body": "Automate your parking with Onebee's smart barrier and access control! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Remote Control",
        "body": "Control your gates from anywhere in the world with Onebee's mobile app! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Anniversary Special",
        "body": "Celebrating 10 years! Get 25% off on all Onebee automation packages! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Advanced Security",
        "body": "Multi-layer security with biometric access and CCTV monitoring from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Free Demo",
        "body": "Experience Onebee's automation systems with a free demonstration! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee VIP Support",
        "body": "Exclusive VIP support for Onebee premium customers with dedicated hotline! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Custom Solutions",
        "body": "Tailored automation solutions for your specific requirements from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🚪 Onebee Sliding Gate Magic",
        "body": "Smooth sliding gates with silent operation and safety features from Onebee! Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Bi-fold Excellence",
        "body": "Space-efficient bi-fold gates perfect for limited driveway space from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee PTZ Camera Systems",
        "body": "Pan-tilt-zoom cameras with 360° coverage for complete surveillance from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Industrial Grade",
        "body": "Heavy-duty automation systems for industrial and commercial use from Onebee! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Smart Homes",
        "body": "Integrate your gates with Alexa and Google Home for voice control from Onebee! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Lightning Fast",
        "body": "Gates that respond in milliseconds for ultimate convenience from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Weather Resistant",
        "body": "All Onebee systems are weather-proof and built to last! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee 24/7 Monitoring",
        "body": "Round-the-clock monitoring with instant alert systems from Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Investment Protection",
        "body": "Protect your property investment with Onebee's advanced security automation! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee RFID Access",
        "body": "Quick vehicle access with RFID tags and automatic recognition from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee App Integration",
        "body": "Seamless integration with your existing smart home ecosystem from Onebee! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee New Year Special",
        "body": "Start 2024 secure! 30% off on all Onebee automation installations! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Military Grade",
        "body": "Military-grade security systems for maximum protection from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Free Quote",
        "body": "Get a detailed quote for your automation needs from Onebee within 24 hours! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Platinum Service",
        "body": "Platinum service with dedicated account manager and priority support from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Expert Consultation",
        "body": "Free consultation with Onebee's automation experts to find the perfect solution! Call 95008 50000."
    },
    {
        "title": "🚪 Onebee Automatic Gates",
        "body": "Experience the luxury of automatic gates with safety sensors from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔄 Onebee Folding Excellence",
        "body": "Premium folding gates with smooth automation and elegant design from Onebee! Call 95008 50000."
    },
    {
        "title": "📹 Onebee Night Vision CCTV",
        "body": "Crystal clear surveillance even in complete darkness from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🏢 Onebee Corporate Security",
        "body": "Enterprise-grade security solutions for corporate environments from Onebee! Call 95008 50000."
    },
    {
        "title": "🏠 Onebee Home Automation",
        "body": "Complete home automation with gates, CCTV, and smart controls from Onebee! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Instant Response",
        "body": "Gates that respond instantly to your commands from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Energy Smart",
        "body": "Solar-powered automation systems for eco-friendly security from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Smart Notifications",
        "body": "Get notified instantly when gates are accessed with Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Money Saving",
        "body": "Save on security personnel costs with Onebee's automated systems! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Vehicle Recognition",
        "body": "Automatic vehicle recognition for seamless access from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Cloud Control",
        "body": "Control your gates from the cloud with Onebee's advanced app! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Holiday Special",
        "body": "Holiday special: Free maintenance for 1 year on all Onebee packages! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Bulletproof Security",
        "body": "Bulletproof security systems for maximum protection from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Site Survey",
        "body": "Free site survey to assess your automation requirements from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Gold Support",
        "body": "Gold support package with 4-hour response time guarantee from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Perfect Fit",
        "body": "Custom automation solutions that fit your exact needs from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🚪 Onebee Silent Operation",
        "body": "Whisper-quiet gate automation for peaceful environments from Onebee! Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Space Saver",
        "body": "Space-saving folding gates perfect for narrow driveways from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee HD Surveillance",
        "body": "High-definition surveillance with advanced recording features from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Business Security",
        "body": "Secure your business with Onebee's professional automation systems! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Family Safety",
        "body": "Keep your family safe with Onebee's automated security systems! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Power Backup",
        "body": "Uninterrupted security with automatic power backup systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Climate Control",
        "body": "All Onebee systems designed to work in extreme weather conditions! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Real-time Alerts",
        "body": "Real-time security alerts sent directly to your phone from Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Value for Money",
        "body": "Premium automation systems at competitive prices from Onebee! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Automatic Parking",
        "body": "Automated parking solutions with barrier control from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Smart Integration",
        "body": "Integrate with your existing smart home devices from Onebee! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Season Sale",
        "body": "Season sale: Up to 40% off on all Onebee automation packages! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Maximum Security",
        "body": "Maximum security with multi-layer protection systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Expert Advice",
        "body": "Free expert advice on choosing the right automation system from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Elite Service",
        "body": "Elite service with dedicated support team and fast response from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Tailored Solutions",
        "body": "Tailored automation solutions for your unique requirements from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🚪 Onebee Luxury Gates",
        "body": "Luxury automatic gates with premium finishes and features from Onebee! Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Compact Design",
        "body": "Compact folding gates for space-constrained properties from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee Advanced CCTV",
        "body": "Advanced CCTV systems with AI-powered motion detection from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Industrial Security",
        "body": "Heavy-duty security solutions for industrial facilities from Onebee! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Residential Security",
        "body": "Complete residential security with automated systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee High Speed",
        "body": "High-speed gate automation for busy environments from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Durability",
        "body": "Built to last with premium materials and engineering from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Instant Updates",
        "body": "Instant updates on all security events and activities from Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Cost Efficient",
        "body": "Cost-efficient automation that pays for itself from Onebee! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Smart Parking",
        "body": "Smart parking solutions with automated access control from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Easy Control",
        "body": "Easy-to-use mobile app for controlling all your systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Special Offer",
        "body": "Special offer: Free upgrade to premium features from Onebee! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Ultimate Protection",
        "body": "Ultimate protection with state-of-the-art security systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Free Assessment",
        "body": "Free security assessment for your property from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Premium Care",
        "body": "Premium care with extended warranty and support from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Expert Installation",
        "body": "Expert installation by certified Onebee technicians! Call 95008 50000."
    },
    {
        "title": "🚪 Onebee Automatic Entry",
        "body": "Automatic entry systems for ultimate convenience from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔄 Onebee Smart Folding",
        "body": "Smart folding gates with intelligent automation from Onebee! Call 95008 50000."
    },
    {
        "title": "📹 Onebee Crystal Clear",
        "body": "Crystal clear surveillance with advanced camera systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🏢 Onebee Corporate Grade",
        "body": "Corporate-grade security for professional environments from Onebee! Call 95008 50000."
    },
    {
        "title": "🏠 Onebee Home Protection",
        "body": "Complete home protection with automated security from Onebee! Contact 95008 50000."
    },
    {
        "title": "⚡ Onebee Quick Access",
        "body": "Quick access with fast-response automation systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🎯 Onebee All Weather",
        "body": "All-weather automation systems for any climate from Onebee! Call 95008 50000."
    },
    {
        "title": "🔔 Onebee Smart Monitoring",
        "body": "Smart monitoring with intelligent alert systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "💰 Onebee Investment Value",
        "body": "Increase your property value with Onebee's security automation! Call 95008 50000."
    },
    {
        "title": "🚗 Onebee Vehicle Security",
        "body": "Vehicle security with automated access control from Onebee! Contact 95008 50000."
    },
    {
        "title": "📱 Onebee Remote Access",
        "body": "Remote access to all your security systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🎊 Onebee Limited Time",
        "body": "Limited time offer: Free consultation and assessment from Onebee! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Fortress Security",
        "body": "Fortress-level security for maximum protection from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Professional Survey",
        "body": "Professional security survey for your property from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee VIP Treatment",
        "body": "VIP treatment with dedicated support and priority service from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Perfect Match",
        "body": "Find the perfect automation solution for your needs from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🚪 Onebee Smart Entry",
        "body": "Smart entry systems with facial recognition from Onebee! Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Biometric Access",
        "body": "Secure biometric access control for your premises from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee 4K Surveillance",
        "body": "Ultra HD 4K surveillance cameras with night vision from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Enterprise Security",
        "body": "Enterprise-grade security solutions for large facilities from Onebee! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Villa Security",
        "body": "Complete villa security with automated systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Instant Access",
        "body": "Instant access with touchless entry systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Solar Powered",
        "body": "Eco-friendly solar-powered automation systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Smart Alerts",
        "body": "Intelligent alerts for all security events from Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Budget Friendly",
        "body": "Affordable automation solutions for every budget from Onebee! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Auto Parking",
        "body": "Fully automated parking solutions from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Voice Control",
        "body": "Voice-controlled gate automation from Onebee! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Mega Sale",
        "body": "Mega sale: Up to 50% off on all Onebee packages! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Maximum Protection",
        "body": "Maximum protection with advanced security systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Free Survey",
        "body": "Free security survey for your property from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Diamond Service",
        "body": "Diamond service with 24/7 dedicated support from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Custom Design",
        "body": "Custom-designed automation solutions from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🚪 Onebee Premium Gates",
        "body": "Premium automatic gates with luxury finishes from Onebee! Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Space Optimized",
        "body": "Space-optimized gate solutions from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee AI Surveillance",
        "body": "AI-powered surveillance with smart detection from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Industrial Security",
        "body": "Heavy-duty industrial security solutions from Onebee! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Smart Villa",
        "body": "Smart villa automation with Onebee! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Ultra Fast",
        "body": "Ultra-fast gate response systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee All Climate",
        "body": "All-climate automation systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Real-time Monitoring",
        "body": "Real-time security monitoring from Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Value Investment",
        "body": "Value investment in security automation from Onebee! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Smart Parking",
        "body": "Smart parking automation from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee App Control",
        "body": "Complete app control for all systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Flash Sale",
        "body": "Flash sale: Limited time offers from Onebee! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Ultimate Security",
        "body": "Ultimate security with Onebee systems! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Expert Survey",
        "body": "Expert security survey from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Royal Service",
        "body": "Royal service with premium support from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Perfect Solution",
        "body": "Perfect automation solution from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🚪 Onebee Luxury Entry",
        "body": "Luxury entry systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🔄 Onebee Smart Automation",
        "body": "Smart automation solutions from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📹 Onebee HD Monitoring",
        "body": "HD monitoring systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🏢 Onebee Corporate Security",
        "body": "Corporate security solutions from Onebee! Contact 95008 50000."
    },
    {
        "title": "🏠 Onebee Home Security",
        "body": "Complete home security from Onebee! Visit www.onebee.in"
    },
    {
        "title": "⚡ Onebee Fast Response",
        "body": "Fast response automation from Onebee! Call 95008 50000."
    },
    {
        "title": "🎯 Onebee Durable Systems",
        "body": "Durable automation systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "🔔 Onebee Instant Alerts",
        "body": "Instant alert systems from Onebee! Call 95008 50000."
    },
    {
        "title": "💰 Onebee Affordable Security",
        "body": "Affordable security solutions from Onebee! Contact 95008 50000."
    },
    {
        "title": "🚗 Onebee Smart Parking",
        "body": "Smart parking solutions from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📱 Onebee Easy Control",
        "body": "Easy control systems from Onebee! Call 95008 50000."
    },
    {
        "title": "🎊 Onebee Great Offers",
        "body": "Great offers from Onebee! Call 95008 50000."
    },
    {
        "title": "🔒 Onebee Top Security",
        "body": "Top security systems from Onebee! Visit www.onebee.in"
    },
    {
        "title": "📋 Onebee Free Quote",
        "body": "Free quote from Onebee! Call 95008 50000."
    },
    {
        "title": "🌟 Onebee Premium Service",
        "body": "Premium service from Onebee! Contact 95008 50000."
    },
    {
        "title": "🎯 Onebee Ideal Solution",
        "body": "Ideal automation solution from Onebee! Visit www.onebee.in"
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
print(f"Sending {len(MESSAGES)} different notifications...")

# Authenticate with service account
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
request = google.auth.transport.requests.Request()
credentials.refresh(request)
access_token = credentials.token

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json; UTF-8"
}

# Track invalid tokens to remove
invalid_tokens = []

# Send a notification to each token
for i, token in enumerate(tokens, 1):
    msg = random.choice(MESSAGES)
    print(f"\n--- Sending Message {i}/{len(tokens)} ---")
    print(f"Title: {msg['title']}")
    print(f"Body: {msg['body']}")
    
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": msg["title"],
                "body": msg["body"]
            },
            "webpush": {
                "fcm_options": {
                    "link": "https://www.onebee.in"
                }
            },
            "data": {
                "message_id": f"msg_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": str(datetime.now().timestamp()),
                "type": "marketing",
                "company": "Onebee",
                "contact": "95008 50000",
                "website": "www.onebee.in"
            }
        }
    }
    
    try:
        response = requests.post(FCM_ENDPOINT, headers=headers, json=message, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully sent to device")
        elif response.status_code == 404:
            error_data = response.json()
            if (error_data.get('error', {}).get('details', [{}])[0].get('errorCode') == 'UNREGISTERED'):
                print(f"❌ Token is unregistered (device uninstalled app or token expired)")
                invalid_tokens.append(token)
            else:
                print(f"❌ Error: {response.text}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    
    # Small delay between messages to avoid rate limiting
    import time
    time.sleep(0.5)

# Remove invalid tokens from the file
if invalid_tokens:
    print(f"\n🗑️  Removing {len(invalid_tokens)} invalid token(s)...")
    valid_tokens = [token for token in tokens if token not in invalid_tokens]
    
    try:
        with open('fcm_tokens.json', 'w') as f:
            json.dump(valid_tokens, f, indent=2)
        print(f"✅ Updated fcm_tokens.json - removed {len(invalid_tokens)} invalid token(s)")
        print(f"📊 Remaining valid tokens: {len(valid_tokens)}")
    except Exception as e:
        print(f"❌ Error updating fcm_tokens.json: {e}")
else:
    print(f"\n✅ No invalid tokens found - all {len(tokens)} tokens are valid")

print(f"\n🎉 Completed sending {len(MESSAGES)} different Onebee notifications!") 