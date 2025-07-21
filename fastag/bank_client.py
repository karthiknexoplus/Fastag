import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import uuid
from signxml import XMLSigner, XMLVerifier
from lxml import etree
import sys
from flask import Flask, request, jsonify
import base64
import re
import random
import xml.dom.minidom
from uuid import uuid4

app = Flask(__name__)

# Configurable URLs (set via environment variable or config file)
UAT_URL = os.getenv('BANK_API_UAT_URL', 'https://uat-bank-url.example.com/sync_time')
PROD_URL = os.getenv('BANK_API_PROD_URL', 'https://prod-bank-url.example.com/sync_time')

# Choose environment: 'UAT' or 'PROD'
BANK_ENV = os.getenv('BANK_API_ENV', 'UAT')

# --- XML Signing and Verification Configuration ---
# Set these to your actual key/cert paths
PRIVATE_KEY_PATH = "privkey.pem"  # Use the local project directory copy
CERT_PATH = "public_cert.pem"      # Use the public cert you shared with the bank
BANK_CERT_PATH = "../etolluatsigner_Public.crt.txt"                      # Bank's public cert for verifying responses

VERIFY_SIGNATURE = False  # Set to True to enable signature verification (recommended for production)
SIGN_REQUEST = True  # Set to False to skip XML signing (for UAT or debugging)

