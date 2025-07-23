from flask import Blueprint, request, Response
import logging
import xml.etree.ElementTree as ET
from signxml import XMLVerifier
from fastag.bank_client import send_sync_time, parse_sync_time_response, send_tag_details, parse_tag_details_response, API_URLS, send_heartbeat
import json
from fastag.pay_error_codes import PAY_ERROR_CODES
from flask import Blueprint, render_template, request
from datetime import datetime

bank_api = Blueprint('bank_api', __name__)
banking = Blueprint('banking', __name__)

def parse_and_log_xml(endpoint_name):
    xml_data = request.data.decode('utf-8')
    print(f"CALLBACK RECEIVED [{endpoint_name}]: {xml_data}")  # Print raw XML immediately
    logging.info(f"{endpoint_name} request: {xml_data}")
    try:
        root = ET.fromstring(xml_data)
        print(f"Parsed XML root: {root.tag}")  # Print parsed root tag
        logging.info(f"Parsed XML root: {root.tag}")
    except Exception as e:
        print(f"XML parsing failed: {e}")  # Print parse errors
        logging.error(f"XML parsing failed: {e}")
        root = None
    return xml_data, root

@bank_api.route('/api/bank/sync_time', methods=['POST'])
def sync_time():
    # Accept JSON input for orgId and msgId
    try:
        data = request.get_json(force=True)
    except Exception:
        data = {}
    orgId = data.get('orgId', 'PGSH')  # Default orgId if not provided
    msgId = data.get('msgId')
    if not msgId:
        from datetime import datetime
        msgId = datetime.now().strftime('%Y%m%d%H%M%S')
    # Call bank_client to send SyncTime
    result = send_sync_time('1.0', orgId, msgId)
    # Return the bank's response as JSON
    return Response(json.dumps(result), mimetype='application/json')

@bank_api.route('/api/bank/tag_details', methods=['POST'])
def tag_details():
    xml_data, root = parse_and_log_xml('Tag Details')

    # Parse XML and extract details
    try:
        ns = {'etc': 'http://npci.org/etc/schema/'}
        # Find all VehicleDetails
        vehicle_details = root.findall('.//etc:VehicleDetails', ns)
        for v in vehicle_details:
            details = {d.attrib['name']: d.attrib['value'] for d in v.findall('etc:Detail', ns)}
            logging.info(f"Extracted Vehicle Details: {details}")
    except Exception as e:
        logging.error(f"XML parsing failed: {e}")

    # Verify signature (optional but recommended)
    try:
        with open('etolluatsigner_Public.crt.txt', 'rb') as f:
            cert = f.read()
        XMLVerifier().verify(xml_data, x509_cert=cert)
        logging.info("Signature verified successfully.")
    except Exception as e:
        logging.error(f"Signature verification failed: {e}")

    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/check_txn_status', methods=['POST'])
def check_txn_status():
    xml_data, root = parse_and_log_xml('Check Transaction Status')
    # TODO: Parse XML, validate, and process Check Transaction Status
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/heartbeat', methods=['POST'])
def heartbeat():
    xml_data, root = parse_and_log_xml('Heart Beat')

    # Parse XML and extract details (same as tag_details)
    try:
        ns = {'etc': 'http://npci.org/etc/schema/'}
        vehicle_details = root.findall('.//etc:VehicleDetails', ns)
        for v in vehicle_details:
            details = {d.attrib['name']: d.attrib['value'] for d in v.findall('etc:Detail', ns)}
            logging.info(f"Extracted Vehicle Details: {details}")
    except Exception as e:
        logging.error(f"XML parsing failed: {e}")

    # Verify signature (optional but recommended, same as tag_details)
    try:
        with open('etolluatsigner_Public.crt.txt', 'rb') as f:
            cert = f.read()
        XMLVerifier().verify(xml_data, x509_cert=cert)
        logging.info("Signature verified successfully.")
    except Exception as e:
        logging.error(f"Signature verification failed: {e}")

    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/pay_response', methods=['POST'])
def pay_response():
    xml_data, root = parse_and_log_xml('Pay Response')
    # Parse for error code and print description if present
    try:
        err_code = None
        resp_code = None
        # Try to find <Resp> element and get respCode and errCode
        resp = None
        if root is not None:
            resp = root.find('.//Resp')
        if resp is not None:
            err_code = resp.attrib.get('errCode')
            resp_code = resp.attrib.get('respCode')
        if err_code:
            err_msg = PAY_ERROR_CODES.get(err_code, 'Unknown error code')
            print(f"[PAY RESPONSE ERROR] errCode: {err_code} - {err_msg}")
        if resp_code:
            resp_msg = PAY_ERROR_CODES.get(resp_code, 'Unknown error code')
            print(f"[PAY RESPONSE ERROR] respCode: {resp_code} - {resp_msg}")
    except Exception as e:
        print(f"[PAY RESPONSE ERROR] Could not parse error code: {e}")
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/exception_response', methods=['POST'])
def exception_response():
    xml_data, root = parse_and_log_xml('Exception List')
    # TODO: Parse XML, validate, and process Exception List
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@banking.route('/banking/sync_time', methods=['GET', 'POST'])
def sync_time():
    response = None
    orgId = 'PGSH'
    msgId = 'AUTO'
    ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    if request.method == 'POST':
        orgId = request.form.get('orgId', 'PGSH')
        msgId = request.form.get('msgId', 'AUTO')
        ts = request.form.get('ts', ts)
        # If msgId or ts is AUTO, generate them
        if msgId == 'AUTO':
            msgId = datetime.now().strftime('%Y%m%d%H%M%S')
        if ts == 'AUTO':
            ts = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        # Call bank_client to send SyncTime
        result = send_sync_time('1.0', orgId, msgId)
        # Show parsed response in a user-friendly way
        if isinstance(result, dict):
            response = "<b>Sync Time Response:</b><br>"
            for k, v in result.items():
                response += f"<b>{k}:</b> {v}<br>"
        else:
            response = result
    return render_template('banking/sync_time.html', orgId=orgId, msgId=msgId, ts=ts, response=response)

