
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
    time.sleep(0.2)
    output= remote_conn.recv(1000)

def enable_Cisco(module,remote_conn):
    remote_conn.send("enable\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)

    remote_conn.send(module.params['password'] + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)
def configure_interface_cisco(module,remote_conn,file,interface):
    file.write(interface)
    remote_conn.send("conf t" + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)
    var = interface.split()

    remote_conn.send("interface " + var[1] + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)

    remote_conn.send("interface " + var[1] + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)
    #configure vlan
    remote_conn.send("interfaces witchport acces vlan " + var[3] + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)

def get_vlan_arp(module,remote_conn,file,interfaces,addresses):
    remote_conn.send("show arp" + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)
    arpTable = output.split("\n")
    for x in xrange(0,len(addresses)):
        #remove \n
        tmp = addresses[x].rstrip()
        indices = [i for i, s in enumerate(arpTable) if tmp in s]
        chaine = arpTable[indices[0]].split()
        indices = [i for i, s in enumerate(chaine) if "Vlan" in s]
        var = chaine[indices[0]].split("Vlan")
        numVlan = var[1]
        interfaces[x] = interfaces[x].rstrip()
        #interfaces : [0] nom [1] interface interne [2] interface externe
        interface = interfaces[x] + " " + numVlan + "\n"
        configure_interface_cisco(module,remote_conn,file,interface)
def get_neighbors_cisco(module,remote_conn,file):
    #recuperation des donnees
    remote_conn.send("show lldp neighbors" + "\n")
    time.sleep(0.2)
    output = remote_conn.recv(5000)
    lldpTable = output.split("\n")
    indices = [i for i, s in enumerate(lldpTable) if "Capability" in s]
    for x in xrange(0,indices[1]+1):
        lldpTable.pop(0)
    for x in xrange(0,4):
        lldpTable.pop()
    #tri des donnees
    interfaces = []
    for x in xrange(0,len(lldpTable)):
        var = lldpTable[x].split()
        if len(var) == 4:
            s = list(var[3])
            s[1] = "/"
            var[3] = ''.join(s)
            interfaces.append(var[0] + "\t" + var[1] + "\t" + var [3] + "\n")  
        elif len(var) == 5:
            interfaces.append(var[0] + "\t" + var[1] + "\t" + var [4] + "\n") 
    #recuperation des addresses ip
    addresses = []
    for x in xrange(0,len(interfaces)):
        var = interfaces[x].split() 
        remote_conn.send("show lldp entry " + var[0] + "\n")
        time.sleep(0.2)
        output = remote_conn.recv(5000)
        tmp = output.split("\n")

        if "Cisco IOS Software" in output:
            #Cisco => show cdp
            remote_conn.send("show cdp entry *\n")
            time.sleep(0.2)
            output = remote_conn.recv(5000)
            tmp = output.split("-------------------------")
            for x in xrange(0,len(tmp)):
                if var[0] in tmp[x]:
                    listTmp = tmp[x].split("\n")
                    indices = [i for i, s in enumerate(listTmp) if "address:" in s]
                    chaine = listTmp[indices[0]]
                    listTmp = chaine.split(": ")
                    addresses.append(listTmp[1])
                    break
                    #adresse IP de Cisco retrouvee et ok
        else:
            addresses.append(var[0] + "\n")
    #adresse IP pour Cisco num serie pour Alcatel Toutes donnees OK pour Recuperer la table ARP
    get_vlan_arp(module,remote_conn,file,interfaces,addresses)

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
