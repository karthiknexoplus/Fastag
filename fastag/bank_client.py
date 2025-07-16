import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import uuid
from signxml import XMLSigner, XMLVerifier
from lxml import etree
import sys
from flask import Flask, request, jsonify
import base64

app = Flask(__name__)

# Configurable URLs (set via environment variable or config file)
UAT_URL = os.getenv('BANK_API_UAT_URL', 'https://uat-bank-url.example.com/sync_time')
PROD_URL = os.getenv('BANK_API_PROD_URL', 'https://prod-bank-url.example.com/sync_time')

# Choose environment: 'UAT' or 'PROD'
BANK_ENV = os.getenv('BANK_API_ENV', 'UAT')

PRIVATE_KEY_PATH = "private.txt"  # Your private key for signing
CERT_PATH = "fastag_only_cert.pem"  # Use Let's Encrypt cert for signing (for testing only)
print(f"[DEBUG] Using cert for signing: {CERT_PATH}")

VERIFY_SIGNATURE = False  # Set to True to enable signature verification (recommended for production)
SIGN_REQUEST = True  # Set to False to skip XML signing (for UAT or debugging)


def get_bank_url():
    if BANK_ENV.upper() == 'PROD':
        return PROD_URL
    return UAT_URL


def build_sync_time_request(ver, ts, orgId, msgId, signature_placeholder='...'):
    root = ET.Element('etc:ReqSyncTime', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
        'ver': ver,
        'ts': ts,
        'orgId': orgId,
        'msgId': msgId
    })
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    return ET.tostring(root, encoding='utf-8', method='xml')


def send_sync_time(ver, orgId, msgId, signature_placeholder='...'):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    xml_data = build_sync_time_request(ver, ts, orgId, msgId, signature_placeholder)
    url = get_bank_url()
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=xml_data, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_sync_time_response(response.content)


