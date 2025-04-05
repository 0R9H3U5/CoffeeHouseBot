#!/usr/bin/env python3
"""
Google Sheets Authentication Script
This script authenticates with Google Sheets API and saves the token to token.json

This script is useful as a one-off to generate a token when running the bot in an environment
which does not have a browser configured.
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import webbrowser 

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    """Shows basic usage of the Google Sheets API.
    Prints the names and majors of students in a sample spreadsheet.
    """
    creds = None
    print(webbrowser._browsers)
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            try:
                # Try browser-based authentication first
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Browser authentication failed: {e}")
                print("Falling back to console-based authentication...")
                # Fall back to console-based authentication
                creds = flow.run_console()
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    print("Authentication successful! Token saved to token.json")

if __name__ == '__main__':
    main() 