from flask import Blueprint, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import logging

fuel_price_bp = Blueprint('fuel_price', __name__)

@fuel_price_bp.route('/fuel-price', methods=['GET'])
def fuel_price():
    city_filter = request.args.get('city', '').strip().lower()
    url = "https://www.coverfox.com/petrol-price-in-india/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first table for city-wise prices
        tables = soup.find_all('table', class_='art-table')
        city_table = tables[0] if tables else None
        prices = []
        cities = set()
        
        if city_table:
            for row in city_table.tbody.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 4:
                    city1 = cols[0].text.strip()
                    price1 = cols[1].text.strip()
                    city2 = cols[2].text.strip()
                    price2 = cols[3].text.strip()
                    prices.append({'city': city1, 'price': price1})
                    prices.append({'city': city2, 'price': price2})
                    cities.add(city1)
                    cities.add(city2)
        
        # Filter if city_filter is set
        if city_filter:
            filtered_prices = [p for p in prices if p['city'].lower() == city_filter]
        else:
            filtered_prices = prices
            
        return render_template('fuel_price.html', 
                             prices=filtered_prices, 
                             cities=sorted(cities), 
                             selected_city=city_filter)
                             
    except Exception as e:
        logging.error(f"Error fetching fuel prices: {e}")
        return render_template('fuel_price.html', 
                             prices=[], 
                             cities=[], 
                             selected_city=city_filter,
                             error="Unable to fetch fuel prices at the moment.") 

@fuel_price_bp.route('/api/fuel-price', methods=['GET'])
def api_fuel_price():
    city_filter = request.args.get('city', '').strip().lower()
    url = "https://www.coverfox.com/petrol-price-in-india/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', class_='art-table')
        city_table = tables[0] if tables else None
        prices = []
        cities = set()
        if city_table:
            for row in city_table.tbody.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 4:
                    city1 = cols[0].text.strip()
                    price1 = cols[1].text.strip()
                    city2 = cols[2].text.strip()
                    price2 = cols[3].text.strip()
                    prices.append({'city': city1, 'price': price1})
                    prices.append({'city': city2, 'price': price2})
                    cities.add(city1)
                    cities.add(city2)
        if city_filter:
            filtered_prices = [p for p in prices if p['city'].lower() == city_filter]
        else:
            filtered_prices = prices
        return jsonify({
            "success": True,
            "prices": filtered_prices,
            "cities": sorted(list(cities)),
            "selected_city": city_filter
        })
    except Exception as e:
        logging.error(f"Error fetching fuel prices: {e}")
        return jsonify({
            "success": False,
            "error": "Unable to fetch fuel prices at the moment."
        }), 500 