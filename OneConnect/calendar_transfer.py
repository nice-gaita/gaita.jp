from __future__ import print_function
import datetime
import os
import pickle
import re

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ===== 環境変数の読み込み =====
load_dotenv()
SOURCE_CALENDAR_ID = os.getenv("SOURCE_CALENDAR_ID")
DEST_CALENDAR_ID = os.getenv("DEST_CALENDAR_ID")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "credentials.json")

# ===== Google API 認証 =====
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds)

# ===== 場所の整形関数 =====
def extract_location(location):
    if location:
        match = re.match(r'(東京都|神奈川県|埼玉県|千葉県)[\w\d\sー\-区市町村]+', location)
        return match.group(0) if match else ''
    return ''

# ===== メイン処理 =====
def transfer_events():
    service = get_service()

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=SOURCE_CALENDAR_ID,
        timeMin=now,
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print("予定が見つかりませんでした。")
        return

    for event in events:
        start = event['start']
        end = event['end']
        location = extract_location(event.get('location', ''))

        new_event = {
            'summary': '予定登録済み',
            'location': location,
            'start': start,
            'end': end,
        }

        service.events().insert(calendarId=DEST_CALENDAR_ID, body=new_event).execute()
        print(f"登録完了: {start.get('dateTime', start.get('date'))}")

# ===== 実行 =====
if __name__ == '__main__':
    transfer_events()