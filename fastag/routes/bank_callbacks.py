from flask import Blueprint, request, Response
import logging
from fastag.bank_client import parse_pay_response
from lxml import etree

bank_callbacks = Blueprint('bank_callbacks', __name__)

@bank_callbacks.route('/api/bank/pay_response', methods=['POST'])
def pay_response():
    xml_data = request.data.decode('utf-8')
    logging.info(f"Received Pay Response callback: {xml_data}")
    # Parse and display RespPay XML in a neat manner
    try:
        parsed = parse_pay_response(xml_data)
        # Additionally, parse for FareType, TollFare, VehicleClass, RegNumber, etc.
        tree = etree.fromstring(xml_data.encode())
        resp = tree.find('.//Resp')
        fare_type = toll_fare = vehicle_class = reg_number = None
        if resp is not None:
            vehicle = resp.find('.//Vehicle')
            if vehicle is not None:
                vdetails = vehicle.find('.//VehicleDetails')
                if vdetails is not None:
                    for detail in vdetails.findall('Detail'):
                        if detail.attrib.get('name', '').upper() == 'VEHICLECLASS':
                            vehicle_class = detail.attrib.get('value')
                        if detail.attrib.get('name', '').upper() == 'REGNUMBER':
                            reg_number = detail.attrib.get('value')
                        if detail.attrib.get('name', '').upper() == 'COMVEHICLE':
                            com_vehicle = detail.attrib.get('value')
            ref = resp.find('.//Ref')
            if ref is not None:
                toll_fare = ref.attrib.get('TollFare')
                fare_type = ref.attrib.get('FareType')
        neat_output = [
            f"Pay Response Parsed:",
            f"  Result: {parsed.get('result')}",
            f"  Response Code: {parsed.get('respCode')}",
            f"  Plaza ID: {parsed.get('plazaId')}",
            f"  Transaction ID: {parsed.get('txnId')}",
            f"  Fare Type: {fare_type}",
            f"  Toll Fare: {toll_fare}",
            f"  Vehicle Class: {vehicle_class}",
            f"  Reg Number: {reg_number}",
        ]
        logging.info('\n'.join(neat_output))
        print('\n'.join(neat_output))
    except Exception as e:
        logging.error(f"Error parsing RespPay XML: {e}")
        print(f"Error parsing RespPay XML: {e}")
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