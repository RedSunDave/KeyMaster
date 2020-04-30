#!backend/algo/.env/bin/python3
"""
Code Written by David Foran - Red Sun Information Systems Corporation

Code written in Python 3.6.9 according to PEP8 Standards. GDrive API Engine
supports various functions needed to support and interact with the GDrive API v3.

Please ensure your 'client_secrets.json' file is located in your 'administrative
folder. See the README for more information.

"""
import os
import time
import sys
import shutil

import backend.database_engine as db
from backend.keymaster_art import ART, print_keymaster_art
from backend.deploy_algo_engine import deploy_algo_server, get_digitalocean_cloud_token
from backend.local_files_engine import copy_keys
from backend.gdrive_api_engine import create_gdrive_api_instance, create_sheets_api_instance, delete_folder_permissions, create_escrow_folder, get_folder_id, synchronize_folders_to_gdrive


if __name__ == "__main__":
    # Generate filepaths for the Algo file locations as well as
    # the directory path where we will create folders for all the
    # users' key and config files.
    ALGO = os.getcwd() + "/backend/algo/configs/*/wireguard/"
    ESCROW = os.getcwd() + "/escrow/"
    CLOUD_TOKEN_PATH = os.getcwd() + "/administrative/cloud_token.txt"
    GDRIVE_ESCROW = "escrow"
    GDRIVE_MANIFEST = "manifest"
    DRIVE = create_gdrive_api_instance()
    SHEETS = create_sheets_api_instance()

    print_keymaster_art(ART)
    print("\n intializing program..... \n")
    time.sleep(3)

    print("Generating Filepaths")
    print("Algo Config filepaths: {}".format(ALGO))
    print("Cloud Token filepaths: {}".format(CLOUD_TOKEN_PATH))
    print("GDrive Escrow folder name: {}".format(GDRIVE_ESCROW))
    print("Local Escrow filepaths: {}".format(ESCROW))
    time.sleep(3)

    db.connect()
    print("Database Connected!")
    time.sleep(3)

    print("Checking for Algo Folder")
    time.sleep(3)
    if os.path.isdir('backend/algo/configs/') is True:
        print("Algo folder exists")
        time.sleep(3)
    else:
        os.chdir("backend/")
        shutil.rmtree('algo/')
        os.system('git clone https://github.com/trailofbits/algo.git')
        os.chdir("..")
        print('Edit the users in the Algo configuration file! Dont forget to setup the .env folder and install requirements. Then run "python3 distribute_keys.py" again')
        time.sleep(3)
        sys.exit(0)

"""
# This set of code needs to be fixed, the implementation to automated virtualenv doesn't work correctly.
    # print("Checking for the Algo VPN '.env' folder...")
    # time.sleep(2)
    # if os.path.isdir('backend/algo/.env') is True:
    #     print("Algo VPN '.env already exists!")
    #     os.system('source backend/algo/.env/bin/activate')
    #     time.sleep(3)
    # else:
    #     print(" Algo VPN '.env' doesn't exist, creating...")
    #     time.sleep(3)
    #     os.system('python3 -m virtualenv --python="$(command -v python3)" backend/algo/.env && \
    #               source backend/algo/.env/bin/activate && \
    #               python3 -m pip install -r backend/algo/requirements.txt && \
    #               python3 -m pip install -r requirements.txt')
    #     time.sleep(3)
"""

    # Deploy algo server
    print("Deploying new algo server (est time to completion: 15 minutes)")
    time.sleep(3)
    #Get API Token for the cloud account
    API_TOKEN = get_digitalocean_cloud_token(CLOUD_TOKEN_PATH)
    print("Acquired Cloud Key: {}".format(API_TOKEN))
    time.sleep(3)
    deploy_algo_server(API_TOKEN)

    # Check for the local 'escrow' folder which will contain folders
    # for each user with their key and config file in it
    print("Checking for the local 'escrow' folder...")
    time.sleep(3)
    if os.path.isdir(ESCROW) is True:
        print(ESCROW + " already exists!")
        time.sleep(3)
    else:
        print("'escrow' doesn't exist, creating...")
        time.sleep(3)
        os.mkdir(ESCROW)
        print("Folder Created: " + ESCROW)
        time.sleep(3)

    # Check for the GDrive 'escrow' folder which will contain folders
    # for each user with their key and config file in it
    FOLDER_ID = get_folder_id(DRIVE, GDRIVE_ESCROW)
    print("Checking for {} in GDrive".format(GDRIVE_ESCROW))
    time.sleep(3)
    if FOLDER_ID is None:
        create_escrow_folder(DRIVE, GDRIVE_ESCROW)
        print("Created Folder: {}".format(GDRIVE_ESCROW))
        time.sleep(3)
        delete_folder_permissions(DRIVE, GDRIVE_ESCROW)
    elif FOLDER_ID is not None:
        print("Folder '{}' already exists".format(GDRIVE_ESCROW))
        time.sleep(3)

    # Copy all keys from algo folder into local escrow
    copy_keys(ALGO, ESCROW)
    # Copy all keys from local escrow into GDrive escrow
    synchronize_folders_to_gdrive(DRIVE, ESCROW)
