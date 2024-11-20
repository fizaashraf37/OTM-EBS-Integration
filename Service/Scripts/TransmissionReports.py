import requests
import logging
from Transmission import Transmission
from datetime import datetime
import base64
from Crypter import Crypter
import configparser
config = configparser.ConfigParser()
config.read('../Settings/Config.ini')
otm = config['OTM Configurations']

class TransmissionReports:

    def __del__(self):
        print("")

    def __init__(self, integration_type, from_date, to_date):
        # url to retrieve transmission reports from OTM Rest Api with status=ERROR and sent to
        # FG.FG_EBS_SHIPMENT_EVENT_OIC external system
        # external system for pickup gate out = G_EBS_SHIPMENT_EVENT_OIC_PROD
        # external system for POD = FG_EBS_SHIPMENT_EVENT_OIC
        self.json = ''
        self.transmissions = []
        crypter = Crypter()
        if integration_type == "GO_POD":
            external_system = crypter.decrypt_message(bytes(otm['ExternalSystem_GO_POD'], 'utf-8'))
        elif (integration_type == "Billing"):
            external_system = crypter.decrypt_message(bytes(otm['ExternalSystem_Billing'], 'utf-8'))
        try:
            self.print_message("Requesting Transmission Reports...")
            url = crypter.decrypt_message(bytes(otm['Rest_URI'], 'utf-8')) + \
                  "transmissionReports?q=externalSystemGid%20co%20%22{0}%22%20and%20status" \
                  "%20eq%20%22ERROR%22%20and%20isInbound%20eq%20%22false%22". \
                format(external_system)
            self.user_credentials = crypter.decrypt_message(bytes(otm['IntegrationUser'], 'utf-8'))
            # user_credentials = otm['IntegrationUser_UserName'] + ':' + otm['IntegrationUser_Password']
            encoded_u = base64.b64encode(self.user_credentials.encode()).decode()
            headers = {
                'Authorization': 'Basic %s' % encoded_u,
                'Cookie': 'JSESSIONID=TduCh-dKfzwmBJwQVnF-O1pQNpcwLpGSxIXMPiD1QiqleqRc3e3T!-1605801020; '
                          '_WL_AUTHCOOKIE_JSESSIONID=oZBHqJihQ7uAg80qMTTl '
            }

            response = requests.request("GET", url, headers=headers)
            # Get the JSON data
            if response.status_code == 200:
                self.json = response.json()
                j = self.json
                for item in j['items']:
                    transmission_id = int(item['senderTransmissionId'])
                    if not ((from_date is None) and (to_date is None)):
                        creation_date = item['createDate']['value'].replace('T', ' ')
                        creation_date = datetime.strptime(creation_date[0: creation_date.index("+")], '%Y-%m-%d %H:%M:%S')
                        if (creation_date >=from_date) and (creation_date<=to_date):
                            print("date: ", creation_date)
                            transmission = Transmission(transmission_id)
                            self.transmissions.append(transmission)
                    else:
                        status = item['status']
                        transmission = Transmission(transmission_id)
                        self.transmissions.append(transmission)
            else:
                self.print_error("Request Error: " + str(response.status_code) + " " + str(response.reason))
        except requests.exceptions.HTTPError as exc:
            self.print_error("Http Error: " + str(exc))
        except requests.exceptions.TooManyRedirects as exc:
            self.print_error("Redirect Error: " + str(exc))
            self.print_message("URL was bad, try a different one")
        except requests.exceptions.ConnectionError as exc:
            self.print_error("Error Connecting: " + str(exc))
        except requests.exceptions.Timeout as exc:
            self.print_error("Timeout Error: " + str(exc))
        except requests.exceptions.RequestException as exc:
            self.print_error("URL Request Error: " + str(exc))

    def print_details(self):
        # Navigate the JSON data using standard Python
        j = self.json
        print('itemCount=', j['count'], '\n')
        print('Items:\n')
        for item in j['items']:
            print('senderTransmissionId=', item['senderTransmissionId'])
            print('externalSystemGid=', item['externalSystemGid'])
            print('transactionCount=', item['transactionCount'])
            print('isInbound=', item['isInbound'])
            print('createDate=', item['createDate']['value'])
            print('status=', item['status'], '\n')

    def get_transmissions(self):
        for transmission in self.transmissions:
            print(transmission.transmission_id)
        return self.transmissions

    def print_transmission_ids(self):
        for transmission in self.transmissions:
            print(transmission.transmission_id)

    def print_error(self, e_message):
        print(e_message)
        logging.error(e_message)

    def print_message(self, message):
        print(message)
        logging.info(message)
