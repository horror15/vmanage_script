import json
import random
import socket
import struct

site_flag = "site-ip did not match"
system_flag = "system-ip did not match"

with open('json') as access_json:
     read_content = json.loads(access_json.read())

def gen_random_site():
    site_id = random.randint(100,1000)
    return site_id

def gen_randomm_system():
    system_ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
    return system_ip

def json_data(site_id, system_ip):
    data_access = read_content["data"]
    for data in data_access:
        try:
            if data['system-ip'] == system_ip:
                return "system-ip did not match"
            if data['site-id'] == site_id:
                return "site-ip did not match"
        except Exception:
              pass
    return 0

val= 1

def get_ip_id():
    val = 1
    while val != 0:
         if  val == "system-ip did not match": 
             system_ip = gen_randomm_system()
         elif val == "site-ip did not match":
              site_id = gen_random_site()
         else:
              site_id = gen_random_site()
              system_ip = gen_randomm_system()
         val = json_data(site_id, system_ip)
    print(system_ip)
    print(site_id)

get_ip_id()
