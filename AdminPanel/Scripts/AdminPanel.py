import PySimpleGUI as sg
from Scripts.Crypter import Crypter

class AppGUI:

    def __init__(self):
        self.crypt = Crypter()
        self.crypt.decrypt_config_file()
        self.gui_loop()

    def gui_loop(self):
        sg.theme('Dark')
        if self.crypt.int_status is True:
            txtcolor = 'green2'
            txt = 'Enabled'
        else:
            txtcolor = 'white'
            txt = 'Disabled'
        self.layout = [
            [sg.Frame(layout=[
                [sg.Checkbox(txt, text_color=txtcolor, size=(20, 1), default=self.crypt.int_status,
                             key='-int_status-', enable_events=True)],
            ], title='Integration Status', title_color='red', relief=sg.RELIEF_SUNKEN),
                sg.Frame(layout=[
                    [sg.Text('Username', text_color='white'), sg.Input(key='-auName-', size=(23, 1), enable_events=True,
                                                                       default_text=self.crypt.app_username),
                     sg.Text('Password', text_color='white'), sg.Input(key='-auPass-', size=(23, 1), enable_events=True,
                                                                       default_text=self.crypt.app_password)],
                ], title='Application User Credentials', title_color='red', relief=sg.RELIEF_SUNKEN)
            ],
            # [sg.Frame(layout=[
            #     [sg.Text('Username', text_color='white'), sg.Input(key='-auName-', size=(35, 1), enable_events=True,
            #                                                        default_text=self.crypt.app_username),
            #      sg.Text('Password', text_color='white'), sg.Input(key='-auPass-', size=(35, 1), enable_events=True,
            #                                                        default_text=self.crypt.app_password), ],
            # ], title='Application User Credentials', title_color='red', relief=sg.RELIEF_SUNKEN)],
            [sg.Frame(layout=[
                [sg.Frame(layout=[
                    [sg.Text('Username', text_color='white'),
                     sg.Input(key='-iuName-', size=(35, 1), enable_events=True, default_text=self.crypt.otm_username),
                     sg.Text('Password', text_color='white'),
                     sg.Input(key='-iuPass-', size=(35, 1), enable_events=True, default_text=self.crypt.otm_password)],
                ], title='Integration User Credentials', title_color='brown1', relief=sg.RELIEF_SUNKEN)],
                [sg.Frame(layout=[
                    [sg.Text('Rest Service URI            ', text_color='white'),
                     sg.Input(key='-rest_uri-', size=(70, 1), enable_events=True, default_text=self.crypt.rest_uri)],
                    [sg.Text('Command Service URI    ', text_color='white'),
                     sg.Input(key='-cmdsvc_uri-', size=(70, 1), enable_events=True,
                              default_text=self.crypt.cmdsvc_uri)],
                    [sg.Text('Transmission Service URI', text_color='white'),
                     sg.Input(key='-tsvc_uri-', size=(70, 1), enable_events=True, default_text=self.crypt.tsvc_uri),
                     ],
                ], title='OTM URLs', title_color='brown1', relief=sg.RELIEF_SUNKEN)],
                [sg.Frame(layout=[
                    [sg.Text('Namespace Alias', text_color='white'),
                     sg.Input(key='-nsp_alias-', size=(10, 1), enable_events=True, default_text=self.crypt.nsp_alias),
                     sg.Text('Namespace URI', text_color='white'),
                     sg.Input(key='-nsp_uri-', size=(49, 1), enable_events=True, default_text=self.crypt.nsp_uri)],
                ], title='Transmission Namespace', title_color='brown1', relief=sg.RELIEF_SUNKEN)],
                [sg.Frame(layout=[
                    [sg.Text('GateOut and POD External System', text_color='white'),
                     sg.Input(key='-gopod_ext-', size=(61, 1), enable_events=True, default_text=self.crypt.gopod_ext)],
                    [sg.Text('Freight Billing External System       ', text_color='white'),
                     sg.Input(key='-billing_ext-', size=(61, 1), enable_events=True, default_text=self.crypt.bill_ext)],
                ], title='External Systems', title_color='brown1', relief=sg.RELIEF_SUNKEN)],
            ], title='OTM Configurations', title_color='red', relief=sg.RELIEF_SUNKEN)],
            [sg.Frame(layout=[
                [sg.Text('Connection String            ', text_color='white'),
                 sg.Input(key='-conn_str-', size=(70, 1), enable_events=True, default_text=self.crypt.conn_str)],
            ], title='EBS Configurations', title_color='red', relief=sg.RELIEF_SUNKEN)],
            [sg.Frame(layout=[
                [sg.Text('Oracle Client Path            ', text_color='white'),
                 sg.Input(key='-client-', size=(70, 1), enable_events=True, default_text=self.crypt.client_path)],
            ], title='Library Path', title_color='red', relief=sg.RELIEF_SUNKEN)],
            [sg.Button('Save Settings')]]
        self.window = sg.Window('OTM Integration Application - Admin Panel (Test Instance)',
                                resizable=False, grab_anywhere=False).Layout(self.layout)
        while True:
            self.event, self.values = self.window.read()
            if self.event in (sg.WIN_CLOSED, 'Exit'):
                break
            elif self.event == '-int_status-':
                if self.values['-int_status-'] is True:
                    self.window['-int_status-'].update(text_color='green2')
                    self.window['-int_status-'].update(text='Enabled')
                else:
                    self.window['-int_status-'].update(text_color='white')
                    self.window['-int_status-'].update(text='Disabled')
            elif self.event == 'Save Settings':
                self.submit()
            elif self.event == 'from':
                self.window['from'].Update(disabled=False)
            elif self.event == 'to':
                print("toooo")
                self.window['to'].Update(disabled=True)
        self.window.close()

    def submit(self):
        try:
            print("int status: ", self.values['-int_status-'])
            if self.values['-int_status-'] is True:
                self.crypt.int_enabled = 'yes'
            else:
                self.crypt.int_enabled = 'no'
            self.crypt.app_username = self.values['-auName-']
            self.crypt.app_password = self.values['-auPass-']
            self.crypt.otm_username = self.values['-iuName-']
            self.crypt.otm_password = self.values['-iuPass-']
            self.crypt.rest_uri = self.values['-rest_uri-']
            self.crypt.cmdsvc_uri = self.values['-cmdsvc_uri-']
            self.crypt.tsvc_uri = self.values['-tsvc_uri-']
            self.crypt.gopod_ext = self.values['-gopod_ext-']
            self.crypt.bill_ext = self.values['-billing_ext-']
            self.crypt.conn_str = self.values['-conn_str-']
            self.crypt.nsp_alias = self.values['-nsp_alias-']
            self.crypt.nsp_uri = self.values['-nsp_uri-']
            self.crypt.client_path = self.values['-client-']
            self.crypt.save_config_settings()
        except KeyError as kerr:
            print("Invalid Key: ", kerr)
        if self.crypt.success:
            # sg.popup_notify("Settings Saved Successfully", location=(470, 300))
            sg.popup_ok("Settings Saved Successfully")
        else:
            sg.popup_ok("Settings are not Saved due to an Unexpected Error")


if __name__ == '__main__':
    AppGUI()
