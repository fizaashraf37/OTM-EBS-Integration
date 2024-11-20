import configparser

config = configparser.ConfigParser()
config.read('../Settings/Config.ini')
app = config['Application User Credentials']
library = config['Libraries Path']

import sys, os
sys.path.append('Scripts')
if 'NEW_PATH' not in os.environ:
    os.environ['LD_LIBRARY_PATH'] = library['OracleClient'] + '/lib'
    os.environ['ORACLE_HOME'] = library['OracleClient']
    os.environ['NEW_PATH'] = ''
    try:
        myapp = sys.executable
        os.execl(myapp, myapp, *sys.argv)
    except Exception as exc:
        print('Failed re-exec:', exc)
        sys.exit(1)

import threading
import duallog
import logging
import datetime
import logging.handlers
from Integrator import ScriptScheduler, Integrator
from Crypter import Crypter
from datetime import datetime
import PySimpleGUI as sg
import base64

# with open("../Images/icon.png", "rb") as img_file:
#     BASE64_ICON = base64.b64encode(img_file.read())
# print(BASE64_ICON)

BASE64_ICON = b'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'

""" 
-----------------------------------------------------------------------------------------------------------------------
Main GUI Class that handles all of the functions performed on button clicks and validates all user inputs 
"""


class AppGUI:

    def __init__(self):
        self.running = True
        duallog.setup('./logs/app_logs')
        self.scheduler = ScriptScheduler(300)
        self.integrator = Integrator()
        self.test_thread = None
        self.sched_pod_thread = None
        self.sched_billing_thread = None
        self.manual_thread = None
        self.gui()
        self.gui_loop()

# gui function creates the gui of the application's main window
    def gui(self):
        sg.theme('DarkBlue')
        # Layout of test integration tab
        tab1_layout = [
            [sg.Text('Input a Valid Transmission Number', text_color='white')],
            [sg.Input(key='-TransID-', enable_events=True)],
            [sg.RButton('Run', key='TestInt')]
        ]
        # Layout of manual integration tab
        tab2_layout = [
            [sg.Text('Enter Valid Transmission ids as a Comma Separated List', text_color='white')],
            [sg.Input(key='-TransList-', size=(108, 1), enable_events=True)],
            [sg.Frame(layout=[
                [sg.T('Enter Date and Time Range'), sg.T('                                           '
                                                         '                                                   '
                                                         '              Select Integration Type'),
                 ],
                [sg.T('From: '), sg.In('', size=(20, 1), key='-FROM-', enable_events=False),
                 sg.CalendarButton('Choose Date', target='-FROM-', key='from', location=(150,250)),
                 sg.T('To: '), sg.In('', size=(20, 1), key='-TO-', enable_events=False),
                 sg.CalendarButton('Choose Date', target='-TO-', key='to', location=(450,250)),
                 sg.InputCombo(values=['GateOut and POD', 'Freight Billing'],
                               default_value='GateOut and POD', size=(16, 1), key='-INT_TYPE-')
                 ],
            ], title='OR', title_color='red', relief=sg.RELIEF_SUNKEN)
            ],
            [sg.RButton('Run', key='ManualInt')],
        ]
        # Layout of scheduled integration sub tab (GateOut and POD)
        tab3_layout = [
            [sg.Text('Schedule GateOut and POD Integration')],
            [sg.RButton('Start Integration', key='-GO_POD_Start-'),
             sg.RButton('Stop Integration', key='-GO_POD_Stop-'), sg.Text('                                 ')],
            [sg.Frame(layout=[
                [sg.Input('300', size=(10, 1), key='-PodTimer-', enable_events=True), sg.T('Seconds'),
                 ],
                [sg.Button('Set', key='-set_pod_timer')],
            ], title='Set Scheduler Time', title_color='white', relief=sg.RELIEF_SUNKEN)]
        ]
        # Layout of scheduled integration sub tab (Freight Billing)
        tab4_layout = [
            [sg.Text('Schedule Billing Integration')],
            [sg.RButton('Start Integration', key='-Billing_Start-'),
             sg.RButton('Stop Integration', key='-Billing_Stop-')],
            [sg.Frame(layout=[
                [sg.Input('300', size=(10, 1), key='-BillingTimer-', enable_events=True), sg.T('Seconds'),
                 ],
                [sg.Button('Set', key='-set_billing_timer')],
            ], title='Set Scheduler Time', title_color='white', relief=sg.RELIEF_SUNKEN)]
        ]
        # Layout of scheduled integration tab
        tab5_layout = [
            [sg.TabGroup([[sg.Tab('GateOut and POD', tab3_layout),
                           sg.Tab('Freight Billing', tab4_layout),
                           ]]),
             ]
        ]
        # Layout of main window
        self.layout = [
            [sg.TabGroup(
                [[sg.Tab('Process Single Transaction', tab1_layout, tooltip='Test One Transmission Processing'),
                  sg.Tab('Process Multiple Transactions', tab2_layout, tooltip='Manually Integrate the Data'),
                  sg.Tab('Scheduled', tab5_layout,
                         tooltip='Schedule the Integration to Process all Transactions')
                  ]])
            ],
            [sg.Output(size=(105, 14), key='-OUTPUT-')],
            [sg.Button('Clear'), sg.Button('Exit')]]

        self.window = sg.Window('OTM Integration Application (Test Instance)', resizable=True, disable_close=True,
                                grab_anywhere=False).Layout(self.layout)

