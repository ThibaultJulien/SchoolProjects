import base64
import paramiko
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.utils.display import Display

def run_command(remote_conn,command):
    remote_conn.send(command + "\n")
    time.sleep(0.5)
    output= remote_conn.recv(5000)
    return output
