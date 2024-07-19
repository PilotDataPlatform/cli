# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
import stat
from pathlib import Path
from typing import Iterable

import ntsecuritycon as con
import win32security


# windows related functions
def create_directory_with_permissions_windows(config_path: Path):
    config_path.mkdir(exist_ok=False)
    user, domain, _ = win32security.LookupAccountName('', os.getlogin())
    sd = win32security.SECURITY_DESCRIPTOR()
    sd.Initialize()

    # Create a DACL (Discretionary Access Control List) to current user ONLY
    dacl = win32security.ACL()
    dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user)
    # Set the DACL in the security descriptor
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    # Apply the security descriptor to the directory
    win32security.SetFileSecurity(str(config_path), win32security.DACL_SECURITY_INFORMATION, sd)


def check_user_permission_windows(path: Path) -> str:
    file_path = str(path)
    # Get the current user's SID
    user_sid, _, _ = win32security.LookupAccountName('', os.getlogin())
    user_sid_str = win32security.ConvertSidToStringSid(user_sid)

    # Get the security descriptor of the file/folder
    sd = win32security.GetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION)

    # Get the DACL (Discretionary Access Control List) from the security descriptor
    dacl = sd.GetSecurityDescriptorDacl()

    for i in range(dacl.GetAceCount()):
        ace = dacl.GetAce(i)
        ace_sid = ace[2]

        ace_sid_str = win32security.ConvertSidToStringSid(ace_sid)
        if ace_sid_str == user_sid_str:
            access_mask = ace[1]

            # for 0o500 read and excute permission
            if (access_mask & con.FILE_GENERIC_READ) and (access_mask & con.FILE_GENERIC_WRITE):
                return None
            elif access_mask & con.FILE_ALL_ACCESS:
                return None

    return (
        f'Permissions for "{path}" are too open. '
        f'Expected permissions are \n'
        '(con.FILE_GENERIC_READ&con.FILE_GENERIC_EXECUTE | access_mask & con.FILE_ALL_ACCESS).'
    )


def check_owner_windows(path: Path) -> str:
    sd = win32security.GetFileSecurity(str(path), win32security.OWNER_SECURITY_INFORMATION)
    owner_sid = sd.GetSecurityDescriptorOwner()
    path_uid, _, _ = win32security.LookupAccountSid(None, owner_sid)
    expected_uid = os.getlogin()

    if path_uid != expected_uid:
        return f'"{path}" is owned by the user id {path_uid}. Expected user id is {expected_uid}.'


# Linux related functions
def check_owner_linux(path: Path) -> str:
    path_stat = path.stat()
    path_uid = path_stat.st_uid
    expected_uid = os.geteuid()

    if path_uid != expected_uid:
        return f'"{path}" is owned by the user id {path_uid}. Expected user id is {expected_uid}.'


def check_user_permission_linux(path: Path, expected_bits: Iterable[int]) -> str:
    path_stat = path.stat()
    path_protection_bits = stat.S_IMODE(path_stat.st_mode)
    if path_protection_bits not in expected_bits:
        existing_permissions = oct(path_protection_bits).replace('0o', '')
        expected_permissions = ', '.join(map(oct, expected_bits)).replace('0o', '')
        return (
            f'Permissions {existing_permissions} for "{path}" are too open. '
            f'Expected permissions are {expected_permissions}.'
        )
