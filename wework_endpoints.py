import requests

_timeout = 10
_base = 'https://members.wework.com/workplaceone/api'


class WeworkClient:
    
    def __init__(self, access_token: str, user_agent: str):
        self._session = requests.Session()
        self._session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'User-Agent': user_agent
        })

    def get(self, path: str, **params) -> dict:
        resp = self._session.get(url=f'{_base}/{path}', params=params, timeout=_timeout)
        resp.raise_for_status()
        return resp.json()
    
    def get_floor_capacity(self, floor_id, date: str, desktype=1) -> tuple[str, str]:
        endpoint = 'BuildingFloor/get-floor-capacity'
        data = self.get(endpoint, floorId=floor_id, StartDate=date, deskType=desktype)
        return data['remainingCapacity'], data['maximumCapacity']

    def get_available_for_reservation(self, floor_id, date: str, desktype=1) -> tuple[bool, str]:
        endpoint = 'Workspace/check-available-reservation-dates-single'
        data = self.get(endpoint, floorId=floor_id, checkDate=date, deskType=desktype)
        return data['Available'], data['Reason']