# Add this at the top of the file (after imports)
UAT_TAGS = [
    {
        'chassis': 'TREE322EW2',
        'tagId': '34161FA820327FA4C8354960',
        'TID': '34161FA820327FA4C8354960',
        'vehicleRegNo': '',
        'vehicleClass': 'VC7',
        'vehicleClassDesc': 'Bus 2-axle',
        'commercialVehicle': 'T',
        'tagStatusProcessing': 'I',
        'issueDate': '24/03/2017',
        'excStatus': 'Hotlist',
        'bankId': '606162',
        'bankName': 'IDFC DIMTS'
    },
    {
        'chassis': 'TY78KL1243',
        'tagId': '34161FA820327FA4C82B57E0',
        'TID': 'E20034120189C2FFEE56CBCD',
        'vehicleRegNo': '',
        'vehicleClass': 'VC7',
        'vehicleClassDesc': 'Bus 2-axle',
        'commercialVehicle': 'F',
        'tagStatusProcessing': 'A',
        'issueDate': '30/11/2016',
        'excStatus': 'Hotlist',
        'bankId': '606162',
        'bankName': 'IDFC DIMTS'
    },
    {
        'chassis': 'MH09BU1360',
        'tagId': '34161FA820327FA40206C6C0',
        'TID': '34161FA820327FA40206C6E0',
        'vehicleRegNo': '',
        'vehicleClass': 'VC20',
        'vehicleClassDesc': 'Tata Ace and Similar mini Light Commercial Vehicle',
        'commercialVehicle': 'T',
        'tagStatusProcessing': 'A',
        'issueDate': '06/07/2017',
        'excStatus': 'Active',
        'bankId': '606162',
        'bankName': 'IDFC DIMTS'
    },
    {
        'chassis': 'DK10OT1111',
        'tagId': '34161FA820327FA4C82BDA40',
        'TID': '34161FA820327FA4C82BDA40',
        'vehicleRegNo': '',
        'vehicleClass': 'VC15',
        'vehicleClassDesc': 'Truck Multi axle ( 7 and above)',
        'commercialVehicle': 'T',
        'tagStatusProcessing': 'A',
        'issueDate': '13/09/2017',
        'excStatus': 'Hotlist',
        'bankId': '606162',
        'bankName': 'IDFC DIMTS'
    },
    {
        'chassis': 'JK89KL1310',
        'tagId': '34161FA820327FA4C834BF40',
        'TID': '34161FA820327FA4C834BF40',
        'vehicleRegNo': '',
        'vehicleClass': 'VC15',
        'vehicleClassDesc': 'Truck Multi axle ( 7 and above)',
        'commercialVehicle': 'T',
        'tagStatusProcessing': 'A',
        'issueDate': '04/04/2017',
        'excStatus': 'Hotlist',
        'bankId': '606162',
        'bankName': 'IDFC DIMTS'
    },
    {
        'chassis': 'MH89AB1021',
        'tagId': '34161FA82032D698022BF9E0',
        'TID': '34161FA82032D698022BF9E0',
        'vehicleRegNo': '',
        'vehicleClass': 'VC4',
        'vehicleClassDesc': 'Car / Jeep / Van',
        'commercialVehicle': 'F',
        'tagStatusProcessing': 'A',
        'issueDate': '17/01/2019',
        'excStatus': 'Active',
        'bankId': '617292',
        'bankName': 'DCBX Bank'
    },
    {
        'chassis': 'TR123TR12',
        'tagId': '34161FA820327FA4C8353220',
        'TID': '34161FA820327FA4C8353220',
        'vehicleRegNo': '',
        'vehicleClass': 'VC7',
        'vehicleClassDesc': 'Bus 2-axle',
        'commercialVehicle': 'T',
        'tagStatusProcessing': 'A',
        'issueDate': '17/02/2017',
        'excStatus': 'Hotlist',
        'bankId': '606162',
        'bankName': 'IDFC DIMTS'
    }
]

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
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    xml_data = build_sync_time_request(ver, ts, orgId, msgId, signature_placeholder)
    url = get_bank_url()
    headers = {'Content-Type': 'application/xml'}
    print("\n[SYNC_TIME] Request XML (unsigned):\n", xml_data.decode() if isinstance(xml_data, bytes) else xml_data)
    print("[SYNC_TIME] URL:", url)
    print("[SYNC_TIME] Headers:", headers)
    if SIGN_REQUEST:
        print("[SYNC_TIME] About to sign XML...")
        signed_xml = sign_xml(xml_data)
        print("[SYNC_TIME] Signed XML generated (actual payload to be sent):")
        print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
        payload = signed_xml  # Ensure this is the post-processed XML
    else:
        print('[SYNC_TIME] Skipping XML signing (SIGN_REQUEST is False). Sending unsigned XML!')
        payload = xml_data
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10, verify=False)
        print("[SYNC_TIME] HTTP Status Code:", response.status_code)
        print("[SYNC_TIME] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
        parsed = parse_sync_time_response(response.content)
        print("[SYNC_TIME] Parsed Response:")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
        return parsed
    except Exception as e:
        print('[SYNC_TIME] Error sending SyncTime request:', e)
        return {'error': str(e)}

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

# --- Toll Plaza Heart Beat API ---
# ICD reference: See sample schema in user prompt, matches V2.5

def validate_heartbeat_xml(xml_bytes):
    errors = []
    try:
        root = ET.fromstring(xml_bytes)
        ns = {'etc': 'http://npci.org/etc/schema/'}
        # Root
        if root.tag != '{http://npci.org/etc/schema/}TollplazaHbeatReq':
            errors.append('Root element or namespace is incorrect.')
        # Head
        head = root.find('Head')
        if head is None:
            errors.append('Missing Head element.')
        else:
            if head.attrib.get('ver') != '1.0':
                errors.append('Head.ver must be "1.0".')
            ts = head.attrib.get('ts', '')
            if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', ts):
                errors.append('Head.ts format invalid.')
            orgId = head.attrib.get('orgId', '')
            if not re.match(r'^[A-Za-z]{4}$', orgId):
                errors.append('Head.orgId must be 4 alphabetic chars.')
            msgId = head.attrib.get('msgId', '')
            if not (1 <= len(msgId) <= 35):
                errors.append('Head.msgId length invalid.')
        # Txn
        txn = root.find('Txn')
        if txn is None:
            errors.append('Missing Txn element.')
        else:
            txn_id = txn.attrib.get('id', '')
            if not (1 <= len(txn_id) <= 22):
                errors.append('Txn.id length invalid.')
            txn_ts = txn.attrib.get('ts', '')
            if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', txn_ts):
                errors.append('Txn.ts format invalid.')
            if txn.attrib.get('type') != 'Hbt':
                errors.append('Txn.type must be "Hbt".')
            # Meta
            meta = txn.find('Meta')
            if meta is None:
                errors.append('Meta element must be present.')
            # No need to check for Meta1/Meta2 children
            # HbtMsg
            hbtmsg = txn.find('HbtMsg')
            if hbtmsg is None or hbtmsg.attrib.get('type') != 'ALIVE' or not hbtmsg.attrib.get('acquirerId'):
                errors.append('HbtMsg must have type="ALIVE" and acquirerId.')
            # Plaza
            plaza = txn.find('Plaza')
            if plaza is None:
                errors.append('Missing Plaza element.')
            else:
                for attr in ['geoCode', 'id', 'name', 'subtype', 'type', 'address', 'fromDistrict', 'toDistrict', 'agencyCode']:
                    if attr not in plaza.attrib:
                        errors.append(f'Plaza missing attribute: {attr}')
                # Lane(s)
                lanes = plaza.findall('Lane')
                if not lanes:
                    errors.append('At least one Lane must be present in Plaza.')
                for lane in lanes:
                    for attr in ['id', 'direction', 'readerId', 'Status', 'Mode', 'laneType']:
                        if attr not in lane.attrib:
                            errors.append(f'Lane missing attribute: {attr}')
        # Signature
        signature = root.find('Signature')
        if signature is None:
            errors.append('Missing Signature element.')
    except Exception as e:
        errors.append(f'XML parsing error: {e}')
    return errors

def build_heartbeat_request(msgId, orgId, ts, txn_id, acquirer_id, plaza_info, lanes, meta=None, signature_placeholder='...'):
    root = ET.Element('etc:TollplazaHbeatReq', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    ET.SubElement(root, 'Head', {
        'msgId': msgId,
        'orgId': orgId,
        'ts': ts,
        'ver': '1.0'
    })
    txn = ET.SubElement(root, 'Txn', {
        'id': txn_id,
        'note': '',
        'orgTxnId': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'Hbt'
    })
    ET.SubElement(txn, 'Meta')
    ET.SubElement(txn, 'HbtMsg', {'acquirerId': acquirer_id, 'type': 'ALIVE'})
    plaza = ET.SubElement(txn, 'Plaza', {
        'address': plaza_info.get('name', ''),
        'agencyCode': plaza_info.get('agencyCode', ''),
        'fromDistrict': plaza_info.get('fromDistrict', ''),
        'geoCode': plaza_info.get('geoCode', ''),
        'id': plaza_info.get('id', ''),
        'name': plaza_info.get('name', ''),
        'subtype': plaza_info.get('subtype', ''),
        'toDistrict': plaza_info.get('toDistrict', ''),
        'type': plaza_info.get('type', '')
    })
    for lane in lanes:
        # Map EntryGate/ExitGate based on lane id
        entry_gate_map = {'IN01': '1', 'IN02': '2'}
        exit_gate_map = {'OUT01': '1', 'OUT02': '2'}
        # Lane (Exit): OUT01/OUT02
        if lane['id'].startswith('OUT'):
            exit_gate = exit_gate_map.get(lane['id'], '1')
            etree.SubElement(plaza, 'Lane', {
                'direction': lane['direction'],
                'id': lane['id'],
                'readerId': lane['readerId'],
                'Status': 'OPEN',
                'Mode': 'Normal',
                'laneType': 'Hybrid',
                'ExitGate': exit_gate,
                'Floor': '1'
            })
        # Lane (Entry): IN01/IN02
        else:
            etree.SubElement(plaza, 'Lane', {
                'direction': lane['direction'],
                'id': lane['id'],
                'readerId': lane['readerId'],
                'Status': 'OPEN',
                'Mode': 'Normal',
                'laneType': 'Hybrid',
                'ExitGate': '',
                'Floor': '1'
            })
        # EntryLane: always set EntryGate for IN01/IN02
        if lane['id'].startswith('IN'):
            entry_gate = entry_gate_map.get(lane['id'], '1')
            etree.SubElement(plaza, 'EntryLane', {
                'direction': lane['direction'],
                'id': lane['id'],
                'readerId': lane['readerId'],
                'Status': 'OPEN',
                'Mode': 'Normal',
                'laneType': 'Hybrid',
                'EntryGate': entry_gate,
                'Floor': '1'
            })
        else:
            etree.SubElement(plaza, 'EntryLane', {
                'direction': lane['direction'],
                'id': lane['id'],
                'readerId': lane['readerId'],
                'Status': 'OPEN',
                'Mode': 'Normal',
                'laneType': 'Hybrid',
                'EntryGate': '',
                'Floor': '1'
            })
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    # Add XML declaration and force encoding to UTF-8 (uppercase)
    xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    xml_str = xml_bytes.decode('utf-8').replace("<?xml version='1.0' encoding='utf-8'?>", '<?xml version="1.0" encoding="UTF-8"?>')
    return xml_str.encode('utf-8')

def send_heartbeat(msgId, orgId=None, acquirer_id=None, plaza_info=None, lanes=None, meta=None, signature_placeholder='...'):
    # Set defaults as per user-provided details
    if orgId is None:
        orgId = 'PGSH'
    if acquirer_id is None:
        acquirer_id = '727274'
    if plaza_info is None:
        plaza_info = {
            'geoCode': '11.0185,76.9778',
            'id': '712764',
            'name': 'PGS hospital',
            'subtype': 'Covered',
            'type': 'Parking',
            'address': '',
            'fromDistrict': '',
            'toDistrict': '',
            'agencyCode': 'TCABO'
        }
    if lanes is None:
        lanes = [
            {'id': 'IN01', 'direction': 'N', 'readerId': '1', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'IN02', 'direction': 'N', 'readerId': '2', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'OUT01', 'direction': 'S', 'readerId': '3', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'OUT02', 'direction': 'S', 'readerId': '4', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
        ]
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    txn_id = str(uuid.uuid4())[:22]
    xml_data = build_heartbeat_request(msgId, orgId, ts, txn_id, acquirer_id, plaza_info, lanes, meta, signature_placeholder)
    url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/TollplazaHbeatReq'
    headers = {'Content-Type': 'application/xml'}
    print("\n[HEARTBEAT] Request XML (unsigned):\n", xml_data.decode() if isinstance(xml_data, bytes) else xml_data)
    print("[HEARTBEAT] URL:", url)
    print("[HEARTBEAT] Headers:", headers)
    if SIGN_REQUEST:
        print("[HEARTBEAT] About to sign Heart Beat XML...")
        signed_xml = sign_xml(xml_data)
        print("[HEARTBEAT] Signed Heart Beat XML generated:")
        print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
        payload = signed_xml
    else:
        print('[HEARTBEAT] Skipping XML signing (SIGN_REQUEST is False). Sending unsigned XML!')
        payload = xml_data
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10, verify=False)
        print("[HEARTBEAT] HTTP Status Code:", response.status_code)
        print("[HEARTBEAT] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
        parsed = parse_heartbeat_response(response.content)
        print("[HEARTBEAT] Parsed Response:")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
        return response.content
    except Exception as e:
        print('[HEARTBEAT] Error sending Heart Beat request:', e)
        return None

def parse_heartbeat_response(xml_response):
    try:
        from lxml import etree
        tree = ET.fromstring(xml_response)
        head = tree.find('Head')
        txn = tree.find('Txn')
        resp = txn.find('Resp') if txn is not None else None
        signature = tree.find('Signature')
        # Optionally verify signature
        if VERIFY_SIGNATURE and signature is not None:
            try:
                with open(ETOLL_SIGNER_CERT_PATH, 'rb') as cert_file:
                    cert = cert_file.read()
                xml_doc = etree.fromstring(xml_response)
                from signxml import XMLVerifier
                XMLVerifier().verify(xml_doc, x509_cert=cert)
                print('[Signature Verification] Heart Beat response signature is valid!')
            except Exception as ve:
                print('[Signature Verification] Heart Beat response signature verification failed:', ve)
        return {
            'msgId': head.attrib.get('msgId') if head is not None else None,
            'orgId': head.attrib.get('orgId') if head is not None else None,
            'ts': head.attrib.get('ts') if head is not None else None,
            'ver': head.attrib.get('ver') if head is not None else None,
            'txnId': txn.attrib.get('id') if txn is not None else None,
            'result': resp.attrib.get('result') if resp is not None else None,
            'respCode': resp.attrib.get('respCode') if resp is not None else None,
            'reason': ERROR_CODE_REASON.get(resp.attrib.get('respCode'), 'Unknown error code') if resp is not None and resp.attrib.get('respCode') else None,
            'signature': signature.text if signature is not None else None
        }
    except Exception as e:
        import traceback
        print('Exception in parse_heartbeat_response:')
        traceback.print_exc()
        return {'error': f'Failed to parse Heart Beat response: {e}'}


def parse_sync_time_response(xml_response):
    import xml.etree.ElementTree as ET
    ns = {'etc': 'http://npci.org/etc/schema/'
}
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
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]
    xml_data = build_check_txn_request(msgId, orgId, ts, txnId, status_list, signature_placeholder)
    url = os.getenv('BANK_API_CHECKTXN_URL', 'https://uat-bank-url.example.com/checktxn')
    headers = {'Content-Type': 'application/xml'}
    print("\n[CHECK_TXN] Request XML (unsigned):\n", xml_data.decode() if isinstance(xml_data, bytes) else xml_data)
    print("[CHECK_TXN] URL:", url)
    print("[CHECK_TXN] Headers:", headers)
    if SIGN_REQUEST:
        print("[CHECK_TXN] About to sign XML...")
        signed_xml = sign_xml(xml_data)
        print("[CHECK_TXN] Signed XML generated:")
        print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
        payload = signed_xml
    else:
        print('[CHECK_TXN] Skipping XML signing (SIGN_REQUEST is False). Sending unsigned XML!')
        payload = xml_data
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10, verify=False)
        print("[CHECK_TXN] HTTP Status Code:", response.status_code)
        print("[CHECK_TXN] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
        parsed = parse_check_txn_response(response.content)
        print("[CHECK_TXN] Parsed Response:")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
        return parsed
    except Exception as e:
        print('[CHECK_TXN] Error sending CheckTxn request:', e)
        return {'error': str(e)}


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


def build_tag_details_request(msgId, orgId, head_ts, txnId, txn_ts, vehicle_info):
    NS = 'http://npci.org/etc/schema/'
    nsmap = {'etc': NS}
    root = etree.Element('{%s}ReqTagDetails' % NS, nsmap=nsmap)
    head = etree.SubElement(root, 'Head', {
        'ver': '1.0',  # Use version 1.2 as required
        'ts': head_ts,
        'orgId': orgId,
        'msgId': msgId
    })
    txn = etree.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'refId': vehicle_info.get('refId', ''),
        'refUrl': '',
        'ts': txn_ts,
        'type': 'FETCH',
        'orgTxnId': ''
    })
    # Vehicle: only TID, vehicleRegNo, tagId (in that order)
    etree.SubElement(txn, 'Vehicle', {
        'TID': '',
        'vehicleRegNo': vehicle_info.get('vehicleRegNo', ''),
        'tagId': vehicle_info.get('tagId', '')
    })
    return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=False)


