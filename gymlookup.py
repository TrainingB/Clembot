import os
import json
from json import load

import ast

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


print(raidmsg_original.split())

print(" ".join(raidmsg_original.split()).lower())