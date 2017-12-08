import datetime
import time


def clembot_time_in_server_timezone():
    server_offset = -6
    clembot_offset = -8

    return time.time()+ 3600 * (server_offset - clembot_offset)


print(time.time())

print(clembot_time_in_server_timezone())

print(datetime.datetime.fromtimestamp(time.time()))

print(datetime.datetime.fromtimestamp(clembot_time_in_server_timezone()))

print(datetime.datetime.fromtimestamp(clembot_time_in_server_timezone()).strftime("%H:%M"))
