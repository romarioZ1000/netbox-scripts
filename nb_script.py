from django.utils.text import slugify
import paramiko
import netbox.settings
from extras.scripts import *
from netmiko import ConnectHandler
from routeros_ssh_connector import MikrotikDevice
from dcim.models import *
from extras.scripts import Script, ObjectVar
import django_filters
from ipam.models import *
from tenancy.models import *
import time
import os
from csv import DictWriter
import datetime
import socket
import requests
from jinja2 import Environment, StrictUndefined


COMMANDS_TEMPLATE = '''/interface bridge add name=Br_{{ vid }} comment=from_NB_{{ timestamp }}
{% for trunk_port in trunks %}
/interface vlan add interface={{ trunk_port }} name=vlan_{{ vid }}_{{ trunk_port }} vlan-id={{ vid }} disable=no comment=from_NB_{{ timestamp }}
/interface bridge port add bridge=Br_{{ vid }} interface=vlan_{{ vid }}_{{ trunk_port }} comment=from_NB_{{ timestamp }}
{% endfor %}
{% for access_port in access %}
/interface bridge port add bridge=Br_{{ vid }} interface={{ access_port }} comment=from_NB_{{ timestamp }}
{% endfor %}
'''

t = datetime.datetime.now()
t1 = f'{t.strftime("%Y_%m_%d_%H_%M_%S")}'

class RunCommand(Script):
    class Meta:
          name = "VLAN"
          description = "Set VLAN"


    device = ObjectVar(
        model=Device,
        label = 'Name Dev',
        required = True
    )

    iin = MultiObjectVar(
        model=Interface,
        label = 'trunk ports VLAN',
        query_params={
            'device_id': '$device'
        }
    )

    iout = MultiObjectVar(
        model=Interface,
        label = 'Access ports VLAN',
        query_params={
            'device_id': '$device'
        }
    )

    vlan_id = ObjectVar(
        model = VLAN,
        label = 'VLAN (ID)',
        )


    def run(self, data, commit):

        host = f'{data["device"].name}'
        vid = f'{data["vlan_id"].vid}'
#        trunk = f'{data["iin"].name}'
#        access = f'{data["iout"].name}'
        trunk_interfaces = data.get('iin')
        access_interfaces = data.get('iout')

        data_to_render = {
            'vid': vid,
            'trunks': [i.name for i in trunk_interfaces],
            'access': [i.name for i in access_interfaces],
            'timestamp': t1
        }

        jenv = Environment(undefined=StrictUndefined, trim_blocks=True)
        jtemplate = jenv.from_string(COMMANDS_TEMPLATE)

        commands = jtemplate.render(data_to_render)

######################### NEW TEST #######################

        mt_username = "admin"
        #ssh_key = paramiko.RSAKey.from_private_key_file("key.ppk")
        mt_password = "admin"
        timeout = 10


        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # set commands ssuccessfully applied flag
        commands_applied = True

        try:
            ssh.connect(host,username=mt_username,password=mt_password,timeout=timeout)

        except socket.timeout:
            print("Connection timeout. Log entry created.")
            with open("error.log","a") as f:
                f.write(time_stamp() + " " + host + " Timeout connecting to the device.\n")
            commands_applied = False

        print("Succsessfully connected to the host.")

        mt_command = commands
        time.sleep(.2)
        try:
            stdin, stdout, stderr = ssh.exec_command(mt_command)
        except Exception:
            commands_applied = False

        print(mt_command)

        print("\nExternal commands are executed successfully.")
        ssh.get_transport().close()
        ssh.close()

#################################################################

        # create NetBox objects if commands applied
        if commands_applied and commit:
            bridge_name = f'Br_{vid}'
            device = data.get('device')
            #intf_to_bridge = data.get('bridged_interfaces')
            #bridge_interface = device.interfaces.create(type='bridge', name=bridge_name)
            bridge_interface, _ = device.interfaces.get_or_create(type='bridge', name=bridge_name)
            if trunk_interfaces:
                trunk_interfaces.update(bridge=bridge_interface)
            if access_interfaces:
                access_interfaces.update(bridge=bridge_interface)

        self.log_debug(str(commands_applied))
        return ''.join("Client:" + "\n" + commands + "\n\n\n")

        for line in stdout:
            print(line.strip('\n'))
        ssh.close()

