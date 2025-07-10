import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid

# Configurable URLs (set via environment variable or config file)
UAT_URL = os.getenv('BANK_API_UAT_URL', 'https://uat-bank-url.example.com/sync_time')
PROD_URL = os.getenv('BANK_API_PROD_URL', 'https://prod-bank-url.example.com/sync_time')

# Choose environment: 'UAT' or 'PROD'
BANK_ENV = os.getenv('BANK_API_ENV', 'UAT')


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


def parse_sync_time_response(xml_response):
    tree = ET.fromstring(xml_response)
    ns = {'etc': 'http://npci.org/etc/schema/'}
    head = tree.find('Head')
    resp = tree.find('Resp')
    time_elem = resp.find('Time') if resp is not None else None
    signature = tree.find('Signature')
    return {
        'msgId': head.attrib.get('msgId') if head is not None else None,
        'orgId': head.attrib.get('orgId') if head is not None else None,
        'ts': head.attrib.get('ts') if head is not None else None,
        'ver': head.attrib.get('ver') if head is not None else None,
        'respCode': resp.attrib.get('respCode') if resp is not None else None,
        'result': resp.attrib.get('result') if resp is not None else None,
        'resp_ts': resp.attrib.get('ts') if resp is not None else None,
        'serverTime': time_elem.attrib.get('serverTime') if time_elem is not None else None,
        'signature': signature.text if signature is not None else None
    }


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


def build_tag_details_request(msgId, orgId, ts, txnId, vehicle_info, signature_placeholder='...'):
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
    ET.SubElement(txn, 'Vehicle', vehicle_info)
    signature = ET.SubElement(root, 'Signature')
    signature.text = signature_placeholder
    return ET.tostring(root, encoding='utf-8', method='xml')


def send_tag_details(msgId, orgId, vehicle_info, signature_placeholder='...'):
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    txnId = str(uuid.uuid4())[:22]
    xml_data = build_tag_details_request(msgId, orgId, ts, txnId, vehicle_info, signature_placeholder)
    url = os.getenv('BANK_API_TAGDETAILS_URL', 'https://uat-bank-url.example.com/tagdetails')
    headers = {'Content-Type': 'application/xml'}
    response = requests.post(url, data=xml_data, headers=headers, timeout=10)
    response.raise_for_status()
    return parse_tag_details_response(response.content)


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


if __name__ == '__main__':
    # Example usage
    result = send_sync_time(ver='1.0', orgId='XXXX', msgId='0001')
    print(result) 