# Purpose
Purpose of this script is to integrate Octopii ( https://github.com/redhuntlabs/Octopii ) to audit images shared on slack org space. 

As internal employees in an organisation shares tons of files on slack as part of their day to day operations for faster collaboration,many a times they forget / might be sharing  sensitive PII which belongs to the clients / customers on public channels which can be indexed and searched by anyone inside organisation. Slack by default creates a public channel which many a times are overlooked by channel creators to make it private.

This results in a regulatory/Complaince lapse for companies dealing in regulated space such as Finance/Banking .

We already have tools such as Slack Watchman which dorks for sensitive information(passwords,secrets,PII,certain file formats) inside a slack org space . However, Slack-Watchman currently does not have capability to detect PII imformation which are part of image files.

Thanks to Project OctoPII ( https://github.com/redhuntlabs/Octopii ) which has the capability to search image files for PII information using machine learning. Currently Octopii does not have direct integration with slack as source of data, hence this script.

## who can use this tool?

bug bounty hunters / red teamers - you found a leaked slack token and extracted lot of data from slack org space using slack watchman ? you might still be missing insights on image files which might contain senstivie and critical PII information ( Passport, national ID's , bank documents uploaded internally on any public channels etc ) 

Internal product security team - you have already setup slackwatchman internally and currently monitoring slack workspace for leaked PII data on regular basis. you can setup this integration script to run as cron / lambda function everyday ( timeframe set to 'd') to gain insights on image files as well.this script complements slackwatchman.

## How to use ? 
(Runs on Python 3)
This script is quite similar to slack-watchman when it comes to config. 

1. Set env variable named 'slack_token' with value pointing to a valid token which can read all  messages inside public channels.
        export slack_token='xoxb-xxxxxx'
2. Edit the config file ,
Example Config File :

```bash
[Properties]
Time_Frame = d   #time frame can be either d,w,m,a . d( scan against image files which were uploaded from past 24 hours)  , w (uploaded from past week) . m (uploaded from past month) , a (all time)
Confidence_Threshold = 50 #threshold confidence score to consider for final result set, leave at 50 by default . check Octopii documentation to understaind more. you can increase this to 75+ if you want less false positive and also ready to miss out true negatives.
Persist_PiiFiles = True # persist result images containing PII info? ( useful for red teamers / bounty hunters ) option values : False / True
```
3. copy the config and the python script to downloaded octopii project folder ( https://github.com/redhuntlabs/Octopii ) (do install the octopii necessary dependencies / requirements ).
4. install python package requirements for the integration script.
  > slack_sdk,
  > configparser
  
5. thats it, run the script 
  ```bash
  python3 pii_slack_monitor.py
  ```

## Results
Output would follow the follwing format. 
```bash
result-date-time.zip
```
Extracted results file would have a json file "pii_results.json" which contains all the detected files with PII information , along with the metadata such as user who uploaded the file, timestamp,channel where it was uploaded and a veification attribute ,  perma_link_verify , which can be used to point out exact message / thread which contains the image .

each of the detected result set would follow the following format, 

```bash
{
        "file_name": "XXXXXXXXX.png",
        "asset_label": "Passport",
        "confidence": 97,
        "download_link": "https://files.slack.com/files-pri/XXXXXXX-XXXXXXXX/download/image.png",
        "user_created_id": "XXXXXXXXXXX",
        "user_name": "user.who.uploaded",
        "timestamp": 165600003,
        "orig_image_name": "image.png",
        "perma_link_verify": "https://<org>.slack.com/files/XXXX00000/0000XXAXXXXX/image.png",
        "shares": {
            "public": {
                "XXXXXXXXX": [
                    {
                        "reply_users": [],
                        "reply_users_count": 0,
                        "reply_count": 0,
                        "ts": "165600003.000000",
                        "channel_name": "temp-pii",
                        "team_id": "XXXXXXX",
                        "share_user_id": "XXXXXXXXX"
                    }
                ]
            }
        }
    }
```
and if Persist PII option is set in config, you would also see all the image files which contains the sensitive Info.

Enhancement plans : add PDF file format capability.

### All thanks and our sincere gratitude to the Octopii Authors , for solving an important usecase for security engineers like me :D ,
   [ https://github.com/redhuntlabs/Octopii ]
