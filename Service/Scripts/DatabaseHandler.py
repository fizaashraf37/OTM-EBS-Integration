import cx_Oracle
import logging
import sys
from Crypter import Crypter
import configparser
config = configparser.ConfigParser()
config.read('../Settings/Config.ini')
ebs = config['EBS Configurations']

class DatabaseHandler:
    """
     connstr = 'user/password@server:1521/orcl'
    "server" is the server, or the IP address if you want.
    "1521" is the port that the database is listening on.
    "orcl" is the name of the instance (or database service).
    """

    def __init__(self):
        self.conn = None
        self.cursor = None
        crypt = Crypter()
        decrypted = crypt.decrypt_message(bytes(ebs['ConnectionString'], 'utf-8'))
        self.conn_string = decrypted
        self.rows_inserted = 0

    def create_connection(self):
        try:
            self.print_message("Establishing Database Connection...")
            # self.conn = cx_Oracle.connect("hr", "oracle", "192.168.0.106/orcl")
            self.conn = cx_Oracle.connect(self.conn_string)
            self.cursor = self.conn.cursor()
        except cx_Oracle.DatabaseError as exc:
            err, = exc.args
            self.print_error("Oracle-Error-Code:" + str(err.code))
            self.print_error("Oracle-Error-Message:" + str(err.message))

    def close_connection(self):
        self.rows_inserted = 0
        if self.conn is not None:
            self.print_message("Closing Database Connection...")
            self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None

    def retrieve_data(self, query, conditions):
        try:
            if self.conn is not None:
                self.cursor.execute(query, conditions)
                value = self.cursor.fetchall()
                return value
            else:
                self.print_message("Cannot retrieve data from database: Connection not Established")
                return None
        except cx_Oracle.DatabaseError as exc:
            err, = exc.args
            self.print_error("Oracle-Error-Code:" + str(err.code))
            self.print_error("Oracle-Error-Message:" + str(err.message))
        except AttributeError as atr:
            self.print_error("Attribute Error:" + str(atr))
            self.print_message("Could not retrieve data")

    def insert_data(self, statement, rows):
        try:
            if self.conn is not None:
                self.cursor.bindarraysize = 2
                self.cursor.setinputsizes(int, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
                                          50,
                                          50)
                self.cursor.executemany(statement, rows)
                self.conn.commit()
            else:
                self.print_message("Cannot insert data into database table: Connection not Established")
        except cx_Oracle.DatabaseError as exc:
            err, = exc.args
            self.print_error("Oracle-Error-Code:" + str(err.code))
            self.print_error("Oracle-Error-Message:" + str(err.message))
        except AttributeError as atr:
            self.print_error("Attribute Error:" + str(atr))
            self.print_message("Could not insert data")

    def insert_data_procedure(self, transaction, rows):
        try:
            if self.conn is not None:
                self.print_message("Inserting data into table")
                if transaction.type == "ORDER RELEASE":
                    self.cursor.callproc('apps.CUST_OTM_INT_PROCESS_P', rows)
                elif transaction.type == "INVOICE":
                    self.cursor.callproc('apps.CUST_OTM_INT_INVOICE_ALL_P', rows)
                if transaction is not None:
                    transaction.processed = True
                self.rows_inserted += 1
            else:
                self.print_message("Cannot insert data into database table: Connection not Established")
        except cx_Oracle.DatabaseError as exc:
            err, = exc.args
            self.print_error("Oracle-Error-Code:" + str(err.code))
            self.print_error("Oracle-Error-Message:" + str(err.message))
            if transaction is not None:
                transaction.processed = False
        except AttributeError as atr:
            self.print_error("Attribute Error:" + str(atr))
            self.print_message("Could not insert data")
            if transaction is not None:
                transaction.processed = False
            self.rows_inserted -= 1

    def print_line(self):
        print('-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '-----------------------------------------------------------------------------------------------------------'
            '----------------------------------------------------------------------------------', file=sys.__stdout__)

    def print_message(self, message):
        print(message)
        logging.info(message)

    def print_error(self, e_message):
        print(e_message)
        logging.error(e_message)

    def print_data(self, transaction_type):
        try:
            if self.conn is not None:
                if transaction_type == "ORDER RELEASE" or transaction_type == "GO_POD":
                    sql = 'SELECT * FROM (select * from apps.cust_otm_process_t ORDER BY transaction_id DESC) ' \
                           'cust_otm_process_t_view WHERE rownum <= :r ORDER BY rownum DESC';
                elif transaction_type == "INVOICE" or transaction_type == "Billing":
                    sql = 'SELECT * FROM (select * from apps.cust_otm_invoice_lines_t ORDER BY creation_date DESC) ' \
                          'cust_otm_invoice_lines_t_view WHERE rownum <= :r ORDER BY rownum';
                condition = {'r': self.rows_inserted}
                column_length = [20, 20, 20, 20, 20, 20, 20, 20, 20, 12, 15, 12, 45, 20, 25, 25, 20, 20, 20, 12, 20, 20,
                                 20, 20, 20, 20, 20, 20, 20, 20, 25, 20, 20, 20, 20, 25, 20, 20, 20, 20]
                statement = self.cursor.execute(sql, condition)
                col_names = [row[0] for row in self.cursor.description]
                if self.rows_inserted <= 0:
                    self.print_message('No new record inserted')
                else:
                    self.print_message('No of records inserted: ' + str(self.rows_inserted))
                    self.print_line()
                    for i in range(len(col_names)):
                        print(col_names[i].ljust(column_length[i]), '  |  ', end='', file=sys.__stdout__)
                    print('', file=sys.__stdout__)
                    self.print_line()
                    for row in statement:
                        for i in range(len(row)):
                            print(str(row[i]).ljust(column_length[i]), '  |  ', end='', file=sys.__stdout__)
                        print('', file=sys.__stdout__)
                    self.print_line()
            else:
                self.print_message("Cannot print data: Connection not Established")
        except cx_Oracle.DatabaseError as exc:
            err, = exc.args
            self.print_error("Oracle-Error-Code:" + str(err.code))
            self.print_error("Oracle-Error-Message:" + str(err.message))
        except AttributeError as atr:
            self.print_error("Attribute Error:" + str(atr))
            self.print_message("Could not print data")
        # finally:
        #     cursor.close()
        #     conn.close()

    """
    create_connection()
    query = "insert into cx_ebs_int_test(SHIPMENT_NUMBER, INVENTORY_ITEM_ID, EVENT_ID, OTM_ORDER_NUMBER, " \
            "INVENTORY_ORG_CODE,STR_MANUAL_NUMBER, PDA_MANUAL_NUMBER, ERP_ORDER_NUMBER, ORDER_TYPE, VEHICLE_NUM, " \
            "BUILTY_NUM, TRANSPORTER_NAME,SUPPLY_SOURCE, DESTINATION, DIVERSION_DEST_CODE, EVENT_DATE, WEIGHT_MTN, " \
            "CREATED_BY, SHIP_UNIT, DIVERSION_TYPE,IS_DIVERTED_POD) values (:1, :2, :3, :4, :5, :6, :7, :8, :9, " \
            ":10, :11, :12, :13, :14, :15, :16, :17, :18, :19, :20, :21)"
    rows = [(39925, 'CAN_80888', 'NN', 'SGD-1319-006', 'FFM', 'NN', 'NN', 'SGD-1319', 'WHP', 'AS11', '11',
                 'GAMZAN ENTERPRISES CARRIAGE CONTRACTOR', 'PFL_PLANT', 'SARGODHA-WH_511801', 'NN', '20200121010204', 
                 '0', 'FG.IMTIAZ_AHMED', '38378', 'NN', 'NN'), (98799, 'NP_80438', 'NN', 'REL-234-003', 'FFM', 'NN', 
                 'NN', 'REL-234', 'WHP', 'LE-1234-12', '4672', 'GAMZAN ENTERPRISES CARRIAGE CONTRACTOR', 'PFL_PLANT', 
                 'SARGODHA-WH_511801', 'NN', '20200121010204', '0', 'FG.FIZA_ASHRAF', '42133', 'NN', 'NN')]
    insert_data(query, rows)
    print_data()
    close_connection()
    """
