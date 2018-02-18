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


def accept_time_input(time_as_text):
    offset = -8
    current_time = datetime.datetime.utcnow() + timedelta(hours=offset)

    try:
        start_time = time.strptime(time_as_text, '%I:%M %p')
    except ValueError:
        try:
            start_time = time.strptime(time_as_text, '%I:%M')
        except ValueError:
            start_time = None




    return start_time


def convert_into_time(time_as_text, require_am_pm=True):
    time_format = ['%I:%M %p', '%I:%M%p']

    for format in time_format:
        try:
            start_time = time.strptime(time_as_text, format)
            break
        except ValueError:
            start_time = None
            continue

    if start_time == None and require_am_pm == False:
        try:
            start_time = datetime.time.strftime(time_as_text, '%H:%M')
        except ValueError:
            start_time = None
            pass

    return start_time




print(convert_into_time("5:22",False))

print(convert_into_time("5:22 pm", False))

print(convert_into_time("16:22 pm", False))

print(convert_into_time("5:22pm"))
#
# print(datetime.datetime.strftime(convert_into_time("5:22pm"),"%H:%M %p"))