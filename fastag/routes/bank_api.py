from flask import Blueprint, request, Response
import logging
import xml.etree.ElementTree as ET
# from signxml import XMLVerifier  # Uncomment if signature verification is needed

bank_api = Blueprint('bank_api', __name__)

def parse_and_log_xml(endpoint_name):
    xml_data = request.data.decode('utf-8')
    logging.info(f"{endpoint_name} request: {xml_data}")
    try:
        root = ET.fromstring(xml_data)
        logging.info(f"Parsed XML root: {root.tag}")
        # Add more XML processing as needed
    except Exception as e:
        logging.error(f"XML parsing failed: {e}")
        root = None
    return xml_data, root

# Uncomment and use if you want to verify XML signatures
# def verify_signature(xml_data):
#     try:
#         with open('etolluatsigner_Public.crt.txt', 'rb') as f:
#             cert = f.read()
#         XMLVerifier().verify(xml_data, x509_cert=cert)
#         logging.info("Signature verified successfully.")
#     except Exception as e:
#         logging.error(f"Signature verification failed: {e}")

@bank_api.route('/api/bank/sync_time', methods=['POST'])
def sync_time():
    xml_data, root = parse_and_log_xml("SyncTime")
    # verify_signature(xml_data)  # Uncomment if needed
    # TODO: Add business logic for SyncTime here
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/tag_details', methods=['POST'])
def tag_details():
    xml_data, root = parse_and_log_xml("Tag Details")
    # verify_signature(xml_data)  # Uncomment if needed
    # TODO: Add business logic for Tag Details here
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/check_txn_status', methods=['POST'])
def check_txn_status():
    xml_data, root = parse_and_log_xml("Check Transaction Status")
    # verify_signature(xml_data)  # Uncomment if needed
    # TODO: Add business logic for Check Transaction Status here
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/heartbeat', methods=['POST'])
def heartbeat():
    xml_data, root = parse_and_log_xml("Toll Plaza Heart Beat")
    # verify_signature(xml_data)  # Uncomment if needed
    # TODO: Add business logic for Heart Beat here
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/pay_response', methods=['POST'])
def pay_response():
    xml_data, root = parse_and_log_xml("ResPay")
    # verify_signature(xml_data)  # Uncomment if needed
    # TODO: Add business logic for Pay Response here
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_api.route('/api/bank/exception_response', methods=['POST'])
def exception_response():
    xml_data, root = parse_and_log_xml("Res Query Exception List")
    # verify_signature(xml_data)  # Uncomment if needed
    # TODO: Add business logic for Exception Response here
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml') 