# Error code to reason mapping (partial, add more as needed)
ERROR_CODE_REASON = {
    '101': 'Version Empty or not 1.0',
    '102': 'Timestamp empty or not in ISO Format',
    '103': 'orgId is not available in Database',
    '104': 'msgId is not in correct format or empty',
    '105': 'Txn Id is empty or not in correct format',
    '106': 'TagId is not in correct format or empty',
    '108': 'Org Id is empty or not in correct format',
    '112': 'TID is empty or not in correct format',
    '113': 'Vehicle Class is empty or not in correct format',
    '114': 'Vehicle class not available in Database',
    '115': 'RegNo empty or not in correct format',
    '118': 'Exception code is empty or not in correct format',
    '119': 'Exception code not in Database',
    '124': 'OrgId is Inactive',
    '125': 'TagId is not present in Database',
    '126': 'Amount empty or not in correct format',
    '127': 'Plaza code empty or not in correct format',
    '133': 'Counter is empty or not in correct format',
    '138': 'Empty Request',
    '139': 'Head Element is not available',
    '140': 'Transaction Element is not available',
    '141': 'Note is not in correct format',
    '142': 'RefId is not in correct format',
    '143': 'RefUrl is not in correct format',
    '144': 'Txn Type is empty or not in the list of types',
    '145': 'Vehicle Tag is null',
    '147': 'Request is not in correct format',
    '150': 'Lane Reader ID is empty or not in correct format',
    '159': 'Last Fetch Time is greater than 24 hours or future time',
    '160': 'Last fetch time is empty or not in correct format',
    '161': 'Risk Score Provider is empty or is not in correct format',
    '162': 'risk score type is empty or not in correct format',
    '163': 'risk score value is empty is not in correct format',
    '164': 'TID ID not mapped with given tagId',
    '165': 'AVC not in correct format',
    '166': 'Plaza name not in correct format',
    '167': 'Plaza geocode is empty or not in correct format',
    '168': 'Plaza type is empty or not in correct format',
    '169': 'Lane Id is empty or not in correct format',
    '170': 'Lane Directon is empty ot not in correct format',
    '171': 'Reader Read time is empty or not in correct format',
    '172': 'Reader Read Time cannot be more than txn time',
    '173': 'Maximum days to push older transactions exceeds (default-Current Time is more than 3 days from reader read time)',
    '174': 'orgTxnId is not in correct format',
    '175': 'Amount should be zero as tagId is in exemption Code',
    '176': 'Cannot initiate TXN as Tag is in Black List or Low Balance List',
    '178': 'Plaza not available in Database',
    '179': 'Plaza not associated with Acquirer ID',
    '180': 'Plaza type is not same as available in DB',
    '181': 'Lane attributes should be empty in case of Plaza type as Parking',
    '185': 'Reader Id is empty or not in correct format',
    '186': 'VEHICLE DETAILS are not in correct format',
    '187': 'Vehicle Class is not associated with tagId',
    '188': 'Reg no. is not associated with tagId',
    '191': 'ExcCode is not associated with tagId',
    '196': 'Currency is empty or not in correct format',
    '198': 'Avc Not in DB',
    '201': 'Transaction ID+Merchant ID+Lane ID should be unique for a transaction',
    '202': 'Meta Element is missing',
    '203': 'Amount should be zero if txn type is ZERO_TXN',
    '205': 'Future Timestamp should not be acceptable',
    '206': 'Not allowed to use particular service',
    '207': 'Exception Code is already added by other bank',
    '208': 'No privledges to add exception Code',
    '209': 'tag Verified is empty or not in correct format',
    '210': 'Public Key CVV is mandatory if TID verified is netc tag',
    '212': 'Public Key CVV is not in correct format',
    '213': 'Sign Auth is not valid',
    '214': 'procRestrictionResult is not in correct format',
    '215': 'Vehicle Auth is not valid',
    '216': 'Txn Counter is empty or not in correct format',
    '217': 'Txn Status is empty or not in correct format',
    '218': 'Txn Amount should be zero if txn status is FAILED',
    '221': 'Heart Beat Msg Type is not in predefined types',
    '222': "Heart Beat msg Acquirer Id is not matched with OrgId's acquirer ",
    '225': 'Lane status is empty or not in correct format',
    '231': 'Comvehicle is Empty or not in correct format',
    '232': 'TID is not in DB',
    '233': 'Vehicle Reg No not in DB',
    '234': 'Any one input either tagid or TID or vehicleRegNo should be present for Request Tag Details',
    '235': 'Plaza Subtype is empty or not in correct format',
    '236': 'Plaza Subtype is not same as available in DB',
    '237': 'Commercial Vehicle Flag is not same in DB',
    '239': 'Only one input is allowed either tagid or TID or vehicleRegNo',
    '241': 'One or more attribute is missing in Head Element',
    '242': 'One or more attribute is missing in Txn Element',
    '243': 'One or more attribute is missing in TagList',
    '244': 'One or more attribute is missing in Meta Element',
    '245': 'One or more attribute is missing in Merchant Element',
    '246': 'One or more attribute is missing in Vehicle Element',
    '250': 'One or more attribute is missing in Exception tag',
    '261': 'Signature is not found in request',
    '262': 'Plaza certificate is not found',
    '263': 'Signature is invalid',
    '264': 'TagID not registered with participant',
    '265': 'Invalid IIN',
    '266': 'Merchant Element not available',
    '267': 'Lane Element is not available',
    '269': 'Reader Verification Result Element is not available',
    '272': 'Amount Element is not available',
    '273': 'Riskscores Element is not available',
    '274': 'Score Element is not available',
    '275': 'Vehicle Element is not available',
    '276': 'Vehicle Details Element is not available',
    '277': 'TagList Element is not available',
    '278': 'Tag Element is not available',
    '279': 'ExceptionList Element is not available',
    '280': 'Exception Element is not available',
    '281': 'Amount should not be zero if txn Type is Credit or Debit',
    '284': 'Signature algorithm is not correct',
    '285': 'Digest algorithm is not correct',
    '287': 'Unreadable XML',
    '288': 'OrgTxnId cannot be null in case txn type is CREDIT',
    '290': 'Credit Happened Already for Specified TxnId.',
    '291': 'Credit amount should not be greater than or equal to debit amount',
    '292': 'Credit Reader read time should not be less than Debit Reader read time',
    '293': 'No Txn happened for debit in last three days',
    '294': 'SignData is empty or not in correct format',
    '295': 'No Matching ECC PublicKey found for Issuer IIN and Key Index',
    '296': 'Tag Signature Verification Failed',
    '297': 'PublicKey CVV of Input Message NOT matched with DB value',
    '299': 'Txn Status Should Not Be Failed',
    '301': 'One or more attribute is missing in Status Element',
    '302': 'Status Element is not available',
    '303': 'Incorrect format for Transaction Date',
    '304': 'Transaction Date is of future date',
    '305': "The given combination for a particular transaction doesn't exist", 
    '306': "Transaction ID doesn't exist in Transaction Master table", 
    '307': 'TxnId in Status element is empty or not in correct format',
    '308': 'Acquirer ID is empty or not in correct format',
    '309': 'Transaction Status Request List element is missing',
    '310': 'Duplicate Status element',
    '311': 'Status tag size exceeds that of system parameter value',
    '333': 'Destination does not send response within SLA',
    '335': 'Invalid Meta Name',
    '336': 'Invalid Meta Value',
    '337': 'Meta TagSize Exceeds That Of SystemParamValue',
    '339': 'Risk TagSize Exceeds That Of SystemParamValue',
    '340': 'One or more attribute is missing in Score Element',
    '346': 'Inactive Vehicle Class',
    '500': 'Amount is more than maximum amount for vehicle class / Transaction amount is more than the defined threshold limit for the VC / internal error',
    '501': 'Command Name is empty or incorrect',
    '502': 'Command Type is empty or incorrect',
    '503': 'Command Id is empty or incorrect',
    '504': 'NumParams is empty or incorrect',
    '505': 'Callback is incorrect',
    '506': 'Param Name is empty or incorrect',
    '507': 'Param Type is empty or incorrect',
    '508': 'Param Value is empty or incorrect',
    '509': 'Param Length is empty or incorrect',
    '510': 'NumObject is empty or incorrect',
    '511': 'Object Name is empty or incorrect',
    '512': 'Object Type is incorrect',
    '513': 'NumItems is empty or incorrect',
    '514': 'Item Name is empty or incorrect',
    '515': 'Item Value is empty or incorrect',
    '516': 'Item Type is incorrect',
    '517': 'Item Length is incorrect',
    '518': 'Result TimeStamp is empty or incorrect',
    '519': 'Result Status is empty or incorrect',
    '520': 'Result Code is incorrect',
    '521': 'Source Address is empty or incorrect',
    '522': 'Source Name is incorrect',
    '523': 'Source Type is empty or incorrect',
    '524': 'Destination Address is empty or incorrect',
    '525': 'Destination Name is incorrect',
    '526': 'Destination Type is empty or incorrect',
    '527': 'Command Tag is missing',
    '528': 'Param Tag is missing',
    '529': 'ObjectList Tag is missing',
    '530': 'Object Tag is missing',
    '531': 'Item Tag is missing',
    '532': 'Result Tag is missing',
    '533': 'Source Tag is missing',
    '534': 'Destination Tag is missing',
    '535': 'One or more attribute is missing in Command Tag',
    '536': 'One or more attribute is missing in Param Tag',
    '537': 'One or more attribute is missing in Object List Tag',
    '538': 'One or more attribute is missing in Object Tag',
    '539': 'One or more attribute is missing in Item Tag',
    '540': 'One or more attribute is missing in Result Tag',
    '541': 'One or more attribute is missing in Source Tag',
    '542': 'One or more attribute is missing in Destination Tag',
    '544': 'Source Address IIN/AID is not matching with Source Type',
    '546': 'Destination Error Code is empty or incorrect',
    '562': 'Source id (Plaza ID/AID) + Destination id (Plaza ID/AID) + Txn id should be unique for the request',
    '563': 'Txn Id in the Response is not Matching with Txn Id of NetcRefId in DB',
    '565': 'Given Command Id is Not in DB',
    '566': 'Command Name is Not Matched with DB value for the given Command Id',
    '567': 'Command Type is Not Matched with DB value for the given Command Id',
    '568': 'NumParams is not matching with Param Count for the combination (Command Id + Txn Type)',
    '569': 'Param Name mismatch with the given command id in DB',
    '573': 'Object Type is not ARRAY',
    '578': 'For Txn Type RQST, both source & destination are matching',
    '579': 'For Txn Type RQST, Destination address is not matching with Type',
    '582': 'For Txn Type RESP, Source details are not matching with DB Destination details',
    '583': 'For Txn Type RESP, Destination details are not matching with DB Source details',
    '584': 'No. of Items mapped in DB for (Param + Txn Type) is not same to the Items List in the message',
    '585': 'No Items are mapped for the given (Param + Txn type)',
    '589': 'Param Value pattern is not matching with Param Type',
    '590': 'Param Type is not matching with corresponding Param Name in the DB',
    '591': 'Param Length value is not matching with its Value length',
    '592': 'Item Value pattern is not matching with Item Type',
    '593': 'Item Length value is not matching with its Value length',
    '594': 'Item Name is not matching with any of the DB values or duplicate item names',
    '596': 'Txn time is ahead of transmission time',
    '600': 'DestSentInvalidResponse',
    '601': 'DestinationIsNotReachable',
    '800': 'Invalid image name',
    '801': 'Invalid ref path',
    '802': 'Invalid audit time',
    '803': 'Future audit time',
    '804': 'Invalid audit result',
    '805': 'Invalid profile data',
    '806': 'Invalid number of axle msg',
    '807': 'Invalid number of axle msg',
    '808': 'Invalid vehicle height',
    '809': 'Invalid double wheel detected',
    '810': 'Invalid vehicle length',
    '811': 'Image detail missing Violations.Violation ImageDetails',
    '812': 'Image detail missing Violations.Violation AVC Profile',
    '813': 'Record not found',
    '814': 'duplicate  request',
    '815': 'Duplicate head msg id',
    '817': 'invalid request',
    '818': 'INVALID HEAD TS',
    '999': 'No Response Message',
    # Add more as needed
}

