import time

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
