# ciscosdwan-wan2sdwan_migration
Objective of this script is to log in to the Cisco WAN Routers and check on the prerequisite of all WAN devices whether they are ok to do the remote upgrade to SDWAN or not. After checking, I will ask for the Remote upgrade for the "Pass" device to controller mode. 

**Prior running this script this is the prerequisite : **
1. Upgrade controller to 20.3.x and above
3. Configure Device Template for the Branch Devices
5. Attached the serial number of the WAN devices to the template and configure required parameter eq. Interface Name or IP Address
6. Make sure this script run on the management linux machine which has access to WAN Router via ssh.
7. Make sure the underlay connectivity from the Tranditional WAN is able to communicate to the Cisco SDWAN Controller either on the cloud or on premise.


**Requirement**

Python 3.7



**Assumption :**

All WAN routers in the list have the "same" username and password.


**Overall Script Flow**
![image](https://user-images.githubusercontent.com/68508144/127443926-e95de095-4b5b-4f45-b95c-86fccfcb293a.png)



# This is the rough explanation on how to run this script
0. Clone script from git repo.
```
git clone https://github.com/saadirek/ciscosdwan-wan2sdwan_migration
Cloning into 'ciscosdwan-wan2sdwan_migration'...
remote: Enumerating objects: 27, done.
remote: Counting objects: 100% (27/27), done.
remote: Compressing objects: 100% (25/25), done.
remote: Total 27 (delta 11), reused 0 (delta 0), pack-reused 0
Unpacking objects: 100% (27/27), done.

cd ciscosdwan-wan2sdwan_migration
```
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

3. Run script 
``` 
python remote-upgrade.py
```

4. The script will ask credential for connecting to WAN Router. Enter the Credential and Enter

```
What is the Username to Connect to the WAN Router ? 
What is the Password to Connect to the WAN Router ? 
```

5. The script will ssh to each of the device in the device_list.csv file. If the script or Management Machine can access the device via SSH. It will go and get the version of the Software. And check if the version is IOS XE : 17.03 or above. If yes. I will mark as Pass. If not, it will make Fail.

Example result : 
```
What is the Username to Connect to the WAN Router ? : admin
What is the Password to Connect to the WAN Router ? : admin
######## Device 1 #########
Checking Device Serial Number: FGL2303129J.... Pass
Checking Device Version : 17.03.02....Pass
Found Existing ciscosdwan.cfg -> Processing file deleted
Found Existing ciscortr.cfg -> Processing file deleted
######## Device 2 #########
Device IP : 10.68.116.134 is failed to connect. Please try again.

```

6. The script will generate the task.csv file containing the flag "Pass" or "Fail". This information will be used later on.
7. The script will ask access to the vManage, credentials. Enter the vManage FQDN or IP address and Its credentail. Note that the Managment machine will also need to have the accessibility to the vManage controller as well.  The script will get the bootstrap file of each device and push it to each of the WAN Router based on the IP address provided initially.
```
What is the vManage IP Address ? [x.x.x.x] : 10.68.116.127 
What is the vManage Username ? : sadirek
What is the vManage Password ? : 
```

7. Once it is done for all devices. It will ask whether you want to continue upgrade of remote router to SDWAN or not. If you want to do it now, then type 'y' to continue. Otherwise, type 'n'

```
Successfully SCP files to FGL2303129J_10.68.116.133
Do you want to continue Upgrade all devices ? [y/n] : y

```
8. The script will issue "controller-mode enable" on the WAN Router to change the mode to the SDWAN Router. 
9. After that, wait for about 6-8 mins. The device will be up in SDWAN Image and connect to the SDWAN Controller right away.







