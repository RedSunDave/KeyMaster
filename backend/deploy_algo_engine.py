#!algo/.env/bin/python3
"""
Code Written by David Foran - Red Sun Information Systems Corporation

Code written in Python 3.6.9 according to PEP8 Standards. This code is
a pexcept script that copies your cloud key and then orchestrates the
deployment of Algo VPN into the cloud.
"""

import datetime
import time
import os
import glob
import shutil
import uuid
import pexpect

import backend.database_engine as db


def get_timestamp():
    """
    Records the timestamp in UTC format. This ensures that
    we can use the coordinated rather than local time for
    logs and deployment, making it easier for compatibility
    """
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def get_server_id():
    """
    Generates and ID string that we will use to name the servers
    """
    random_id = uuid.uuid1()
    server_id = str(random_id)
    return server_id

def get_digitalocean_cloud_token(filepath):
    """
    Grab the Cloud Token from the administrative folder
    for the algo deployment, opens and reads the token
    exporting it as 'contents'
    """
    file = open(filepath, "r")
    contents = str(file.read())
    file.close()
    return contents

def delete_old_server_folders():
    """
    This deletes the old media related to other servers in the
    algo folder. This keeps the filepaths clean so that we are
    not distributing older keys
    """
    folder_path = os.getcwd() + "/backend/algo/configs/"
    media_list = glob.glob(folder_path + '*')
    for media in media_list:
        try:
            shutil.rmtree(media)
            print("{} deleted successfully!".format(media))
        except OSError as _error:
            print("Not Deleting: {} : {}".format(media, _error.strerror))

def deploy_algo_server(api_token):
    """
    Controlling applications with pexpect is a create mechanism for
    orchestration and automation. Start by 'spawning' the algo application,
    'expect' the questions, and then 'sendline' the command that you want
    to execute. I found allowing a pause in between expect and sendline
    helps with making sure the program executes correctly.
    """

    # Clear out old server folders, keys, etc
    delete_old_server_folders()
    # Get api token before too changing directory
    print("Cloud Token: {}".format(api_token))

    os.chdir("backend/algo/")
    # Create child algo app process
    child = pexpect.spawn("./algo")

    # Provide digital ocean
    print("Choosing Provider....Digital Ocean")
    child.expect('Enter the number of your desired provider')
    time.sleep(5)
    child.sendline('1')

    # Name the algo server: algoserver datetime
    print("Naming the Algo VPN Server")
    child.expect('[algo]')
    time.sleep(5)
    algo_server_id = get_server_id()
    child.sendline(algo_server_id)

    # Do you want macOS/iOS clients to enable "Connect On Demand" when
    # connected to cellular networks?
    print("Allow macOS/iOS clients to enable connect on demand to cellphone networks")
    child.expect('[y/N]')
    time.sleep(5)
    child.sendline('y')

    # Do you want macOS/iOS clients to enable "Connect On Demand" when connected to Wi-Fi?
    print("Don't allow to connect to Wi-Fi on Demand")
    child.expect('[y/N]')
    time.sleep(5)
    child.sendline('N')

    # List the names of any trusted Wi-Fi networks where
    # macOS/iOS clients should not use "Connect On Demand"
    # print("Entering Names of any trusted networks")
    # child.expect('HomeNet,OfficeWifi,AlgoWiFi')
    # child.sendline('None')

    # Do you want to retain the keys (PKI)? (required to add
    # users in the future, but less secure)?
    print("Don't retain PKI keys")
    child.expect('[y/N]')
    time.sleep(5)
    child.sendline('N')

    # Do you want to enable DNS ad blocking on this VPN server?
    print("Enable DNS Blocking on the VPN server")
    child.expect('[y/N]')
    time.sleep(5)
    child.sendline('y')

    # Do you want each user to have their own account for SSH tunneling?
    print("Don't provide each user their own SSH Tunnel")
    child.expect('[y/N]')
    time.sleep(5)
    child.sendline('N')

    # Enter your API token. The token must have read and write permissions
    print("Entering API Token")
    child.expect('output is hidden')
    time.sleep(5)
    child.sendline(api_token)

    # Enter the number of your desired region
    print("Choosing desired region, New York")
    child.expect('Enter the number of your desired region')
    time.sleep(5)
    child.sendline("6")

    algo_server_timestamp = get_timestamp()
    print("Server {} activated on {}, finishing installation".format(algo_server_id,
                                                                     algo_server_timestamp))

    # It normally takes around 7min-10min seconds to setup a server
    # I give it 15 min just in case
    time.sleep(60*15)

    os.chdir("../..")

    # Log the deployment of the server in the database
    db.log_datetime(algo_server_id, algo_server_timestamp)
