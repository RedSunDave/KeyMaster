#!.venv/bin/python3

"""
Code Written by David Foran - Red Sun Information Systems Corporation

Code written in Python 3.6.9 according to PEP8 Standards. GDrive API Engine
supports various functions needed to support and interact with the GDrive API v3.

In order for the code to work you do need a Credential File which can be obtained
by enabling the Drive API:

 - Drive API (https://developers.google.com/drive/api/v3/quickstart/python)

and obtaining oauth2client credentials from here:

 - https://console.developers.google.com/apis/credentials

Notes on oauth are here

 - https://developers.google.com/identity/protocols/oauth2

These credentials should be placed into the administrative folder.
"""

import glob
import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file as oauth2file, client, tools
import backend.database_engine as db

GDRIVE_SCOPES = 'https://www.googleapis.com/auth/drive'
GDRIVE_CREDENTIAL_FILE = 'administrative/client_secrets.json'
GDRIVE_TOKEN_FILE = 'administrative/gdrive_sync_token.json'
SHEETS_SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
SHEETS_CREDENTIAL_FILE = 'administrative/sheets_client_secrets.json'
SHEETS_TOKEN_FILE = 'administrative/sheets_token.json'

def create_gdrive_api_instance():
    """
    Synchronizes the folder by building an instance of GDrive API
    and then connecting, reading through folders, and printing them out.
    """
    store = oauth2file.Storage(GDRIVE_TOKEN_FILE)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(GDRIVE_CREDENTIAL_FILE, GDRIVE_SCOPES)
        creds = tools.run_flow(flow, store)
    gdrive_instance = build('drive', 'v3', http=creds.authorize(Http()))
    return gdrive_instance

def create_sheets_api_instance():
    """
    Synchronizes the folder by building an instance of GDrive API
    and then connecting, reading through folders, and printing them out.
    """
    store = oauth2file.Storage(TOKEN_FILE)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CREDENTIAL_FILE, SCOPES)
        creds = tools.run_flow(flow, store)
    sheets_api_instance = build('sheets', 'v4', http=creds.authorize(Http()))
    return sheets_api_instance

def read_spreadsheet(sheets_api_instance):
    """
    Reads a spreadsheet in the gdrive to pull information down into a manifest
    object. The manifest (basically a list of people needing vpn access) helps
    to determine deployment date of the vpn, destruction date of vpn, users, and
    their associated emails.
    """
    sheet = sheets_api_instance.spreadsheets()
    date_start = sheet.values().get(spreadsheetId='1xbW9a2ruDVMSC5t6nY7ANdPD8g7fKEI7ah_RTaLeg3c',
                                range='A2:A').execute()
    date_end = sheet.values().get(spreadsheetId='1xbW9a2ruDVMSC5t6nY7ANdPD8g7fKEI7ah_RTaLeg3c',
                                range='B2:B').execute()
    personnel = sheet.values().get(spreadsheetId='1xbW9a2ruDVMSC5t6nY7ANdPD8g7fKEI7ah_RTaLeg3c',
                                range='C2:C').execute()
    emails = sheet.values().get(spreadsheetId='1xbW9a2ruDVMSC5t6nY7ANdPD8g7fKEI7ah_RTaLeg3c',
                                range='D2:D').execute()

    date_start = date_start.get('values', [])
    date_end = date_end.get('values', [])
    personnel_list = personnel.get('values', [])
    email_list = emails.get('values', [])

    return date_start, date_end, personnel_list, email_list

def add_manifest_personnel_to_algo_config(manifest, filepath):
    """
    This uses the manifest data pulled from 'read_spreadsheets' in order to
    edit the algo configuration file in backend/algo/config.cfg to create
    deploy the appropriate users with the algo server
    """
    config_file = open("backend/algo/config.cfg", mode="r")
    string_list = config_file.readlines()
    
    delete_lines_start = get_line_number_start(filepath)
    delete_lines_end = get_line_number_end(filepath)

    del string_list[delete_lines_start:delete_lines_end]

    personnel_list = []

    for person in manifest[2]:
        personnel_list.append(person[0])

    user_list = "".join(map(lambda x: '  - '+str(x)+'\n', personnel_list))
    string_list[8] = user_list
    config_file = open("backend/algo/config.cfg", "w")
    new_config_file_contents = "".join(string_list)
    config_file.write(new_config_file_contents)
    config_file.close()

