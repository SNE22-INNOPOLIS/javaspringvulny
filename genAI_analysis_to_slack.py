#!/usr/bin/env python3

# Import modules
import json
import requests
import os
import tiktoken 

def sanitize_json(file_path):
    """
    Load, sanitize, and format a JSON file.
    - Removes whitespace.
    - Strips sensitive information like credentials.
    - Ensures the JSON format is correct.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)  # Load the JSON file

        # Remove sensitive information (e.g., keys, tokens, passwords)
        sensitive_keys = ['password', 'token', 'apikey', 'key', 'secret']
        def remove_sensitive_info(d):
            if isinstance(d, dict):
                return {k: remove_sensitive_info(v) for k, v in d.items() if k.lower() not in sensitive_keys}
            elif isinstance(d, list):
                return [remove_sensitive_info(item) for item in d]
            else:
                return d

        sanitized_data = remove_sensitive_info(data)

        # Ensure the JSON is formatted and compact
        sanitized_data_str = json.dumps(sanitized_data, separators=(',', ':'))  # Remove unnecessary spaces

        # Return the sanitized JSON as a Python object
        return json.loads(sanitized_data_str)
    except Exception as e:
        raise Exception(f"Error sanitizing file {file_path}: {str(e)}")

def send_slack_error(message):
    """
    Send an error message to Slack if sanitization or processing fails.
    """
    slack_webhook_url = os.environ.get('SLACK_WEBHOOKS')
    if not slack_webhook_url:
        print("Slack webhook URL is missing.")
        return
    slack_payload = {"text": f"Error: {message}"}
    requests.post(slack_webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(slack_payload))

def count_tokens(text, model="gpt-4"):
    """
    Count the tokens in a given text for a specific OpenAI model.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def fragment_data(data_str, max_tokens=4096):
    """
    Fragment the data into chunks that fit within the token limit.
    """
    tokens = count_tokens(data_str)
    if tokens <= max_tokens:
        return [data_str]  # Return as a single chunk if within the limit

    encoding = tiktoken.encoding_for_model("gpt-4")
    tokenized = encoding.encode(data_str)
    chunks = []

    while tokenized:
        chunk = tokenized[:max_tokens]
        tokenized = tokenized[max_tokens:]
        chunks.append(encoding.decode(chunk))

    return chunks

def send_openai_request(chunk, headers, api_url):
    """
    Send a single chunk to the OpenAI API and return the response.
    """
    payload = {
        "model": "gpt-4o",  
        "messages": [
            {"role": "user", "content": f"Analyze this data: {chunk}. Provide a unified result of the vulnerabilities beautifully, detailing each line of code. Use fun emojis to indicate the severity of each vulnerability. Include a summary and recommendations for fixing them at the end."}
        ]
    }
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"OpenAI API Error {response.status_code}: {response.text}")

def main():
    try:
        # Sanitize the SAST and DAST JSON files
        sast_data = sanitize_json('sast.json')
        dast_data = sanitize_json('dast.json')

        # Convert the sanitized JSON data to strings
        sast_data_str = json.dumps(sast_data)
        dast_data_str = json.dumps(dast_data)

        # Concatenate the two data strings
        combined_data_str = f"SAST Data: {sast_data_str}\n\nDAST Data: {dast_data_str}"

        # Set up the OpenAI API key, URL, and headers
        OPENAPI_KEY = os.environ.get('OPENAI_API_TOKEN')
        if not OPENAPI_KEY:
            raise ValueError("OpenAI API token is missing.")

        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAPI_KEY}"
        }

        # Fragment the data if it exceeds the token limit
        max_tokens = 4096 - 500  # Reserve tokens for the instruction prompt
        chunks = fragment_data(combined_data_str, max_tokens)

        # Send each chunk to the API and collect responses
        responses = []
        for chunk in chunks:
            response = send_openai_request(chunk, headers, api_url)
            responses.append(response)

        # Combine all responses
        final_response = "\n\n".join(responses)

        # Send the final response to Slack
        slack_webhook_url = os.environ.get('SLACK_WEBHOOKS')
        if not slack_webhook_url:
            raise ValueError("Slack webhook URL is missing.")

        slack_payload = {"text": final_response}
        slack_response = requests.post(slack_webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(slack_payload))

        if slack_response.status_code == 200:
            print("Great job! Analysis data was sent to Slack successfully.")
        else:
            print(f"Failed to send analysis data to Slack with status code: {slack_response.status_code}")
            print("Slack response:", slack_response.text)
    except Exception as e:
        error_message = str(e)
        print(f"An error occurred: {error_message}")
        send_slack_error(error_message)

if __name__ == "__main__":
    main()
