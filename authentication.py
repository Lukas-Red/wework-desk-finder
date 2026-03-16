import requests


timeout_seconds = 10

oauth_endpoint = 'https://idp.wework.com/oauth/token'


def get_access_token_from_refresh(refresh_token, client_id, user_agent):
    try:
        response = requests.post(
        oauth_endpoint,
        json={
            "grant_type": "refresh_token",
            "refresh_token": f"{refresh_token}",
            "client_id": f"{client_id}",
        },
        headers={"Content-Type": "application/json", "User-Agent": f"{user_agent}"}, timeout=timeout_seconds)
        response.raise_for_status()
        return response.json()["access_token"], response.json()["refresh_token"], ""
    except Exception as e:
        return "", "", f"Exception during access token request: {e}"
