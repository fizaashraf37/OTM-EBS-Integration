from cryptography.fernet import Fernet

import os
import configparser
configfile_name = "../Settings/Config.ini"
config = configparser.ConfigParser()
config.read(configfile_name)
app = config['Application User Credentials']
otm = config['OTM Configurations']
ebs = config['EBS Configurations']
default = config['DEFAULT']

class Crypter:

    def __init__(self):
        self.load_key_from_file = False

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("../Settings/secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("../Settings/secret.key", "rb").read()

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
    def encrypt_config_file(self, configfile_name):
        # encrypt the updated fields
        cfgfile = open(configfile_name, "w")
        app_user = self.encrypt_message(config['app_user'])
        integration_user = self.encrypt_message(config['integration_user'])
        connectionstring = self.encrypt_message(config['connectionstring'])
        rest_uri = self.encrypt_message(config['rest_uri'])
        commandservice_uri = self.encrypt_message(config['commandservice_uri'])
        transmissionservice_uri = self.encrypt_message(config['transmissionservice_uri'])
        externalsystem_go_pod = self.encrypt_message(config['externalsystem_go_pod'])
        externalsystem_billing = self.encrypt_message(config['externalsystem_billing'])

        # save the ecncrypted settings in config.ini file
        config.set('Application User Credentials', "AppUser", app_user.decode("utf-8"))
        config.set('OTM Configurations', "IntegrationUser", integration_user.decode("utf-8"))
        config.set('EBS Configurations', "ConnectionString", connectionstring.decode("utf-8"))
        config.set('OTM Configurations', "Rest_URI", rest_uri.decode("utf-8"))
        config.set('OTM Configurations', "CommandService_URI", commandservice_uri.decode("utf-8"))
        config.set('OTM Configurations', "TransmissionService_URI", transmissionservice_uri.decode("utf-8"))
        config.set('OTM Configurations', "ExternalSystem_GO_POD", externalsystem_go_pod.decode("utf-8"))
        config.set('OTM Configurations', "ExternalSystem_Billing", externalsystem_billing.decode("utf-8"))
        config.write(cfgfile)
        cfgfile.close()

    def decrypt_config_file(self):
        decrypted = self.decrypt_message(bytes(app['AppUser'], 'utf-8'))
        username, password = decrypted.split(':')
        print("app_username: ", username, " , app_password: ", password)
        decrypted = self.decrypt_message(bytes(otm['IntegrationUser'], 'utf-8'))
        username, password = decrypted.split(':')
        print("otm_username: ", username, " , otm_password: ", password)
        decrypted = self.decrypt_message(bytes(ebs['ConnectionString'], 'utf-8'))
        print("connectionstring: ", decrypted)
        decrypted = self.decrypt_message(bytes(otm['Rest_URI'], 'utf-8'))
        print("rest_uri: ", decrypted)
        decrypted = self.decrypt_message(bytes(otm['CommandService_URI'], 'utf-8'))
        print("commandservice_uri: ", decrypted)
        decrypted = self.decrypt_message(bytes(otm['TransmissionService_URI'], 'utf-8'))
        print("transmissionservice_uri: ", decrypted)
        decrypted = self.decrypt_message(bytes(otm['ExternalSystem_GO_POD'], 'utf-8'))
        print("external system go_pod: ", decrypted)
        decrypted = self.decrypt_message(bytes(otm['ExternalSystem_Billing'], 'utf-8'))
        print("external system billing: ", decrypted)

if __name__ == "__main__":
    crypt = Crypter()
    # crypt.encrypt_config_file(configfile_name)
    crypt.decrypt_config_file()