def parse_sync_time_response(xml_response):
    import xml.etree.ElementTree as ET
    ns = {'etc': 'http://npci.org/etc/schema/'}
    try:
        root = ET.fromstring(xml_response)
        head = root.find('Head')
        resp = root.find('Resp')
        resp_code = resp.attrib.get('respCode') if resp is not None else None
        result = {
            'msgId': head.attrib.get('msgId') if head is not None else None,
            'orgId': head.attrib.get('orgId') if head is not None else None,
            'ts': head.attrib.get('ts') if head is not None else None,
            'ver': head.attrib.get('ver') if head is not None else None,
            'respCode': resp_code,
            'result': resp.attrib.get('result') if resp is not None else None,
            'serverTime': None
        }
        time_elem = resp.find('Time') if resp is not None else None
        if time_elem is not None:
            result['serverTime'] = time_elem.attrib.get('serverTime')
        # Add reason if respCode is present
        if resp_code:
            result['reason'] = ERROR_CODE_REASON.get(resp_code, 'Unknown error code')
        return result
    except Exception as e:
        return {'error': f'Failed to parse response: {e}'}


def build_heartbeat_request(msgId, orgId, ts, txnId, lanes, plaza_info, signature_placeholder='...'):
    root = ET.Element('etc:TollplazaHbeatReq', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
        'msgId': msgId,
        'orgId': orgId,
        'ts': ts,
        'ver': '1.0'
    })
    txn = ET.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'Hbt',
        'orgTxnId': ''
    })
    meta = ET.SubElement(txn, 'Meta')
    ET.SubElement(meta, 'Meta1', {'name': '', 'value': ''})
    ET.SubElement(meta, 'Meta2', {'name': '', 'value': ''})
    ET.SubElement(txn, 'HbtMsg', {'type': 'ALIVE', 'acquirerId': ''})
    plaza = ET.SubElement(txn, 'Plaza', plaza_info)
    for lane in lanes:
        ET.SubElement(plaza, 'Lane', lane)
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    return ET.tostring(root, encoding='utf-8', method='xml')


