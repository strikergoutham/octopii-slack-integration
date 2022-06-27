import os
import subprocess
from slack_sdk import WebClient
import time
from datetime import date
import datetime
import requests
import json
import shutil
import configparser

#for timestamp calculation
day_epoch = 86400
week_epoch = 604800
month_epoch = 2592000
current_timestamp = int(time.time())
slack_token=os.environ['slack_token']

#read from config
config = configparser.ConfigParser()
config.read('slack_config.conf')
time_frame = config['Properties']['Time_Frame'] #d,w,m,all
confidence_threshold = int(config['Properties']['Confidence_Threshold'])
persist_piifiles = config['Properties']['Persist_PiiFiles']
persist_piifiles = persist_piifiles.lower()
execution_date = time.strftime("%Y%m%d-%H%M%S")



result_list = []

bearer_val = "Bearer "+slack_token
headers = {
            'Authorization': bearer_val
}

timestamp_from = ""

def setTimeStamp():
    global timestamp_from
    if time_frame == "d":
        tf = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_timestamp - day_epoch))
        date = datetime.datetime.strptime(tf, "%Y-%m-%d %H:%M:%S")
        timestamp_from = datetime.datetime.timestamp(date)
    if time_frame == "w":
        tf = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_timestamp - week_epoch))
        date = datetime.datetime.strptime(tf, "%Y-%m-%d %H:%M:%S")
        timestamp_from = datetime.datetime.timestamp(date)
    if time_frame == "m":
        tf = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_timestamp - month_epoch))
        date = datetime.datetime.strptime(tf, "%Y-%m-%d %H:%M:%S")
        timestamp_from = datetime.datetime.timestamp(date)
    if time_frame == "a":
        timestamp_from = ""

def connectSlack():
    try:
        client = WebClient(token=slack_token)
        return client
    except:
        print("[-]Error connecting! Please check the slack token provided...")
        exit()

def callOctopii():
    dir = "./temp_output_slack_pii"
    cmd = "python3 octopii.py "+ dir +" > result.json"
    subprocess.call(cmd,shell=True)

def getAllSlackFiles(client):
    resp = client.files_list(types="images",ts_from=timestamp_from)
    numPages = resp['paging']['pages']
    total_res = resp['paging']['total']
    last_page_count = total_res % 100
    os.mkdir("./temp_output_slack_pii")
    for i in range(0,numPages):
        count = 100
        pageNum = i+1
        resp = client.files_list(types="images",ts_from=timestamp_from,page=pageNum,count=count)
        for j in range(0,len(resp['files'])):
            file_id = resp['files'][j]['id']
            url = resp['files'][j]['url_private_download']
            r = requests.get(url, allow_redirects=True,headers=headers)
            ext = r.headers.get('content-type')
            ext = ext.split("/")[-1]
            file_output = "./temp_output_slack_pii/"+file_id + "." + ext
            open(file_output, 'wb').write(r.content)
            
def parseOctopiiResults(client):
    global result_list
    try:
        with open("result.json",'r') as f:
            content = f.read()
            aftersplit = content.split("[")[-1]
            aftersplit = "[" + aftersplit
            res_list = json.loads(aftersplit)
            for obj in res_list:
                if obj['confidence'] >= confidence_threshold:
                    file_name = obj['file_name'].split(".")[0]
                    fileData = client.files_info(file = file_name)
                    fileData = dict(fileData['file'])
                    usernameData = client.users_info(user=fileData['user'])
                    final_res = {'file_name':obj['file_name'],'asset_label':obj['asset_type'],'confidence':obj['confidence'],'download_link':fileData['url_private_download'],'user_created_id':fileData['user'],'user_name':usernameData['user']['name'],'timestamp':fileData['timestamp'],'orig_image_name':fileData['name'],'perma_link_verify':fileData['permalink'],'shares':fileData['shares']}
                    final_res_copy = final_res.copy()
                    result_list.append(final_res_copy)
        with open('pii_results.json', 'w', encoding='utf-8') as f:
             json.dump(result_list, f, ensure_ascii=False, indent=4)
                
    except Exception as e:
        print("[-]error in parsing result........")
        print(e)
        print(usernameData)

def cleanUp():
    tmp_dir = './temp_output_slack_pii/'
    if persist_piifiles == "true":
        fileList = []
        with open('pii_results.json') as f2:
            content = f2.read()
            contentdict = json.loads(content)
            for obj in contentdict:
                fileList.append(obj['file_name'])
        for f3 in os.listdir(tmp_dir):
            if f3 not in fileList:
                os.remove(os.path.join(tmp_dir, f3))
        shutil.move("./pii_results.json",tmp_dir+"pii_results.json")
        os.remove("./result.json")
        output_filename = "results" + execution_date
        shutil.make_archive(output_filename, 'zip', tmp_dir)
        
    else:
        for f3 in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f3))
        shutil.move("./pii_results.json",tmp_dir+"pii_results.json")
        os.remove("./result.json")
        output_filename = "results" + execution_date
        shutil.make_archive(output_filename, 'zip', tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=False, onerror=None)

def PreReq():
    tmp_dir = './temp_output_slack_pii/'
    if os.path.exists(tmp_dir):
       shutil.rmtree(tmp_dir, ignore_errors=False, onerror=None)
    if os.path.exists("./result.json"):
       os.remove("./result.json")
    if os.path.exists("./pii_results.json"):
       os.remove("./pii_results.json")


def main():
    PreReq()
    slack_conn = connectSlack()
    setTimeStamp()
    print("[+]getting image files from slack ...")
    getAllSlackFiles(slack_conn)
    print("[+]running Octopii....")
    callOctopii()
    print("[+]Parsing results....")
    parseOctopiiResults(slack_conn)
    print("[+]Generating output and Cleaning up......")
    cleanUp()

main()
