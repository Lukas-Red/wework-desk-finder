import requests
from time import sleep
from datetime import timezone, datetime
import wework_authentication

_cooldown_between_retries = 1
_timeout = 10
_base = 'https://members.wework.com/workplaceone/api'
_oauth_endpoint = 'https://idp.wework.com/oauth/token'


class WeworkClient:
    
    def __init__(self, access_token: str, refresh_token: str, client_id: str, token_duration_sec:int, user_agent: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.token_duration_sec = token_duration_sec
        self.user_agent = user_agent
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': user_agent,
            'Authorization': f'bearer {access_token}'
        })


    @classmethod
    def from_credentials(cls, username: str, password: str, user_agent: str):
        json_resp = wework_authentication.auth_with_creds(
            username=username, 
            password=password,
            user_agent=user_agent
        )
        return cls(
            json_resp['access_token'], 
            json_resp['refresh_token'], 
            json_resp['client_id'], 
            json_resp['expires_in'],
            user_agent=user_agent
        )

    @classmethod
    def from_refresh_token(cls, refresh_token: str, client_id: str, user_agent: str):
        json_resp = wework_authentication.auth_with_refresh_token(
            refresh_token=refresh_token,
            client_id=client_id,
            user_agent=user_agent
        )
        return cls(
            json_resp['access_token'], 
            json_resp['refresh_token'], 
            client_id=client_id, 
            token_duration_sec = json_resp['expires_in'],
            user_agent=user_agent
        )



    def get(self, path: str, **params) -> dict:

        resp = self._session.get(url=f'{_base}/{path}', params=params, timeout=_timeout)

        # if the status and response payload match an invalid access_token (401 + no body), try to refresh once
        if resp.status_code == 401 and resp.text == '':
            sleep(_cooldown_between_retries)
            self.refresh_auth()
            sleep(_cooldown_between_retries)
            resp = self._session.get(url=f'{_base}/{path}', params=params, timeout=_timeout)

        resp.raise_for_status()
        return resp.json()


    def post(self, path: str, json_body: dict, **params):

        resp = self._session.post(url=f'{_base}/{path}', json=json_body, params=params, timeout=_timeout)

        # if the status and response payload match an invalid access_token (401 + no body), try to refresh once
        if resp.status_code == 401 and resp.text == '':
            sleep(_cooldown_between_retries)
            self.refresh_auth()
            sleep(_cooldown_between_retries)
            resp = self._session.post(url=f'{_base}/{path}', json=json_body, params=params, timeout=_timeout)

        resp.raise_for_status()
        return resp.json()


    def get_floor_capacity(self, floor_id: int, date: str, desktype=1) -> tuple[int, int]:
        endpoint = 'BuildingFloor/get-floor-capacity'
        data = self.get(endpoint, floorId=floor_id, StartDate=date, deskType=desktype)
        return data['remainingCapacity'], data['maximumCapacity']


    def get_available_for_reservation(self, floor_id, date: str, desktype=1) -> tuple[bool, str]:
        endpoint = 'Workspace/check-available-reservation-dates-single'
        data = self.get(endpoint, floorId=floor_id, checkDate=date, deskType=desktype)
        # When room is available, Weworks API does not return a Reason, hence the default
        return data['Available'], data.get('Reason', '')

    # see the response sample for the json structure
    def get_upcoming_reservations(self) -> list[dict]:
        endpoint = 'common-booking/get-app-upcoming-bookings'
        return self.get(
            endpoint,
            isPastBooking =  'false',
            platFormType = 1,
            startDate = '',
            endDate = ''
        )
    

    def book_desk(self, floor_id: int, date: str, desktype=1):
        endpoint = 'Workspace/reserve-workspace'
        # example value for CEST: "+02:00"
        utc_offset = datetime.now(timezone.utc).astimezone().isoformat()[-6:]
        
        post_body = {
            'startDate': date,
            'endDate': date,
            'visitPurpose': '',
            'FrequencyType': 3,
            'UserId': 0,
            'buildingFloorName': '',
            'isBookingonBehalf': 'false',
            'DeskType': desktype,
            'applicationType': 'WeWorkWorkplace',
            'platformType': 'WEB',
            'AllowBookingInOtherZones': 'false',
            'offSet': utc_offset,
            'currentLocationDate': datetime.now().strftime(r'%m/%d/%Y'),
            'TriggerCalenderEvent': 'true',
            'reservationType': 5,
            'selectedWorkspace': 0,
            'floorId': floor_id
        }
        self.post(endpoint, post_body)


    def refresh_auth(self):
        try:
            json_resp = wework_authentication.auth_with_refresh_token(
                self.refresh_token,
                self.client_id,
                self.user_agent
            )
        except Exception as e:
            raise WeworkAuthError(str(e)) from e
        
        self._session.headers.update({
            'Authorization': f'bearer {json_resp['access_token']}'
        })
        self.refresh_token = json_resp['refresh_token']
        self.token_duration_sec = json_resp['expires_in']

class WeworkAuthError(Exception):
    # custom exception to distinguish auth errors
    pass
