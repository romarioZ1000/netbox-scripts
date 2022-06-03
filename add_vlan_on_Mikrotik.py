#add netmiko to the local_requirements.txt
from django.utils.text import slugify
import paramiko
import netbox.settings
from extras.scripts import *
from netmiko import ConnectHandler
from routeros_ssh_connector import MikrotikDevice

class RunCommand(Script):
    class Meta:
        name = "VLAN on Mikrotik"
        description = "Configure Mikrotik via SSH"
        field_order = [
                       'input_ip',
                       'input_bridge',
                       'input_vlan_name',
                       'input_vlan_id'
                      ]

    input_ip = StringVar(
        description="Enter the IP Address:"
    )
    input_bridge = StringVar(
        description="Name Bdrige:"
    )

    input_vlan_name = StringVar(
        description="Vlan Name:"
    )

    input_vlan_id = StringVar(
        description="Vlan id:"
    )

    def run(self, data, commit):


        command = '/interface bridge add name='+data['input_bridge'] + '\n'
        command1 = '/interface vlan add interface=ether1 name='+data['input_vlan_name'] + '' ' vlan-id='+data['input_vlan_id'] + '\n'
        command2 = '/interface bridge port add bridge='+data['input_bridge'] + '' ' interface='+data['input_vlan_name'] + '' 'add bridge='+data['input_bridge'] + '' ' interface=ether2 \n'
        command3 = '/interface bridge port add bridge='+data['input_bridge'] + 'interface=ether2 \n'
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(data['input_ip'], username='admin+ct80h', password='admin')
        stdin, stdout, stderr = client.exec_command(command + command1 + command2 + command3)

        cisco1 = {
            "device_type": "mikrotik_routeros",
            "host": data['input_ip'],
            "username": "admin+ct",
            "password": "admin",
        }
        
        with ConnectHandler(**cisco1) as net_connect:
            output = net_connect.send_command('/interface print \n')

            self.log_success("Configured Mikrotik via SSH")
        return ''.join(output)

        for line in stdout:
            print(line.strip('\n'))
        client.close()
