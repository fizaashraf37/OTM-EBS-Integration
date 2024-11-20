import sys
sys.path.append('Scripts')

from TransmissionReports import TransmissionReports, Transmission
from DatabaseHandler import DatabaseHandler
from xml.etree import ElementTree
import logging
from datetime import datetime

import configparser
config = configparser.ConfigParser()
config.read('../Settings/Config.ini')
otm = config['OTM Configurations']

"""
Main Integration class that pareses the retrieved data from XML and push it to EBS
"""
class Integrator:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        # current transaction under processing
        self.transaction = None
        self.type = None
        self.from_date = None
        self.to_date = None
        self.pod_timer = None
        self.billing_timer = None

    """
     Process the transaction fetched from OTM and save the data in transaction object dictionary
    """
    def parse_transaction_xml(self, transaction_xml):
        try:
            root = ElementTree.fromstring(transaction_xml)
            namespace = {otm['namespace_alias']: otm['namespace_uri']}
            # namespace = {'otm': 'http://xmlns.oracle.com/apps/otm/transmission/v6.4'}
            if self.transaction.element == "Release" and self.transaction.type == "ORDER RELEASE":
                self.parse_go_pod_transaction(root, namespace)
            elif self.transaction.element == "Billing" and self.transaction.type == "INVOICE":
                self.parse_billing_transaction(root, namespace)
        except TypeError as err:
            self.print_error("An error encountered during Mapping of XML data: " + str(err))
            self.transaction.parsed = False
            self.transaction.processed = False

    def parse_go_pod_transaction(self, root, namespace):
        currentTag = root.find("otm:ShipToLocationRef/otm:LocationRef/otm:LocationGid/otm:Gid", namespace)
        dictValue = currentTag[1].text
        self.transaction.add_new_element('SHIP_TO_LOCATION', dictValue)
        currentTag = root.find("otm:ShipFromLocationRef/otm:LocationRef/otm:LocationGid/otm:Gid", namespace)
        dictValue = currentTag[1].text
        self.transaction.add_new_element('SHIP_FROM_LOCATION', dictValue)
        currentTag = root.find("otm:ReleaseLine/otm:PackagedItemRef/otm:PackagedItemGid/otm:Gid", namespace)
        dictValue = currentTag[1].text
        self.transaction.add_new_element('PACKAGED_ITEM', dictValue)
        currentTag = root.find("otm:ReleaseGid/otm:Gid", namespace)
        dictValue = currentTag[1].text
        self.transaction.add_new_element('RELEASE_GID', dictValue)
        release_refnums = root.findall("otm:ReleaseRefnum", namespace)
        for refnum in release_refnums:
            try:
                refnum_tag = refnum[0][0][1]
                refnum_value = refnum[1]
                if refnum_tag.text == 'SHIPMENT_EVENT_ID':
                    if refnum_value.text == 'AF':
                        refnum_value.text = 'PICK_UP_GATE_OUT'
                    elif refnum_value.text == 'D1':
                        refnum_value.text = 'POD'
                    elif refnum_value.text == 'X6':
                        refnum_value.text = 'DIVERSION'
                self.transaction.add_new_element(refnum_tag.text, refnum_value.text)
            except IndexError:
                pass
            self.transaction.parsed = True

    def parse_billing_transaction(self, root, namespace):
        print("Parsing Billing Data")
        currentTag = root.find("otm:Payment/otm:PaymentHeader/otm:InvoiceGid/otm:Gid/otm:Xid", namespace)
        self.transaction.add_new_element('INVOICE_GID', currentTag.text)
        currentTag = root.find("otm:Payment/otm:PaymentHeader/otm:InvoiceDate/otm:GLogDate", namespace)
        self.transaction.add_new_element('INVOICE_DATE', currentTag.text)
        currentTag = root.find("otm:Payment/otm:PaymentHeader/otm:ServiceProviderGid/otm:Gid/otm:Xid", namespace)
        self.transaction.add_new_element('SERVICE_PROVIDER_GID', currentTag.text)
        invoice_refnums = root.findall("otm:Payment/otm:PaymentHeader/otm:InvoiceRefnum", namespace)
        for refnum in invoice_refnums:
            try:
                refnum_tag = refnum[0][0][1]
                refnum_value = refnum[1]
                refnum_id = refnum_tag.text
                if (refnum_id == 'FG_PARENT_INVOICE_AMOUNT' or refnum_id == 'FG_INVOICE_TYPE' or
                        refnum_id == 'FG_PARENT_INVOICE_INSERT_USER' or refnum_id == 'FG_SHIPMENT_ID' or
                        refnum_id == 'FG_PARENT_INVOICE_ID' or refnum_id == 'FG_PARENT_INVOICE_DATE'):
                    self.transaction.add_new_element(refnum_tag.text, refnum_value.text)
            except IndexError:
                pass
        shipment_refnums = root.findall("otm:Shipment/otm:ShipmentHeader/otm:ShipmentRefnum", namespace)
        currentTag = root.find(
            "otm:Shipment/otm:ShipmentHeader/otm:ShipmentInvoiceCostInfo/otm:TotalMatchedInvoiceCost"
            "/otm:FinancialAmount/otm:MonetaryAmount", namespace)
        self.transaction.add_new_element('SHIPMENT_INVOICE_COST', currentTag.text)
        currentTag = root.find("otm:Shipment/otm:ShipmentHeader/otm:ShipmentGid/otm:Gid/otm:Xid", namespace)
        self.transaction.add_new_element('CH_SHIPMENT_ID', currentTag.text)
        for refnum in shipment_refnums:
            try:
                refnum_tag = refnum[0][0][1]
                refnum_value = refnum[1]
                refnum_id = refnum_tag.text
                if refnum_id == 'INVENTORY_ORG_CODE':
                    self.transaction.add_new_element(refnum_tag.text, refnum_value.text)
            except IndexError:
                pass
        self.transaction.parsed = True

    """
         search for an id/value of a column in EBS staging table, if the id exists then return true
    """
    def search(self, list, id):
        for i in range(len(list)):
            if list[i][1] == id:
                return True
        return False

    """
     push the data stored in transaction dictionary to EBS staging table
    """
    def push_transaction_to_ebs_proc(self, t_dict):
        if self.transaction.element == "Release" and self.transaction.type == "ORDER RELEASE":
            self.insert_go_pod_data(t_dict)
        elif self.transaction.element == "Billing" and self.transaction.type == "INVOICE":
            self.insert_billing_data(t_dict)

    def insert_go_pod_data(self, t_dict):
        try:
            rows = [t_dict.get('SHIPMENT_NUMBER'), t_dict.get('PACKAGED_ITEM'), t_dict.get('SHIPMENT_EVENT_ID'),
                    t_dict.get('RELEASE_GID'), t_dict.get('INVENTORY_ORG_CODE'), t_dict.get('STR_MANUAL_NUMBER'),
                    t_dict.get('PDA_MANUAL_NUMBER'), t_dict.get('SUPPLIER_NUMBER'), t_dict.get('FG_ORDER_BASE_NUMBER'),
                    t_dict.get('ORDER_TYPE'), t_dict.get('FG_EE_VEHICLE_NUMBER'), t_dict.get('FG_EE_BUILTY'),
                    t_dict.get('TRANSPORTER_NAME'), t_dict.get('SHIP_FROM_LOCATION'), t_dict.get('SHIP_TO_LOCATION'),
                    t_dict.get('FG_DIVERTED_LOCATION'), t_dict.get('DIVERSION_SHIP_DATE'),
                    t_dict.get('SHIPMENT_EVENT_DATE'),
                    float(t_dict.get('SHIPMENT_EVENT_RECEIVED_WEIGHT')), t_dict.get('ATTRIBUTE_1'),
                    t_dict.get('ATTRIBUTE_2'),
                    t_dict.get('ATTRIBUTE_3'), t_dict.get('ATTRIBUTE_4'), t_dict.get('ATTRIBUTE_5'),
                    t_dict.get('CREATION_DATE'), t_dict.get('FG_SE_INSERT_USER'), t_dict.get('EBS_STATUS', None),
                    t_dict.get('FG_S_SHIP_UNIT_ID'), t_dict.get('FG_DIVERSION_TYPE'), t_dict.get('FG_IS_DIVERTED_POD'),
                    'SUCCESS']
            self.print_message("Shipment No. " + str(t_dict.get('SHIPMENT_NUMBER')) +
                               " , Ship Unit: " + t_dict.get('FG_S_SHIP_UNIT_ID') +
                               " , Event ID: " + t_dict.get('SHIPMENT_EVENT_ID'))
            self.db_handler.insert_data_procedure(self.transaction, rows)
        except TypeError as err:
            self.print_error("Type Error:" + str(err))
            self.print_message("Cannot not insert invalid data into table")
        except ValueError as err:
            self.print_error("Value Error:" + str(err))
            self.print_message("Cannot not insert invalid data into table")

    def insert_billing_data(self, t_dict):
        try:
            rows = [t_dict.get('FG_PARENT_INVOICE_ID'), t_dict.get('FG_PARENT_INVOICE_DATE'),
                    t_dict.get('FG_PARENT_INVOICE_ID'), int(float(t_dict.get('FG_PARENT_INVOICE_AMOUNT'))),
                    t_dict.get('FG_INVOICE_TYPE'), t_dict.get('H_ATTRIBUTE_1'), t_dict.get('H_ATTRIBUTE_2'),
                    t_dict.get('H_ATTRIBUTE_3'), t_dict.get('H_ATTRIBUTE_4'), t_dict.get('H_ATTRIBUTE_5'),
                    t_dict.get('P_H_CREATION_DATE'), t_dict.get('FG_PARENT_INVOICE_INSERT_USER'),
                    t_dict.get('P_H_LAST_UPDATE_DATE'), t_dict.get('P_H_LAST_UPDATED_BY'),
                    t_dict.get('P_H_LAST_UPDATE_LOGIN'), t_dict.get('CH_SHIPMENT_ID'), t_dict.get('INVOICE_GID'),
                    int(float(t_dict.get('SHIPMENT_INVOICE_COST'))), t_dict.get('CH_SHIPMENT_ID'),
                    t_dict.get('CH_ATTRIBUTE_1'), t_dict.get('CH_ATTRIBUTE_2'), t_dict.get('CH_ATTRIBUTE_3'),
                    t_dict.get('CH_ATTRIBUTE_4'), t_dict.get('CH_ATTRIBUTE_5'), t_dict.get('P_CH_CREATION_DATE'),
                    t_dict.get('FG_PARENT_INVOICE_INSERT_USER'), t_dict.get('SERVICE_PROVIDER_GID'),
                    t_dict.get('INVENTORY_ORG_CODE'),
                    'SUCCESS']
            self.print_message("Parent Invoice ID: " + str(t_dict.get('FG_PARENT_INVOICE_ID')) +
                               " , Child Invoice ID: " + t_dict.get('INVOICE_GID') +
                               " , Shipment ID: " + t_dict.get('CH_SHIPMENT_ID'))
            self.db_handler.insert_data_procedure(self.transaction, rows)
        except TypeError as err:
            self.print_error("Type Error:" + str(err))
            self.print_message("Cannot not insert invalid data into table")
        except ValueError as err:
            self.print_error("Value Error:" + str(err))
            self.print_message("Cannot not insert invalid data into table")

    """
     check if all of the transactions of a transmission have been inserted into staging table and then update
     the transmission by sending an ack transmission to OTM
    """
    def check_and_update_transmission(self, transmission):
        for transaction in transmission.transactions:
            if not transaction.processed:
                transmission.processed = False
                # send an email alert with statistics of transmissions that could not be processed, save statistics in
                # a file
                break
            else:
                self.print_message("Transaction Processed with id: " + str(transaction.transaction_id))
            transmission.processed = True
        if transmission.processed:
            # self.print_message("Updating Transmission: " + str(transmission.transmission_id))
            transmission.update_transmission()

    """
         Test the integration of one transmission
    """
    def integrate_one(self, transmission_id):
        self.print_message('---------------------------------------------------------------------'
                           'Processing Single Transaction-----------------------------------------------------------------')
        transmission = Transmission(transmission_id)
        if transmission.initiated:
            self.print_message("Processing Transmission: " + str(transmission.transmission_id))
            self.db_handler.create_connection()
            for transaction in transmission.transactions:
                # mapping will be done here for each transaction and sent to EBS staging table
                self.transaction = transaction
                self.print_message("Transaction ID: " + str(transaction.transaction_id) +
                                   ",  Transaction Type:" + str(transaction.type))
                self.parse_transaction_xml(self.transaction.transaction_details)
                if self.transaction.parsed:
                    self.push_transaction_to_ebs_proc(self.transaction.dictionary)
            self.db_handler.print_data(self.transaction.type)
            self.check_and_update_transmission(transmission)
            self.db_handler.close_connection()
        elif transmission.status == 'PROCESSED':
            self.print_message('')
        else:
            self.print_message("No transmission to process")
        self.print_message('--------------------------------------------------------------------------------'
                           'Ending-----------------------------------------------------------------------------------')
        self.print_message('')

    """
             Integrate data manually by transmission ids or date range
        """

    def integrate_many(self, transmission_ids):
        self.print_message('-----------------------------------------------------------------'
                           'Processing Manual Integration------------------------------------------------------------------')
        if len(transmission_ids) > 0:
            self.db_handler.create_connection()
            for id in transmission_ids:
                transmission = Transmission(id)
                if transmission.initiated:
                    self.print_message("Processing Transmission: " + str(transmission.transmission_id) +
                                       " with Status: " + str(transmission.status))
                    # Process each transaction of each transmission
                    for transaction in transmission.transactions:
                        self.print_message("Transaction ID: " + str(transaction.transaction_id) +
                                           ",  Transaction Type:" + str(transaction.type))
                        self.transaction = transaction
                        # Parse fields (xml elements) of current transaction and store those fields in transaction dictionary
                        self.parse_transaction_xml(self.transaction.transaction_details)
                        # Push OTM transaction fields stored in transaction dictionary to EBS staging table
                        if self.transaction.parsed:
                            self.push_transaction_to_ebs_proc(self.transaction.dictionary)
                        # maybe we need to get acknowledgment for each transaction stored in EBS
                        # after getting acknowledgment from EBS, transmission status will be updated
                        self.check_and_update_transmission(transmission)
                elif transmission.status == 'PROCESSED':
                    self.print_message('')
                self.print_message('')
            if self.transaction is not None:
                self.db_handler.print_data(self.transaction.type)
            self.db_handler.close_connection()
        else:
            self.print_message("Could not retrieve any transmission")
            self.print_message("No transmissions to process")
        self.print_message('--------------------------------------------------------------------------------'
                           'Ending-----------------------------------------------------------------------------------')
        self.print_message('')

    """
     Retrieve all non processed transmissions from OTM and store all of the transactions of that transmission
     in EBS staging table after transformation of OTM fields into EBS fields
    """

    def scheduled_integration(self):
        # Retrieve transmission reports of all transmissions which were sent to FG.FG_EBS_SHIPMENT_EVENT_OIC
        # external system and could not be processed (i.e in Error)
        transmissionReports = TransmissionReports(self.type, self.from_date, self.to_date)
        reports_count = len(transmissionReports.transmissions)
        self.print_message("Reports Count: " + str(reports_count) + '\n')
        if reports_count > 0:
            self.db_handler.create_connection()
            # Process each transmission
            for transmission in transmissionReports.transmissions:
                if transmission.initiated:
                    self.print_message("Processing Transmission: " + str(transmission.transmission_id) +
                                       " with Status: " + str(transmission.status))
                    # Process each transaction of each transmission
                    for transaction in transmission.transactions:
                        self.print_message("Transaction ID: " + str(transaction.transaction_id) +
                                           ",  Transaction Type:" + str(transaction.type))
                        self.transaction = transaction
                        # Parse fields (xml elements) of current transaction and store those fields in transaction dictionary
                        self.parse_transaction_xml(self.transaction.transaction_details)
                        # Push OTM transaction fields stored in transaction dictionary to EBS staging table
                        if self.transaction.parsed:
                            self.push_transaction_to_ebs_proc(self.transaction.dictionary)
                        # maybe we need to get acknowledgment for each transaction stored in EBS
                        # after getting acknowledgment from EBS, transmission status will be updated
                        self.check_and_update_transmission(transmission)
                elif transmission.status == 'PROCESSED':
                    self.print_message('')
                else:
                    self.print_message("Could not retrieve the transmission: " + str(transmission.transmission_id))
                self.print_message('')
            self.db_handler.print_data(self.type)
            self.db_handler.close_connection()

        else:
            self.print_message("Could not retrieve any transmission")
            self.print_message("No transmissions to process")

    def print_message(self, message):
        print(message)
        logging.info(message)

    def print_error(self, e_message):
        print(e_message)
        logging.error(e_message)


