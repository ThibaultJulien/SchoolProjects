import base64
import paramiko
import sys
import time
import logging
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types
from ansible.utils.display import Display

def disable_paging(remote_conn):
    "Disable paging on a Cisco device"
    remote_conn.send("terminal length 0\n")
    time.sleep(0.5)
    output= remote_conn.recv(1000)

def run_command(command):
    remote_conn.send(command + "\n")
    time.sleep(0.5)
    output= remote_conn.recv(5000)
    return output

def enable_cisco(remote_conn,password):
    disable_paging(remote_conn)
    remote_conn.send(" enable\n")
    time.sleep(0.5)
    output = remote_conn.recv(5000)
    remote_conn.send(password + "\n")
    time.sleep(0.5)
    output = remote_conn.recv(5000)