def send_tag_details(msgId, orgId, vehicle_info):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    plaza_id = '712764'  # Example Plaza ID
    lane_id = '001'      # Example Lane ID (last 3 digits)
    txnId = generate_txn_id(plaza_id, lane_id, datetime.now())
    vehicle_info = vehicle_info.copy()
    vehicle_info.setdefault('txn_ts', ts)
    xml_data = build_tag_details_request(msgId, orgId, ts, txnId, txn_ts, vehicle_info)
    xml_str = xml_data.decode() if isinstance(xml_data, bytes) else xml_data
    if xml_str.startswith('<?xml'):
        xml_str = xml_str.replace("encoding='utf-8'", 'encoding="UTF-8"', 1)
        xml_str = xml_str.replace('encoding="utf-8"', 'encoding="UTF-8"', 1)
    print(f'\n[TAG_DETAILS] Request XML (unsigned, no signature), TxnId: {txnId}')
    print(xml_str)
    payload = xml_data
    # Hardcode the /v2 endpoint
    url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails'
    print("[DEBUG] Hardcoded URL for request:", url)
    headers = {'Content-Type': 'application/xml'}
    print("[TAG_DETAILS] URL:", url)
    print("[TAG_DETAILS] Headers:", headers)
    try:
        req_xml_doc = etree.fromstring(xml_str.encode())
        signer = XMLSigner(signature_algorithm="rsa-sha256")
        with open(PRIVATE_KEY_PATH, 'rb') as key_file, open(CERT_PATH, 'rb') as cert_file:
            key = key_file.read()
            cert = cert_file.read()
        signed_xml = signer.sign(req_xml_doc, key=key, cert=cert)
        signed_xml_str = etree.tostring(signed_xml, pretty_print=False, xml_declaration=True, encoding="UTF-8")
        print('\n[TAG_DETAILS] Request XML (signed):')
        print(signed_xml_str.decode())
    except Exception as e:
        print('[TAG_DETAILS] Error signing Tag Details XML:', e)
        signed_xml_str = xml_str.encode()

    # Use signed XML as payload
    try:
        response = requests.post(url, data=signed_xml_str, headers=headers, timeout=10, verify=False)
        print("[TAG_DETAILS] HTTP Status Code:", response.status_code)
        print("[TAG_DETAILS] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
        parsed = parse_tag_details_response(response.content)
        print("[TAG_DETAILS] Parsed Response:")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print('[TAG_DETAILS] Error sending Tag Details request:', e)
        return None


def parse_tag_details_response(xml_response):
    tree = ET.fromstring(xml_response)
    head = tree.find('Head')
    txn = tree.find('Txn')
    resp = txn.find('Resp') if txn is not None else None
    signature = tree.find('Signature')
    # Extract all <Detail> name/value pairs from <VehicleDetails>
    details_dict = {}
    try:
        ns = {'etc': 'http://npci.org/etc/schema/'}
        vehicle_details = tree.find('.//VehicleDetails')
        if vehicle_details is not None:
            for detail in vehicle_details.findall('Detail'):
                name = detail.attrib.get('name')
                value = detail.attrib.get('value')
                details_dict[name] = value
    except Exception as e:
        details_dict['error'] = f'Failed to parse VehicleDetails: {e}'
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
        'signature': signature.text if signature is not None else None,
        'vehicle_details': details_dict
    }


