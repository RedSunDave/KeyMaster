#!usr/bin/python3
"""
Code Written by David Foran - Red Sun Information Systems Corporation

Code written in Python 3.6.9 according to PEP8 Standards. GDrive API Engine
supports various functions needed to support and interact with the GDrive API v3.

Please ensure your 'client_secrets.json' file is located in your 'administrative
folder. See the README for more information.

"""
import glob, os, shutil, re

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file as oauth2file, client, tools
from datetime import datetime

import backend.database_engine as db
from backend.local_files_engine import copy_keys
from backend.gdrive_api_engine import create_gdrive_api_instance, delete_folder_permissions, create_escrow_folder, get_folder_id, synchronize_folders_to_GDrive


if __name__ == "__main__":
    """
    Generate filepaths for the Algo file locations as well as 
    the directory path where we will create folders for all the 
    users' key and config files. 
    """
    ALGO = os.getcwd() + "/algo/configs/*/wireguard/"
    ESCROW = os.getcwd() + "/escrow/"
    GDRIVE_ESCROW = "escrow"
    DRIVE = create_gdrive_api_instance()
    db.connect()

    # Check for the local 'escrow' folder which will contain folders
    # for each user with their key and config file in it
    print("Checking for the local 'escrow' folder...")
    if os.path.isdir(ESCROW) == True:
        print(ESCROW + " already exists!")
    else:
        print("'escrow' doesn't exist, creating...")
        os.mkdir(ESCROW)
        print("Folder Created: " + ESCROW)
    
    # Check for the GDrive 'escrow' folder which will contain folders
    # for each user with their key and config file in it
    folder_id = get_folder_id(DRIVE, GDRIVE_ESCROW)
    print("Checking for {} in GDrive".format(GDRIVE_ESCROW))
    if folder_id is None:
        create_escrow_folder(DRIVE, GDRIVE_ESCROW)
        print("Created Folder: {}".format(GDRIVE_ESCROW))
        delete_folder_permissions(DRIVE, GDRIVE_ESCROW)
    elif folder_id is not None:
        print("Folder '{}' already exists".format(GDRIVE_ESCROW))
        pass
    
    # Copy all keys from algo folder into local escrow
    copy_keys(ALGO, ESCROW)
    # Copy all keys from local escrow into GDrive escrow
    synchronize_folders_to_GDrive(DRIVE, ESCROW)