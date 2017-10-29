import os
import json
from json import load

import re

import ast
import time
from datetime import tzinfo, timedelta, datetime



raid_info = {}
gym_info_list = {}

script_path = os.path.dirname(os.path.realpath(__file__))

def load_config():
    global raid_info
    global gym_info_list

    with open(os.path.join(script_path, "raid_info.json"), "r") as fd:
        raid_info = json.load(fd)

    with open(os.path.join(script_path, "gym_info.json"), "r") as fd:
        gym_info_list = json.load(fd)
    # if gym_info_file:
    #     gym_info_list = gym_info_file.get('gym_info')

load_config()



# print(gym_info_list.get('AAMU'))

def get_gym_info(gym_code, attribute = None):
    gym_info = gym_info_list.get(gym_code)
    if gym_info:
        if attribute:
            return gym_info[attribute]
        else:
            return gym_info
    return None


def get_gym_info_for(gym_code_prefix):

    matching_gyms = []

    for gym_code in gym_info_list.keys():
        if gym_code.startswith(gym_code_prefix):
            matching_gyms.append(gym_info_list.get(gym_code))

    return matching_gyms


for gym_info in get_gym_info_for('R'):
    print("{gym_code} - {gym_name}".format(gym_code=gym_info.get('gym_code'),gym_name=gym_info.get('gym_name')))
    a = 1

raidmsg_original="""!add 34°10'23.1"N 118°21'16.7"W
https://goo.gl/maps/9kmoz2SJTgs"""


# print(raidmsg_original.split())

# print(" ".join(raidmsg_original.split()).lower())


numbers = {
    "0" : ":zero:",
    "1" : ":one:",
    "2" : ":two:",
    "3" : ":three:",
    "4" : ":four:",
    "5" : ":five:",
    "6" : ":six:",
    "7" : ":seven:",
    "8" : ":eight:",
    "9" : ":nine:"
}


def print_number(number):

    number_emoji =""

    reverse = "".join(reversed(str(number)))

    for digit in reverse[::-1]:
        number_emoji = number_emoji + numbers.get(digit)

    number_emoji = "[" + number_emoji + "]"

    return number_emoji


# print_number(1223432)

# print_number(10)

longlat = "34.193277,-118.345691"

def fetch_gmap_image_link(longlat):
    key = "AIzaSyCoS20_EWol8TgnAiTk1417ybvUIRoEIQw"
    gmap_base_url = "https://maps.googleapis.com/maps/api/staticmap?center={0}&markers=color:red%7C{1}&maptype=roadmap&size=250x125&zoom=15&key={2}"

    gmap_image_link = gmap_base_url.format(longlat, longlat, key)
    return gmap_image_link


# print(fetch_gmap_image_link(longlat))


def extract_longlat_from(gmap_link):

    longlat = gmap_link.replace("http://maps.google.com/maps?q=","")
    longlat = longlat.replace("https://maps.google.com/maps?q=", "")
    longlat = longlat.replace("https://www.google.com/maps/place/", "")

    pattern = re.compile("^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$")

    if pattern.match(longlat):
        return longlat

    return None

#print(extract_longlat_from("https://www.google.com/maps/place/34.193277,-118.345691"))
