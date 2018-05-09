
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



def Groupe(module,result,file):
    warnings = list()
    #commands = command(module.params['commands'])
    try:
        remote_conn_pre = paramiko.SSHClient()
        remote_conn_pre.load_system_host_keys()
        remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy)      
        remote_conn_pre.connect(module.params['hostname'], username = module.params['username'], port=module.params['port'],password = module.params['password'],look_for_keys= False, allow_agent= False)
        remote_conn = remote_conn_pre.invoke_shell()
 
        if module.params['os'] == "ios":    
            enable_cisco(remote_conn,password = module.params['password'])
        #else:
        # ALCATEL
        
        for item in list(module.params['commands']):
            output = run_command(remote_conn,command=item)
            file.write(output)
        file.close()
        result['Titre'] = 'Commands'
        result['message'] = output
        
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
        commands=dict(type='list', required=True),
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
    file = open("./Result.txt","w")
    Groupe(module,result,file)

if __name__ == '__main__':
    main()