# gui_loop function checks for the events on GUI elements continuously until the application is exited
    def gui_loop(self):
        while self.running:
            self.event, self.values = self.window.read()

            # if user clicks the exit button then display a confirm window
            if self.event in (sg.WIN_CLOSED, 'Exit'):
                if self.scheduler.go_pod_running or self.scheduler.freight_running:
                    confirm = sg.popup_yes_no('An integration is still running. Closing the application will stop'
                                              ' the integration. Do you wish to continue？', title='Warning')
                else:
                    confirm = sg.popup_yes_no('Are you sure you wish to exit？', title='Confirm')
                # if user clicks the yes button on confirm window then stop all the integrations and
                # close the application
                if confirm is 'Yes':
                    sg.PrintClose()
                    self.stop_pod()
                    self.stop_billing()
                    self.running = False
                    self.window.close()
                    break
            # perform actions on button clicks
            elif self.event == 'TestInt':
                self.start_test_thread()
            elif self.event == 'ManualInt':
                self.start_manual_thread()
            elif self.event == '-GO_POD_Start-':
                self.start_sched_pod_thread()
            elif self.event == '-GO_POD_Stop-':
                self.stop_pod()
            elif self.event == '-Billing_Start-':
                self.start_sched_billing_thread()
            elif self.event == '-Billing_Stop-':
                self.stop_billing()
            elif self.event == '-set_pod_timer':
                self.scheduler.set_pod_timer(self.values['-PodTimer-'])
            elif self.event == '-set_billing_timer':
                self.scheduler.set_billing_timer(self.values['-BillingTimer-'])
            elif self.event == 'Clear':
                self.clear_output()
            # perform validations on all input elements
            elif self.event == '-TransID-' and self.values['-TransID-']:
                try:
                    int(self.values['-TransID-'])
                except:
                    if len(self.values['-TransID-']) == 1 and self.values['-TransID-'][0] == '-':
                        continue
                    self.window['-TransID-'].update(self.values['-TransID-'][:-1])
            elif self.event == '-PodTimer-' and self.values['-PodTimer-']:
                try:
                    int(self.values['-PodTimer-'])
                except:
                    if len(self.values['-PodTimer-']) == 1 and self.values['-PodTimer-'][0] == '-':
                        continue
                    self.window['-PodTimer-'].update(self.values['-PodTimer-'][:-1])
            elif self.event == '-BillingTimer-' and self.values['-BillingTimer-']:
                try:
                    int(self.values['-BillingTimer-'])
                except:
                    if len(self.values['-BillingTimer-']) == 1 and self.values['-BillingTimer-'][0] == '-':
                        continue
                    self.window['-BillingTimer-'].update(self.values['-BillingTimer-'][:-1])
            elif self.event == '-FROM-' and self.values['-FROM-'] and self.values['-FROM-'][-1] not in (
                    '0123456789-: '):
                self.window['-FROM-'].update(self.values['-FROM-'][:-1])
            elif self.event == '-TO-' and self.values['-TO-'] and self.values['-TO-'][-1] not in ('0123456789-: '):
                self.window['-TO-'].update(self.values['-TO-'][:-1])
        self.window.close()

