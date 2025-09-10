import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

def get_zoom_access_token():
    url = "https://zoom.us/oauth/token"
    client_id = settings.ZOOM_CLIENT_ID
    client_secret = settings.ZOOM_CLIENT_SECRET
    account_id = settings.ZOOM_ACCOUNT_ID

    payload = {
        "grant_type": "account_credentials",
        "account_id": account_id
    }

    response = requests.post(url, data=payload, auth=HTTPBasicAuth(client_id, client_secret))
    data = response.json()
    return data.get("access_token")


def create_zoom_meeting(topic="Skill Session"):
    token = get_zoom_access_token()
    url = f"https://api.zoom.us/v2/users/{settings.ZOOM_EMAIL}/meetings"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "topic": topic,
        "type": 1  # instant meeting
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()  # contains join_url & start_url