def build_pay_request(amount_value):
    NS = 'http://npci.org/etc/schema/'
    nsmap = {'etc': NS}
    root = etree.Element('{%s}ReqPay' % NS, nsmap=nsmap)
    head = etree.SubElement(root, 'Head', {
        'msgId': msgId,
        'orgId': orgId,
        'ts': ts,
        'ver': '1.0'
    })
    meta = etree.SubElement(root, 'Meta')
    etree.SubElement(meta, 'Tag', {'name': 'BBPSTXNID', 'value': msgId})
    txn = etree.SubElement(root, 'Txn', {
        'id': txnId,
        'note': '',
        'orgTxnId': '',
        'refId': '',
        'refUrl': '',
        'ts': ts,
        'type': 'DEBIT'
    })
    etree.SubElement(txn, 'EntryTxn', {
        'id': entry_txn_id,
        'tsRead': ts,
        'ts': ts,
        'type': 'DEBIT'
    })
    plaza = etree.SubElement(root, 'Plaza', {
        'geoCode': plaza_info['geoCode'],
        'id': plaza_info['id'],
        'name': plaza_info['name'],
        'subtype': plaza_info['subtype'],
        'type': plaza_info['type']
    })
    etree.SubElement(plaza, 'EntryPlaza', {
        'geoCode': plaza_info['geoCode'],
        'id': plaza_info['id'],
        'name': plaza_info['name'],
        'subtype': plaza_info['subtype'],
        'type': plaza_info['type']
    })
    etree.SubElement(plaza, 'Lane', {
        'direction': lane['direction'],
        'id': lane['id'],
        'readerId': lane['readerId'],
        'Status': 'OPEN',
        'Mode': 'Normal',
        'laneType': 'Hybrid',
        'ExitGate': '1',
        'Floor': '1'
    })
    etree.SubElement(plaza, 'EntryLane', {
        'direction': lane['direction'],
        'id': lane['id'],
        'readerId': lane['readerId'],
        'Status': 'OPEN',
        'Mode': 'Normal',
        'laneType': 'Hybrid',
        'EntryGate': '1',
        'Floor': '1'
    })
    rvr = etree.SubElement(plaza, 'ReaderVerificationResult', {
        'publicKeyCVV': '', 'procRestrictionResult': 'ok', 'signAuth': 'VALID', 'tagVerified': 'NETC TAG', 'ts': ts, 'txnCounter': '1', 'txnStatus': 'SUCCESS', 'vehicleAuth': 'YES'
    })
    tum = etree.SubElement(rvr, 'TagUserMemory')
    etree.SubElement(tum, 'Detail', {'name': 'TagSignature', 'value': TID})
    etree.SubElement(tum, 'Detail', {'name': 'TagVRN', 'value': vehicleRegNo})
    etree.SubElement(tum, 'Detail', {'name': 'TagVC', 'value': avc})
    vehicle = etree.SubElement(root, 'Vehicle', {
        'TID': TID,
        'tagId': tagId,
        'wim': '',
        'staticweight': '0'
    })
    vdetails = etree.SubElement(vehicle, 'VehicleDetails')
    etree.SubElement(vdetails, 'Detail', {'name': 'AVC', 'value': avc.zfill(2)})
    etree.SubElement(vdetails, 'Detail', {'name': 'LPNumber', 'value': vehicleRegNo})
    payment = etree.SubElement(root, 'Payment')
    amount = etree.SubElement(payment, 'Amount', {'curr': 'INR', 'value': amount_value, 'PriceMode': 'CUSTOM', 'IsOverWeightCharged': 'FALSE', 'PaymentMode': 'Tag'})
    etree.SubElement(amount, 'OverwightAmount', {'curr': 'INR', 'value': '0', 'PaymentMode': 'Tag'})
    return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=False)