# clear_output function clears the logs from output window
    def clear_output(self):
        self.window['-OUTPUT-'].update('')

# test_one_transmission function processes a single transmission by taking the transmission id that is entered by
# the user in Test Integration tab
    def test_one_transmission(self):
        try:
            if self.values['-TransID-'] == '':
                print("Please Enter a Transmission Number for Testing!")
            elif int(self.values['-TransID-']) > 0:
                self.integrator.integrate_one(int(self.values['-TransID-']))
                self.window.Refresh()
            else:
                print("Please Enter a Valid Transmission Number!")
        except ValueError:
            print("Please Enter a Valid Transmission Number!")

# manual_integration function processes the transmission by taking their transmission ids that are entered by
# the user in Manual Integration tab. If user does not enters any transmission ids then date_based_manual_integration
# function is called, which checks if the user has entered any date range and then processes the transmissions by
# their creation dates
    def manual_integration(self):
        valid_ids = 0
        if not (self.values['-TransList-'] == ''):
            try:
                input = self.values['-TransList-'].replace(" ", "")
                transmission_ids = input.split(",")
                for id in transmission_ids:
                    if (int(id) > 0):
                        valid_ids += 1
                if valid_ids != len(transmission_ids):
                    print("Please Enter Valid Transmission Ids: Do not Enter Negative Values")
                else:
                    print("Starting Manual Integration")
                    if not (self.values['-FROM-'] == '' and self.values['-TO-'] == ''):
                        print("Integrating from provided transmission ids, dates will be ignored. If you want to "
                              "integrate using date range, then do not enter any transmission ids.")
                    self.integrator.integrate_many(transmission_ids)
            except ValueError:
                print("Please Enter Valid Transmission Ids")
        else:
            self.date_based_manual_integration()

# date_based_manual_integration function validates the date range entered by the user and calls the
# start_date_based_integration function if validation is successful
    def date_based_manual_integration(self):
        if not (self.values['-FROM-'] == '' and self.values['-TO-'] == ''):
            if self.values['-FROM-'] == '' or self.values['-TO-'] == '':
                print("Please enter both dates, or do not enter any date")
            else:
                try:
                    from_date = datetime.strptime(self.values['-FROM-'], '%Y-%m-%d %H:%M:%S')
                    to_date = datetime.strptime(self.values['-TO-'], '%Y-%m-%d %H:%M:%S')
                    if (from_date >= to_date):
                        print("FROM Date cannot be greater than or equal to TO Date")
                    else:
                        self.integrator.from_date = from_date
                        self.integrator.to_date = to_date
                        self.start_date_based_integration(self.values['-INT_TYPE-'])
                except ValueError:
                    print("Invalid date format - Please enter dates in valid format: yyyy-mm-dd hh:mm:ss")

# start_date_based_integration function processes the transmissions that were created on specific dates. User enters
# the date range by providing from and to dates and only those transmissions are processed that fall under this range
    def start_date_based_integration(self, integration_type):
        if not (integration_type == "GateOut and POD" or integration_type == "Freight Billing"):
            print("Invalid Integration Type")
        else:
            if integration_type == 'GateOut and POD':
                self.integrator.type = "GO_POD"
                self.print_message(
                    "------------------------------------------------------"
                    "Starting Date Based GateOut and POD Integration"
                    "------------------------------------------------------")
            elif integration_type == 'Freight Billing':
                self.print_message(
                    "-------------------------------------------------------"
                    "-------Starting Date Based Billing integration--------"
                    "-------------------------------------------------------")
                self.integrator.type = "Billing"
            self.integrator.scheduled_integration()
            self.print_message(
                "-------------------------------------------------------"
                "-------------------------------Ending-----------------------------"
                "-------------------------------------------------------")

