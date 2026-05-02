import argparse
from datetime import datetime
from time import sleep
from random import uniform

import wework_endpoints
import util


desc = "This Wework reservation tool can automatically book a wework desk of a given office/floor " \
"on a given date as soon as it becomes available. Supports custom User-Agent and randomized delay " \
"between requests to evade basic anti botting blocks."

user_agent = util.get_random_user_agent()
wework_date_format = r'%m/%d/%y'
wework_date_format_human_readable = 'MM/DD/YY'
request_freq_mins = 10
max_consecutive_errors = 3

# cooldown variation multiplier. Example with 600 and 0.2: 480s <= cooldown <= 720s
requests_cooldown_variation = 0.2

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-c', '--client-id', help='Your session client_id', required=True)
parser.add_argument('-r', '--refresh-token', help='Your session refresh_token (if you are running the script manually, you can skipt this arg and enter the refresh_token in a prompt instead)')
parser.add_argument('-fi', '--floor-id', help='Floor Id(s) to book. Can be a single value, or a comma separated list of Ids (the script will try them in order, and stop once one goes through)', required=True)
parser.add_argument('-d', '--date', help=f'Booking date. Use this format: "{wework_date_format_human_readable}"', required=True)
parser.add_argument('-cd', '--cooldown', help=f'The average cooldown between availability checks (in minutes). Default value: {request_freq_mins}', default=request_freq_mins)
parser.add_argument('-so', '--start-offset', help='How long the script will wait before sending requests (format: "XdYhZm", examples: 2d1h, 5h30m, 1d6h15m). Default: start immediately')
parser.add_argument('-o', '--output', help=f'Path for the logs. Default: stdout')

args = parser.parse_args()

floors_to_book = [int(i) for i in args.floor_id.replace(' ', '').split(',')]

refresh_token = args.refresh_token
if not refresh_token:
    refresh_token = input('Enter your refresh_token: ')


# Authentication check
print('Authentication test. Attempting to fetch an access token...')
try:
    test_client = wework_endpoints.WeworkClient(args.client_id, refresh_token=refresh_token, user_agent=user_agent)
    refresh_token = test_client.get_refresh_token()
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


if args.start_offset:
    start_delta = util.time_offset_to_timedelta(args.start_offset)
    print(f'Start offset detected. Sleeping until {datetime.now() + start_delta}...')
    sleep(start_delta.total_seconds())



def sleep_short():
    sleep(uniform(2, 5))

consecutive_errors = 0

while True:

    try:
        ww_client = wework_endpoints.WeworkClient(args.client_id, refresh_token=refresh_token, user_agent=user_agent)
    except wework_endpoints.WeworkAuthError:
        util.send_output('Authentication exception occured. Exiting')
        exit(1)

    for floor in floors_to_book:
        try:
            util.send_output(f'Attempting to fetch availability of floor {floor}...')
            available, reason = ww_client.get_available_for_reservation(floor, args.date)
            if available:
                util.send_output(args.ouput, f'Floor {floor} can be booked!')
                sleep_short()
                util.send_output(args.ouput, f'Attempting to book floor {floor} for {args.date}...')
                ww_client.book_desk(floor, args.date)
                util.send_output(args.ouput, f'Request successful! Attempting to fetch reservation details...')
                sleep_short()
                reservation = util.get_reservation(ww_client.get_upcoming_reservations())
                if not reservation:
                    util.send_output(args.output, 'Unexpected error, resrvation not found, trying again next cycle')
                    raise Exception(f'Error during reservation of floor {floor} on {args.date}')
                util.send_output(args.output, f'Reservation found: '\
                                 f'{reservation.get('employeeName', '_name_')}, '\
                                 f'{reservation.get('buildingFloorName', '_floor_info_')}, '\
                                 f'{reservation.get('bookingDate', '_booking_date_')}')
                exit(0)

            else:
                util.send_output(args.ouput, f'Floor {floor} is unavailable ({reason})')

            consecutive_errors = 0

        except Exception as e:
            util.send_output(args.ouput, f'Exception occured during request cycle: {e}')
            consecutive_errors += 1

    if consecutive_errors >= max_consecutive_errors:
        util.send_output(args.output, 'Too many consecutive errors. Exiting')
    
    sleep(uniform(request_freq_mins*60*(1-requests_cooldown_variation), request_freq_mins*60*(1+requests_cooldown_variation)))