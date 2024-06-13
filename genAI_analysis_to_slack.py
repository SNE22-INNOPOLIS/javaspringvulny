#!/usr/bin/env python3

# import modules
import json
import requests
import os

# loading the snyk.json file
with open('snyk.json', 'r') as file:
    snyk_data = json.load(file)

# converting the JSON data to a string
snyk_data_str = json.dumps(snyk_data)

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
        {"role": "user", "content": f"Start with summarizing this:\n{snyk_data_str} with only the lines of the code that are vulnerable. Add the vulnerability for each lines of code. Use fun emojis to indicate the severity of each vulnerability"}
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
        "text": f"Here is the analysis of the Snyk scan results:\n{analysis_data}"
    }

    # sending the analysis data to Slack
    slack_response = requests.post(slack_webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(slack_payload))

    # checking if the Slack request was successful
    if slack_response.status_code == 200:
        print("Great job! Analysis data sent to Slack successfully.")
    else:
        print(f"Failed to send analysis data to Slack with status code: {slack_response.status_code}")
        print("Slack response:", slack_response.text)
else:
    print(f"Request to OpenAI API failed with status code: {response.status_code}")
    print("OpenAI response:", response.text)
