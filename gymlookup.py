import os
import json
from json import load

raid_info = {}
gym_info_file = {}

script_path = os.path.dirname(os.path.realpath(__file__))

def load_config():
    global gym_info_file
    global raid_info
    global gym_info_list

    with open(os.path.join(script_path, "raid_info.json"), "r") as fd:
        raid_info = json.load(fd)

    with open(os.path.join(script_path, "gym_info.json"), "r") as fd:
        gym_info_file = json.load(fd)
    if gym_info_file:
        gym_info_list = gym_info_file.get('gym_info')

load_config()


def get_gym_info(gym_code, attribute = None):
    gym_info = gym_info_list.get(gym_code)
    if gym_info:
        if attribute:
            return gym_info[attribute]
        else:
            return gym_info
    return None

print(get_gym_info('MESC','gym_name'))

print(get_gym_info('BUVI'))
