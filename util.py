from datetime import datetime, timedelta
from random import randint
import re

user_agent_file = './user-agents'

def send_output(path, text, timestamp = True):
    if timestamp:
        text = datetime.now().strftime(r'%Y-%m-%d %H:%M:%S') + ' - ' + text
    if not path:
        print(text)
    else:
        try:
            fp = open(path, 'a', encoding='utf-8')
            fp.write(f'{text}\n')
            fp.close()
        except Exception as e:
            print(f"I/O Exception: unable to write to {path}")
            print(e)
            exit(1)


def parse_date_range(date_range: str, date_format: str) -> list[datetime]:
    start_date, end_date = date_range.split('-', 1)
    start_date, end_date = datetime.strptime(start_date, date_format), datetime.strptime(end_date, date_format)
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    dates = [start_date]
    current_date = start_date
    while end_date > current_date:
        current_date += timedelta(days=1)
        dates.append(current_date)
    
    return dates


def get_random_user_agent():
    user_agents = open(user_agent_file, 'r').read().splitlines()
    return user_agents[randint(0, len(user_agents)-1)]


# expects a time offset in string format (format: "XdYhZm", examples: 2d1h, 5h30m, 1d6h15m)
def time_offset_to_timedelta(time_offset: str) -> timedelta:
    search_pattern = r'^(\d*?)d?(\d*?)h?(\d*?)m?$'
    res = re.search(search_pattern, time_offset)
    days, hours, minutes = tuple([int(i) if i != '' else 0 for i in res.groups()])
    return timedelta(days=days, hours=hours, minutes=minutes)


def get_reservation(reservation_list: list[dict], date_str: str, floor_id: int) -> dict:
    date = datetime.strptime(date_str, r'%m/%d/%y')
    for reservation in reservation_list:
        reservation_date = datetime.strptime(reservation.get('bookingDate', ''), r'%Y-%m-%dT%H:%M:%S')
        if reservation.get('floorId', '') == floor_id and reservation_date == date:
            return reservation
    return {}