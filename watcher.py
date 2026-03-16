import argparse
import authentication

desc = "The goal of this script is to watch one or multiple wework spaces for availability." \
" The space, frequency and output method can all be configured. Authentication requires a valid client_id and refresh_token. " \
"If you are unsure how to get those, check out the github page: https://github.com/Lukas-Red/wework-desk-finder \n" \
"Username/password authentication is not currently implemented."

default_spoofed_user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0'


parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-c', '--client-id', help='Your session client_id', required=True)
parser.add_argument('-r', '--refresh-token', help='Your session refresh_token (if you are running the script manually, you can omit the token from the args and enter it in a prompt instead)')
parser.add_argument('-u', '--user-agent', help='User agent header that will be used in all requests (default is a Linux/Firefox one)', default=default_spoofed_user_agent)


args = parser.parse_args()

print('\n')

user_agent = args.user_agent
client_id = args.client_id
refresh_token = args.refresh_token
if not refresh_token:
    refresh_token = input("Enter your refresh_token: ")

print("Attempting to fetch an access token...")
access_token, refresh_token, error = authentication.get_access_token_from_refresh(refresh_token=refresh_token, client_id=client_id, user_agent=user_agent)
if error:
    print(f"Error occured during the access_token request:\n{error}")
print("Success")

