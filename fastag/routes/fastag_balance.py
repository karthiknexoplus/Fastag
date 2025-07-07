from flask import Blueprint, render_template, request, jsonify
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fastag Billers data
FASTAG_BILLERS = [
    {"name": "Airtel Payments Bank", "billerId": "9fae6085-9be7-4975-9300-60d9a737f5c7"},
    {"name": "Axis Bank", "billerId": "ae721976-ab51-4a49-b692-6951de295376"},
    {"name": "HDFC Bank", "billerId": "57813979-5935-4d1a-aae7-db1914a8e106"},
    {"name": "ICICI Bank", "billerId": "d084a832-6880-4fbf-81f3-e284021bf320"},
    {"name": "IDFC FIRST Bank", "billerId": "e5ce08e4-82f9-499c-9b37-d8d64a241d42"},
    {"name": "SBI", "billerId": "91b24509-0d1e-4ff9-8f7d-812092f02d9d"},
    {"name": "AU Small Finance Bank", "billerId": "6b3d5ac9-2ae2-4043-98b0-b2baef1b047e"},
    {"name": "Bandhan Bank", "billerId": "a5813ec6-df65-419d-b4cf-284ea1cf6279"},
    {"name": "Bank of Baroda", "billerId": "f73b8416-ad55-4c65-93bb-3a00003b25fd"},
    {"name": "Bank of Maharashtra", "billerId": "90d80ef2-6711-428c-8b93-776b759400fb"},
    {"name": "Canara Bank", "billerId": "c4d2a96c-2fd6-4eef-9763-f9658fc33f18"},
    {"name": "Equitas Small Finance Bank", "billerId": "c672087b-ea11-4974-b132-4e0f17a8d1a0"},
    {"name": "Federal Bank", "billerId": "217bbe27-7459-443a-b04a-1b7c2f88af32"},
    {"name": "IDBI Bank", "billerId": "dfa6f62e-589f-4594-834e-32462346e769"},
    {"name": "Indian Bank", "billerId": "574384d7-2cea-42b7-bb8e-d02821675897"},
    {"name": "IndusInd Bank", "billerId": "8c64e1e7-de05-42f3-9b65-b730f95a7359"},
    {"name": "IOB", "billerId": "d04485e2-2745-435e-893e-5f6180832b2a"},
    {"name": "Jammu and Kashmir Bank", "billerId": "6e3abf92-bf9e-492c-b20e-320c0d308905"},
    {"name": "Karnataka Bank", "billerId": "e8ef4cc6-5fe0-45aa-b251-1da32e0bf582"},
    {"name": "Kotak Mahindra Bank", "billerId": "b2b0fce9-c0ac-4468-a4ee-f22ffa263c9c"},
    {"name": "Livquick Technology", "billerId": "f869c0f4-4dee-4a13-b70e-e988eb50dc4a"},
    {"name": "South Indian Bank", "billerId": "be95d909-ad89-4b5d-b62a-fe13446fd16c"},
    {"name": "UCO Bank", "billerId": "696f84a4-10bb-4546-ad33-6ffee4daa1c8"},
    {"name": "Union Bank of India", "billerId": "12302d69-13f4-43f8-b030-75a9ba87d0bb"},
]

fastag_balance_bp = Blueprint('fastag_balance', __name__)