def send_heartbeat(msgId, orgId, lanes, plaza_info, signature_placeholder='...'):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]  # Ensure max 22 chars
    xml_data = build_heartbeat_request(msgId, orgId, ts, txnId, lanes, plaza_info, signature_placeholder)
    url = os.getenv('BANK_API_HEARTBEAT_URL', 'https://uat-bank-url.example.com/heartbeat')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=xml_data, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_heartbeat_response(response.content)


def parse_heartbeat_response(xml_response):
    tree = ET.fromstring(xml_response)
    head = tree.find('Head')
    txn = tree.find('Txn')
    resp = txn.find('Resp') if txn is not None else None
    signature = tree.find('Signature')
    return {
        'msgId': head.attrib.get('msgId') if head is not None else None,
        'orgId': head.attrib.get('orgId') if head is not None else None,
        'ts': head.attrib.get('ts') if head is not None else None,
        'ver': head.attrib.get('ver') if head is not None else None,
        'txnId': txn.attrib.get('id') if txn is not None else None,
        'result': resp.attrib.get('result') if resp is not None else None,
        'errCode': resp.attrib.get('errCode') if resp is not None else None,
        'resp_ts': resp.attrib.get('ts') if resp is not None else None,
        'signature': signature.text if signature is not None else None
    }


def build_check_txn_request(msgId, orgId, ts, txnId, status_list, signature_placeholder='...'):
    root = ET.Element('etc:ReqChkTxn', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
        'ver': '1.0',
        'ts': ts,
        'orgId': orgId,
        'msgId': msgId
    })
    txn = ET.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'ChkTxn',
        'orgTxnId': ''
    })
    req_list = ET.SubElement(txn, 'TxnStatusReqList')
    for status in status_list:
        ET.SubElement(req_list, 'Status', status)
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    return ET.tostring(root, encoding='utf-8', method='xml')


def send_check_txn(msgId, orgId, status_list, signature_placeholder='...'):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]
    xml_data = build_check_txn_request(msgId, orgId, ts, txnId, status_list, signature_placeholder)
    url = os.getenv('BANK_API_CHECKTXN_URL', 'https://uat-bank-url.example.com/checktxn')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=xml_data, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_check_txn_response(response.content)


def parse_check_txn_response(xml_response):
    tree = ET.fromstring(xml_response)
    head = tree.find('Head')
    txn = tree.find('Txn')
    resp = txn.find('Resp') if txn is not None else None
    signature = tree.find('Signature')
    return {
        'msgId': head.attrib.get('msgId') if head is not None else None,
        'orgId': head.attrib.get('orgId') if head is not None else None,
        'ts': head.attrib.get('ts') if head is not None else None,
        'ver': head.attrib.get('ver') if head is not None else None,
        'txnId': txn.attrib.get('id') if txn is not None else None,
        'result': resp.attrib.get('result') if resp is not None else None,
        'respCode': resp.attrib.get('respCode') if resp is not None else None,
        'totReqCnt': resp.attrib.get('totReqCnt') if resp is not None else None,
        'sucessReqCnt': resp.attrib.get('sucessReqCnt') if resp is not None else None,
        'signature': signature.text if signature is not None else None
    }


def build_tag_details_request(msgId, orgId, ts, txnId, vehicle_info):
    root = ET.Element('etc:ReqTagDetails', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
        'ver': '1.0',
        'ts': ts,
        'orgId': orgId,
        'msgId': msgId
    })
    txn = ET.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'FETCH',
        'orgTxnId': ''
    })
    vehicle = ET.SubElement(txn, 'Vehicle')
    # Always include all three attributes as per ICD: TID, vehicleRegNo, tagId (lowercase)
    vehicle.set('TID', vehicle_info.get('TID', ''))
    vehicle.set('vehicleRegNo', vehicle_info.get('vehicleRegNo', ''))
    vehicle.set('tagId', vehicle_info.get('tagId', ''))
    # Remove Meta, MessageSignature, and licensekey for strict ICD compliance
    return ET.tostring(root, encoding='utf-8', method='xml')

def sign_xml(xml_data):
    # Parse XML with lxml
    root = etree.fromstring(xml_data)
    # Load private key and cert
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = key_file.read()
    with open(CERT_PATH, "rb") as cert_file:
        cert = cert_file.read()
    # Sign the XML (default method)
    signer = XMLSigner(signature_algorithm="rsa-sha256")
    signed_root = signer.sign(root, key=private_key, cert=cert, reference_uri=None)
    # Remove the empty <Signature> placeholder from the original XML
    placeholder = signed_root.find(".//Signature")
    if placeholder is not None:
        parent = placeholder.getparent()
        parent.remove(placeholder)
    # Find the generated <ds:Signature> element
    ds_signature = signed_root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
    if ds_signature is not None:
        # Create a new <Signature> element (no namespace)
        new_sig = etree.Element("Signature")
        new_sig.append(ds_signature)
        # Insert the new <Signature> element as the last child of the root
        signed_root.append(new_sig)
    return etree.tostring(signed_root)

