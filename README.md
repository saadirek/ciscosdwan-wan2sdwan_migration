# ciscosdwan-wan2sdwan_migration
Objective of this script is to log in to the Cisco WAN Routers and check on the prerequisite of all WAN devices whether they are ok to do the remote upgrade to SDWAN or not. After checking, I will ask for the Remote upgrade for the "Pass" device to controller mode. 

**Prior running this script this is the prerequisite : **
1. Upgrade controller to 20.3.x and above
2. Configure Device Template for the Branch Devices
3. Attached the serial number of the WAN devices to the template and configure required parameter eq. Interface Name or IP Address
4. Make sure this script run on the management linux machine which has access to WAN Router via ssh.

**Requirement **
Python 3.7

**Assumption :**
All WAN routers in the list have the "same" username and password.

**This is the rough explanation on how to run this script**
1. Open the device_list.csv and fill up the WAN device information. Following this format _"IP Address,Serial Number,Device Model"_
For Example
```
10.68.116.133,FGL2303119J,C1111-4P
10.68.116.134,FGL2303129Y,C1111-4P
10.68.116.135,FGL2303129Y,C1111-4P
```
and save.

2. Install the dependancies or requirement before running this scripts
```
python3.7 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```


