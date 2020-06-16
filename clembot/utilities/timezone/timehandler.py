import os
from datetime import datetime, timedelta, timezone
from calendar import timegm
import time
from dateparser import parse
import pytz
from clembot.core.logs import Logger

_UTC = 'UTC'
_GUILD_TIMEZONE = 'America/New_York'

"""

current_epoch() -> get current time with or without second precision
epoch(datetime, timezone) -> if datetime is not timezone aware, localize using timezone and then give epoch
as_local_time(epoch, timezone) -> converts epoch to timezone aware datetime



"""

def is_tz_aware(dt : datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def localize(dt: datetime, tz) -> datetime:
    if is_tz_aware(dt):
        return dt.astimezone(tz)
    return tz.localize(dt)


def epoch(date_time: datetime, zone: str = None) -> float:
    """localize the datetime and then calculate epoch"""

    if is_tz_aware(date_time):
        return timegm(date_time.utctimetuple())

    return timegm(pytz.timezone(zone).localize(date_time).utctimetuple())


def current_epoch(second_precision: bool=True) -> float:
    """
    Returns UTC Epoch (TZ aware date time converted into epoch)
    second & microseconds are removed if second_precision is false
    """
    if second_precision:
        return time.time()

    return epoch(pytz.UTC.localize(datetime.utcnow().replace(second=0, microsecond=0)), _UTC)


def is_in_future(utc_timestamp: float) -> bool:
    """checks if the provided epoch is in future"""
    # print(f"{as_local_readable_time(utc_timestamp, PST)} > {as_local_readable_time(current_epoch(), PST)} => {utc_timestamp > current_epoch()}")
    if utc_timestamp and utc_timestamp > current_epoch():
        return True
    return False


def as_local_time(utc_timestamp: float, zone: str=_UTC) -> datetime:
    """convert utc_timestamp into local_time datetime"""
    utc_datetime = pytz.UTC.localize(datetime.utcfromtimestamp(utc_timestamp))
    return utc_datetime.astimezone(pytz.timezone(zone))

def as_local_readable_time(utc_timestamp: float, zone: str=_UTC) -> str:
    as_tz_aware_datetime = as_local_time(utc_timestamp, zone)
    return f'{as_tz_aware_datetime.strftime("%I:%M %p")} ({as_tz_aware_datetime.strftime("%H:%M")})'


def add_time(utc_timestamp: float, delta: timedelta):
    """Adds a time duration to given epoch timestamp, returns new epoch value"""
    as_datetime = as_local_time(utc_timestamp)
    new_datetime = as_datetime + delta
    return epoch(new_datetime)




PST = 'America/Los_Angeles'

def date_timestamp_test():

    utc = pytz.UTC
    pst = pytz.timezone(PST)

    my_epoch = current_epoch(second_precision=False)
    epoch_from_dt = datetime.utcnow().timestamp()
    new_epoch_from_time = add_time(my_epoch, timedelta(hours=1, minutes=45))

    print("><><><><><><><><><><><><><><><><><><><><>< Current EPOCH without precision ><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><")
    print(f"Current EPOCH            : {my_epoch}  {epoch_from_dt} " )
    print(f"Local Time (PST)         : {as_local_time(my_epoch, PST)}  {as_local_time(epoch_from_dt, PST)}  ")
    print(f"Local Time (GMT)         : {as_local_time(my_epoch, _UTC)}  {as_local_time(epoch_from_dt, _UTC)}  ")
    print(f"Readable Time (PST)      : {as_local_readable_time(my_epoch, PST)}  {as_local_readable_time(epoch_from_dt, PST)}  ")
    print(f"Readable Time (GMT)      : {as_local_readable_time(my_epoch, _UTC)}  {as_local_readable_time(epoch_from_dt, _UTC)}  ")
    print(f"Local Time (PST)         : {as_local_readable_time(new_epoch_from_time, PST)} ")


    my_epoch = current_epoch()
    epoch_from_dt = datetime.utcnow().timestamp()
    new_epoch_from_time = add_time(my_epoch, timedelta(hours=1, minutes=45))

    print("><><><><><><><><><><><><><><><><><><><><><>< Current EPOCH with precision  ><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><")
    print(f"Current EPOCH            : {my_epoch}  {epoch_from_dt}  ")
    print(f"Local Time (PST)         : {as_local_time(my_epoch, PST)}  {as_local_time(epoch_from_dt, PST)} ")
    print(f"Local Time (GMT)         : {as_local_time(my_epoch, _UTC)}  {as_local_time(epoch_from_dt, _UTC)} ")
    print(f"Readable Time (PST)      : {as_local_readable_time(my_epoch, PST)}  {as_local_readable_time(epoch_from_dt, PST)} ")
    print(f"Readable Time (GMT)      : {as_local_readable_time(my_epoch, _UTC)}  {as_local_readable_time(epoch_from_dt, _UTC)} ")
    print(f"Local Time (PST)         : {as_local_readable_time(new_epoch_from_time, PST)}")

    input_date_tz = parse("10:35 am", settings={'TIMEZONE': PST, 'RETURN_AS_TIMEZONE_AWARE': True})
    print(input_date_tz)
    input_timestamp = epoch(input_date_tz, pst)
    new_epoch_from_time = add_time(input_timestamp, timedelta(hours=1, minutes=45))



    print("><><><><><><><><><><><><><><><><><><><><><><     Timezone aware input      ><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><")
    print(f"Input EPOCH              : {input_timestamp} ")
    print(f"Input EPOCH (PST)        : {as_local_time(input_timestamp, PST)} ")
    print(f"Input EPOCH (GMT)        : {as_local_time(input_timestamp)} ")
    print(f"Readable Time (PST)      : {as_local_readable_time(input_timestamp, PST)} ")
    print(f"Readable Time (GMT)      : {as_local_readable_time(input_timestamp, _UTC)} ")
    print(f"Local Time (PST)         : {as_local_readable_time(new_epoch_from_time, PST)}")

    input_date_tz = parse("11:35 pm", settings={'TIMEZONE': PST, 'RETURN_AS_TIMEZONE_AWARE': False})
    print(input_date_tz)
    input_timestamp = epoch(input_date_tz, PST)
    new_epoch_from_time = add_time(input_timestamp, timedelta(hours=1, minutes=45))


    print("><><><><><><><><><><><><><><><><><><><><><><    Timezone unaware input     ><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><")
    print(f"Input EPOCH              : {input_timestamp} ")
    print(f"Input EPOCH (PST)        : {as_local_time(input_timestamp, PST)} ")
    print(f"Input EPOCH (GMT)        : {as_local_time(input_timestamp)}")
    print(f"Readable Time (PST)      : {as_local_readable_time(input_timestamp, PST)} ")
    print(f"Readable Time (GMT)      : {as_local_readable_time(input_timestamp, _UTC)} ")
    print(f"Local Time (PST)         : {as_local_readable_time(new_epoch_from_time, PST)}")



def get_offset(date_time):
    return date_time.replace(pytz.UTC).utcoffset()


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
            start_time = time.strptime(time_as_text, '%H:%M')
        except ValueError:
            start_time = None
            pass

    return start_time

def convert_to_timestamp(hours_min: str, zone: str):
    try:
        input_date_tz = parse(hours_min, settings={'TIMEZONE': zone, 'RETURN_AS_TIMEZONE_AWARE': True})

        if input_date_tz:
            tz_epoch = epoch(input_date_tz, zone)
            return tz_epoch
    except Exception as error:
        Logger.error(error)

    return None


def main():
    # timestamp_to_timezone_datetime()
    date_timestamp_test()


if __name__=='__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")