def generate_txn_id(plaza_id, lane_id, dt=None):
    """
    Generate transaction ID as Plaza ID (6 digits) + Lane ID (last 3 digits) + Transaction Date & Time (DDMMYYHHMMSS)
    """
    if dt is None:
        dt = datetime.now()
    date_str = dt.strftime("%d%m%y%H%M%S")
    return f"{plaza_id}{lane_id[-3:]}{date_str}"

def send_tag_details(msgId, orgId, vehicle_info):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    # Use transaction ID logic: Plaza ID (6 digits) + Lane ID (last 3 digits) + DateTime (DDMMYYHHMMSS)
    plaza_id = '712764'  # Example Plaza ID
    lane_id = '001'      # Example Lane ID (last 3 digits)
    txnId = generate_txn_id(plaza_id, lane_id, datetime.now())
    xml_data = build_tag_details_request(msgId, orgId, ts, txnId, vehicle_info)
    print(f'Request XML (unsigned), TxnId: {txnId}')
    print(xml_data.decode() if isinstance(xml_data, bytes) else xml_data)
    if SIGN_REQUEST:
        print("DEBUG: About to sign XML...")
        signed_xml = sign_xml(xml_data)
        print("DEBUG: Signed XML generated.")
        print('Request XML (signed):')
        print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
        payload = signed_xml
    else:
        print('WARNING: Skipping XML signing (SIGN_REQUEST is False). Sending unsigned XML!')
        payload = xml_data
    url = os.getenv('BANK_API_TAGDETAILS_URL', 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails/v2')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=payload, headers=headers, timeout=10, verify=False)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print("Error details from bank:", response.text)
        raise
    # --- Signature Verification (for response) ---
    ETOLL_SIGNER_CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etolluatsigner_Public.crt.txt')
    print(f"[DEBUG] Using signer cert path: {ETOLL_SIGNER_CERT_PATH}")
    try:
        from lxml import etree
        with open(ETOLL_SIGNER_CERT_PATH, 'rb') as f:
            cert = f.read()
        from signxml import XMLVerifier
        verified_data = XMLVerifier().verify(response.content, x509_cert=cert).signed_xml
        print("[Signature Verification] Signature is valid!")
        print(etree.tostring(verified_data, pretty_print=True).decode())
    except Exception as e:
        print("[Signature Verification] Signature verification failed:", e)
    return response.content


def parse_tag_details_response(xml_response):
    tree = ET.fromstring(xml_response)
    head = tree.find('Head')
    txn = tree.find('Txn')
    resp = txn.find('Resp') if txn is not None else None
    signature = tree.find('Signature')
    return {
        'msgId': head.attrib.get('msgId') if head is not None else None,
        'orgId': head.attrib.get('orgId') if head is not None else None,
        'ts': head.attrib.get('ts') if head is not None else None,
        'ver': head.attrib.get('ver') if head is not None else None,
        'txnId': txn.attrib.get('id') if txn is not None else None,
        'result': resp.attrib.get('result') if resp is not None else None,
        'respCode': resp.attrib.get('respCode') if resp is not None else None,
        'successReqCnt': resp.attrib.get('successReqCnt') if resp is not None else None,
        'totReqCnt': resp.attrib.get('totReqCnt') if resp is not None else None,
        'signature': signature.text if signature is not None else None
    }


def build_pay_request(msgId, orgId, ts, txnId, entryTxnId, pay_data, signature_placeholder='...'):
    root = ET.Element('etc:ReqPay', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
        'msgId': msgId,
        'orgId': orgId,
        'ts': ts,
        'ver': '1.0'
    })
    meta = ET.SubElement(root, 'Meta')
    # Optionally add <Tag> elements to meta if present in pay_data['meta']
    for tag in pay_data.get('meta', []):
        ET.SubElement(meta, 'Tag', tag)
    txn = ET.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'orgTxnId': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': pay_data.get('txn_type', 'DEBIT')
    })
    entry_txn = ET.SubElement(txn, 'EntryTxn', {
        'id': entryTxnId,
        'tsRead': ts,
        'type': pay_data.get('entry_txn_type', 'DEBIT')
    })
    plaza = ET.SubElement(root, 'Plaza', pay_data.get('plaza', {}))
    if 'entry_plaza' in pay_data:
        ET.SubElement(plaza, 'EntryPlaza', pay_data['entry_plaza'])
    if 'lane' in pay_data:
        ET.SubElement(plaza, 'Lane', pay_data['lane'])
    if 'entry_lane' in pay_data:
        ET.SubElement(plaza, 'EntryLane', pay_data['entry_lane'])
    if 'reader_verification' in pay_data:
        rv = ET.SubElement(plaza, 'ReaderVerificationResult', pay_data['reader_verification'])
        if 'tag_user_memory' in pay_data:
            tum = ET.SubElement(rv, 'TagUserMemory')
            for detail in pay_data['tag_user_memory']:
                ET.SubElement(tum, 'Detail', detail)
    vehicle = ET.SubElement(root, 'Vehicle', pay_data.get('vehicle', {}))
    if 'vehicle_details' in pay_data:
        vd = ET.SubElement(vehicle, 'VehicleDetails')
        for detail in pay_data['vehicle_details']:
            ET.SubElement(vd, 'Detail', detail)
    payment = ET.SubElement(root, 'Payment')
    amount = ET.SubElement(payment, 'Amount', pay_data.get('amount', {}))
    if 'overweight_amount' in pay_data:
        ET.SubElement(amount, 'OverwightAmount', pay_data['overweight_amount'])
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    return ET.tostring(root, encoding='utf-8', method='xml')