# start_pod function starts the scheduled GateOut and POD integration
    def start_pod(self):
        # sg.Print('GateOut and POD Integration Started', size=(20, 5),
        #          do_not_reroute_stdout=True, no_button=True)
        self.print_message("\nStarting GateOut and POD Integration")
        self.scheduler.schedule_pod()
        self.window.Refresh()
        # sg.PrintClose()

# start_billing function starts the scheduled Freight Billing integration
    def start_billing(self):
        # sg.Print('Billing Integration Started', size=(20, 5),
        #          do_not_reroute_stdout=True, no_button=True)
        self.print_message("\nStarting Freight Billing Integration")
        self.scheduler.schedule_billing()
        self.window.Refresh()
        # sg.PrintClose()

# start_test_thread function starts a separate thread to process a single transmission
    def start_test_thread(self):
        if (self.scheduler.freight_running or self.scheduler.go_pod_running):
            print("A scheduled job is already running, you can test the integration after scheduling")
        elif ((self.manual_thread is not None) and (self.manual_thread.is_alive())):
            print("Please wait for the manual integration to end")
        else:
            if (self.test_thread is not None) and (self.test_thread.is_alive()):
                print("Processing previously entered transmission, please wait for the processing to end")
            else:
                self.test_thread = threading.Thread(target=self.test_one_transmission)
                self.test_thread.daemon = True
                self.test_thread.start()

# start_manual_thread function starts a separate thread to process multiple transmissions
    def start_manual_thread(self):
        if (self.scheduler.freight_running or self.scheduler.go_pod_running):
            print("A scheduled job is already running, you can start manual integration after scheduling")
        elif ((self.test_thread is not None) and (self.test_thread.is_alive())):
            print("Please wait for the test integration to end")
        else:
            if ((self.manual_thread is not None) and (self.manual_thread.is_alive())):
                print("Processing previously started integration, please wait for the processing to end")
            else:
                self.manual_thread = threading.Thread(target=self.manual_integration)
                self.manual_thread.daemon = True
                self.manual_thread.start()

# start_sched_pod_thread function starts a separate thread for scheduling GateOut and POD integration.
    def start_sched_pod_thread(self):
        if ((self.test_thread is not None) and (self.test_thread.is_alive())):
            print("Please wait for the test integration to end")
        elif ((self.manual_thread is not None) and (self.manual_thread.is_alive())):
            print("Please wait for the manual integration to end")
        elif (self.scheduler.go_pod_running):
            print("GateOut and POD Integration is already running")
        else:
            if ((self.sched_pod_thread is not None) and (self.sched_pod_thread.is_alive())):
                print("Please wait for the current running thread to stop")
            else:
                self.sched_pod_thread = threading.Thread(target=self.start_pod)
                self.sched_pod_thread.daemon = True
                self.sched_pod_thread.start()

# start_sched_billing_thread function starts a separate thread for scheduling Freight Billing integration.
    def start_sched_billing_thread(self):
        if ((self.test_thread is not None) and (self.test_thread.is_alive())):
            print("Please wait for the test integration to end")
        elif ((self.manual_thread is not None) and (self.manual_thread.is_alive())):
            print("Please wait for the manual integration to end")
        elif (self.scheduler.freight_running):
            print("Billing Integration is already running")
        else:
            if ((self.sched_billing_thread is not None) and (self.sched_billing_thread.is_alive())):
                print("Please wait for the current running thread to stop")
            else:
                self.sched_billing_thread = threading.Thread(target=self.start_billing)
                self.sched_billing_thread.daemon = True
                self.sched_billing_thread.start()

