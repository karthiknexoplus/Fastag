from flask import Blueprint, render_template, request, jsonify
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fastag_balance_bp = Blueprint('fastag_balance', __name__)

@fastag_balance_bp.route('/fastag_balance', methods=['GET', 'POST'])
def fastag_balance():
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip().upper()
        biller_id = request.form.get('biller_id', '').strip()
        
        if not reg_no:
            return render_template('fastag_balance.html', error="Registration number is required")
        
        if not biller_id:
            return render_template('fastag_balance.html', error="Biller ID is required")
        
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
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"API Response Data: {json.dumps(data, indent=2)}")
                    
                    if 'data' in data and data['data']:
                        fastag_info = data['data'][0]
                        return render_template('fastag_balance.html', 
                                            fastag_info=fastag_info,
                                            reg_no=reg_no,
                                            biller_id=biller_id)
                    else:
                        return render_template('fastag_balance.html', 
                                            error="No Fastag data found for the provided registration number",
                                            reg_no=reg_no,
                                            biller_id=biller_id)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Response content: {response.text}")
                    return render_template('fastag_balance.html', 
                                        error="Invalid response format from API",
                                        reg_no=reg_no,
                                        biller_id=biller_id)
            else:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return render_template('fastag_balance.html', 
                                    error=f"API request failed with status {response.status_code}",
                                    reg_no=reg_no,
                                    biller_id=biller_id)
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return render_template('fastag_balance.html', 
                                error="Request timed out. Please try again.",
                                reg_no=reg_no,
                                biller_id=biller_id)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to API")
            return render_template('fastag_balance.html', 
                                error="Connection error. Please check your internet connection.",
                                reg_no=reg_no,
                                biller_id=biller_id)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return render_template('fastag_balance.html', 
                                error=f"An unexpected error occurred: {str(e)}",
                                reg_no=reg_no,
                                biller_id=biller_id)
    
    return render_template('fastag_balance.html') 