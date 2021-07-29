#
# Script to Remote Upgrade Traditional WAN to SDWAN
# Version 1.0
#

import sys
from netmiko import ConnectHandler, ssh_exception, file_transfer
import csv
import re
from sdwan_query import rest_api_lib
import json
import os
import requests
import urllib.request 
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import shutil

#################################################
#### PRE-SETUP 
#################################################

sys.path.append(".")
csv_serial_number =[]
csv_ip_address=[]


# Delete bootstrap folder and recreate it **** Do not delete the bootstrap folder
if (os.path.exists('./bootstrap')):
    shutil.rmtree('./bootstrap')
os.makedirs('./bootstrap')

# Delete backup_config folder and recreate it **** Do not delete the backup_config folder
if (os.path.exists('./backup_config')):
    shutil.rmtree('./backup_config')
os.makedirs('./backup_config')



# Read Device list CSV 
with open('device_list.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        csv_ip_address.append(row[0]) # IP address 
        csv_serial_number.append(row[1]) # serial number 
    #print(csv_ip_address)


# Create "new" task.csv for the device upgrade list 
f = open('task.csv', 'w', encoding='UTF8', newline='')




#################################################
#### FUNCTION CHECKING PREREQUISITE
#################################################

   
def check_prerequisite ():
    
    for i in range(int(len(csv_ip_address))):
        print("######## Device " + str(i+1) + ' #########')
        device = {
            "host" : csv_ip_address[i],
            "username" : DEVICE_USERNAME,
            "password" : DEVICE_PASSWORD,
            "device_type" : "cisco_ios",
            "fast_cli" : True    
        }
        upgradable_status = 'Fail'
        try:
            with ConnectHandler(**device) as device_connect:
                device_connect.enable()
               
                # Backup Configuration 
                backup = device_connect.send_command("show running")
                os.makedirs('./backup_config/backup_'+csv_ip_address[i])
                backup_file = open('./backup_config/backup_'+csv_ip_address[i]+"/ciscortr.cfg", 'w', encoding='UTF8', newline='')
                backup_file.write(backup)
                backup_file.close()

                # Get the show crypto result 

                show_crypto_result = device_connect.send_command("show crypto pki certificates CISCO_IDEVID_SUDI")
                serial_extract_pattern =  ' SN:.*'
                serial = re.findall(serial_extract_pattern, show_crypto_result)
                serial_txt = serial[0][4:]
                print("Checking Device Serial Number: " + csv_serial_number[i] + "....", end =" ")
                if serial_txt in csv_serial_number[i]:
                    print("Pass")
                else:
                    print("Fail")

                print("Checking Device Version : ", end = "") 
                show_version = device_connect.send_command("show version")
                version_extract_pattern =  'Version (.*)'
                version = re.findall(version_extract_pattern, show_version)[0]
                major_version = int(re.findall('[0-9].',version)[0])
                minor_version = int(re.findall('[0-9].',version)[1])
                print (version + "....", end ="")  
                
                if major_version >=17 and minor_version >= 3:
                    print("Pass")
                    upgradable_status = "Pass"
                else:
                    print("Fail - Device Need upgrade")
                    upgradable_status = "Fail"
                
                #print('\n')
                device_connect.send_config_set('ip scp server enable')
                
                # remove existing ciscosdwan.cfg if exist

                output = device_connect.send_command_timing('delete ciscosdwan.cfg')
                if 'Delete filename [ciscosdwan.cfg]?' in output:
                    output += device_connect.send_command_timing('\n', strip_prompt=False, strip_command=False)
                    output += device_connect.send_command_timing('\n', strip_prompt=False, strip_command=False)
                    print("Found Existing ciscosdwan.cfg -> Processing file deleted")
                output = device_connect.send_command_timing('delete ciscortr.cfg')
                if 'Delete filename [ciscortr.cfg]?' in output:
                    output += device_connect.send_command_timing('\n', strip_prompt=False, strip_command=False)
                    output += device_connect.send_command_timing('\n', strip_prompt=False, strip_command=False)
                    print("Found Existing ciscortr.cfg -> Processing file deleted")
                device_connect.save_config()

        except(ssh_exception.NetMikoAuthenticationException, ssh_exception.NetMikoTimeoutException, ssh_exception.AuthenticationException):
            print("Device IP : " + csv_ip_address[i] + " is failed to connect. Please try again.\n")

        f.write(csv_ip_address[i]+','+csv_serial_number[i] + ',' +upgradable_status+"\n")
    f.close()


###################################################################################################
#### FUNCTION SCP BOOTSTRAP / BACKUP CONFIG to the Pass-Criteria Devics in the task.csv
###################################################################################################

def scp_to_device():
    device_ip = []
    device_serial = []
    device_upgrade_flag = []
   
    with open('task.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            device_ip.append(row[0]) # IP address 
            device_serial.append(row[1]) # serial number
            device_upgrade_flag.append(row[2]) # Flag 
    #print(device_upgrade_flag)
    for i in range(int(len(device_ip))): 
        
        if device_upgrade_flag[i] == "Pass":
            
            device = {
                "host" : device_ip[i],
                "username" : DEVICE_USERNAME,
                "password" : DEVICE_PASSWORD,
                "device_type" : "cisco_ios",
                "fast_cli" : True    
            }
            bootstrap_path = "./bootstrap/bootstrap_"+device_ip[i]+"/ciscosdwan.cfg"
            backup_path = "./backup_config/backup_"+device_ip[i]+"/ciscortr.cfg"
            #print(bootstrap_path)
            try:
                with ConnectHandler(**device) as scp_connect:
                    scp_connect.enable()
                    scp_transfer = file_transfer(scp_connect,source_file=bootstrap_path,dest_file="ciscosdwan.cfg",file_system="bootflash:",)
                    #print(scp_transfer)
                    scp_transfer = file_transfer(scp_connect,source_file=backup_path,dest_file="ciscortr.cfg",file_system="bootflash:",)
                    print("Successfully SCP files to " +device_serial[i]+ "_"+device_ip[i])

            except(ssh_exception.NetMikoAuthenticationException, ssh_exception.NetMikoTimeoutException, ssh_exception.AuthenticationException):
                print("Transfer Failed")
         
###################################################################################################
#### FUNCTION GET BOOTSTRAP / BACKUP CONFIG From VMANAGE and FROM Devices
###################################################################################################
          
def get_bootstrap():
    device_ip = []
    device_serial= []
    device_upgrade_flag= []
    wan_edge_list = sdwanp.get_request('system/device/vedges')
    wan_edge_list_json = json.loads(wan_edge_list)
    with open('task.csv', 'r') as file:
        reader = csv.reader(file)
        
        for row in reader:
            device_ip.append(row[0]) # IP address 
            device_serial.append(row[1]) # serial number
            device_upgrade_flag.append(row[2]) # Flag 
        file.close()    
    for i in range(int(len(device_ip))): 
        if device_upgrade_flag[i] == "Pass":
            for x in wan_edge_list_json['data']:           
                if x['subjectSerialNumber'] == device_serial[i]:
                    #get chasis number
                    chasis_number = x['chasisNumber'] 
                    res_bootstrap = sdwanp.get_request('system/device/bootstrap/device/' +  chasis_number+'?configtype=cloudinit&inclDefRootCert=false')
                    res_bootstrap_json = json.loads(res_bootstrap)
                    bootstrap = res_bootstrap_json["bootstrapConfig"]
                    os.makedirs('./bootstrap/bootstrap_'+device_ip[i])
                    f = open('./bootstrap/bootstrap_'+device_ip[i]+'/'+'ciscosdwan.cfg', 'w', encoding='UTF8', newline='')
                    f.write(bootstrap)
                    f.close()
               


###################################################################################################
#### PERFORM UPGRADE FOR ALL DEVICES WHICH PASS THE PRE-CHECKS
###################################################################################################

def sdwan_migrate(): 
    device_ip = []
    device_serial= []
    device_upgrade_flag= []
    with open('task.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            device_ip.append(row[0]) # IP address 
            device_serial.append(row[1]) # serial number
            device_upgrade_flag.append(row[2]) # Flag 
        file.close()    
    for i in range(int(len(device_ip))): 
        if device_upgrade_flag[i] == "Pass":
            device = {
                "host" : device_ip[i],
                "username" : DEVICE_USERNAME,
                "password" : DEVICE_PASSWORD,
                "device_type" : "cisco_ios",
                "fast_cli" : True    
            }
            try:
                with ConnectHandler(**device) as device_connect:
                    device_connect.enable()
                    output = device_connect.send_command_timing('controller-mode enable')
                    output += device_connect.send_command_timing('\n', strip_prompt=False, strip_command=False)
                    output += device_connect.send_command_timing('n', strip_prompt=False, strip_command=False)
                    output += device_connect.send_command_timing('\n', strip_prompt=False, strip_command=False)
            except(ssh_exception.NetMikoAuthenticationException, ssh_exception.NetMikoTimeoutException, ssh_exception.AuthenticationException):
                print("Connecting to the device Failed")




#################################################
#### MAIN FUNCTION STARTS HERE
#################################################

DEVICE_USERNAME = input("What is the Username to Connect to the WAN Router ? : " )
DEVICE_PASSWORD = input("What is the Password to Connect to the WAN Router ? : " )

check_prerequisite()

# Get information for vManage 
SDWAN_IP = input("What is the vManage IP Address ? [x.x.x.x] : " )
SDWAN_USERNAME = input("What is the vManage Username ? : " )
SDWAN_PASSWORD = input("What is the vManage Password ? : " )
sdwanp = rest_api_lib(SDWAN_IP, SDWAN_USERNAME, SDWAN_PASSWORD)


get_bootstrap()
scp_to_device()

# Proceed Upgrade or not ! 
proceed_upgrade = input("Do you want to continue Upgrade all devices ? [y/n] : " )
if proceed_upgrade == 'y':
    sdwan_migrate()
else:
    print("Preparation is done. Please login to the device and issue Controller mode enable to activate SDWAN mode")

