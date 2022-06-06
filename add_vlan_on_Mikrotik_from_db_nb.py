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

   class RunCommand(Script):
      class Meta:
          name = " VLAN on Mikrotik"
          description = "Run command on Mikrotik Devices via SSH"
          field_order = [
    'device',
    'interface_in',
    'interface_out',
    'interfacebridge',
    'vlan_id',
    ]


    device = ObjectVar(
        model=Device,
    )

    interface_in = ObjectVar(
        model=Interface,
         query_params={
         'device_id': '$device'
    }
    )

    interface_out = ObjectVar(
        model=Interface,
         query_params={
         'device_id': '$device'
    }
    )

    interfacebridge = ObjectVar(
        model=Interface,
        query_params={
        'device_id': '$device'
        }
     )

    vlan_id = ObjectVar(
        model=VLAN,
        label='VLAN (ID)',
    )


    def run(self, data, commit):

        host=f'{data["device"].name}'

        command = f'/interface bridge add name=bridge_{data["interfacebridge"].name} comment=from_NB \n'
        command1 = f'/interface vlan add interface={data["interface_in"].name} name=vlan_{data["vlan_id"].name} vlan-id={data["vlan_id"].name} disable=no comment=from_NB\n'
        command2 = f'/interface bridge port add bridge=bridge_{data["interfacebridge"].name} interface={data["interface_out"].name} comment=from_NB \n'
        command3 = f'/interface bridge port add bridge={data["interfacebridge"].name} interface=vlan_{data["vlan_id"].name} comment=from_NB\n'
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username='admin+ct80h', password='admin')
        stdin, stdout, stderr = client.exec_command(command + command1 + command2 + command3)

        mik1 = {
            "device_type": "mikrotik_routeros",
            "host": host,
            "username": "admin+ct",
            "password": "admin",
        }


        with ConnectHandler(**mik1) as net_connect:
             output = net_connect.send_command('/interface print')

             self.log_success("View the information bellow")
        return ''.join(output)



        for line in stdout:
            print(line.strip('\n'))
        client.close()
