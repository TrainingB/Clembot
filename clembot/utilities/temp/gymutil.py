import json
import os

city_wide_gym_list = {}
script_path = os.path.dirname(os.path.realpath(__file__))

def load_gyms():
    global city_wide_gym_list

    directory = os.path.join(script_path,"..","data","gyminfo")
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            print("Loading..." + os.path.join(directory, filename))

            city_state = filename.split(".")[0].upper()
            with open(os.path.join(directory, filename), "r") as fd:
                city_wide_gym_list[city_state] = json.load(fd)

            continue
        else:
            continue


# --B--
def get_gym_info(gym_code, attribute=None, city_state=None):
    city_state_list = []

    # if city_state is None:
    #     city_state_list = list(city_wide_gym_list.keys())
    # else:

    city_state_list.extend(city_state)

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

    except Exception as error:
        Logger.error(f"{traceback.format_exc()}")
        return None



def get_matching_gym_info(gym_code_prefix, city_state=None):
    city_state_list = []

    if city_state:
        city_state_list.extend(city_state)
    else:
        city_state_list = list(city_wide_gym_list.keys())

    matching_gyms = []

    for city_state_element in city_state_list:
        city_gym_list = city_wide_gym_list.get(city_state_element)
        if city_gym_list:
            for gym_code in city_wide_gym_list.get(city_state_element).keys():
                if gym_code.startswith(gym_code_prefix):
                    matching_gyms.append(city_wide_gym_list.get(city_state_element).get(gym_code))

    return matching_gyms



#
# load_gyms()
# #
# print(get_gym_info("CLCO", city_state=["BURBANKCA"]))
# #
# #
# # print(get_matching_gym_info("SUPA", city_state=["QUINCYIL"]))
# #
# # print(get_matching_gym_info("VI", city_state=["BURBANKCA"]))
#
#
# print(get_gym_info("ILSTEP", city_state=["SPRINGFIELDIL"]))
# print(get_gym_info("ILSTEP", city_state=["SPRINGFIELDIL"]))
# print(get_gym_info("SHNAPA", city_state=["FRONTROYALVA"]))
# #
# print(city_wide_gym_list['BURBANKCA'])
# #
# print(city_wide_gym_list['SPRINGFIELDIL'])
# #
# #
# # for city_state in city_wide_gym_list.keys():
# #     print(city_wide_gym_list.get(city_state))
