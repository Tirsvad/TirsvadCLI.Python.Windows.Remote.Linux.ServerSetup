"""
Constants is defined here
"""

import os

# Locale path
BASE_PATH = f"{os.path.dirname(os.path.realpath(__file__))}{os.path.sep}"
APP_FILES_PATH = f"{BASE_PATH}app_files{os.path.sep}"
INSTANCE_PATH = f"{BASE_PATH}instance{os.path.sep}"
CUSTOMS_FILES_PATH = f"{BASE_PATH}custom_files{os.path.sep}"


# Locale file
NFTABLE_FILE = os.path.realpath(
    f"{APP_FILES_PATH}nftables{os.path.sep}nftables.conf"
)
INIT_DONE_FILE = os.path.realpath(f"{CUSTOMS_FILES_PATH}.init_done")
SETTINGS_FILE = os.path.realpath(f"{CUSTOMS_FILES_PATH}settings.json")
SETTINGS_TEMPLATE_FILE = os.path.realpath(f"{BASE_PATH}settings.json")

# INSTANCE FILE
INSTANCE_NFTABLE_FILE = os.path.realpath(f"{INSTANCE_PATH}nftables.conf")
INSTANCE_LOGGING_FILE = os.path.realpath(f"{INSTANCE_PATH}setup.log")

# WINDOWS POWERSHELL
SSH_ASKPASS_FILE = os.path.realpath(f"{INSTANCE_PATH}ssh_askpass.ps1")
