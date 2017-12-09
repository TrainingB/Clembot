import datetime
import time
from datetime import timedelta
import calendar

def fetch_current_time():
    offset = -8
    current_time = datetime.datetime.utcnow() + timedelta(hours=offset)

    return current_time


def clembot_time_in_server_timezone():
    server_offset = -6
    clembot_offset = -8

    return time.time()+ 3600 * (server_offset - clembot_offset)

test_time = calendar.timegm(fetch_current_time().utctimetuple())


def convert_to_epoch(current_time):
    return calendar.timegm(fetch_current_time().utctimetuple())


print(test_time)
print(timedelta(minutes=5).seconds)

print(test_time + timedelta(minutes=5).seconds)

print(clembot_time_in_server_timezone())

print(clembot_time_in_server_timezone()+timedelta(minutes=10).seconds)

print(datetime.datetime.fromtimestamp(time.time()))

print(datetime.datetime.fromtimestamp(clembot_time_in_server_timezone()))

print(datetime.datetime.fromtimestamp(clembot_time_in_server_timezone()).strftime("%H:%M"))
