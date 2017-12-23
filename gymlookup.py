import os
import json

city_wide_gym_list = {}

raid_info = {}
gym_info_list = {}
icon_list = {}
script_path = os.path.dirname(os.path.realpath(__file__))


def load_gyms():
    global city_wide_gym_list
    with open(os.path.join(script_path+"\data\gyminfo", "burbankca.json"), "r") as fd:
        city_wide_gym_list['BURBANKCA'] = json.load(fd)

    with open(os.path.join(script_path+"\data\gyminfo", "quincyil.json"), "r") as fd:
        city_wide_gym_list['QUINCYIL'] = json.load(fd)


def load_config():
    global raid_info

    global icon_list
    global city_wide_gym_list
    load_gyms()


load_config()


print(city_wide_gym_list['BURBANKCA'])

print(city_wide_gym_list['QUINCYIL'])


for city_state in city_wide_gym_list.keys():
    print(city_wide_gym_list.get(city_state))



# --B--
def get_gym_info(gym_code, attribute=None, city_state=None):
    city_state_list = []

    if city_state is None:
        city_state_list = list(city_wide_gym_list.keys())
    else:
        city_state_list.__add__(city_state)

    for city_state_element in city_state_list:
        gym_info = _get_gym_info(gym_code, attribute, city_state_element)

        if gym_info:
            return gym_info
    return None

def _get_gym_info(gym_code, attribute=None, city_state=None):
    try:
        gym_info = city_wide_gym_list.get(city_state).get(gym_code.upper())
        if gym_info:
            if attribute:
                return gym_info[attribute]
            else:
                return gym_info
        return None

    except:
        return None



def get_matching_gyms_info(gym_code_prefix, city_state=None):
    city_state_list = []

    if city_state is None:
        city_state_list = list(city_wide_gym_list.keys())
    else:
        city_state_list.__add__(city_state)

    matching_gyms = []

    for city_state_element in city_state_list:
        for gym_code in city_wide_gym_list.get(city_state_element).keys():
            if gym_code.startswith(gym_code_prefix):
                matching_gyms.append(city_wide_gym_list.get(city_state_element).get(gym_code))

    return matching_gyms



print(get_gym_info("BUCE"))


print(get_matching_gyms_info("BU"))


#
#
# def get_icon_url(pokedex_number):
#     url = icon_list.get(pokedex_number)
#     if url:
#         return url
#     return None
#
#
#
# print (get_icon_url(str(19)))
#
#
# # print(gym_info_list.get('AAMU'))
#
# def get_gym_info(gym_code, attribute = None):
#     gym_info = gym_info_list.get(gym_code)
#     if gym_info:
#         if attribute:
#             return gym_info[attribute]
#         else:
#             return gym_info
#     return None
#
#
# def get_gym_info_for(gym_code_prefix):
#
#     matching_gyms = []
#
#     for gym_code in gym_info_list.keys():
#         if gym_code.startswith(gym_code_prefix):
#             matching_gyms.append(gym_info_list.get(gym_code))
#
#     return matching_gyms
#
#
# for gym_info in get_gym_info_for('R'):
#     print("{gym_code} - {gym_name}".format(gym_code=gym_info.get('gym_code'),gym_name=gym_info.get('gym_name')))
#     a = 1
#
#
# print(get_gym_info("CAN"))
#
# raidmsg_original="""!add 34°10'23.1"N 118°21'16.7"W
# https://goo.gl/maps/9kmoz2SJTgs"""
#
#
# # print(raidmsg_original.split())
#
# # print(" ".join(raidmsg_original.split()).lower())
#
#
# numbers = {
#     "0" : ":zero:",
#     "1" : ":one:",
#     "2" : ":two:",
#     "3" : ":three:",
#     "4" : ":four:",
#     "5" : ":five:",
#     "6" : ":six:",
#     "7" : ":seven:",
#     "8" : ":eight:",
#     "9" : ":nine:"
# }
#
#
# def print_number(number):
#
#     number_emoji =""
#
#     reverse = "".join(reversed(str(number)))
#
#     for digit in reverse[::-1]:
#         number_emoji = number_emoji + numbers.get(digit)
#
#     number_emoji = "[" + number_emoji + "]"
#
#     return number_emoji
#
#
# # print_number(1223432)
#
# # print_number(10)
#
# longlat = "34.193277,-118.345691"
#
# def fetch_gmap_image_link(longlat):
#     key = "AIzaSyCoS20_EWol8TgnAiTk1417ybvUIRoEIQw"
#     gmap_base_url = "https://maps.googleapis.com/maps/api/staticmap?center={0}&markers=color:red%7C{1}&maptype=roadmap&size=250x125&zoom=15&key={2}"
#
#     gmap_image_link = gmap_base_url.format(longlat, longlat, key)
#     return gmap_image_link
#
#
# # print(fetch_gmap_image_link(longlat))
#
#
# def extract_longlat_from(gmap_link):
#
#     longlat = gmap_link.replace("http://maps.google.com/maps?q=","")
#     longlat = longlat.replace("https://maps.google.com/maps?q=", "")
#     longlat = longlat.replace("https://www.google.com/maps/place/", "")
#
#     pattern = re.compile("^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$")
#
#     if pattern.match(longlat):
#         return longlat
#
#     return None
#
# #print(extract_longlat_from("https://www.google.com/maps/place/34.193277,-118.345691"))


