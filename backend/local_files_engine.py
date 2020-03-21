#!.venv/bin/python3

"""
Code Written by David Foran - Red Sun Information Systems Corporation

Code written in Python 3.6.9 according to PEP8 Standards. This code is
a simple set up scripts that copy your Algo QR Keys/Config files for
wireguard and transfer them into your 'escrow' folder and creating and
moving them into a folder for each user.
"""

import glob, os, shutil, re

def copy_keys(algopath, escrowpath):
    """
    This function copies all key/config files from the algo folder
    location that they autogenerate in. It will check the 'escrow folder'
    and determine whether or not a user folder exists. If not, it will
    create the folder and then it copies algo configuration and qr codes
    into each users folder
    """
    # Create lists of all the configuration / key files in algo folders
    conf_file_list = glob.glob(algopath + '*.conf')
    qr_key_list = glob.glob(algopath + '*.png')

    # Loop through all config files and add them to user folders
    for _file in conf_file_list:
        configname = get_username_from_configuration(_file)
        print('Config File Username: {}/'.format(configname))
        configfolder = os.path.join(escrowpath, configname)

        if os.path.isdir(configfolder) is True:
            print("{} found, copying!".format(configfolder))
        else:
            os.mkdir(configfolder)
            print("Folder Created: {}".format(configfolder))


        shutil.copy(_file, configfolder)
        print("{}'s config file was copied to {}".format(configname, configfolder))

    # Loop through all key files and add them to user folders
    for _key in qr_key_list:
        key_owner = get_username_from_qrcode(_key)
        print('Config File Username: {}'.format(key_owner))
        keyfolder = os.path.join(escrowpath, key_owner)

        shutil.copy(_key, keyfolder)
        print("{}'s config file was copied to {}".format(key_owner, keyfolder))

def get_username_from_configuration(string):
    """ Uses Regex to pull the user's name off of the Config file filepath """
    username = re.sub(r'((?:/home).*wireguard/)|(?:.conf)', "", string, flags=re.I)
    return username

def get_username_from_qrcode(string):
    """ Uses Regex to pull the user's name off of the QR Code filepath """
    username = re.sub(r'((?:/home).*wireguard/)|(?:.png)', "", string, flags=re.I)
    return username
