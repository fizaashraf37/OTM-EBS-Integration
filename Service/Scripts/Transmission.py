import requests
from xml.etree import ElementTree
import base64
import pprint
import logging
import configparser
from Crypter import Crypter

config = configparser.ConfigParser()
config.read('../Settings/Config.ini')
otm = config['OTM Configurations']


class Transmission:
    # def __del__(self):
    #       print("deleting transmission: ", self.transmission_id)

    def __init__(self, transmission_id):
        try:
            self.initiated = False
            self.print_message("Requesting Transmission with id: " + str(transmission_id))
            self.transmission_id = transmission_id
            self.status = None
            self.processed = False
            self.transactions = []
            self.crypter = Crypter()
            url = self.crypter.decrypt_message(bytes(otm['CommandService_URI'], 'utf-8'))
            querystring = {"WSDL": ""}
            self.user_credentials = self.crypter.decrypt_message(bytes(otm['IntegrationUser'], 'utf-8'))
            self.iuser_username, self.iuser_password = self.user_credentials.split(':')
            encoded_u = base64.b64encode(self.user_credentials.encode()).decode()
            headers = {
                'content-type': "text/xml",
                'authorization': 'Basic %s' % encoded_u,
                'cache-control': "no-cache",
                'postman-token': "76eea474-914a-2da4-bcfa-7be5ab8eaad1"
            }
            self.get_transmission_status(transmission_id, url, querystring, headers)
            if self.status is None:
                self.print_message("Transmission does not exist with id: " + str(transmission_id))
            elif self.status == 'PROCESSED':
                self.print_message("Transmission Already Processed with id: " + str(transmission_id))
            else:
                self.get_transactions_xml(transmission_id, url, querystring, headers)
        except requests.exceptions.RequestException as exc:
            self.print_error("URL Request Error: " + str(exc))
            self.initiated = False

    def get_transmission_status(self, transmission_id, url, querystring, headers):
        query = "select status from i_transmission where i_transmission_no={0}".format(transmission_id)
        payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
                  "xmlns:ns1=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd\" " \
                  "xmlns:ns2=\"http://xmlns.oracle.com/apps/otm\">\r\n<env:Header>\r\n<ns1:Security>\r\n" \
                  "<ns1:UsernameToken>\r\n<ns1:Username>" + self.iuser_username + "</ns1:Username>\r\n" \
                                                                                              "<ns1:Password>" + \
                  self.iuser_password + "</ns1:Password>\r\n" \
                                                    "</ns1:UsernameToken>\r\n</ns1:Security>" \
                                                    "\r\n</env:Header>\r\n<env:Body>\r\n<xmlExport>\r\n\t<sql2xml>\r\n\t\t<Query>\r\n    \t\t" \
                                                    "<RootName>Location</RootName>\r\n    \t\t" \
                                                    "<Statement>" + query + "</Statement>\r\n\t\t" \
                                                                            "</Query>\r\n\t</sql2xml>\r\n</xmlExport>\r\n</env:Body>\r\n</env:Envelope>"
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        if response.status_code == 200:
            responseXml = ElementTree.fromstring(response.content)
            for child in responseXml.iter('Location'):
                transmission_status = child.attrib['STATUS']
                self.status = transmission_status
        else:
            self.print_error("Request Error: " + str(response.status_code) + " " + str(response.reason))

    def get_transactions_xml(self, transmission_id, url, querystring, headers):
        query = "select * from i_transaction where i_transmission_no={0}".format(transmission_id)
        payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
                  "xmlns:ns1=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd\" " \
                  "xmlns:ns2=\"http://xmlns.oracle.com/apps/otm\">\r\n<env:Header>\r\n<ns1:Security>\r\n" \
                  "<ns1:UsernameToken>\r\n" \
                  "<ns1:Username>" + self.iuser_username + "</ns1:Username>\r\n" \
                                                                       "<ns1:Password>" + \
                  self.iuser_password + "</ns1:Password>\r\n" \
                                                    "</ns1:UsernameToken>\r\n</ns1:Security>" \
                                                    "\r\n</env:Header>\r\n<env:Body>\r\n<xmlExport>\r\n\t<sql2xml>\r\n\t\t<Query>\r\n    \t\t" \
                                                    "<RootName>Location</RootName>\r\n    \t\t" \
                                                    "<Statement>" + query + "</Statement>\r\n\t\t" \
                                                                            "</Query>\r\n\t</sql2xml>\r\n</xmlExport>\r\n</env:Body>\r\n</env:Envelope>"
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        if response.status_code == 200:
            responseXml = ElementTree.fromstring(response.content)
            # the element <dbxml:TRANSACTION_SET> contains all the transactions, and each transaction is contained in
            # <location> element, the data we need from each transaction is present in XML_BLOB field in base64 format,
            # so we need to decode XML_BLOB of each transaction to get the actual data, this data is returned in xml
            # format
            for child in responseXml.iter('Location'):
                transaction_id = int(child.attrib['I_TRANSACTION_NO'])
                transaction_status = child.attrib['STATUS']
                if transaction_status == 'OUTBOUND':
                    type = child.attrib['DATA_QUERY_TYPE_GID']
                    element = child.attrib['ELEMENT_NAME']
                    xml_blob = child.attrib['XML_BLOB']
                    transaction = Transaction(transaction_id, xml_blob, type, element)
                    self.transactions.append(transaction)
            if len(self.transactions) > 0:
                self.initiated = True
            else:
                print("Invalid Transaction Found: Please Enter Transmission id with valid Transaction type")
                print("Valid Transaction types: ORDER RELEASE, INVOICE")
        else:
            self.print_error("Request Error: " + str(response.status_code) + " " + str(response.reason))

    def print_transaction_ids(self):
        for transaction in self.transactions:
            print("Transaction: ", transaction.transaction_id)

    # This function will send an inbound transmission acknowledgment as a soap message to OTM. OTM will trigger an
    # Agent on the receipt of transmission acknowledgment and update the status of transmission to processed if
    # acknowledgment status is success
    def update_transmission(self):
        try:
            transmission_id = str(self.transmission_id)
            print("Updating Transmission: " + transmission_id)

            # url = "https://otmgtm-test-a435004.otm.em3.oraclecloud.com/GC3Services/TransmissionService/call"
            url = self.crypter.decrypt_message(bytes(otm['TransmissionService_URI'], 'utf-8'))
            querystring = {"WSDL": ""}

            payload = "<env:Envelope xmlns:env=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
                      "xmlns:ns1=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd\" " \
                      "xmlns:ns2=\"http://xmlns.oracle.com/apps/otm\" xmlns:srv=\"http://xmlns.oracle.com/apps/otm/" \
                      "TransmissionService\">\r\n<env:Header>\r\n<ns1:Security>\r\n<ns1:UsernameToken>\r\n" \
                      "<ns1:Username>" + self.iuser_username + "</ns1:Username>\r\n" \
                                                                           "<ns1:Password>" + \
                      self.iuser_password + "</ns1:Password>\r\n" \
                                                        "</ns1:UsernameToken>\r\n</ns1:Security>\r\n</env:Header>\r\n<env:Body>\r\n<srv:publish>\r\n" \
                                                        "<ns2:TransmissionAck>\r\n    <ns2:EchoedTransmissionHeader>\r\n        " \
                                                        "<ns2:TransmissionHeader>\r\n            <ns2:SenderTransmissionNo>" \
                      + transmission_id + \
                      "</ns2:SenderTransmissionNo>\r\n        </ns2:TransmissionHeader>\r\n    " \
                      "</ns2:EchoedTransmissionHeader>\r\n    <ns2:TransmissionAckStatus>SUCCESS" \
                      "</ns2:TransmissionAckStatus>\r\n    <ns2:TransmissionAckReason>" \
                      "Processed by Backup System</ns2:TransmissionAckReason>\r\n" \
                      "</ns2:TransmissionAck>\r\n</srv:publish>\r\n</env:Body>\r\n</env:Envelope>\r\n"
            user_credentials = self.user_credentials
            encoded_u = base64.b64encode(user_credentials.encode()).decode()
            headers = {
                'content-type': "text/xml",
                'authorization': 'Basic %s' % encoded_u,
                'cache-control': "no-cache",
                'postman-token': "18594c93-e881-daa6-e9a3-fe7725589c36"
            }

            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            if response.status_code == 200:
                self.print_message("Transmission Status Updated Successfully")
            else:
                self.print_error("Could not update the status of transmission")
        except requests.exceptions.RequestException as exc:
            self.print_error("URL Request Error: " + str(exc))
            self.print_message("Could not update transmission")

    def print_error(self, e_message):
        print(e_message)
        logging.error(e_message)

    def print_message(self, message):
        print(message)
        logging.info(message)


class Transaction:

    # def __del__(self):
    #     print("deleting transaction: ", self.transaction_id)

    def __init__(self, transaction_id, xml_blob, type, element):
        self.transaction_id = transaction_id
        self.xml_blob = xml_blob
        self.transaction_details = base64.b64decode(xml_blob)
        self.type = type
        self.element = element
        self.dictionary = {}
        self.processed = False
        self.parsed = False

    def add_new_element(self, key, value):
        self.dictionary[key] = value

    def remove_an_element(self, key):
        try:
            self.dictionary.pop("testing")
        except KeyError:
            print("Key not found")
