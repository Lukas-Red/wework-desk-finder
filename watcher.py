import argparse
import random
from datetime import datetime, timedelta
from time import sleep

import util
from wework_endpoints import WeworkClient

desc = "This script was a proof of concept for the booker script. " \
"The goal here is to watch one or multiple wework spaces for availability. " \
"The space, frequency and output method can all be configured. Authentication requires a valid client_id and refresh_token. " \
"If you are unsure how to get those, check out the github page: https://github.com/Lukas-Red/wework-desk-finder \n" \
"Username/password authentication is not currently implemented. " \
"The script will stop automatically once all the watched dates are in the past."

user_agent = util.get_random_user_agent()
default_day_threshold = 10
default_output = './wework_floor_watch.txt'
input_date_format = r'%Y/%m/%d'
wework_date_format = r'%m/%d/%Y'
default_freq = 10

# The variable range to wait between cooldowns
# 0.2 means the watcher will wait anywhere between 0.8*cooldown and 1.2*cooldown. 0 means it always waits the exact cooldown
request_cooldown_variation = 0.2


parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-c', '--client-id', help='Your session client_id', required=True)
parser.add_argument('-r', '--refresh-token', help='Your session refresh_token (if you are running the script manually, you can skipt this arg and enter the refresh_token in a prompt instead)')
parser.add_argument('-fi', '--floor-id', help='Floor Id(s) to watch. Can be a single value, or a comma separated list of Ids', required=True)
parser.add_argument('-cd', '--cooldown', help=f'The average cooldown the watcher should wait between floor checks (in minutes). Default value: {default_freq}', default=default_freq)
parser.add_argument('-d', '--date', help='A date or multiple to watch for the specified floor(s). Dates MUST be in the yyyy/mm/dd format. You can set multiple dates via a comma separated list, a range of dates with a hyphen (-), or both', required=True)
parser.add_argument('-dt', '--day-threshold', help=f'Only query for dates that are \'day-threshold\' days away or fewer. Default value: {default_day_threshold}', default=default_day_threshold, type=int)
parser.add_argument('-o', '--output', help=f'Path of the file where watcher should write its data. Default value: {default_output}', default=default_output)
parser.add_argument('-s', '--stdout', help='Set this flag to output the data to stdout instead of a file. Any output path specified with -o will be ignored', action='store_true')

args = parser.parse_args()


floors_to_watch = args.floor_id.split(',')

refresh_token = args.refresh_token
if not refresh_token:
    refresh_token = input("Enter your refresh_token: ")


# Authentication 
print("Attempting to fetch an access token...")
try:
    ww_client = WeworkClient(args.client_id, refresh_token=refresh_token, user_agent=user_agent)
except Exception as e:
    print(f'Unable to authenticate: {e}')
    exit(1)




# Parse dates
in_dates = args.date.split(',')
dates = []
for in_date in in_dates:
    if '-' in in_date:
        for date in util.parse_date_range(in_date, input_date_format):
            dates.append(date)
    else:
        dates.append(datetime.strptime(in_date, input_date_format))

dates = list(set(dates))
dates.sort()

# Parse floor_ids
floor_ids = args.floor_id.split(',')


# Immediate write test
util.send_output(args.stdout, f'\n\n{datetime.now()} - Starting watch on floors {floors_to_watch} every {args.cooldown} minutes', args.output)


# DEBUG PRINTS
# print(f"DEBUG ONLY\naccess_token:\n{access_token}\nrefresh_token:\n{refresh_token}")
for date in dates:
    print(date)

print(f'\n\n{datetime.now()} - Starting watch on floors {floors_to_watch} every {args.cooldown} minutes')

# define a secondary cooldown, that will increase if the server continually gives errors
current_cooldown = args.cooldown

# The script runs while there are dates left to scan, while skipping the ones above the day_threshold value
while dates:
    first_write = True

    for floor_id in floor_ids:

        for date in dates:
            if date > datetime.now() + timedelta(days=args.day_threshold):
                continue
            if first_write:
                util.send_output('\n\n')
                first_write = False

            try:
                # TODO handle results from both endpoints
                ww_client
            except Exception as e:
                pass

    # run through loop to remove outdated dates

    # scales the cooldown based on request_cooldown_variation
    rnd_cd_mutilplier = random.random() * request_cooldown_variation * 2 - request_cooldown_variation + 1
    sleep(args.cooldown * 60 * rnd_cd_mutilplier)