def send_pay(msgId, orgId, pay_data, signature_placeholder='...'):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]
    entryTxnId = str(uuid.uuid4())[:22]
    xml_data = build_pay_request(msgId, orgId, ts, txnId, entryTxnId, pay_data, signature_placeholder)
    url = os.getenv('BANK_API_PAY_URL', 'https://uat-bank-url.example.com/pay')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=xml_data, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_pay_response(response.content)


def parse_pay_response(xml_response):
    tree = ET.fromstring(xml_response)
    head = tree.find('Head')
    txn = tree.find('Txn')
    resp = tree.find('Resp')
    signature = tree.find('Signature')
    return {
        'msgId': head.attrib.get('msgId') if head is not None else None,
        'orgId': head.attrib.get('orgId') if head is not None else None,
        'ts': head.attrib.get('ts') if head is not None else None,
        'ver': head.attrib.get('ver') if head is not None else None,
        'txnId': txn.attrib.get('id') if txn is not None else None,
        'result': resp.attrib.get('result') if resp is not None else None,
        'respCode': resp.attrib.get('respCode') if resp is not None else None,
        'plazaId': resp.attrib.get('plazaId') if resp is not None else None,
        'signature': signature.text if signature is not None else None
    }

# Placeholder for additional API functions
# def send_other_api(...):
#     pass


def build_query_exception_list_request(msgId, orgId, ts, txnId, exception_list, signature_placeholder='...'):
    root = ET.Element('etc:ReqQueryExceptionList', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
        'ver': '1.0',
        'ts': ts,
        'orgId': orgId,
        'msgId': msgId
    })
    txn = ET.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'Query',
        'orgTxnId': ''
    })
    exc_list = ET.SubElement(txn, 'ExceptionList')
    for exc in exception_list:
        ET.SubElement(exc_list, 'Exception', exc)
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    return ET.tostring(root, encoding='utf-8', method='xml')


def send_query_exception_list(msgId, orgId, exception_list, signature_placeholder='...'):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]
    xml_data = build_query_exception_list_request(msgId, orgId, ts, txnId, exception_list, signature_placeholder)
    url = os.getenv('BANK_API_EXCEPTIONLIST_URL', 'https://uat-bank-url.example.com/exceptionlist')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=xml_data, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_query_exception_list_response(response.content)


def parse_query_exception_list_response(xml_response):
    tree = ET.fromstring(xml_response)
    head = tree.find('Head')
    txn = tree.find('Txn')
    resp = txn.find('Resp') if txn is not None else None
    signature = tree.find('Signature')
    return {
        'msgId': head.attrib.get('msgId') if head is not None else None,
        'orgId': head.attrib.get('orgId') if head is not None else None,
        'ts': head.attrib.get('ts') if head is not None else None,
        'ver': head.attrib.get('ver') if head is not None else None,
        'txnId': txn.attrib.get('id') if txn is not None else None,
        'result': resp.attrib.get('result') if resp is not None else None,
        'respCode': resp.attrib.get('respCode') if resp is not None else None,
        'msgNum': resp.attrib.get('msgNum') if resp is not None else None,
        'successReqCnt': resp.attrib.get('successReqCnt') if resp is not None else None,
        'totReqCnt': resp.attrib.get('totReqCnt') if resp is not None else None,
        'totalMsg': resp.attrib.get('totalMsg') if resp is not None else None,
        'totalTagsInMsg': resp.attrib.get('totalTagsInMsg') if resp is not None else None,
        'totalTagsInResponse': resp.attrib.get('totalTagsInResponse') if resp is not None else None,
        'signature': signature.text if signature is not None else None
    }