def get_line_number_end(filepath):
    """
    Grabs the last line that needs to be replaced to add users automatically
    to the configuration file. This is the line before "### Review these options"
    """
    config_file = open(filepath, mode="r")
    text_match = "### Review these options"
    num = 0
    for line in config_file:
        num += 1
        if text_match in line:
            line_number_end = num - 2

    return line_number_end

def get_line_number_start(filepath):
    """
    Grabs the first line that needs to be replaced to add users automatically
    to the configuration file. This is the line after "users:
    """
    config_file = open(filepath, mode="r")
    text_match = "users:"
    num = 0
    for line in config_file:
        num += 1
        if text_match in line:
            line_number_start = num

    return line_number_start

def read_all_folders(gdrive_instance, folder_name):
    """
    Reads all of the folders within the drive and prints them to CLI.
    """
    parent_folder_id = get_folder_id(gdrive_instance, folder_name)
    page_token = None
    while True:
        response = gdrive_instance.files().list(q="mimeType = 'application/vnd.google-apps.folder'and parents in '{}'".format(parent_folder_id),
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()

        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return response

def get_folder_id(gdrive_instance, folder_name):
    """
    This function searches for a specific folder. It takes the current
    gdrive instance and a name as arguments, and passes them to GDrive to
    verify if a folder exists.
    """
    page_token = None
    query_string = '(mimeType = \'application/vnd.google-apps.folder\') and \
                    (name = \'{}\')'.format(folder_name)
    while True:
        response = gdrive_instance.files().list(q=query_string,
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()

        for file in response.get('files', []):
            return file.get('id')

        page_token = response.get('nextPageToken', None)

        if page_token is None:
            break

def create_folder(gdrive_instance, folder_name, parent_folder):
    """
    Create a folder, 'parent_folder_id' is the id of the folder
    that we are creating a folder inside of. 'folder_name' is the
    name that we will pass to our folder. 'mimeType' is the type of
    object we are passing to be created. 'mimeType' must come before
    'parents' in the parameters.
    """
    # Retrieve ID for the parent folder
    parent_folder_id = get_folder_id(gdrive_instance, parent_folder)
    # mimeType must always come second or else the func wont work
    folder_parameters = {'name': folder_name,
                         'mimeType': 'application/vnd.google-apps.folder',
                         'parents': [parent_folder_id]
                        }

    gdrive_instance.files().create(body=folder_parameters).execute()

def create_escrow_folder(gdrive_instance, folder_name):
    """
    Create a folder, 'folder_name' is the name that we will pass to
    our folder. 'mimeType' is the type of object we are passing to
    be created. 'mimeType' must come before 'parents' in the parameters.
    Creates the folder in the main drive.
    """
    folder_parameters = {'name': folder_name,
                         'mimeType': 'application/vnd.google-apps.folder'
                        }

    gdrive_instance.files().create(body=folder_parameters).execute()

def upload_file(gdrive_instance, file_name, filepath, parent_folder):
    """
    Upload a file (file_name) to a specific folder (parent_folder)
    """
    parent_folder_id = get_folder_id(gdrive_instance, parent_folder)
    file_parameters = {'name': file_name,
                       'parents': [parent_folder_id]}
    # mimetype is usually a variable in MediaFileUpload, but was
    # not included so that it would work with pictures and text
    media = MediaFileUpload(
                filepath,
                resumable=True
                )

    gdrive_instance.files().create(body=file_parameters,
                                   media_body=media,
                                   fields='id').execute()

def delete_files(gdrive_instance, file_name, folder_name):
    """
    This folder will get all of the files within a specifice folder and delete
    them from the folder.
    """
    # example: List files
    folder_id = get_folder_id(gdrive_instance, folder_name)
    results = gdrive_instance.files().list(q="name contains '{}' and parents in '{}'".format(file_name, folder_id),
                                           pageSize=50,
                                           fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Clearing out (deleting) older files....')
        for item in items:
            print('{0} ({1})'.format(item['name'], item['id']))
            gdrive_instance.files().delete(fileId=item['id']).execute()

def callback(request_id, response, exception):
    """
    Prints out shared folder's permission id upon completion
    """
    if exception:
        print(exception)
    else:
        print('Permission ID: {}'.format(response.get('id')))

def delete_folder_permissions(gdrive_instance, folder_name):
    """
    This is a function to be applied to newly created folders prior
    to sharing them with a user. It will extract the permissionId
    for their 'domain' sharing permissions and then it will delete
    the 'domain' sharing permissions so that only the file owner
    has access to it.
    """
    folder_id = get_folder_id(gdrive_instance, folder_name)
    # Retrieve permissions
    permissions = gdrive_instance.permissions().list(fileId=folder_id).execute()
    permission_id_list = (list(x['id'] for x in permissions['permissions']))
    # permission_list = (list({x['type']: x['id']} for x in permissions['permissions']))
    print("Folder Permission ID's are: {}".format(permission_id_list))
    permission_id = permission_id_list[0]
    batch = gdrive_instance.new_batch_http_request()

    batch.add(gdrive_instance.permissions().delete(
        fileId=folder_id,
        permissionId=permission_id,
        fields='id'

    ))

    print("Folder domain sharing for folder '{}' permissions are deleted".format(folder_name))
    batch.execute()
    return

def share_folder(gdrive_instance, folder_name, email):
    """
    This function uses a folder name and email to share it with
    the user associated with the email address.
    """
    folder_id = get_folder_id(gdrive_instance, folder_name)
    batch = gdrive_instance.new_batch_http_request(callback=callback)

    user_permission = {
        'type': 'user',
        'role': 'reader',
        'emailAddress': email
    }

    batch.add(gdrive_instance.permissions().create(
        fileId=folder_id,
        body=user_permission,
        fields='id'
    ))
    print("Folder id: '{}' and folder name: '{}' shared with email address: '{}'!".format(folder_id, folder_name, email[0]))
    batch.execute()

def synchronize_folders_to_gdrive(gdrive_instance, escrowpath):
    """
    Syncronizeds all folders from local escrow folder to the gdrive folder
    """
    local_folder_list = glob.glob(escrowpath + "*")
    # gdrive_folder_list = read_all_folders(gdrive_instance, 'escrow')

    for _folder in local_folder_list:
        folder_name = os.path.basename(_folder)
        fid = get_folder_id(gdrive_instance, folder_name)
        print("Checking for {} in GDrive".format(folder_name))
        if fid is None:
            create_folder(gdrive_instance, folder_name, 'escrow')
            delete_folder_permissions(gdrive_instance, folder_name)
            print("Created Folder: {}".format(folder_name))
            print("Domain access permissions for Folder: {} removed".format(folder_name))
        elif fid is not None:
            print("Folder '{}' already exists".format(folder_name))
        file_path = _folder + "/"
        print("File Path is {}".format(file_path))

        # Clean out folder before uploading new keys
        delete_files(gdrive_instance, folder_name, folder_name)

        # Upload new QR Key file to the appropriate folder
        qr_key_path = glob.glob(file_path + "*.png")
        qr_key_name = folder_name + ".png"
        upload_file(gdrive_instance, qr_key_name, qr_key_path[0], folder_name)
        print("QR Codekey '{}' uploaded".format(qr_key_name))

        # Upload config file to the appropriate folder
        config_file_path = glob.glob(file_path + "*.conf")
        config_file_name = folder_name + ".conf"
        upload_file(gdrive_instance, config_file_name, config_file_path[0], folder_name)
        print("Config File '{}' uploaded".format(qr_key_name))

        email = db.query_username(folder_name)
        share_folder(gdrive_instance, folder_name, email)

    print("Finished GDrive Folder Synchronization")
    return
