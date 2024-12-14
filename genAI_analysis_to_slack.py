#!/usr/bin/env python3

# import modules
import json
import requests
import os

# Load data from sast_dvna.json
with open('sast_dvna.json', 'r') as file_dvna:
    sast_dvna_data = json.load(file_dvna)

# Load data from sast_javaspring.json
with open('sast_javaspring.json', 'r') as file_javaspring:
    sast_javaspring_data = json.load(file_javaspring)

# converting the sast JSON data to a string
sast_data_str1 = json.dumps(sast_javaspring_data)
sast_data_str2 = json.dumps(sast_dvna_data)

# loading the dast.json file
with open('dast.json', 'r') as file:
    dast_data = json.load(file)

# converting the dast JSON data to a string
dast_data_str = json.dumps(dast_data)

# setting up the OpenAI API key, API URL and headers
OPENAPI_KEY = os.environ['OPENAI_API_TOKEN']
api_url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAPI_KEY}"
}

# creating the payload for the API request
payload = {
    "model": "gpt-4o",
    "messages": [
        {"role": "user", "content": f"Analyze this SAST data: {sast_data_str1}, {sast_data_str2} and DAST data: {dast_data_str}. Provide a unified result of the vulnerabilities beautifully, detailing each line of code. The vulnerabilities should be categorized into SAST and DAST sections. Use fun emojis to indicate the severity of each vulnerability. Include a summary of all vulnerabilities and a recommendations section for fixing the vulnerabilities at the end of the feedback. Overall, format the feedback for presentation in a slack channel. Make it understandable by anyone."}
    ]
}

# Sending the request to the OpenAI API
response = requests.post(api_url, headers=headers, json=payload)

# Checking if the request was successful
if response.status_code == 200:
    # parsing the response
    response_data = response.json()
    analysis_data = response_data['choices'][0]['message']['content']
    # print("Analysis:\n", analysis)

    # setting up the Slack webhook URL
    slack_webhook_url = os.environ['SLACK_WEBHOOKS']

    # creating the payload for the Slack request
    slack_payload = {
        "text": f"{analysis_data}"
    }

    # sending the analysis data to Slack
    slack_response = requests.post(slack_webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(slack_payload))

    # checking if the Slack request was successful
    if slack_response.status_code == 200:
        print("Great job! Analysis data was sent to Slack successfully.")
    else:
        print(f"Failed to send analysis data to Slack with status code: {slack_response.status_code}")
        print("Slack response:", slack_response.text)
else:
    print(f"Request to OpenAI API failed with status code: {response.status_code}")
    print("OpenAI response:", response.text)

exit()
