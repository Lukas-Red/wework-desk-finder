import requests
from time import sleep

_cooldown_between_retries = 1
_timeout = 10
_base = 'https://members.wework.com/workplaceone/api'
_oauth_endpoint = 'https://idp.wework.com/oauth/token'


class WeworkClient:
    
    def __init__(self, client_id: str, refresh_token: str, user_agent: str, authenticate_now = True):
        self._client_id = client_id
        self._refresh_token = refresh_token
        self._user_agent = user_agent
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': user_agent
        })
        if authenticate_now:
            self._set_access_token_from_refresh()
        

    def get(self, path: str, **params) -> dict:
        resp = self._session.get(url=f'{_base}/{path}', params=params, timeout=_timeout)
        # if the status and response payload match an invalid access_token (401 + no body), try to refresh once
        if resp.status_code == 401 and resp.text == '':
            sleep(_cooldown_between_retries)
            self._set_access_token_from_refresh()
            sleep(_cooldown_between_retries)
            resp = self._session.get(url=f'{_base}/{path}', params=params, timeout=_timeout)
        resp.raise_for_status()
        return resp.json()
    
    # TODO check if the endpoint really returns ints
    def get_floor_capacity(self, floor_id, date: str, desktype=1) -> tuple[str, str]:
        endpoint = 'BuildingFloor/get-floor-capacity'
        data = self.get(endpoint, floorId=floor_id, StartDate=date, deskType=desktype)
        return data['remainingCapacity'], data['maximumCapacity']

    def get_available_for_reservation(self, floor_id, date: str, desktype=1) -> tuple[bool, str]:
        endpoint = 'Workspace/check-available-reservation-dates-single'
        data = self.get(endpoint, floorId=floor_id, checkDate=date, deskType=desktype)
        return data['Available'], data['Reason']

    def set_access_token_from_refresh(self):
        response = requests.post(
            _oauth_endpoint,
            json={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
            },
            headers={"Content-Type": "application/json", "User-Agent": f"{self._user_agent}"}, timeout=_timeout)
        if response.status_code >= 400:
            raise WeworkAuthError(f'Authentication error - {response.status_code}: {response.text}')
        self._session.headers.update({
            'Authorization': f'Bearer {response.json()['access_token']}'
        })
        self._refresh_token = response.json()['refresh_token']
        

class WeworkAuthError(Exception):
    # custom exception to distinguish auth errors
    pass