def send_pay(msgId, orgId, pay_data, signature_placeholder='...'):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]
    entryTxnId = str(uuid.uuid4())[:22]
    xml_data = build_pay_request(msgId, orgId, ts, txnId, entryTxnId, pay_data, signature_placeholder)
    url = os.getenv('BANK_API_PAY_URL', 'https://uat-bank-url.example.com/pay')
    headers = {'Content-Type': 'application/xml'}
    print("\n[PAY] Request XML (unsigned):\n", xml_data.decode() if isinstance(xml_data, bytes) else xml_data)
    print("[PAY] URL:", url)
    print("[PAY] Headers:", headers)
    if SIGN_REQUEST:
        print("[PAY] About to sign XML...")
        signed_xml = sign_xml(xml_data)
        print("[PAY] Signed XML generated:")
        print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
        payload = signed_xml
    else:
        print('[PAY] Skipping XML signing (SIGN_REQUEST is False). Sending unsigned XML!')
        payload = xml_data
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10, verify=False)
        print("[PAY] HTTP Status Code:", response.status_code)
        print("[PAY] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
        parsed = parse_pay_response(response.content)
        print("[PAY] Parsed Response:")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
        return parsed
    except Exception as e:
        print('[PAY] Error sending Pay request:', e)
        return {'error': str(e)}


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


def build_query_exception_list_request(msgId, orgId, ts, txn_id, exception_list, signature_placeholder='...'):
    root = ET.Element('etc:ReqQueryExceptionList', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
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
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    txn_id = str(uuid.uuid4())[:22]
    xml_data = build_query_exception_list_request(msgId, orgId, ts, txn_id, exception_list, signature_placeholder)
    url = os.getenv('BANK_API_EXCEPTIONLIST_URL', 'https://uat-bank-url.example.com/exceptionlist')
    headers = {'Content-Type': 'application/xml'}
    print("\n[QUERY_EXCEPTION_LIST] Request XML (unsigned):\n", xml_data.decode() if isinstance(xml_data, bytes) else xml_data)
    print("[QUERY_EXCEPTION_LIST] URL:", url)
    print("[QUERY_EXCEPTION_LIST] Headers:", headers)
    if SIGN_REQUEST:
        print("[QUERY_EXCEPTION_LIST] About to sign XML...")
        signed_xml = sign_xml(xml_data)
        print("[QUERY_EXCEPTION_LIST] Signed XML generated:")
        print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
        payload = signed_xml
    else:
        print('[QUERY_EXCEPTION_LIST] Skipping XML signing (SIGN_REQUEST is False). Sending unsigned XML!')
        payload = xml_data
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10, verify=False)
        print("[QUERY_EXCEPTION_LIST] HTTP Status Code:", response.status_code)
        print("[QUERY_EXCEPTION_LIST] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
        parsed = parse_query_exception_list_response(response.content)
        print("[QUERY_EXCEPTION_LIST] Parsed Response:")
        for k, v in parsed.items():
            print(f"  {k}: {v}")
        return parsed
    except Exception as e:
        print('[QUERY_EXCEPTION_LIST] Error sending Query Exception List request:', e)
        return {'error': str(e)}


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
    msgId = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
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

def send_query_exception_list_icd(msgId, orgId, exception_list):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    # Use timestamp-based txn_id matching msgId for compliance
    txn_id = msgId  # Use the same as msgId, as in Heart Beat/SyncTime
    unsigned_xml = build_query_exception_list_request_icd(msgId, orgId, ts, txn_id, exception_list)
    print('Query Exception List Request XML (unsigned):')
    print(unsigned_xml.decode() if isinstance(unsigned_xml, bytes) else unsigned_xml)
    # Validate XML
    errors = validate_query_exception_list_xml(unsigned_xml)
    if errors:
        print('Validation errors:')
        for err in errors:
            print('-', err)
        print('Request not sent due to validation errors.')
        sys.exit(1)
    else:
        print('XML is ICD-compliant!')
    print('DEBUG: About to sign Query Exception List XML...')
    signed_xml = sign_xml(unsigned_xml)
    print('DEBUG: Signed Query Exception List XML generated.')
    print('Query Exception List Request XML (signed):')
    print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
    url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqQueryExceptionList'
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=signed_xml, headers=headers, timeout=10, verify=False)
    print('HTTP Status Code:', response.status_code)
    print('Response:')
    print(response.content.decode() if isinstance(response.content, bytes) else response.content)
    return response.content

def build_query_exception_list_request_icd(msgId, orgId, ts, txn_id, exception_list):
    root = ET.Element('etc:ReqQueryExceptionList', {'xmlns:etc': 'http://npci.org/etc/schema/'})
    head = ET.SubElement(root, 'Head', {
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
        'type': 'Query',
        'orgTxnId': ''
    })
    exc_list = ET.SubElement(txn, 'ExceptionList')
    for exc in exception_list:
        ET.SubElement(exc_list, 'Exception', exc)
    signature = ET.SubElement(root, 'Signature')
    signature.text = '...' # Placeholder, will be replaced by actual signature
    return ET.tostring(root, encoding='utf-8', method='xml')

def validate_query_exception_list_xml(xml_bytes):
    errors = []
    try:
        root = ET.fromstring(xml_bytes)
        # Correct root tag for Query Exception List
        if root.tag != '{http://npci.org/etc/schema/}ReqQueryExceptionList':
            errors.append('Root element or namespace is incorrect for exception list.')
        head = root.find('Head')
        if head is None:
            errors.append('Missing Head element for exception list.')
        else:
            if head.attrib.get('ver') != '1.0':
                errors.append('Head.ver must be "1.0" for exception list.')
            ts = head.attrib.get('ts', '')
            if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', ts):
                errors.append('Head.ts format invalid for exception list.')
            orgId = head.attrib.get('orgId', '')
            if not re.match(r'^[A-Za-z]{4}$', orgId):
                errors.append('Head.orgId must be 4 alphabetic chars for exception list.')
            msgId = head.attrib.get('msgId', '')
            if not (1 <= len(msgId) <= 35):
                errors.append('Head.msgId length invalid for exception list.')
        txn = root.find('Txn')
        if txn is None:
            errors.append('Missing Txn element for exception list.')
        else:
            txn_id = txn.attrib.get('id', '')
            if not (1 <= len(txn_id) <= 22):
                errors.append('Txn.id length invalid for exception list.')
            txn_ts = txn.attrib.get('ts', '')
            if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', txn_ts):
                errors.append('Txn.ts format invalid for exception list.')
            if txn.attrib.get('type') != 'Query':
                errors.append('Txn.type must be "Query" for exception list.')
            # ExceptionList
            exc_list = txn.find('ExceptionList')
            if exc_list is None:
                errors.append('Missing ExceptionList element for exception list.')
            else:
                for exc in exc_list.findall('Exception'):
                    exc_code = exc.attrib.get('excCode', '')
                    if not re.match(r'^[0-9]{2}$', exc_code):
                        errors.append(f'Exception.excCode "{exc_code}" is not in correct format (2 digits).')
                    last_fetch_time = exc.attrib.get('lastFetchTime', '')
                    if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', last_fetch_time):
                        errors.append(f'Exception.lastFetchTime "{last_fetch_time}" is not in ISO format.')
                    else:
                        # Check if lastFetchTime is not more than 24 hours ago
                        try:
                            from datetime import datetime, timezone, timedelta
                            lft_dt = datetime.strptime(last_fetch_time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                            now_dt = datetime.now(timezone.utc)
                            if (now_dt - lft_dt) > timedelta(hours=24):
                                errors.append(f'Exception.lastFetchTime "{last_fetch_time}" is more than 24 hours ago.')
                        except Exception as e:
                            errors.append(f'Exception.lastFetchTime "{last_fetch_time}" could not be parsed: {e}')
        # Signature
        signature = root.find('Signature')
        if signature is None:
            errors.append('Missing Signature element for exception list.')
    except Exception as e:
        errors.append(f'XML parsing error for exception list: {e}')
    return errors

def generate_txn_id(plaza_id, lane_id, dt=None):
    """
    Generate transaction ID as Plaza ID (6 digits) + Lane ID (last 3 digits) + Transaction Date & Time (DDMMYYHHMMSS)
    """
    if dt is None:
        dt = datetime.now()
    date_str = dt.strftime("%d%m%y%H%M%S")
    return f"{plaza_id}{lane_id[-3:]}{date_str}"

def sign_xml(xml_data):
    # Parse XML with lxml
    root = etree.fromstring(xml_data)
    # Load private key and cert
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = key_file.read()
    with open(CERT_PATH, "rb") as cert_file:
        cert = cert_file.read()
    # Use the same canonicalization and signature method as SyncTime
    signer = XMLSigner(
        signature_algorithm="rsa-sha256",
        c14n_algorithm="http://www.w3.org/2006/12/xml-c14n11"
    )
    signed_root = signer.sign(root, key=private_key, cert=cert, reference_uri=None)
    # Return the signed XML as bytes, no post-processing
    return etree.tostring(signed_root, encoding='utf-8', xml_declaration=False)

def pretty_print_xml(xml_bytes):
    try:
        parsed = xml.dom.minidom.parseString(xml_bytes.decode('utf-8'))
        return parsed.toprettyxml(indent="  ")
    except Exception as e:
        return xml_bytes.decode('utf-8')

def print_participants_table(participants):
    print("\nList of Participants:")
    print(f"{'S.No':<5} {'Issuer IIN':<10} {'Name'}")
    print("-" * 40)
    for idx, p in enumerate(participants, 1):
        print(f"{idx:<5} {p.get('issuerIin', ''):<10} {p.get('name', '')}")
    print("-" * 40)

# In the Tag Details menu logic, when a UAT tag is selected, map vehicleClass to avc number and do not include TID in vehicle_info
AVC_MAP = {
    'VC7': '5',
    'VC20': '20',
    'VC15': '15',
    'VC4': '4',
    # Add more mappings as needed
}

if __name__ == '__main__':
    print('Choose which request to send:')
    print('1. Tag Details')
    print('2. SyncTime')
    print('3. List Participants')
    print('4. Heart Beat')
    print('5. Request Query Exception List')
    print('6. Request Pay')
    choice = input('Enter 1, 2, 3, 4, 5, or 6: ').strip()
    if choice == '1':
        print('--- Tag Details API Test ---')
        print('Select a UAT Tag to test:')
        for idx, tag in enumerate(UAT_TAGS, 1):
            print(f"{idx}. Chassis: {tag['chassis']}, Tag ID: {tag['tagId']}, TID: {tag['TID']}, Status: {tag['excStatus']}, Bank: {tag['bankName']}")
        print(f"{len(UAT_TAGS)+1}. Enter manually")
        sel = input(f"Enter 1-{len(UAT_TAGS)+1}: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(UAT_TAGS):
            tag = UAT_TAGS[int(sel)-1]
            avc_num = ''
            m = re.match(r'VC(\d+)', tag['vehicleClass'])
            if m:
                avc_num = m.group(1)
            vehicle_info = {
                'tagId': tag['tagId'],
                'avc': avc_num,
                'vehicleRegNo': tag['vehicleRegNo'],
                # Generate refId similar to working sample: 6 digits + 'L' + 14 digits
                'refId': f"{random.randint(100000,999999)}L{datetime.now().strftime('%d%m%y%H%M%S')}"
            }
        else:
            tagid = input('Enter tagId: ').strip()
            avc = input('Enter avc (number, e.g. 7): ').strip()
            vehicleRegNo = input('Enter vehicleRegNo (optional): ').strip()
            vehicle_info = {
                'tagId': tagid,
                'avc': avc,
                'vehicleRegNo': vehicleRegNo,
                'refId': f"{random.randint(100000,999999)}L{datetime.now().strftime('%d%m%y%H%M%S')}"
            }
        # Check mandatory field
        if not vehicle_info['tagId']:
            print('Error: tagId is mandatory!')
        else:
            now = datetime.now()
            txn_ts = (now - timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S')
            head_ts = now.strftime('%Y-%m-%dT%H:%M:%S')
            # Generate numeric-only msgId and txnId, 20 digits each
            msgId = now.strftime('%y%m%d%H%M%S%f')[:20]
            txnId = str(int(msgId) + 1)  # Just increment by 1 for txnId
            xml_data = build_tag_details_request(msgId, 'PGSH', head_ts, txnId, txn_ts, vehicle_info)
            xml_str = xml_data.decode() if isinstance(xml_data, bytes) else xml_data
            if xml_str.startswith('<?xml'):
                xml_str = xml_str.replace("encoding='utf-8'", 'encoding="UTF-8"', 1)
                xml_str = xml_str.replace('encoding="utf-8"', 'encoding="UTF-8"', 1)
            print(f'\n[TAG_DETAILS] Request XML (unsigned, no signature), TxnId: {txnId}')
            print(xml_str)
            # Prompt for endpoint
            print("Select Tag Details endpoint:")
            print("1. https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails")
            print("2. https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails/v2")
            url_choice = input("Enter 1 or 2: ").strip()
            if url_choice == '2':
                url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails/v2'
            else:
                url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqTagDetails'
            print("[DEBUG] Selected URL for request:", url)
            headers = {'Content-Type': 'application/xml'}
            print("[TAG_DETAILS] URL:", url)
            print("[TAG_DETAILS] Headers:", headers)
            try:
                req_xml_doc = etree.fromstring(xml_str.encode())
                signer = XMLSigner(signature_algorithm="rsa-sha256")
                with open(PRIVATE_KEY_PATH, 'rb') as key_file, open(CERT_PATH, 'rb') as cert_file:
                    key = key_file.read()
                    cert = cert_file.read()
                signed_xml = signer.sign(req_xml_doc, key=key, cert=cert)
                signed_xml_str = etree.tostring(signed_xml, pretty_print=False, xml_declaration=True, encoding="UTF-8")
                print('\n[TAG_DETAILS] Request XML (signed):')
                print(signed_xml_str.decode())
            except Exception as e:
                print('[TAG_DETAILS] Error signing Tag Details XML:', e)
                signed_xml_str = xml_str.encode()

            # Use signed XML as payload
            try:
                response = requests.post(url, data=signed_xml_str, headers=headers, timeout=10, verify=False)
                print("[TAG_DETAILS] HTTP Status Code:", response.status_code)
                print("[TAG_DETAILS] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
                parsed = parse_tag_details_response(response.content)
                print("[TAG_DETAILS] Parsed Response:")
                for k, v in parsed.items():
                    print(f"  {k}: {v}")
            except Exception as e:
                print('[TAG_DETAILS] Error sending Tag Details request:', e)
                
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
            print('HTTP Status Code:', sync_response.status_code)
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
            print('HTTP Status Code:', response.status_code)
            print('ListParticipant Response:')
            print('Raw XML Response:')
            print(response.content.decode())
            # Call certificate comparison utility before signature verification
            extract_and_compare_xml_certificate(response.content)
            parsed = parse_list_participant_response(response.content)
            print('Minimal Response:', parsed)
            # Print tabular view in terminal
            if 'participants' in parsed and isinstance(parsed['participants'], list):
                print_participants_table(parsed['participants'])
        except Exception as e:
            print('Error sending ListParticipant request:', e)
    elif choice == '4':
        print('--- Toll Plaza Heart Beat API Test ---')
        orgId = 'PGSH'
        plazaId = '712764'
        acquirerId = '727274'
        plazaGeoCode = '11.0185946,76.9778221'
        plazaName = 'PGS hospital'
        plazaSubtype = 'State'
        plazaType = 'Toll'
        address = 'PGS hospital, Coimbatore, Tamilnadu'
        fromDistrict = 'Coimbatore'
        toDistrict = 'Coimbatore'
        agencyCode = 'TCABO'
        # Use official mapping for lane IDs and directions
        lanes = [
            {'id': 'IN01', 'direction': 'N', 'readerId': '1', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'IN02', 'direction': 'N', 'readerId': '2', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'OUT01', 'direction': 'S', 'readerId': '3', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
            {'id': 'OUT02', 'direction': 'S', 'readerId': '4', 'Status': 'Open', 'Mode': 'Normal', 'laneType': 'Hybrid'},
        ]
        plaza_info = {
            'geoCode': plazaGeoCode,
            'id': plazaId,
            'name': plazaName,
            'subtype': plazaSubtype,
            'type': plazaType,
            'address': address,
            'fromDistrict': fromDistrict,
            'toDistrict': toDistrict,
            'agencyCode': agencyCode
        }
        now = datetime.now()
        msgId = now.strftime('%Y%m%d%H%M%S') + 'HBRQ'
        txn_id = msgId
        try:
            ts = now.strftime('%Y-%m-%dT%H:%M:%S')
            unsigned_xml = build_heartbeat_request(msgId, orgId, ts, txn_id, acquirerId, plaza_info, lanes)
            print('Heart Beat Request XML (unsigned, pretty-printed):')
            print(pretty_print_xml(unsigned_xml))
            errors = validate_heartbeat_xml(unsigned_xml)
            if errors:
                print('Validation errors:')
                for err in errors:
                    print('-', err)
                print('Request not sent due to validation errors.')
                sys.exit(1)
            else:
                print('XML is ICD-compliant!')
            print('DEBUG: About to sign Heart Beat XML...')
            signed_xml = sign_xml(unsigned_xml)
            print('DEBUG: Signed Heart Beat XML generated.')
            print(signed_xml.decode() if isinstance(signed_xml, bytes) else signed_xml)
            url = os.getenv('BANK_API_HEARTBEAT_URL', 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/TollplazaHbeatReq')
            headers = {'Content-Type': 'application/xml'}
            print(f'Heart Beat Endpoint URL: {url}')
            response = requests.post(url, data=signed_xml, headers=headers, timeout=10, verify=False)
            print('HTTP Status Code:', response.status_code)
            print('Response:')
            print(response.content.decode() if isinstance(response.content, bytes) else response.content)
            print('--- FULL RAW RESPONSE ---')
            print('Headers:', response.headers)
            print('Text:', response.text)
            print('Raw bytes:', response.content)
            print('------------------------')
            parsed = parse_heartbeat_response(response.content)
            print('\n--- Parsed Heart Beat Response ---')
            for k, v in parsed.items():
                if k == 'respCode' and v:
                    reason = ERROR_CODE_REASON.get(v, 'Unknown error code')
                    print(f"{k}: {v} ({reason})")
                else:
                    print(f"{k}: {v}")
            print('-------------------------------\n')
        except Exception as e:
            if hasattr(e, 'response') and e.response is not None:
                print('Raw Response from bank:')
                print(e.response.content.decode(errors='replace'))
            print('Error sending Heart Beat request:', e)
    elif choice == '5':
        print('--- Request Query Exception List API Test ---')
        orgId = 'PGSH'
        # Use timestamp-based msgId/txn_id for compliance
        now = datetime.now()
        msgId = now.strftime('%Y%m%d%H%M%S') + 'EXC'
        # Use current UTC time for lastFetchTime to ensure it's within 24 hours
        from datetime import datetime, timezone
        now_utc = datetime.now(timezone.utc)
        recent_fetch_time = now_utc.strftime('%Y-%m-%dT%H:%M:%S')
        exception_list = [
            {'excCode': '01', 'lastFetchTime': recent_fetch_time},
            {'excCode': '02', 'lastFetchTime': recent_fetch_time}
        ]
        try:
            response_content = send_query_exception_list_icd(msgId, orgId, exception_list)
            try:
                parsed = parse_query_exception_list_response(response_content)
                print('\n--- Parsed Query Exception List Response ---')
                for k, v in parsed.items():
                    print(f"{k}: {v}")
                print('-------------------------------\n')
            except Exception as e:
                print('Could not parse response as XML:', e)
        except Exception as e:
            print('Error sending Query Exception List request:', e)
    elif choice == '6':
        print('--- Request Pay API Test ---')
        # Prompt for UAT tag (reuse Tag Details logic)
        print('Select a UAT Tag to use:')
        for idx, tag in enumerate(UAT_TAGS, 1):
            print(f"{idx}. Chassis: {tag['chassis']}, Tag ID: {tag['tagId']}, TID: {tag['TID']}, Status: {tag['excStatus']}, Bank: {tag['bankName']}")
        print(f"{len(UAT_TAGS)+1}. Enter manually")
        sel = input(f"Enter 1-{len(UAT_TAGS)+1}: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(UAT_TAGS):
            tag = UAT_TAGS[int(sel)-1]
            tagId = tag['tagId']
            TID = tag['TID']
            vehicleRegNo = tag.get('vehicleRegNo', '') or tag['chassis']
            avc = tag['vehicleClass'][2:] if tag['vehicleClass'].startswith('VC') else tag['vehicleClass']
        else:
            tagId = input('Enter tagId: ').strip()
            TID = input('Enter TID: ').strip()
            vehicleRegNo = input('Enter vehicleRegNo: ').strip()
            avc = input('Enter avc (number, e.g. 7): ').strip()
        # Prompt for lane/reader/direction (reuse Heart Beat logic)
        print('Select Lane:')
        lane_options = [
            {'id': 'IN01', 'direction': 'N', 'readerId': '1'},
            {'id': 'IN02', 'direction': 'N', 'readerId': '2'},
            {'id': 'OUT01', 'direction': 'S', 'readerId': '3'},
            {'id': 'OUT02', 'direction': 'S', 'readerId': '4'},
        ]
        for idx, lane in enumerate(lane_options, 1):
            print(f"{idx}. Lane ID: {lane['id']}, Direction: {lane['direction']}, Reader ID: {lane['readerId']}")
        lane_sel = input(f"Enter 1-{len(lane_options)}: ").strip()
        if lane_sel.isdigit() and 1 <= int(lane_sel) <= len(lane_options):
            lane = lane_options[int(lane_sel)-1]
        else:
            lane = lane_options[0]
        # Use similar data as Heart Beat for plaza
        orgId = 'PGSH'
        plaza_info = {
            'geoCode': '11,76',
            'id': '712764',
            'name': 'PGS hospital',
            'subtype': 'Covered',
            'type': 'Parking',
            'address': '',
            'fromDistrict': '',
            'toDistrict': '',
            'agencyCode': 'TCABO'
        }
        now = datetime.now()
        ts = now.strftime('%Y-%m-%dT%H:%M:%S')
        msgId = now.strftime('%Y%m%d%H%M%S%f')[:26]
        txnId = now.strftime('%Y%m%d%H%M%S%f')[:21]
        entry_txn_id = txnId
        # Prompt for amount to be debited
        amount_value = input('Enter amount to be debited (e.g. 455.00): ').strip()
        if not amount_value:
            amount_value = '455.00'
        xml_data = build_pay_request(amount_value)
        xml_str = xml_data.decode() if isinstance(xml_data, bytes) else xml_data
        if xml_str.startswith('<?xml'):
            xml_str = xml_str.replace("encoding='utf-8'", 'encoding="UTF-8"', 1)
            xml_str = xml_str.replace('encoding="utf-8"', 'encoding="UTF-8"', 1)
        print(f'\n[PAY] Request XML (unsigned, no signature), TxnId: {txnId}')
        print(xml_str)
        # Sign the XML
        try:
            req_xml_doc = etree.fromstring(xml_str.encode())
            signer = XMLSigner(signature_algorithm="rsa-sha256")
            with open(PRIVATE_KEY_PATH, 'rb') as key_file, open(CERT_PATH, 'rb') as cert_file:
                key = key_file.read()
                cert = cert_file.read()
            signed_xml = signer.sign(req_xml_doc, key=key, cert=cert)
            signed_xml_str = etree.tostring(signed_xml, pretty_print=False, xml_declaration=True, encoding="UTF-8")
            print('\n[PAY] Request XML (signed):')
            print(signed_xml_str.decode())
        except Exception as e:
            print('[PAY] Error signing Pay XML:', e)
            signed_xml_str = xml_str.encode()
        # Send the request
        url = 'https://etolluatapi.idfcfirstbank.com/dimtspay_toll_services/toll/ReqPay'
        headers = {'Content-Type': 'application/xml'}
        print("[PAY] URL:", url)
        print("[PAY] Headers:", headers)
        try:
            response = requests.post(url, data=signed_xml_str, headers=headers, timeout=10, verify=False)
            print("[PAY] HTTP Status Code:", response.status_code)
            print("[PAY] Response Content:\n", response.content.decode() if isinstance(response.content, bytes) else response.content)
            # Optionally parse response here
        except Exception as e:
            print('[PAY] Error sending Pay request:', e)
    else:
        print('Invalid choice. Exiting.') 