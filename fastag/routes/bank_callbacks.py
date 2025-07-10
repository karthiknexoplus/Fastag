from flask import Blueprint, request, Response
import logging

bank_callbacks = Blueprint('bank_callbacks', __name__)

@bank_callbacks.route('/api/bank/pay_response', methods=['POST'])
def pay_response():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Pay Response callback: {xml_data}")
    # TODO: Parse XML, validate, and process the pay response as needed
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml')

@bank_callbacks.route('/api/bank/exception_response', methods=['POST'])
def exception_response():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Exception List callback: {xml_data}")
    # TODO: Parse XML, validate, and process the exception list as needed
    ack_xml = '<Ack>OK</Ack>'
    return Response(ack_xml, mimetype='application/xml') 