"""
Scheduler class that schedules the Integrations
"""

import sched, time

class ScriptScheduler:
    def __init__(self, timeLen):
        self.timeLen = timeLen
        self.pod_timer = timeLen
        self.billing_timer = timeLen
        self.sched = None
        self.sched_pod = None
        self.sched_billing = None
        self.running = False
        self.go_pod_running = False
        self.freight_running = False

    def set_pod_timer(self, timeLen):
        try:
            timeLen = int(timeLen)
            self.pod_timer = timeLen
            self.print_message('GateOut and POD Timer Updated -> New Time: ' + str(timeLen) + ' Seconds')
        except:
            print("Please Enter Valid Time in Seconds")

    def set_billing_timer(self, timeLen):
        try:
            timeLen = int(timeLen)
            self.billing_timer = timeLen
            self.print_message('Billing Integration Timer Updated -> New Time: ' + str(timeLen) + ' Seconds')
        except:
            print("Please Enter Valid Time in Seconds")

    def run_pod_instance(self):
        tt = time.localtime()
        self.print_message('')
        i = Integrator()
        i.pod_timer = self.pod_timer
        self.print_message("Start Time: " + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.print_message('----------------------------------------------'
                            'Executing Scheduled GateOut and POD Integration--------------------------------------------')
        i.type = "GO_POD"
        i.scheduled_integration()
        self.print_message('----------------------------------------------'
                           'GateOut and POD Integration Process Completed----------------------------------------------\n')
        self.print_message('Next Scheduled GateOut and POD integration will start in ' + str(self.pod_timer) +
                           ' seconds\n')
        # t = time.mktime(tt) + self.timeLen
        t = time.mktime(tt) + self.pod_timer
        del i
        if(self.go_pod_running):
            self.sched_pod.enterabs(t, 0, self.run_pod_instance)

    def run_billing_instance(self):
        tt = time.localtime()
        self.print_message('')
        i = Integrator()
        i.billing_timer = self.billing_timer
        self.print_message("Start Time: " + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.print_message('---------------------------------------------------------'
                            'Executing Scheduled Freight Billing Integration-------------------------------------------')
        i.type = "Billing"
        i.scheduled_integration()
        self.print_message('-------------------------------------------------------'
                           'Billing Integration Process Completed--------------------------------------------------------\n')
        self.print_message('Next scheduled Billing integration will start in ' + str(self.billing_timer) +
                           ' seconds\n')
        # t = time.mktime(tt) + self.timeLen
        t = time.mktime(tt) + self.billing_timer
        del i
        if(self.freight_running):
            self.sched_billing.enterabs(t, 0, self.run_billing_instance)

    def stop_pod(self):
        if(not self.go_pod_running):
            self.message = "GateOut and POD Integration is already stopped"
            print(self.message)
        elif(self.sched_pod.empty()):
            self.message = "Cant stop the GateOut and POD integration at this stage, " \
                           "please wait for the processing to end"
            print(self.message)
        else:
            self.message = "Stopping GateOut and POD Integration"
            self.print_message(self.message)
            for job in self.sched_pod.queue:
                self.sched_pod.cancel(job)
            self.go_pod_running = False

    def stop_billing(self):
        if(not self.freight_running):
            self.message = "Billing Integration is already stopped"
            print(self.message)
        elif(self.sched_billing.empty()):
            self.message = "Cant stop the billing integration at this stage, " \
                           "please wait for the processing to end"
            print(self.message)
        else:
            self.message = "Stopping Freight Billing Integration"
            self.print_message(self.message)
            for job in self.sched_billing.queue:
                self.sched_billing.cancel(job)
            self.freight_running = False

    def schedule_pod(self):
        if (self.go_pod_running):
            self.message = "GateOut and POD Integration is already running"
            print(self.message)
        else:
            if ((self.sched_pod is not None) and (self.sched_pod.empty() is False)):
                self.message = "Waiting for queue to empty"
                self.print_message(self.message)
                self.go_pod_running = True
            else:
                self.go_pod_running = True
                self.sched_pod = sched.scheduler(time.time, time.sleep)
                tt = time.localtime()
                # t = time.mktime(tt) + (6 - tt.tm_min) * self.timeLen
                t = time.mktime(tt) + (6 - tt.tm_min) * self.pod_timer
                self.print_message("Scheduling...")
                self.sched_pod.enterabs(t, 0, self.run_pod_instance)
                self.sched_pod.run(blocking=True)  # Run all scheduled events

    def schedule_billing(self):
        if (self.freight_running):
            self.message = "Billing Integration is already running"
            print(self.message)
        else:
            if ((self.sched_billing is not None) and (self.sched_billing.empty() is False)):
                self.message = "Waiting for queue to empty"
                self.print_message(self.message)
                self.freight_running = True
            else:
                self.freight_running = True
                self.sched_billing = sched.scheduler(time.time, time.sleep)
                tt = time.localtime()
                # t = time.mktime(tt) + (6 - tt.tm_min) * self.timeLen
                t = time.mktime(tt) + (6 - tt.tm_min) * self.billing_timer
                self.print_message("Scheduling...")
                self.sched_billing.enterabs(t, 0, self.run_billing_instance)
                self.sched_billing.run(blocking=True)  # Run all scheduled events

    def resume_scheduler(self):
        tt = time.localtime()
        t = time.mktime(tt) + (6 - tt.tm_min) * self.timeLen
        self.sched.enterabs(t, 0, self.run_instance)

    def print_message(self, message):
        print(message)
        logging.info(message)