# stop_pod function stops the scheduled GateOut and POD integration.
    def stop_pod(self):
        if (self.scheduler.go_pod_running):
            self.scheduler.stop_pod()
        else:
            self.print_message("GateOut and POD integration is already stopped")
        self.window.Refresh()

# stop_billing function stops the scheduled Freight Billing integration.
    def stop_billing(self):
        if (self.scheduler.freight_running):
            self.scheduler.stop_billing()
        else:
            self.print_message("Billing integration is already stopped")
        self.window.Refresh()

# print_message function prints the log message to the output window and also save these logs to a
# log file in logs folder
    def print_message(self, message):
        print(message)
        logging.info(message)


""" 
-----------------------------------------------------------------------------------------------------------------------
User Login Class that displays the user login window and handles actions performed on that window. 
It also stores the session logs in a log file.    
"""

class UserLogin:

    def __init__(self):
        self.authenticated = False
        self.logger = None
        self.filehandler = None
        self.sessions_log('./logs/session_logs/')
        self.gui()
        self.gui_loop()

# gui function creates the gui of login window which is displayed at the start of the application
    def gui(self):
        sg.theme('DarkBlue')

        self.layout = [
            [sg.Text('Please Login to start the application', text_color='white')],
            [sg.Text('Username', text_color='white'), sg.Input(key='-username-', size=(20, 1), enable_events=True)],
            [sg.Text('Password', text_color='white'),
             sg.Input(key='-password-', size=(20, 1), enable_events=True, password_char='*')],
            [sg.RButton('Login', key='login')]
        ]
        self.window = sg.Window('OTM Integration Application', resizable=False,
                                grab_anywhere=False, size=(400, 200)).Layout(self.layout)

# gui_loop function checks for the events on GUI elements continuously until the user is not authenticated
    def gui_loop(self):
        while (not self.authenticated):
            self.event, self.values = self.window.read()
            # print(self.button, self.values)

            if self.event in (sg.WIN_CLOSED, 'Exit'):
                break
            elif self.event == 'login':
                self.login()
        self.window.close()

# login function validates the user inputs and performs user authentication. once the user is authenticated
# and integration is enabled, the main gui window is opened
    def login(self):
        crypt = Crypter()
        decrypted = crypt.decrypt_message(bytes(app['AppUser'], 'utf-8'))
        username, password = decrypted.split(':')
        if self.values['-username-'] == username and self.values['-password-'] == password:
            logging.info("Authentication Successful")
            if config['DEFAULT']['IntegrationEnabled'] == 'yes':
                self.authenticated = True
                self.window.close()
                if (self.logger is not None) and (self.filehandler is not None):
                    self.logger.removeHandler(self.filehandler)
                AppGUI()
            else:
                message = 'Application cannot be started: \n' + 'The integration is disabled. ' \
                                                                'Please ask the admin to enable the integration first.'
                sg.popup(message, title='Warning')
                logging.info(message)
        else:
            logging.warning("Invalid username or password")
            sg.popup('Invalid username or password', title='Warning')

# sessions_log function writes the user sessions log in a log file
    def sessions_log(self, logdir='log'):
        # Create the root logger.
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # Validate the given directory.
        logdir = os.path.normpath(logdir)

        # Create a folder for the logfiles.
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        # Construct the logfile name.
        t = datetime.now()
        logfile = 'sessions.log'
        logfile = os.path.join(logdir, logfile)

        # Set up logging to the logfile.
        self.filehandler = logging.handlers.RotatingFileHandler(
            filename=logfile,
            mode='w',
            maxBytes=10 * 1024 * 1024)
        self.filehandler.setLevel(logging.INFO)
        fileformatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s: %(message)s')
        self.filehandler.setFormatter(fileformatter)
        self.logger.addHandler(self.filehandler)

# main function which initiates the UserLogin() class and a login window is displayed
if __name__ == '__main__':
    # AppGUI()
    UserLogin()
