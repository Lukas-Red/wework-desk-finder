import argparse
from datetime import datetime
from time import sleep
from random import uniform
from getpass import getpass

import wework_endpoints
import util
from wework_authentication import auth_with_creds


desc = "This Wework reservation tool can automatically book a wework desk of a given office/floor " \
"on a given date as soon as it becomes available. Supports custom User-Agent and randomized delay " \
"between requests to evade basic anti botting blocks."

user_agent = util.get_random_user_agent()
wework_date_format = r'%m/%d/%y'
wework_date_format_human_readable = 'MM/DD/YY'
request_freq_mins = 10
max_consecutive_errors = 3
default_req_delay_range = '1,3'

# cooldown variation multiplier. Example with 600 and 0.2: 480s <= cooldown <= 720s
requests_cooldown_variation = 0.2

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-u', '--client-id', help='Your Wework username. Can be omitted, the script will then prompt it at runtime instead.')
parser.add_argument('-fi', '--floor-id', help='Floor Id(s) to book. Can be a single value, or a comma separated list of Ids (the script will try them in order, and stop once one goes through)', required=True)
parser.add_argument('-d', '--date', help=f'Booking date. Use this format: "{wework_date_format_human_readable}"', required=True)
parser.add_argument('-cd', '--cooldown', help=f'The average cooldown between availability checks (in minutes). Default value: {request_freq_mins}', default=request_freq_mins)
parser.add_argument('-so', '--start-offset', help='How long the script will wait before sending requests (format: "XdYhZm", examples: 2d1h, 5h30m, 1d6h15m). Default: start immediately')
parser.add_argument('-rd', '--request-delay', help=f'The range of delay between individual requests. Format: {{min_int}},{{max_int}}. Default value: {default_req_delay_range}', default=default_req_delay_range)
parser.add_argument('-o', '--output', help=f'Path for the logs. Default: stdout')

args = parser.parse_args()

floors_to_book = [int(i) for i in args.floor_id.replace(' ', '').split(',')]
delay_min, delay_max = [int(i) for i in args.request_delay]

refresh_token = args.refresh_token
if not refresh_token:
    refresh_token = input('Enter your refresh_token: ')


if not args.username:
    username = input('Wework username: ')
else:
    username = args.username

password = getpass('Wework password: ')




# Authentication check
print('Authentication test. Attempting to fetch an access token...')
try:
    test_client = wework_endpoints.WeworkClient.from_credentials(
        username=username,
        password=password,
        user_agent=user_agent
    )
    print('Test successful\n\n')
except Exception as e:
    print(f'Unable to authenticate: {e}')
    exit(1)

# Date check
try:
    test_date = datetime.strptime(args.date, wework_date_format)
except ValueError as e:
    print(f'Invalid date argument {args.date}. Use format {wework_date_format_human_readable} (python {wework_date_format})')
    print(f'Exception: {e}')
    exit(1)

# If a start offset is set, sleep that long, while periodically refreshing the access token to keep it alive
if args.start_offset:
    start_delta = util.time_offset_to_timedelta(args.start_offset)
    print(f'Start offset detected. Sleeping until {datetime.now() + start_delta}...')
    time_to_sleep_secs = start_delta.total_seconds()
    while time_to_sleep_secs > 0:
        if time_to_sleep_secs > test_client._token_duration_seconds * 0.9:
            sub_time_to_sleep = test_client._token_duration_seconds * uniform(0.8, 0.9)
            sleep(sub_time_to_sleep)
            time_to_sleep_secs -= sub_time_to_sleep
        else:
            sleep(time_to_sleep_secs)
            time_to_sleep_secs = 0
    sleep()



def sleep_short():
    sleep(uniform(delay_min, delay_max))

consecutive_errors = 0

while True:

    try:
        ww_client = wework_endpoints.WeworkClient.from_credentials(
        username=username,
        password=password,
        user_agent=user_agent
    )
    except wework_endpoints.WeworkAuthError:
        util.send_output(args.output, 'Authentication exception occured. Exiting')
        exit(1)

    for floor in floors_to_book:
        try:
            util.send_output(args.output, f'Attempting to fetch availability of floor {floor}...')
            available, reason = ww_client.get_available_for_reservation(floor, args.date)
            if available:
                util.send_output(args.output, f'Floor {floor} can be booked!')
                sleep_short()
                util.send_output(args.output, f'Attempting to book floor {floor} for {args.date}...')
                ww_client.book_desk(floor, args.date)
                util.send_output(args.output, f'Request successful! Attempting to fetch reservation details...')
                sleep_short()
                reservation = util.get_reservation(ww_client.get_upcoming_reservations(), args.date, floor)
                if not reservation:
                    util.send_output(args.output, 'Unexpected error, resrvation not found, trying again next cycle')
                    raise Exception(f'Error during reservation of floor {floor} on {args.date}')
                util.send_output(args.output, f'Reservation found: '\
                                 f'{reservation.get('employeeName', '_name_')}, '\
                                 f'{reservation.get('buildingFloorName', '_floor_info_')}, '\
                                 f'{reservation.get('bookingDate', '_booking_date_')}')
                exit(0)

            else:
                util.send_output(args.output, f'Floor {floor} is unavailable ({reason})')

            consecutive_errors = 0

        except Exception as e:
            util.send_output(args.output, f'Exception occured during request cycle: {e}')
            consecutive_errors += 1

    if consecutive_errors >= max_consecutive_errors:
        util.send_output(args.output, 'Too many consecutive errors. Exiting')
    
    sleep(request_freq_mins * 60 * uniform(1-requests_cooldown_variation, 1+requests_cooldown_variation))