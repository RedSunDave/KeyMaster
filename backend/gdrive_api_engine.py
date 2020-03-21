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

SCOPES = 'https://www.googleapis.com/auth/drive'
CREDENTIAL_FILE = 'administrative/client_secrets.json'
TOKEN_FILE = 'administrative/gdrive_sync_token.json'

def create_gdrive_api_instance():
    """
    Synchronizes the folder by building an instance of GDrive API
    and then connecting, reading through folders, and printing them out.
    """
    store = oauth2file.Storage(TOKEN_FILE)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CREDENTIAL_FILE, SCOPES)
        creds = tools.run_flow(flow, store)
    gdrive_instance = build('drive', 'v3', http=creds.authorize(Http()))
    return gdrive_instance

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
            pass
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
