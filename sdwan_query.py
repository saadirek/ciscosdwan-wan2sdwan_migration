
import requests
import sys
import json
import os
import socket
import time
import urllib.request 
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)



class rest_api_lib:
    def __init__(self, vmanage_ip, username, password):
        self.vmanage_ip = vmanage_ip
        self.session = {}
        self.login(self.vmanage_ip, username, password)

    def login(self, vmanage_ip, username, password):
        """Login to vmanage"""
        base_url_str = 'https://%s:443/'%vmanage_ip

        login_action = '/j_security_check'

        #Format data for loginForm
        login_data = {'j_username' : username, 'j_password' : password}

        #Url for posting login data
        login_url = base_url_str + login_action
        url = base_url_str + login_url


        #URL for retrieving client token
        token_url = base_url_str + 'dataservice/client/token'

        sess = requests.session()
        #If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, data=login_data, verify=False)



        if b'<html>' in login_response.content:
            print ("Login Failed")
            sys.exit(0)

        login_token = sess.get(url=token_url, verify=False)
        if b'<html>' in login_token.content:
            print ("Login Token Failed")
            exit(0)

        #update token to session headers
        sess.headers['X-XSRF-TOKEN'] = login_token.content
        # print(login_token.content)
        self.session[vmanage_ip] = sess

    def get_request(self, mount_point,headers={'Content-Type': 'application/json'}):
        """GET request"""
        url = "https://%s:443/dataservice/%s"%(self.vmanage_ip, mount_point)
        #print url
        response = self.session[self.vmanage_ip].get(url=url,headers = headers,  verify=False)
        data = response.content
        return data

    def post_request(self, mount_point, payload, headers={'Content-Type': 'application/json'}):
        """POST request"""
        url = "https://%s:443/dataservice/%s"%(self.vmanage_ip, mount_point)
        payload = json.dumps(payload)
        #print (payload)
        params = {'confirm':'true'}
        response = self.session[self.vmanage_ip].post(url=url, data=payload, params = params,headers=headers, verify=False)
        data = response.contentWA
        
        return data

    def put_request(self, mount_point, payload,headers={'Content-Type' : 'application/json'}):
        """POST request"""
        url = "https://%s:443/dataservice/%s"%(self.vmanage_ip, mount_point)
        # payload = json.dumps(payload)
        #print (payload)

        response = self.session[self.vmanage_ip].put(url=url, data=payload,headers=headers,verify=False)
        # print(response.status_code)
        # data = response.json()
        # return data


#https://10.68.116.127/dataservice/system/device/vedges
#https://10.68.116.127/dataservice/system/device/bootstrap/device/C1111-4P-FGL2303129J?configtype=cloudinit&inclDefRootCert=false
