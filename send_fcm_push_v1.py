#!/usr/bin/env python3
"""
Send 200 different test push notifications to all FCM tokens using the HTTP v1 API and a Google service account.
Now uses database instead of JSON file for better tracking.
"""
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import random
from datetime import datetime
import sqlite3
import os

# TODO: Fill in your service account JSON file path and Firebase project ID
SERVICE_ACCOUNT_FILE = 'pwapush-4e4e4-5a979a55d9d3.json'
FIREBASE_PROJECT_ID = 'pwapush-4e4e4'
DATABASE_PATH = 'instance/fastag.db'

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

def get_all_user_names():
    """Get all user names from kyc_users table and cache them"""
    if not os.path.exists(DATABASE_PATH):
        return {}
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT contact_number, name FROM kyc_users 
            WHERE contact_number IS NOT NULL AND contact_number != ''
        ''')
        
        user_names = {}
        for row in cursor.fetchall():
            mobile = row[0]
            name = row[1]
            # Store both with and without spaces for flexible matching
            user_names[mobile] = name
            user_names[mobile.replace(' ', '')] = name
        
        print(f"✅ Loaded {len(set(user_names.values()))} user names from database")
        return user_names
    except Exception as e:
        print(f"Error fetching user names: {e}")
        return {}
    finally:
        conn.close()

def get_user_name_from_mobile(mobile_number, user_names_cache):
    """Get user's name from cache using mobile number"""
    if not mobile_number or mobile_number == 'anonymous':
        return None
    
    # Try exact match first
    if mobile_number in user_names_cache:
        return user_names_cache[mobile_number]
    
    # Try without spaces
    clean_mobile = mobile_number.replace(' ', '')
    if clean_mobile in user_names_cache:
        return user_names_cache[clean_mobile]
    
    return None

def get_tokens_from_database():
    """Get active FCM tokens from database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return []
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT token, username, device_type, browser, os, created_at 
            FROM fcm_tokens 
            WHERE is_active = 1 AND token IS NOT NULL AND token != ''
        ''')
        tokens = cursor.fetchall()
        return tokens
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        print("FCM tokens table may not exist. Please run database initialization first.")
        return []
    finally:
        conn.close()

def mark_token_inactive(token):
    """Mark a token as inactive in the database"""
    if not os.path.exists(DATABASE_PATH):
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE fcm_tokens 
            SET is_active = 0, last_used = CURRENT_TIMESTAMP 
            WHERE token = ?
        ''', (token,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error marking token inactive: {e}")
        return False
    finally:
        conn.close()

# Load tokens from database
tokens_data = get_tokens_from_database()

if not tokens_data:
    print("No active FCM tokens found in database.")
    print("Please enable push notifications in your PWA first.")
    exit(1)

print(f"Found {len(tokens_data)} active FCM token(s) in database")
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
print(f"\n🚀 Starting push notification campaign...")
print(f"📊 Total users to notify: {len(tokens_data)}")

# Track statistics
success_count = 0
error_count = 0
user_stats = {}

# Load user names once
user_names_cache = get_all_user_names()

for i, token_row in enumerate(tokens_data, 1):
    token = token_row['token']
    mobile_number = token_row['username'] or 'anonymous'
    device_type = token_row['device_type'] or 'unknown'
    browser = token_row['browser'] or 'unknown'
    os_name = token_row['os'] or 'unknown'
    created_at = token_row['created_at'] or 'unknown'
    
    # Get user's actual name from kyc_users table
    user_name = get_user_name_from_mobile(mobile_number, user_names_cache)
    display_name = user_name if user_name else mobile_number
    
    # Track user statistics
    if mobile_number not in user_stats:
        user_stats[mobile_number] = {'devices': set(), 'success': 0, 'errors': 0, 'name': user_name}
    user_stats[mobile_number]['devices'].add(f"{device_type} ({os_name})")
    
    msg = random.choice(MESSAGES)
    print(f"\n{'='*60}")
    print(f"📱 Message {i}/{len(tokens_data)} - User: {display_name}")
    print(f"📱 Mobile: {mobile_number}")
    print(f"🖥️  Device: {device_type} ({os_name}, {browser})")
    print(f"📅 Registered: {created_at}")
    
    # Personalize the notification with user's actual name
    if mobile_number.lower() == 'anonymous':
        personalized_title = f"🚀 {msg['title']}"
        personalized_body = f"{msg['body']}"
    else:
        # Create more personal greeting based on time and user's name
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = f"Good morning {display_name}!"
        elif 12 <= current_hour < 17:
            greeting = f"Good afternoon {display_name}!"
        elif 17 <= current_hour < 21:
            greeting = f"Good evening {display_name}!"
        else:
            greeting = f"Hi {display_name}!"
        
        personalized_title = f"{greeting} {msg['title']}"
        personalized_body = f"{msg['body']}"
    
    print(f"📢 Title: {personalized_title}")
    print(f"📝 Body: {personalized_body}")
    print(f"{'='*60}")
    
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": personalized_title,
                "body": personalized_body
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
                "website": "www.onebee.in",
                "username": mobile_number,
                "user_name": user_name or mobile_number,
                "device_type": device_type,
                "campaign": "onebee_marketing",
                "personalized": "true"
            }
        }
    }
    
    try:
        response = requests.post(FCM_ENDPOINT, headers=headers, json=message, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: Delivered to {display_name} on {device_type}")
            success_count += 1
            user_stats[mobile_number]['success'] += 1
        elif response.status_code == 404:
            error_data = response.json()
            if (error_data.get('error', {}).get('details', [{}])[0].get('errorCode') == 'UNREGISTERED'):
                print(f"❌ UNREGISTERED: {display_name}'s device uninstalled app or token expired")
                invalid_tokens.append(token)
                error_count += 1
                user_stats[mobile_number]['errors'] += 1
            else:
                print(f"❌ ERROR: {response.text}")
                error_count += 1
                user_stats[mobile_number]['errors'] += 1
        else:
            print(f"❌ ERROR: {response.text}")
            error_count += 1
            user_stats[mobile_number]['errors'] += 1
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        error_count += 1
        user_stats[mobile_number]['errors'] += 1
    
    # Small delay between messages to avoid rate limiting
    import time
    time.sleep(0.5)

# Mark invalid tokens as inactive in database
if invalid_tokens:
    print(f"\n🗑️  Cleaning up invalid tokens...")
    marked_count = 0
    
    for token in invalid_tokens:
        if mark_token_inactive(token):
            marked_count += 1
    
    print(f"✅ Marked {marked_count} tokens as inactive in database")
    
    # Get updated count
    remaining_tokens = get_tokens_from_database()
    print(f"📊 Remaining active tokens: {len(remaining_tokens)}")
else:
    print(f"\n✅ All {len(tokens_data)} tokens are valid!")

# Print user statistics
print(f"\n{'='*60}")
print(f"📈 CAMPAIGN SUMMARY")
print(f"{'='*60}")
print(f"✅ Successful deliveries: {success_count}")
print(f"❌ Failed deliveries: {error_count}")
print(f"📊 Success rate: {(success_count/(success_count+error_count)*100):.1f}%")

print(f"\n👥 USER BREAKDOWN:")
for mobile_number, stats in user_stats.items():
    devices = ', '.join(stats['devices'])
    user_display = stats['name'] if stats['name'] else mobile_number
    print(f"  • {user_display} ({mobile_number}): {stats['success']} success, {stats['errors']} errors")
    print(f"    Devices: {devices}")

print(f"\n🎉 Campaign completed! Sent {len(MESSAGES)} different Onebee notifications!") 