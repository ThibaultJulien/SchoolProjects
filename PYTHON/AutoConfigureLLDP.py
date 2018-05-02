
import base64
import paramiko
import sys
import time
import logging
import re
from ansible.module_utils.network.ios.ios import run_commands
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types
from ansible.utils.display import Display

def disable_paging(remote_conn):
    "Disable paging on a Cisco device"
    remote_conn.send("terminal length 0\n")
    time.sleep(1)
    output= remote_conn.recv(1000)

def enable_Cisco(module,remote_conn):
    remote_conn.send("enable\n")
    time.sleep(1)
    output = remote_conn.recv(5000)

    remote_conn.send(module.params['password'] + "\n")
    time.sleep(1)
    output = remote_conn.recv(5000)

def get_neighbors_cisco(module,remote_conn,file):
    remote_conn.send("show lldp neighbors" + "\n")
    time.sleep(1)
    output = remote_conn.recv(5000)
    lldpTable = output.split("\n")
    indices = [i for i, s in enumerate(lldpTable) if "Capability" in s]
    for x in xrange(0,indices[1]+1):
        lldpTable.pop(0)
    for x in xrange(0,4):
        lldpTable.pop()
    #tri des données
    for x in xrange(0,len(lldpTable)):
        var = lldpTable[x].split()
        if len(var) == 4:
            interfaces = var[1] + "\t" + var [3] + "\n"
        elif len(var) == 5:
            interfaces = var[1] + "\t" + var [4] + "\n"
        file.write(interfaces)

def get_lldp_cisco(module,result):
    try:
        #Instanciation de la connection au device
        remote_conn_pre = paramiko.SSHClient()
        remote_conn_pre.load_system_host_keys()
        remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        remote_conn_pre.connect(module.params['hostname'], username = module.params['username'], port=module.params['port'],password = module.params['password'],look_for_keys= False, allow_agent= False)
        remote_conn = remote_conn_pre.invoke_shell()
        file = open("/home/thibault/Ansible_Script/FILES/Result.txt","w")

        disable_paging(remote_conn)
        enable_Cisco(module,remote_conn)
        get_neighbors_cisco(module,remote_conn,file)

        
        result.update({
        'changed': False,
        'stdout': output,
        'stdout_lines': list(to_lines(output))
        })
    finally:
        file.close()
        remote_conn_pre.close()
        module.exit_json(**result)

def get_lldp_alcatel(module,result):
    print "hello"

def Groupe(module):  
    result = dict(
        changed=False,
        Titre='',
        message=''
    )
    try:
        remote_conn_pre = paramiko.SSHClient()
        remote_conn_pre.load_system_host_keys()
        remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy)

        remote_conn_pre.connect(module.params['hostname'], username = module.params['username'], port=module.params['port'],password = module.params['password'],look_for_keys= False, allow_agent= False)
        remote_conn = remote_conn_pre.invoke_shell()
        disable_paging(remote_conn)
        
        file = open("/home/thibault/Ansible_Script/FILES/Result.txt","w")

        remote_conn.send(" enable\n")
        time.sleep(1)
        output = remote_conn.recv(5000)

        remote_conn.send(module.params['password'] + "\n")
        time.sleep(1)
        output = remote_conn.recv(5000)

#        for item in list():
#            remote_conn.send(item + "\n")
#            time.sleep(2)
#            output = remote_conn.recv(5000)
#            file.write(output)
#        file.close()
        
        result.update({
        'changed': False,
        'stdout': output,
        'stdout_lines': list(to_lines(output))
        })
    finally:
        remote_conn_pre.close()
        module.exit_json(**result)
def main():
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        hostname=dict(type='str', required=True),
        port=dict(type='int'),
        aim=dict(type='str', required=True),
        os=dict(type='str', required=True),
    )
    result = dict(
        changed=False,
        Titre='',
        message=''
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    if module.params['os'] == "ios":
        get_lldp_cisco(module,result)
    elif module.params['os'] == "aos":
        get_lldp_alcatel(module,result)

if __name__ == '__main__':
    main()