@banking.route('/banking/tag_details', methods=['GET', 'POST'])
def tag_details():
    response = None
    tagId = ''
    orgId = API_URLS.get('org_id', 'PGSH') if hasattr(API_URLS, 'get') else 'PGSH'
    if request.method == 'POST':
        tagId = request.form.get('tagId', '')
        orgId = request.form.get('orgId', orgId)
        # Prepare vehicle_info for tag details
        vehicle_info = {'tagId': tagId, 'vehicleRegNo': ''}
        # Use the same logic as send_tag_details, but allow dynamic orgId/tagId
        try:
            result = send_tag_details(msgId=datetime.now().strftime('%Y%m%d%H%M%S'), orgId=orgId, vehicle_info=vehicle_info)
            if isinstance(result, dict):
                response = "<b>Tag Details Response:</b><br>"
                for k, v in result.items():
                    response += f"<b>{k}:</b> {v}<br>"
            else:
                response = result
        except Exception as e:
            response = f"<b>Error:</b> {e}"
    return render_template('banking/tag_details.html', tagId=tagId, orgId=orgId, response=response)

@banking.route('/banking/heartbeat', methods=['GET', 'POST'])
def heartbeat():
    response = None
    static = API_URLS.get('STATIC', {}) if hasattr(API_URLS, 'get') else {}
    orgId = static.get('org_id', 'PGSH')
    plazaId = static.get('plaza_id', '712764')
    acquirerId = static.get('acquirer_id', '727274')
    agencyId = static.get('agency_id', 'TCABO')
    plazaGeoCode = static.get('plaza_geo_code', '11.0185,76.9778')
    if request.method == 'POST':
        orgId = request.form.get('orgId', orgId)
        plazaId = request.form.get('plazaId', plazaId)
        acquirerId = request.form.get('acquirerId', acquirerId)
        agencyId = request.form.get('agencyId', agencyId)
        plazaGeoCode = request.form.get('plazaGeoCode', plazaGeoCode)
        # Build plaza_info and lanes from config/static
        plaza_info = {
            'geoCode': plazaGeoCode,
            'id': plazaId,
            'name': static.get('plaza_name', ''),
            'subtype': 'Covered',
            'type': 'Parking',
            'address': '',
            'fromDistrict': '',
            'toDistrict': '',
            'agencyCode': agencyId
        }
        lanes = static.get('lanes', [
            {'id': 'IN01', 'direction': 'N', 'readerId': '1', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'IN02', 'direction': 'N', 'readerId': '2', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'OUT01', 'direction': 'S', 'readerId': '3', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'OUT02', 'direction': 'S', 'readerId': '4', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
        ])
        # Generate valid msgId and txn_id (timestamp + 'HBRQ')
        now = datetime.now()
        msgId = now.strftime('%Y%m%d%H%M%S') + 'HBRQ'
        txn_id = msgId
        # Call bank_client to send Heartbeat
        try:
            result = send_heartbeat(msgId=msgId, orgId=orgId, acquirer_id=acquirerId, plaza_info=plaza_info, lanes=lanes, meta=None, signature_placeholder='...', txn_id=txn_id)
            if isinstance(result, dict):
                response = "<b>Heartbeat Response:</b><br>"
                for k, v in result.items():
                    response += f"<b>{k}:</b> {v}<br>"
            else:
                response = result
        except Exception as e:
            response = f"<b>Error:</b> {e}"
    return render_template('banking/heartbeat.html', orgId=orgId, plazaId=plazaId, acquirerId=acquirerId, agencyId=agencyId, plazaGeoCode=plazaGeoCode, response=response)

@banking.route('/banking/query_exception', methods=['GET', 'POST'])
def query_exception():
    response = None
    orgId = 'PGSH'
    if request.method == 'POST':
        orgId = request.form.get('orgId', 'PGSH')
        # Prepare a default exception list (can be enhanced to take user input)
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        recent_fetch_time = now_utc.strftime('%Y-%m-%dT%H:%M:%S')
        exception_list = [
            {'excCode': '01', 'lastFetchTime': recent_fetch_time},
            {'excCode': '02', 'lastFetchTime': recent_fetch_time}
        ]
        try:
            from fastag.bank_client import send_query_exception_list
            msgId = datetime.now().strftime('%Y%m%d%H%M%S') + 'EXC'
            result = send_query_exception_list(msgId, orgId, exception_list)
            if isinstance(result, dict):
                response = "<b>Query Exception Response:</b><br>"
                for k, v in result.items():
                    response += f"<b>{k}:</b> {v}<br>"
            else:
                response = result
        except Exception as e:
            response = f"<b>Error:</b> {e}"
    return render_template('banking/query_exception.html', orgId=orgId, response=response)

@banking.route('/banking/request_pay', methods=['GET', 'POST'])
def request_pay():
    return render_template('banking/request_pay.html')

@banking.route('/banking/response_pay', methods=['GET', 'POST'])
def response_pay():
    return render_template('banking/response_pay.html')

@banking.route('/banking/transaction_status', methods=['GET', 'POST'])
def transaction_status():
    return render_template('banking/transaction_status.html') 