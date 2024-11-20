from cryptography.fernet import Fernet

import os
import configparser

configfile_name = "../Config.ini"
config = configparser.ConfigParser()
config.read(configfile_name)
try:
    app = config['Application User Credentials']
    otm = config['OTM Configurations']
    ebs = config['EBS Configurations']
    default = config['DEFAULT']
    lib = config['Libraries Path']
except KeyError as kerr:
    print("Invalid Key: ", kerr)


class Crypter:

    def __init__(self):
        self.success = False
        self.load_key_from_file = False
        self.app_username = config['app_username']
        self.app_password = config['app_password']
        self.otm_username = config['otm_username']
        self.otm_password = config['otm_password']
        self.rest_uri = config['rest_uri']
        self.cmdsvc_uri = config['cmdsvc_uri']
        self.tsvc_uri = config['tsvc_uri']
        self.gopod_ext = config['gopod_ext']
        self.bill_ext = config['bill_ext']
        self.conn_str = config['conn_str']
        try:
            self.nsp_alias = otm['namespace_alias']
            self.nsp_uri = otm['namespace_uri']
            self.client_path = lib['OracleClient']
            self.int_enabled = config['DEFAULT']['IntegrationEnabled']
            if self.int_enabled == 'yes':
                self.int_status = True
            else:
                self.int_status = False
        except KeyError as kerr:
            print("Invalid Key: ", kerr)
        except NameError as nerr:
            print("Name Error: ", nerr)

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("secret.key", "rb").read()

    def encrypt_message(self, message):
        """
        Encrypts a message
        """
        if default['Load_Encryption_Key_From_File'] == 'yes':
            key = self.load_key()
        else:
            key = config['key']
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)

        print(encrypted_message)
        return encrypted_message

    # if __name__ == "__main__":
    #     encrypt_message("encrypt this message")

    def decrypt_message(self, encrypted_message):
        """
        Decrypts an encrypted message
        """
        if default['Load_Encryption_Key_From_File'] == 'yes':
            key = self.load_key()
        else:
            key = config['key']
        f = Fernet(key)
        decrypted_message = f.decrypt(encrypted_message)

        # print(decrypted_message.decode())
        return decrypted_message.decode()

    """
    use this function to encrypt any configuration setting that is updated
    """

    def encrypt_config_file(self):
        # encrypt the updated fields
        app_user = self.encrypt_message(self.app_username + ':' + self.app_password)
        integration_user = self.encrypt_message(self.otm_username + ":" + self.otm_password)
        connectionstring = self.encrypt_message(self.conn_str)
        rest_uri = self.encrypt_message(self.rest_uri)
        commandservice_uri = self.encrypt_message(self.cmdsvc_uri)
        transmissionservice_uri = self.encrypt_message(self.tsvc_uri)
        externalsystem_go_pod = self.encrypt_message(self.gopod_ext)
        externalsystem_billing = self.encrypt_message(self.bill_ext)

        # save the ecncrypted settings in config.ini file
        config.set('Application User Credentials', "AppUser", app_user.decode("utf-8"))
        config.set('OTM Configurations', "IntegrationUser", integration_user.decode("utf-8"))
        config.set('EBS Configurations', "ConnectionString", connectionstring.decode("utf-8"))
        config.set('OTM Configurations', "Rest_URI", rest_uri.decode("utf-8"))
        config.set('OTM Configurations', "CommandService_URI", commandservice_uri.decode("utf-8"))
        config.set('OTM Configurations', "TransmissionService_URI", transmissionservice_uri.decode("utf-8"))
        config.set('OTM Configurations', "ExternalSystem_GO_POD", externalsystem_go_pod.decode("utf-8"))
        config.set('OTM Configurations', "ExternalSystem_Billing", externalsystem_billing.decode("utf-8"))

    def decrypt_config_file(self):
        try:
            decrypted = self.decrypt_message(bytes(app['AppUser'], 'utf-8'))
            self.app_username, self.app_password = decrypted.split(':')
            print("app_username: ", self.app_username, " , app_password: ", self.app_password)
            decrypted = self.decrypt_message(bytes(otm['IntegrationUser'], 'utf-8'))
            self.otm_username, self.otm_password = decrypted.split(':')
            print("otm_username: ", self.otm_username, " , otm_password: ", self.otm_password)
            self.conn_str = self.decrypt_message(bytes(ebs['ConnectionString'], 'utf-8'))
            print("connectionstring: ", self.conn_str)
            self.rest_uri = self.decrypt_message(bytes(otm['Rest_URI'], 'utf-8'))
            print("rest_uri: ", self.rest_uri)
            self.cmdsvc_uri = self.decrypt_message(bytes(otm['CommandService_URI'], 'utf-8'))
            print("commandservice_uri: ", self.cmdsvc_uri)
            self.tsvc_uri = self.decrypt_message(bytes(otm['TransmissionService_URI'], 'utf-8'))
            print("transmissionservice_uri: ", self.tsvc_uri)
            self.gopod_ext = self.decrypt_message(bytes(otm['ExternalSystem_GO_POD'], 'utf-8'))
            print("external system go_pod: ", self.gopod_ext)
            self.bill_ext = self.decrypt_message(bytes(otm['ExternalSystem_Billing'], 'utf-8'))
            print("external system billing: ", self.bill_ext)
        except KeyError as kerr:
            print("Invalid Key: ", kerr)
        except NameError as nerr:
            print("Name Error: ", nerr)

    def save_config_settings(self):
        try:
            cfgfile = open(configfile_name, "w")
            self.encrypt_config_file()
            config.set('OTM Configurations', "namespace_alias", self.nsp_alias)
            config.set('OTM Configurations', "namespace_uri", self.nsp_uri)
            config.set('Libraries Path', "OracleClient", self.client_path)
            config.set('DEFAULT', "IntegrationEnabled", self.int_enabled)
            config.write(cfgfile)
            cfgfile.close()
            self.success = True
        except KeyError as kerr:
            print("Invalid Key: ", kerr)
            self.success = False


if __name__ == "__main__":
    crypt = Crypter()
    # crypt.encrypt_config_file(configfile_name)
    crypt.decrypt_config_file()
