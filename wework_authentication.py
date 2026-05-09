from hashlib import sha256
from base64 import urlsafe_b64encode
from secrets import token_bytes
from urllib.parse import urlparse, parse_qs
from time import sleep
from random import uniform
import requests

"""
This method reproduces the wework authentication flow
Wework uses Auth0's OAuth scheme with PKCE, detailed here: https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-pkce
This implementation is based on RFC 7636: https://datatracker.ietf.org/doc/html/rfc7636
"""
def wework_username_password_athentication(username: str, password: str, user_agent: str, sleep_floor = 1, sleep_ceil = 3) -> dict[str, str]:

    # data generation
    print('\nStarting the Wework authentication flow. Generating state, nonce, code_verifier and code_challenge.')
    state = urlsafe_b64encode(token_bytes(32)).rstrip(b'=').decode()
    nonce = urlsafe_b64encode(token_bytes(32)).rstrip(b'=').decode()
    code_verifier = urlsafe_b64encode(token_bytes(32)).rstrip(b'=').decode()
    code_challenge = urlsafe_b64encode(sha256(code_verifier.encode('ascii')).digest()).rstrip(b'=').decode()

    session = requests.Session()

    # Request 1 - base call, set cookies
    req1_url = 'https://members.wework.com/'
    print(f'\n\nRequesting base page at "{req1_url}"...')
    resp = session.get(url='https://members.wework.com/')
    print(resp.status_code)
    resp.raise_for_status
    sleep(uniform(sleep_floor, sleep_ceil))


    # Request 2 - auth0 config - get client_id
    req2_url = 'https://members.wework.com/workplaceone/api/auth0/v2/config?domain=members.wework.com'
    print(f'\n\nRequesting domain config at "{req2_url}"...')
    resp = session.get(url=req2_url)
    print(resp.status_code)
    resp.raise_for_status
    client_id = resp.json()['clientId']
    sleep(uniform(sleep_floor, sleep_ceil))


    # Request 3 - Authorize
    params = {
        'client_id': client_id,
        'scope': 'openid profile email offline_access',
        'display': '',
        'prompt': '',
        'screen_hint': 'login',
        'audience': 'wework',
        'redirect_uri': 'https://members.wework.com/workplaceone/api/auth0/v2/callback?domain=members.wework.com/workplaceone',
        'ui_locales': 'en-US',
        'ext-weblogin': 'true',
        'response_type': 'code',
        'response_mode': 'query',
        'state': state,
        'nonce': nonce,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'auth0Client': 'eyJuYW1lIjoiQGF1dGgwL2F1dGgwLWFuZ3VsYXIiLCJ2ZXJzaW9uIjoiMi4yLjMifQ=='
    }
    session.headers.update({'referer': 'https://members.wework.com/'})
    req3_url = 'https://idp.wework.com/authorize'
    print(f'\n\nRequesting authorization at "{req3_url}"...')
    resp = session.get(
        url=req3_url,
        params=params,
        allow_redirects=True
    )
    print(resp.status_code)
    resp.raise_for_status
    post_redirect_url = resp.url
    state_auth0 = parse_qs(urlparse(post_redirect_url).query)['state'][0]
    sleep(uniform(sleep_floor, sleep_ceil))


    # Request 4 part 1 - Post username
    body = {
        'state': state_auth0,
        'username': username,
        'js-available': 'true',
        'webauthn-available': 'true',
        'is-brave': 'false',
        'webauthn-platform-available': 'false',
        'action': 'default'
    }
    session.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'referer': post_redirect_url
    })
    print(f'\n\nSending username at {post_redirect_url}...')
    resp = session.post(
        url = post_redirect_url,
        data=body,
        allow_redirects=True
    )
    print(resp.status_code)
    resp.raise_for_status
    password_url = resp.url
    sleep(uniform(sleep_floor, sleep_ceil))


    # Request 4 part 2 - Post password
    body = {
        'state': state_auth0,
        'username': username,
        'password': password,
        'action': 'default'
    }
    session.headers.update({
        'referer': password_url
    })
    print(f'\n\nSending password at {password_url}...')
    resp = session.post(
        url = password_url,
        data = body,
        allow_redirects = True
    )
    print(resp.status_code)
    resp.raise_for_status
    new_state_after_creds = parse_qs(urlparse(resp.url).query)['state'][0]
    sleep(uniform(sleep_floor, sleep_ceil))

    
    # Request 5 - MFA capabilities
    body = {
        'state': new_state_after_creds,
        'action': 'default',
        'js-available': 'true',
        'webauthn-available': 'true',
        'is-brave': 'false',
        'webauthn-platform-available': 'false'
    }
    print(f'\n\nSending MFA capabilities at {resp.url}...')
    resp = session.post(
        url=resp.url,
        data=body,
        allow_redirects=True
    )
    print(resp.status_code)
    resp.raise_for_status
    code = parse_qs(urlparse(resp.url).query)['code'][0]
    sleep(uniform(sleep_floor, sleep_ceil))


    # Request 6 - access_token
    access_token_url = 'https://idp.wework.com/oauth/token'
    body = {
        'client_id': client_id,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://members.wework.com/workplaceone/api/auth0/v2/callback?domain=members.wework.com/workplaceone'
    }
    session.headers.update({
        'referer': 'https://members.wework.com/', 
        'auth0-client': 'eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjIuMS4yIn0='
    })
    print(f'\n\nRequesting access token at {access_token_url}...')
    print(resp.status_code)
    resp.raise_for_status
    resp = session.post(url=access_token_url, data=body)
    return resp.json()
