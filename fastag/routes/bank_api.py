from flask import Blueprint, request, Response
import logging
import xml.etree.ElementTree as ET
from signxml import XMLVerifier

bank_api = Blueprint('bank_api', __name__)

@bank_api.route('/api/bank/sync_time', methods=['POST'])
def sync_time():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received SyncTime request: {xml_data}")
    # TODO: Parse XML, validate, and process SyncTime
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/tag_details', methods=['POST'])
def tag_details():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Tag Details request: {xml_data}")

    # Parse XML and extract details
    try:
        root = ET.fromstring(xml_data)
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
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Check Transaction Status request: {xml_data}")
    # TODO: Parse XML, validate, and process Check Transaction Status
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/heartbeat', methods=['POST'])
def heartbeat():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Heart Beat request: {xml_data}")
    # TODO: Parse XML, validate, and process Heart Beat
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/pay_response', methods=['POST'])
def pay_response():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Pay Response callback: {xml_data}")
    # TODO: Parse XML, validate, and process Pay Response
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/exception_response', methods=['POST'])
def exception_response():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Exception List callback: {xml_data}")
    # TODO: Parse XML, validate, and process Exception List
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml') 