def build_list_participant_request(orgId, msgId, txn_id, ts):
    root = ET.Element('etc:ReqListParticipant', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    ET.SubElement(root, 'Head', {
        'ver': '1.0',
        'ts': ts,
        'orgId': orgId,
        'msgId': msgId
    })
    txn = ET.SubElement(root, 'Txn', {
        'id': txn_id,
        'note': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'ListParticipant',
        'orgTxnId': ''
    })
    plist = ET.SubElement(txn, 'ParticipantList')
    ET.SubElement(plist, 'Participant', {'BankCode': 'ALL'})
    return ET.tostring(root, encoding='utf-8', method='xml')

# Always look for the cert in the project root
ETOLL_SIGNER_CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etolluatsigner_Public.crt.txt')
print(f"[DEBUG] Using signer cert path: {ETOLL_SIGNER_CERT_PATH}")

def parse_list_participant_response(xml_response):
    import xml.etree.ElementTree as ET
    try:
        from signxml import XMLVerifier
        if VERIFY_SIGNATURE:
            try:
                with open(ETOLL_SIGNER_CERT_PATH, 'rb') as cert_file:
                    cert = cert_file.read()
                if isinstance(xml_response, str):
                    xml_response_bytes = xml_response.encode()
                else:
                    xml_response_bytes = xml_response
                from lxml import etree
                xml_doc = etree.fromstring(xml_response_bytes)
                XMLVerifier().verify(xml_doc, x509_cert=cert)
            except Exception as ve:
                import traceback
                print('Signature verification failed:')
                traceback.print_exc()
                return {'error': f'Signature verification failed: {ve}'}
        else:
            print('WARNING: Skipping signature verification (VERIFY_SIGNATURE is False)')
        ns = {'etc': 'http://npci.org/etc/schema/'}
        root = ET.fromstring(xml_response)
        # Find Head and Txn with namespace
        head = root.find('etc:Head', ns)
        txn = root.find('etc:Txn', ns)
        # Resp is inside Txn, but may not have namespace
        resp = None
        if txn is not None:
            # Try with and without namespace
            resp = txn.find('etc:Resp', ns)
            if resp is None:
                resp = txn.find('Resp')
        if resp is None:
            # Fallback: try to find Resp anywhere
            resp = root.find('.//Resp')
        result = {
            'msgId': head.attrib.get('msgId') if head is not None else None,
            'orgId': head.attrib.get('orgId') if head is not None else None,
            'head_ts': head.attrib.get('ts') if head is not None else None,
            'ver': head.attrib.get('ver') if head is not None else None,
            'txnId': txn.attrib.get('id') if txn is not None else None,
            'txn_note': txn.attrib.get('note') if txn is not None else None,
            'txn_refId': txn.attrib.get('refId') if txn is not None else None,
            'txn_refUrl': txn.attrib.get('refUrl') if txn is not None else None,
            'txn_ts': txn.attrib.get('ts') if txn is not None else None,
            'txn_type': txn.attrib.get('type') if txn is not None else None,
            'txn_orgTxnId': txn.attrib.get('orgTxnId') if txn is not None else None,
            'resp_ts': resp.attrib.get('ts') if resp is not None else None,
            'respCode': resp.attrib.get('respCode') if resp is not None else None,
            'result': resp.attrib.get('result') if resp is not None else None,
            'NoOfParticipant': resp.attrib.get('NoOfParticipant') if resp is not None else None,
            'reason': ERROR_CODE_REASON.get(resp.attrib.get('respCode'), 'Unknown error code') if resp is not None and resp.attrib.get('respCode') else None,
            'participants': []
        }
        # Try to find ParticipantList inside resp (with or without namespace)
        plist = None
        if resp is not None:
            plist = resp.find('ParticipantList')
            if plist is None:
                plist = resp.find('etc:ParticipantList', ns)
        if plist is not None:
            for p in plist.findall('Participant'):
                result['participants'].append(dict(p.attrib))
        return result
    except Exception as e:
        import traceback
        print('Exception in parse_list_participant_response:')
        traceback.print_exc()
        return {'error': f'Failed to parse response: {e}'}


def extract_and_compare_xml_certificate(xml_response):
    import xml.etree.ElementTree as ET
    try:
        # Parse XML and find the X509Certificate value
        root = ET.fromstring(xml_response)
        cert_b64 = None
        for elem in root.iter():
            if elem.tag.endswith('X509Certificate'):
                cert_b64 = elem.text.strip().replace('\n', '').replace('\r', '')
                break
        if not cert_b64:
            print('No <X509Certificate> found in XML.')
            return False
        # Convert to PEM
        pem = '-----BEGIN CERTIFICATE-----\n'
        for i in range(0, len(cert_b64), 64):
            pem += cert_b64[i:i+64] + '\n'
        pem += '-----END CERTIFICATE-----\n'
        # Read local cert
        with open(ETOLL_SIGNER_CERT_PATH, 'r') as f:
            local_pem = f.read().replace('\r', '')
        # Compare
        match = pem.strip() == local_pem.strip()
        print('Certificate in XML matches local etolluatsigner_Public.crt.txt:' if match else 'Certificate in XML does NOT match local etolluatsigner_Public.crt.txt!')
        if not match:
            print('\n--- Certificate from XML ---\n')
            print(pem)
            print('\n--- Local Certificate ---\n')
            print(local_pem)
        return match
    except Exception as e:
        print(f'Error extracting or comparing certificate: {e}')
        return False


@app.route('/api/bank/sync_time', methods=['POST'])
def api_sync_time():
    """API endpoint to trigger a SyncTime request to the bank and return the response."""
    orgId = request.json.get('orgId', 'PGSH')
    # Generate a unique msgId for every request
    msgId = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    sync_time_url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqSyncTime'
    sync_root = ET.Element('etc:ReqSyncTime', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    ET.SubElement(sync_root, 'Head', {
        'ver': '1.0',
        'ts': ts,
        'orgId': orgId,
        'msgId': msgId
    })
    sync_xml_str = ET.tostring(sync_root, encoding='utf-8', method='xml')
    from lxml import etree
    sync_xml_doc = etree.fromstring(sync_xml_str)
    signer = XMLSigner(signature_algorithm="rsa-sha256")
    with open(PRIVATE_KEY_PATH, 'rb') as key_file, open(CERT_PATH, 'rb') as cert_file:
        key = key_file.read()
        cert = cert_file.read()
    signed_sync_xml = signer.sign(sync_xml_doc, key=key, cert=cert)
    signed_sync_xml_str = etree.tostring(signed_sync_xml, pretty_print=False, xml_declaration=False)
    headers = {'Content-Type': 'application/xml'}
    try:
        sync_response = requests.post(sync_time_url, data=signed_sync_xml_str, headers=headers, timeout=10, verify=False)
        parsed = parse_sync_time_response(sync_response.content)
        return jsonify(parsed), sync_response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

TAG_DETAILS_URL = "https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails"

if __name__ == '__main__':
    print('Choose which request to send:')
    print('1. Tag Details')
    print('2. SyncTime')
    print('3. List Participants')
    choice = input('Enter 1 or 2: ').strip()
    if choice == '1':
        print('--- Tag Details API Test ---')
        print("DEBUG: Running latest bank_client.py")
        os.environ['BANK_API_TAGDETAILS_URL'] = TAG_DETAILS_URL
        orgId = 'PGSH'
        plazaId = '712764'
        agencyId = 'TCABO'
        acquirerId = '727274'
        plazaGeoCode = '11.0185,76.9778'
        vehicle_info = {
            'TID': '',
            'vehicleRegNo': '',
            'tagId': '34161FA82033E8E4037B2920'
        }
        from datetime import datetime
        now = datetime.now()
        lane_id = '001'
        txn_id = f"{plazaId}{lane_id}{now.strftime('%d%m%y%H%M%S')}"
        msgId = txn_id
        try:
            response = send_tag_details(msgId, orgId, vehicle_info)
            print('Response:')
            print(response.decode() if isinstance(response, bytes) else response)
            # Parse and print a neat summary
            parsed = parse_tag_details_response(response)
            print('\n--- Parsed Tag Details Response ---')
            for k, v in parsed.items():
                if k == 'respCode' and v:
                    reason = ERROR_CODE_REASON.get(v, 'Unknown error code')
                    print(f"{k}: {v} ({reason})")
                else:
                    print(f"{k}: {v}")
            print('-------------------------------\n')
        except Exception as e:
            print('Error sending Tag Details request:', e)
    elif choice == '2':
        print('--- SyncTime API Test ---')
        sync_time_url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqSyncTime'
        now = datetime.now()
        ts = now.strftime('%Y-%m-%dT%H:%M:%S')
        sync_msgId = now.strftime('%Y%m%d%H%M%S%f')  # Unique msgId for every request
        orgId = 'PGSH'
        sync_root = ET.Element('etc:ReqSyncTime', {'xmlns:etc': 'http://npci.org/etc/schema/'})
        ET.SubElement(sync_root, 'Head', {
            'ver': '1.0',
            'ts': ts,
            'orgId': orgId,
            'msgId': sync_msgId
        })
        sync_xml_str = ET.tostring(sync_root, encoding='utf-8', method='xml')
        print('SyncTime Request XML (unsigned):')
        print(sync_xml_str.decode())
        from lxml import etree
        sync_xml_doc = etree.fromstring(sync_xml_str)
        signer = XMLSigner(signature_algorithm="rsa-sha256")
        with open(PRIVATE_KEY_PATH, 'rb') as key_file, open(CERT_PATH, 'rb') as cert_file:
            key = key_file.read()
            cert = cert_file.read()
        signed_sync_xml = signer.sign(sync_xml_doc, key=key, cert=cert)
        signed_sync_xml_str = etree.tostring(signed_sync_xml, pretty_print=False, xml_declaration=False)
        print('SyncTime Request XML (signed):')
        print(signed_sync_xml_str.decode())
        headers = {'Content-Type': 'application/xml'}
        try:
            sync_response = requests.post(sync_time_url, data=signed_sync_xml_str, headers=headers, timeout=10, verify=False)
            print('SyncTime Response:')
            parsed = parse_sync_time_response(sync_response.content)
            print('Minimal Response:', parsed)
        except Exception as e:
            print('Error sending SyncTime request:', e)
    elif choice == '3':
        print('--- List Participants API Test ---')
        list_participant_url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/listParticipant'
        now = datetime.now()
        ts = now.strftime('%Y-%m-%dT%H:%M:%S')
        msgId = now.strftime('%Y%m%d%H%M%S%f')
        orgId = 'PGSH'
        txn_id = msgId
        req_xml = build_list_participant_request(orgId, msgId, txn_id, ts)
        print('ListParticipant Request XML (unsigned):')
        print(req_xml.decode())
        from lxml import etree
        req_xml_doc = etree.fromstring(req_xml)
        signer = XMLSigner(signature_algorithm="rsa-sha256")
        with open(PRIVATE_KEY_PATH, 'rb') as key_file, open(CERT_PATH, 'rb') as cert_file:
            key = key_file.read()
            cert = cert_file.read()
        signed_xml = signer.sign(req_xml_doc, key=key, cert=cert)
        signed_xml_str = etree.tostring(signed_xml, pretty_print=False, xml_declaration=False)
        print('ListParticipant Request XML (signed):')
        print(signed_xml_str.decode())
        headers = {'Content-Type': 'application/xml'}
        try:
            response = requests.post(list_participant_url, data=signed_xml_str, headers=headers, timeout=10, verify=False)
            print('ListParticipant Response:')
            print('Raw XML Response:')
            print(response.content.decode())
            # Call certificate comparison utility before signature verification
            extract_and_compare_xml_certificate(response.content)
            parsed = parse_list_participant_response(response.content)
            print('Minimal Response:', parsed)
        except Exception as e:
            print('Error sending ListParticipant request:', e)
    else:
        print('Invalid choice. Exiting.') 