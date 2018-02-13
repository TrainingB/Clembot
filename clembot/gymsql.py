import os
import json
import sqlite3


DB_NAME = ""

script_path = os.path.dirname(os.path.realpath(__file__))


connection = None
cursor = None

def set_db_name(db_name:DB_NAME):
    global DB_NAME
    DB_NAME=db_name
    connect(DB_NAME)
    return

def connect(db_name=DB_NAME):
    print("connect() called {db_name}".format(db_name=db_name))
    try:
        global connection
        global cursor

        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
    except Exception as error:
        print(error)
    return

def disconnect():
    print("disconnect() called")
    connection.close()

def read_server_city(server_id):
    try:
        print("read_server_city({server_id})".format(server_id=server_id))

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select city_state from server_channel_city where server_id = {server_id} and channel_id is null".format(server_id=server_id))

        all_rows = cursor.fetchall()

        if len(all_rows) < 1:
            return None

        return all_rows[0][0]
    except Exception as error:
        print(error)

    return None

def read_channel_city(server_id, channel_id):
    try:
        print("read_channel_city({server_id}, {channel_id})".format(server_id=server_id, channel_id=channel_id))

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select city_state from server_channel_city where server_id = {server_id} and channel_id = {channel_id}".format(server_id=server_id, channel_id=channel_id))

        all_rows = cursor.fetchall()

        if len(all_rows) < 1:
            return None

        return all_rows[0][0]
    except Exception as error:
        print(error)

    return None




# connect()
#
# test()
#
# disconnect()
#

#print(read_channel_city(393545294337277970, 411817126102302720))



#--SQL-- insert into server_channel_city (server_id, channel_id, city_state) select server_id, channel_id, city_state from channel_city;


def save_server_city(server_id, city_state):

    try:
        print("save_server_city({server_id}, {city_state})".format(server_id=server_id,city_state=city_state))

        global cursor, connection
        if cursor == None:
            connect()

        # try updating first
        cursor.execute("update server_channel_city set city_state = '{city_state}' where server_id = {server_id} and channel_id is null"
                     .format(server_id=server_id,city_state=city_state))
        # otherwise insert the new row
        cursor.execute("insert into server_channel_city (server_id, city_state ) "
                     "SELECT {server_id}, '{city_state}'  where (select Changes() = 0)"
                     .format(server_id=server_id,city_state=city_state))

        connection.commit()
        return city_state
    except Exception as error:
        print(error)

    return None


def save_channel_city(server_id, channel_id, city_state):

    try:
        print("save_channel_city({server_id}, {channel_id}, {city_state})".format(server_id=server_id,channel_id=channel_id,city_state=city_state))

        global cursor, connection
        if cursor == None:
            connect()

        # try updating first
        cursor.execute("update server_channel_city set city_state = '{city_state}' where server_id = {server_id} and channel_id = {channel_id}"
                     .format(server_id=server_id,channel_id=channel_id,city_state=city_state))
        # otherwise insert the new row
        cursor.execute("insert into server_channel_city (server_id, channel_id , city_state ) "
                     "SELECT {server_id}, {channel_id}, '{city_state}'  where (select Changes() = 0)"
                     .format(server_id=server_id,channel_id=channel_id,city_state=city_state))

        connection.commit()
        return city_state
    except Exception as error:
        print(error)

    return None






#
# save_channel_city(1, 1, "BURBANKCA")
# save_channel_city(1, 1, "BURBANKCA")
#
# test()
#
#
# disconnect()

#
# def load_gyms():
#     global city_wide_gym_list
#
#     directory = os.path.join(script_path,"..","data","gyminfo")
#     for filename in os.listdir(directory):
#         if filename.endswith(".json"):
#             print("Loading..." + os.path.join(directory, filename))
#
#             city_state = filename.split(".")[0].upper()
#             with open(os.path.join(directory, filename), "r") as fd:
#                 city_wide_gym_list[city_state] = json.load(fd)
#
#             continue
#         else:
#             continue
#
#
# # --B--
# def get_gym_info(gym_code, attribute=None, city_state=None):
#     city_state_list = []
#
#     if city_state is None:
#         city_state_list = list(city_wide_gym_list.keys())
#     else:
#         city_state_list.extend(city_state)
#
#     for city_state_element in city_state_list:
#         gym_info = _get_gym_info(gym_code, attribute, city_state_element)
#
#         if gym_info:
#             return gym_info
#     return None
#
# def _get_gym_info(gym_code, attribute=None, city_state=None):
#     try:
#         gym_info = city_wide_gym_list.get(city_state).get(gym_code.upper())
#         if gym_info:
#             if attribute:
#                 return gym_info[attribute]
#             else:
#                 return gym_info
#         return None
#
#     except Exception as error:
#         print(error)
#         return None
#
#
#
# def get_matching_gym_info(gym_code_prefix, city_state=None):
#     city_state_list = []
#
#     if city_state:
#         city_state_list.extend(city_state)
#     else:
#         city_state_list = list(city_wide_gym_list.keys())
#
#     matching_gyms = []
#
#     for city_state_element in city_state_list:
#         for gym_code in city_wide_gym_list.get(city_state_element).keys():
#             if gym_code.startswith(gym_code_prefix):
#                 matching_gyms.append(city_wide_gym_list.get(city_state_element).get(gym_code))
#
#     return matching_gyms



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