@fastag_balance_bp.route('/fastag_balance', methods=['GET', 'POST'])
def fastag_balance():
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip().upper()
        selected_bank = request.form.get('selected_bank', '').strip()
        
        if not reg_no:
            return render_template('fastag_balance.html', 
                                error="Registration number is required",
                                billers=FASTAG_BILLERS)
        
        if not selected_bank:
            return render_template('fastag_balance.html', 
                                error="Please select a bank",
                                billers=FASTAG_BILLERS,
                                reg_no=reg_no)
        
        # Find the biller ID for the selected bank
        biller_id = None
        selected_bank_name = ""
        for biller in FASTAG_BILLERS:
            if biller['name'] == selected_bank:
                biller_id = biller['billerId']
                selected_bank_name = biller['name']
                break
        
        if not biller_id:
            return render_template('fastag_balance.html', 
                                error="Invalid bank selection",
                                billers=FASTAG_BILLERS,
                                reg_no=reg_no)
        
        try:
            # Acko API endpoint
            url = f"https://www.acko.com/api/app/fastag/"
            
            # Parameters
            params = {
                'regNo': reg_no,
                'billerId': biller_id,
                'type': 'fastag_balance'
            }
            
            # Headers from the curl command
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'cookie': 'trackerid=58db3079-80b0-40a3-b71e-0aa17adcd4ff; acko_visit=x8ElVS1q2_DEl6IDUssemg; _ga=GA1.1.2025589563.1751304220; FPID=FPID2.2.ToGOKuS7C2efkVbq%2Bx%2BpCXn0yjg%2FwGQS6y4ntw7Wk90%3D.1751304220; FPLC=4WHTGc00JE4rFKdtZKJz2AKLoX%2F99XQ1t%2F06nL5OIGP2lS0Zo4hxZQEAyjb4bg57bnDwjhqd6Pt1gftdDkLeB3MUu9y50sUolSs8fxF7ANdnVQJ2SzV7%2BpQDF87Zag%3D%3D; FPAU=1.2.1994248006.1751304220; _gtmeec=e30%3D; _fbp=fb.1.1751304220057.1374344911; user_id=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJFUHhtZUwzV0hDLTVsNTQ1VHNld2kwYTU3SFRlZy0ySXpmZk9zM0hOUEhNIn0.eyJleHAiOjE3NTEzOTA2NTAsImlhdCI6MTc1MTMwNDI1MCwiYXV0aF90aW1lIjoxNzUxMzA0MjQ5LCJqdGkiOiJlMGY5ZDE5Ni0wNTg2LTQ5N2YtOThkYi1jZDc5OGRjNzkxZDYiLCJpc3MiOiJodHRwczovL2NlbnRyYWwtYXV0aC1wcm9kLmludGVybmFsLmxpdmUuYWNrby5jb20vcmVhbG1zL2Fja28iLCJzdWIiOiItcDhfUEJTZF92QXJxOXozc3gwamNRIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZmFzdGFnX3dpZGdldCIsInNlc3Npb25fc3RhdGUiOiI1OGFmNmNiNC1mMDk5LTQ5NzMtYjVjYS01MGFmMDg2ZGMxMjAiLCJzY29wZSI6Im9mZmxpbmVfYWNjZXNzIiwic2lkIjoiNThhZjZjYjQtZjA5OS00OTczLWI1Y2EtNTBhZjA4NmRjMTIwIn0.npdxSeT_eA2ek-Nb14Gjj4aXByow6OqRv_qhTu5cVk-OZbdkot0FE_dOwefgqhOOAIc8JJ63iDjMHrrRxClzrCjP1s5yuqRnL-JDckXrBfFWDIBz5obXfX0QZZ5gfpQmoc2mW2T1AOc5WJHZz6wHdReqATIKuqocZM9WoxsdK82_EHzluZb8OAH-vg27Zc-jSroptHoxWqzOFUw9zkz3MY6TR3V3WidI2Q2CQ08C7gmVkaSYaD3guve96BR5FAJXobQiaWZbFUKV9K23Cf6rRr0dqIR46Bqroqc-1iT20fCNhFXpN2XlgfBf6Sb6_FXk2xqxpJmNi-ESP32KAVv2HYw; refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIwZmVmYzE3Yi03OGUwLTRkZjUtOGI4OC1iZmVmNDlkMGRkZTgifQ.eyJpYXQiOjE3NTEzMDQyNTAsImp0aSI6IjIyOTU0ZGNmLWVlMjEtNGIyOC04NmNjLWY5YjBhZjRhYjhiNyIsImlzcyI6Imh0dHBzOi8vY2VudHJhbC1hdXRoLXByb2QuaW50ZXJuYWwubGl2ZS5hY2tvLmNvbS9yZWFsbXMvYWNrbyIsImF1ZCI6Imh0dHBzOi8vY2VudHJhbC1hdXRoLXByb2QuaW50ZXJuYWwubGl2ZS5hY2tvLmNvbS9yZWFsbXMvYWNrbyIsInN1YiI6Ii1wOF9QQlNkX3ZBcnE5ejNzeDBqY1EiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoiZmFzdGFnX3dpZGdldCIsInNlc3Npb25fc3RhdGUiOiI1OGFmNmNiNC1mMDk5LTQ5NzMtYjVjYS01MGFmMDg2ZGMxMjAiLCJzY29wZSI6Im9mZmxpbmVfYWNjZXNzIiwic2lkIjoiNThhZjZjYjQtZjA5OS00OTczLWI1Y2EtNTBhZjA4NmRjMTIwIn0.e06PkvVCbCk--NhXOQ-WuL1_YADx2XCA7nA6IbKO8U8; __cf_bm=SQ.9E9im7aexpiRMSzS6OLVCHVjP8vaVwxSmp9elgic-1751304250-1.0.1.1-2_.HGn_LQWldYq_UHgPQWEqKMW0U7ZtiFy.tJyYrjSYmddLbIFQHc5xUl5ALmcYRLXip4h0VIncHSmxIuBWk7HGStOGxsY_10jgzJc0X8jg; FPGSID=1.1751304220.1751304915.G-W47KBK64MF.HJAU5FxFaGKZ4onrhqTYKQ; _ga_W47KBK64MF=GS2.1.s1751304219$o1$g1$t1751304930$j45$l0$h1260810729; trackerid=58db3079-80b0-40a3-b71e-0aa17adcd4ff; acko_visit=HY1ie1g4FMneftwtfqSLmA',
                'priority': 'u=1, i',
                'referer': 'https://www.acko.com/automobile/fastag/',
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
            }
            
            logger.info(f"Making API request to Acko for registration number: {reg_no}")
            
            # Make the API request
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Headers: {dict(response.headers)}")
            logger.info(f"API Response Content: {response.text}")
            logger.info(f"API Response URL: {response.url}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"API Response Data: {json.dumps(data, indent=2)}")
                    
                    if 'data' in data and data['data']:
                        fastag_info = data['data'][0]
                        return render_template('fastag_balance.html', 
                                            fastag_info=fastag_info,
                                            reg_no=reg_no,
                                            selected_bank=selected_bank_name,
                                            billers=FASTAG_BILLERS)
                    else:
                        return render_template('fastag_balance.html', 
                                            error="No Fastag data found for the provided registration number",
                                            reg_no=reg_no,
                                            selected_bank=selected_bank_name,
                                            billers=FASTAG_BILLERS)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Response content: {response.text}")
                    logger.error(f"Response status: {response.status_code}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                    return render_template('fastag_balance.html', 
                                        error=f"Invalid response format from API. Status: {response.status_code}. Response: {response.text[:200]}...",
                                        reg_no=reg_no,
                                        selected_bank=selected_bank_name,
                                        billers=FASTAG_BILLERS)
            else:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                logger.error(f"Response headers: {dict(response.headers)}")
                return render_template('fastag_balance.html', 
                                    error=f"API request failed with status {response.status_code}. Response: {response.text[:200]}...",
                                    reg_no=reg_no,
                                    selected_bank=selected_bank_name,
                                    billers=FASTAG_BILLERS)
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return render_template('fastag_balance.html', 
                                error="Request timed out. Please try again.",
                                reg_no=reg_no,
                                selected_bank=selected_bank_name,
                                billers=FASTAG_BILLERS)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to API")
            return render_template('fastag_balance.html', 
                                error="Connection error. Please check your internet connection.",
                                reg_no=reg_no,
                                selected_bank=selected_bank_name,
                                billers=FASTAG_BILLERS)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return render_template('fastag_balance.html', 
                                error=f"An unexpected error occurred: {str(e)}",
                                reg_no=reg_no,
                                selected_bank=selected_bank_name,
                                billers=FASTAG_BILLERS)
    
    return render_template('fastag_balance.html', billers=FASTAG_BILLERS)

@fastag_balance_bp.route('/debug_fastag_api', methods=['GET'])
def debug_fastag_api():
    """Debug route to test the API directly"""
    import requests
    
    # Test parameters
    reg_no = "KA04MJ6369"
    biller_id = "e5ce08e4-82f9-499c-9b37-d8d64a241d42"  # IDFC FIRST Bank
    
    url = "https://www.acko.com/api/app/fastag/"
    params = {
        'regNo': reg_no,
        'billerId': biller_id,
        'type': 'fastag_balance'
    }
    
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cookie': 'trackerid=58db3079-80b0-40a3-b71e-0aa17adcd4ff; acko_visit=x8ElVS1q2_DEl6IDUssemg; _ga=GA1.1.2025589563.1751304220; FPID=FPID2.2.ToGOKuS7C2efkVbq%2Bx%2BpCXn0yjg%2FwGQS6y4ntw7Wk90%3D.1751304220; FPLC=4WHTGc00JE4rFKdtZKJz2AKLoX%2F99XQ1t%2F06nL5OIGP2lS0Zo4hxZQEAyjb4bg57bnDwjhqd6Pt1gftdDkLeB3MUu9y50sUolSs8fxF7ANdnVQJ2SzV7%2BpQDF87Zag%3D%3D; FPAU=1.2.1994248006.1751304220; _gtmeec=e30%3D; _fbp=fb.1.1751304220057.1374344911; user_id=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJFUHhtZUwzV0hDLTVsNTQ1VHNld2kwYTU3SFRlZy0ySXpmZk9zM0hOUEhNIn0.eyJleHAiOjE3NTEzOTA2NTAsImlhdCI6MTc1MTMwNDI1MCwiYXV0aF90aW1lIjoxNzUxMzA0MjQ5LCJqdGkiOiJlMGY5ZDE5Ni0wNTg2LTQ5N2YtOThkYi1jZDc5OGRjNzkxZDYiLCJpc3MiOiJodHRwczovL2NlbnRyYWwtYXV0aC1wcm9kLmludGVybmFsLmxpdmUuYWNrby5jb20vcmVhbG1zL2Fja28iLCJzdWIiOiItcDhfUEJTZF92QXJxOXozc3gwamNRIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZmFzdGFnX3dpZGdldCIsInNlc3Npb25fc3RhdGUiOiI1OGFmNmNiNC1mMDk5LTQ5NzMtYjVjYS01MGFmMDg2ZGMxMjAiLCJzY29wZSI6Im9mZmxpbmVfYWNjZXNzIiwic2lkIjoiNThhZjZjYjQtZjA5OS00OTczLWI1Y2EtNTBhZjA4NmRjMTIwIn0.npdxSeT_eA2ek-Nb14Gjj4aXByow6OqRv_qhTu5cVk-OZbdkot0FE_dOwefgqhOOAIc8JJ63iDjMHrrRxClzrCjP1s5yuqRnL-JDckXrBfFWDIBz5obXfX0QZZ5gfpQmoc2mW2T1AOc5WJHZz6wHdReqATIKuqocZM9WoxsdK82_EHzluZb8OAH-vg27Zc-jSroptHoxWqzOFUw9zkz3MY6TR3V3WidI2Q2CQ08C7gmVkaSYaD3guve96BR5FAJXobQiaWZbFUKV9K23Cf6rRr0dqIR46Bqroqc-1iT20fCNhFXpN2XlgfBf6Sb6_FXk2xqxpJmNi-ESP32KAVv2HYw; refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIwZmVmYzE3Yi03OGUwLTRkZjUtOGI4OC1iZmVmNDlkMGRkZTgifQ.eyJpYXQiOjE3NTEzMDQyNTAsImp0aSI6IjIyOTU0ZGNmLWVlMjEtNGIyOC04NmNjLWY5YjBhZjRhYjhiNyIsImlzcyI6Imh0dHBzOi8vY2VudHJhbC1hdXRoLXByb2QuaW50ZXJuYWwubGl2ZS5hY2tvLmNvbS9yZWFsbXMvYWNrbyIsImF1ZCI6Imh0dHBzOi8vY2VudHJhbC1hdXRoLXByb2QuaW50ZXJuYWwubGl2ZS5hY2tvLmNvbS9yZWFsbXMvYWNrbyIsInN1YiI6Ii1wOF9QQlNkX3ZBcnE5ejNzeDBqY1EiLCJ0eXAiOiJPZmZsaW5lIiwiYXpwIjoiZmFzdGFnX3dpZGdldCIsInNlc3Npb25fc3RhdGUiOiI1OGFmNmNiNC1mMDk5LTQ5NzMtYjVjYS01MGFmMDg2ZGMxMjAiLCJzY29wZSI6Im9mZmxpbmVfYWNjZXNzIiwic2lkIjoiNThhZjZjYjQtZjA5OS00OTczLWI1Y2EtNTBhZjA4NmRjMTIwIn0.e06PkvVCbCk--NhXOQ-WuL1_YADx2XCA7nA6IbKO8U8; __cf_bm=SQ.9E9im7aexpiRMSzS6OLVCHVjP8vaVwxSmp9elgic-1751304250-1.0.1.1-2_.HGn_LQWldYq_UHgPQWEqKMW0U7ZtiFy.tJyYrjSYmddLbIFQHc5xUl5ALmcYRLXip4h0VIncHSmxIuBWk7HGStOGxsY_10jgzJc0X8jg; FPGSID=1.1751304220.1751304915.G-W47KBK64MF.HJAU5FxFaGKZ4onrhqTYKQ; _ga_W47KBK64MF=GS2.1.s1751304219$o1$g1$t1751304930$j45$l0$h1260810729; trackerid=58db3079-80b0-40a3-b71e-0aa17adcd4ff; acko_visit=HY1ie1g4FMneftwtfqSLmA',
        'priority': 'u=1, i',
        'referer': 'https://www.acko.com/automobile/fastag/',
        'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    }
    
    try:
        logger.info(f"Debug API call - URL: {url}")
        logger.info(f"Debug API call - Params: {params}")
        logger.info(f"Debug API call - Headers: {headers}")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        logger.info(f"Debug API Response Status: {response.status_code}")
        logger.info(f"Debug API Response URL: {response.url}")
        logger.info(f"Debug API Response Headers: {dict(response.headers)}")
        logger.info(f"Debug API Response Content: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Debug API Response JSON: {json.dumps(data, indent=2)}")
                return jsonify({
                    "status": "success",
                    "status_code": response.status_code,
                    "url": response.url,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "json_data": data
                })
            except json.JSONDecodeError as e:
                logger.error(f"Debug JSON decode error: {e}")
                return jsonify({
                    "status": "json_error",
                    "status_code": response.status_code,
                    "url": response.url,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "error": str(e)
                })
        else:
            return jsonify({
                "status": "http_error",
                "status_code": response.status_code,
                "url": response.url,
                "headers": dict(response.headers),
                "content": response.text
            })
            
    except Exception as e:
        logger.error(f"Debug API exception: {e}")
        return jsonify({
            "status": "exception",
            "error": str(e)
        }) 