# def convert_into_time(time_as_text):
#     try:
#         start_time = time.strptime(time_as_text, '%I:%M %p')
#     except ValueError:
#         try:
#             start_time = time.strptime(time_as_text, '%I:%M')
#         except ValueError:
#             start_time = None
#
#     return start_time
#
#
# print(convert_into_time("7:43"))
#
#
# print(convert_into_time("21:43"))
#
def convert_into_current_time(time_hour_and_min_only):
    offset = -8
    current_time = datetime.datetime.utcnow() + timedelta(hours=offset)
    current_time = cu
    start_time = current_time.replace(hour=time_hour_and_min_only.tm_hour, minute=time_hour_and_min_only.tm_min)

    print("{a} - {b} >> {c}".format(a=current_time, b=start_time,c=start_time-current_time))

    if current_time.hour > 11:
        start_time = start_time + timedelta(hours=12)
        print("{a} - {b} >> {c}".format(a=current_time, b=start_time, c=start_time-current_time))

    return start_time


print(convert_into_current_time(convert_into_time("7:43")))

print(convert_into_current_time(convert_into_time("11:43")))

print(convert_into_current_time(convert_into_time("12:55")))

print(convert_into_current_time(convert_into_time("1:10")))

print(convert_into_current_time(convert_into_time("4:10")))
#
#
#
# async def validate_start_time(channel, start_time):
#     raid_expires_at = fetch_channel_expire_time(channel)
#
#     offset = -8
#     current_datetime = datetime.datetime.utcnow() + timedelta(hours=offset)
#
#     suggested_start_time = convert_into_current_time(channel, start_time)
#
#     # modified time for raidegg
#     if is_raid_egg:
#         current_datetime = raid_expires_at
#         raid_expires_at = raid_expires_at + timedelta(hours=1)
#
#     if suggested_start_time:
#         if suggested_start_time > raid_expires_at:
#             await Clembot.send_message(channel, ("Beep Beep...! start time cannot be after raid expiry time!"))
#             return None
#         elif suggested_start_time < current_datetime:
#             if is_raid_egg:
#                 await Clembot.send_message(channel, ("Beep Beep...! start time cannot be before the egg hatches!"))
#             else:
#                 await Clembot.send_message(channel, ("Beep Beep...! start time cannot be in past!"))
#             return None
#     else:
#         return None
#
#     return suggested_start_time
