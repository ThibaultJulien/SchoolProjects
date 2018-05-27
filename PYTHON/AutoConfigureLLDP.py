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
from ansible.my_modules.ios import enable_cisco
from ansible.my_modules.common import run_command


def configure_interface_cisco(module,remote_conn,interface):
    # L'interface contient : 0 SysName 1 vlan 2 IP 3 Interface
    output = run_command(remote_conn,command="conf t")
    var = interface.split()
    output = run_command(remote_conn,command="interface " + var[3])
    #configure vlan
    output = run_command(remote_conn,command="switchport acces vlan " + var[1])
    output = run_command(remote_conn,command="end")

def configure_interface_alcatel(module,remote_conn,interface):
    var = interface.split()
    output = run_command(remote_conn,command="vlan  " + var[0] + " port default "+ var[2])
    #Si linkagg alors recherche du linkagg et configuration de celui-ci
    if "ERROR" in output:
        output = run_command(remote_conn,command="show linkagg port")
        linkagg = output.split("\n")
        indices = [i for i, s in enumerate(linkagg) if var[2] in s]       
        tmp = linkagg[indices[0]].split()
        output = run_command(remote_conn,command="vlan  " + var[0] + " port default "+ tmp[4])

def get_neighbors_cisco(module,remote_conn):
    #recuperation des donnees
    output = run_command(remote_conn,command="show lldp entry *")
    lldpTable = output.split("-------------------------")
    #information pour chaque liens
    
    for x in xrange(1,len(lldpTable)):
        if "Vlan ID: - not advertised" in lldpTable[x]:
            #Pas partage
            print "TMP"
        elif "Enabled Capabilities: B" in lldpTable[x]:
            #Infos partagees
            var = lldpTable[x].split("\n")

            indices = [i for i, s in enumerate(var) if "System Name:" in s]
            tmp = var[indices[0]].split("System Name: ")
            interface = tmp[1].rstrip()
            name =tmp[1].rstrip()

            indices = [i for i, s in enumerate(var) if "Vlan ID:" in s]
            tmp = var[indices[0]].split("Vlan ID: ")
            interface = interface + "\t" + tmp[1].rstrip()

            indices = [i for i, s in enumerate(var) if "IP:" in s]
            tmp = var[indices[0]].split("IP: ")
            interface = interface + "\t" + tmp[1].rstrip()

            output = run_command(remote_conn,command="show lldp neighbors")
            chaine = output.split("\n")
            indices = [i for i, s in enumerate(chaine) if name in s]
            tmp = chaine[indices[0]].split()
            interface = interface + "\t" + tmp[1] 
            # L'interface contient : 0 SysName 1 vlan 2 IP 3 Interface
            configure_interface_cisco(module,remote_conn,interface)
def get_neighbors_alcatel(module,remote_conn):
    #recuperation des donnees
    output = run_command(remote_conn,command="show lldp remote-system")
    lldpTable = output.split("Remote LLDP Agents on Local Slot/Port ")
    for x in xrange(1,len(lldpTable)):
        if "Vlan ID" in lldpTable[x] and "Capabilities Enabled        = Bridge" in lldpTable[x]:
            # vlan partage
            var = lldpTable[x].split("\n")
            # 0 vlan 1 IP 2 interface

            indices = [i for i, s in enumerate(var) if "Vlan ID" in s]
            tmp = var[indices[0]].split("= ")
            chaine = tmp[1].split(",")
            interface = chaine[0].rstrip()

            indices = [i for i, s in enumerate(var) if "Management IP Address" in s]
            tmp = var[indices[0]].split("= ")
            chaine = tmp[1].split(",")
            interface = interface + "\t" + chaine[0].rstrip()

            chaine = var[0].split(":")
            interface = interface + "\t" + chaine[0].rstrip() 
            #infos completes
            configure_interface_alcatel(module,remote_conn,interface)


def get_lldp_cisco(module,remote_conn,result):
    try:
        #Instanciation de la connection au device
        enable_cisco(remote_conn,password = module.params['password'])
        get_neighbors_cisco(module,remote_conn)
        result.update({
        'changed': False,
        'stdout': output,
        'stdout_lines': list(to_lines(output))
        })
    finally:
        remote_conn.close()
        module.exit_json(**result)

def get_lldp_alcatel(module,remote_conn,result):
    try:
        
        get_neighbors_alcatel(module,remote_conn)
        result.update({
        'changed': False,
        'stdout': output,
        'stdout_lines': list(to_lines(output))
        })
    finally:
        remote_conn.close()
        module.exit_json(**result)

def main():
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        hostname=dict(type='str', required=True),
        port=dict(type='int'),
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

    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.load_system_host_keys()
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    remote_conn_pre.connect(module.params['hostname'], username = module.params['username'], port=module.params['port'],password = module.params['password'],look_for_keys= False, allow_agent= False)
    remote_conn = remote_conn_pre.invoke_shell()
    if module.params['os'] == "ios":
        get_lldp_cisco(module,remote_conn,result)
    elif module.params['os'] == "aos":
        get_lldp_alcatel(module,remote_conn,result)

if __name__ == '__main__':
    main()
