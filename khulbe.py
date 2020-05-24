import json
import random
import socket
import struct
from vmanage_session import vmanage_session 
import re
import netmiko
import paramiko
from scp import SCPClient
import time
from netmiko import ConnectHandler, file_transfer

cisco = {'device_type': 'cisco_ios', 'host': '10.78.108.98', 'username': 'prisaha22', 'password': '33prisaha'}

start_session = vmanage_session('10.78.25.207', 'devgroup', 'devgroup')
response = start_session.get_request('device', False)
read_content = response.json()

def createClient(host, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username, password)
    return ssh


def gen_random_id():
    site_id = random.randint(100,1000)
    return site_id

def gen_random_ip():
    system_ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
    return system_ip

def json_data(site_id, system_ip):
    data_access = read_content["data"]
    for data in data_access:
        try:
            if data['system-ip'] == system_ip:
                return "system-ip did not match"
            if data['site-id'] == site_id:
                return "site-id did not match"
        except Exception:
              pass
    return "match"


def get_ip_id():
    val = "not match"
    while val != "match":
         if  val == "system-ip did not match":
             system_ip = gen_random_ip()
         elif val == "site-id did not match":
              site_id = gen_random_id()
         else:
              site_id = gen_random_id()
              system_ip = gen_random_ip()
         val = json_data(site_id, system_ip)
    return system_ip,site_id

def get_wan_intr():
    string = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    ssh_conn = ConnectHandler(**cisco)
    response = ssh_conn.send_command("show ip interface brief")
    print(response)

    for line in response.split("\n"):
        match = re.search(string,line)
        if match is not None:
            wan_side_intr = re.split(' +',line)
            match = re.search("GigabitEthernet",wan_side_intr[0])
            if match is not None:
                break

    ssh_conn.disconnect()
    return wan_side_intr[0]


def get_serial_chasis_num():
    string1 = "(?<!..)serial-num(?= )"
    string2 = "chassis-num"
    ssh_conn = ConnectHandler(**cisco)
    response = ssh_conn.send_command("show sdwan control local-properties")

    for line in response.split("\n"):
        match1 = re.search(string1,line)
        match2 = re.search(string2,line)
        if match1 is not None:
            serial_num = re.split(' +',line)
        if match2 is not None:
            chassis_num = re.split(' +',line)


    output = chassis_num[1] + "," + serial_num[1]
    f = open("nkhulbe92.csv","w")
    f.write(output)
    ssh_conn.disconnect()
    f.close()
    

def register_device():

    get_serial_chasis_num()
    ssh = createClient('10.65.126.165', '22', 'tester', 'v1ptela0212')
    scp = SCPClient(ssh.get_transport())
    scp.put('nkhulbe92.csv', '/home/tester/nkhulbe92.csv')
    stdin, stdout, stderr = ssh.exec_command('python /home/tester/vtest/addons/zprov/signing.py --csvfile nkhulbe92.csv --orgname sdwan-blr-master --output nkhulbe92.viptela')
    print(stdout.readlines())
    scp.get('/home/tester/nkhulbe92.viptela', 'nkhulbe92.viptela')
    ssh.close()
    del ssh, stdin, stdout, stderr
    
    print("---------------------device registered with vmanage----------------------------------")
    
    print("---------------------------loading file to vmanage-------------------------------")

    time.sleep(5)
    payload = {"validity":"valid", "upload":"true"} 
    start_session.post_request(payload)



def install_certificate():
    source_file = 'cacert.pem'
    dest_file = 'cacert.pem'
    direction = 'put'
    file_system = 'bootflash:'
    ssh_conn = ConnectHandler(**cisco)
    response = file_transfer(ssh_conn, source_file=source_file, dest_file=dest_file, file_system=file_system, direction=direction, disable_md5=True, overwrite_file=False)
    print(response)
    response = ssh_conn.send_command("request platform software sdwan root-cert-chain install bootflash:cacert.pem")
    print(response)
    ssh_conn.disconnect()


    ssh = createClient('10.78.108.98','22','prisaha22','33prisaha')
    scp = SCPClient(ssh.get_transport())
    stdin, stdout, stderr = ssh.exec_command('request platform software sdwan csr upload bootflash:nk26.csr')
    stdin.write('sdwan-blr-master' + '\n')
    stdin.write('sdwan-blr-master' + '\n')
    stdin.flush()
    print(stdout.readlines())
    ssh.close()
    del ssh, stdin, stdout, stderr

    ssh = createClient('10.78.108.98','22','prisaha22','33prisaha')
    scp = SCPClient(ssh.get_transport())
    scp.get('nk26.csr', 'nk26.csr')
    #print(stdout.readlines())
    ssh.close()
    del ssh
     
    ssh = createClient('10.65.126.165', '22', 'tester', 'v1ptela0212')
    scp = SCPClient(ssh.get_transport())
    scp.put('nk26.csr', '/home/tester/root_ca/nk26.csr')
    stdin, stdout, stderr = ssh.exec_command('cd /home/tester/root_ca')
    stdin, stdout, stderr = ssh.exec_command('openssl ca -config openssl.cnf -in /home/tester/root_ca/nk26.csr -out /home/tester/root_ca/nk26.pem')
    stdin.write('f3rrar1' + '\n')
    stdin.write('y' + '\n')
    stdin.write('y' + '\n')
    stdin.flush()
    print(stdout.readlines())
    scp.get('/home/tester/root_ca/nk26.pem', 'nk26.pem')
    ssh.close()
    del ssh, stdin, stdout, stderr
    
    time.sleep(5)

    source_file = 'nk26.pem'
    dest_file = 'nk26.pem'
    direction = 'put'
    file_system = 'bootflash:'
    ssh_conn = ConnectHandler(**cisco)
    response = file_transfer(ssh_conn, source_file=source_file, dest_file=dest_file, file_system=file_system, direction=direction,disable_md5=True, overwrite_file=False)
    print(response)
    response = ssh_conn.send_command("request platform software sdwan certificate install bootflash:nk26.pem")
    print(response)

    ssh_conn.disconnect()

    print("----------------------------certificate installed successfully----------------------------------")

    time.sleep(5)

    print("-----------------------------------register device-----------------------------")
    
    register_device()
    


def exec_config():
    count = 0;
    response = get_ip_id()
    response = list(response)
    system_ip = response[0]
    site_id = str(response[1])
    print(system_ip)
    print(site_id)
    wan_side_intr = get_wan_intr()
    print(wan_side_intr)
    string = ":"
    ssh_conn = ConnectHandler(**cisco)
    data = open("configure1", "r")
    for line in data:
        match = re.search(string,line)
        if match is not None:
            output = line.split(':')
            if output[0] == 'system-ip ':
                command = output[0] + system_ip
            elif output[0] == 'site-id ':
                command = output[0] + site_id
            elif output[0] == 'ip unnumbered ':
                command = output[0] + wan_side_intr
            elif output[0] == 'tunnel source ':
                command = output[0] + wan_side_intr
            elif output[0] == 'interface ':
                command = output[0] + wan_side_intr
            else:
                print("error is gen")
        else:
            command = line
        response = ssh_conn.send_command(command,auto_find_prompt=False)
        #print(response)
    ssh_conn.disconnect()

    print("----------------------exec_config succcessful---------------------")
    
    time.sleep(5)

    print("----------intalling certificates-----------------------------------")

    install_certificate()


exec_config()




