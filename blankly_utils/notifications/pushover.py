#!/usr/bin/env python3

import sys
import requests
import os
from dotenv import load_dotenv

load_dotenv()
PUSHOVER_USER_ID = os.environ["PUSHOVER_USER_ID"]
PUSHOVER_API_TOKEN = os.environ["PUSHOVER_API_TOKEN"]


def send_message(text):
    """Send a message"""
    payload = {"message": text, "user": PUSHOVER_USER_ID, "token": PUSHOVER_API_TOKEN}
    base_url = "https://api.pushover.net"
    endpoint = "/1/messages.json"
    url = base_url + endpoint
    r = requests.post(
        url,
        data=payload,
        headers={"User-Agent": "Python"},
    )
    return r


def main():
    """Main function to send notification using command line."""
    r = send_message(" ".join(sys.argv[1:]))
    if r.status_code != 200:
        print("Error sending", r.text)


if __name__ == "__main__":
    main()
