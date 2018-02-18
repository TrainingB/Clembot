import os
import json
import sqlite3


DB_NAME = ""

script_path = os.path.dirname(os.path.realpath(__file__))

SQLITE_DB = "C:\\_MyDrive\\Codebase\\Discord\\Clembot\\database\\clembot_db"

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

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# GYM Lookup via Database
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_gym_list_by_code(city_state_key, gym_code_key) -> []:
    try:
        print("get_gym_list_by_code({city_state_key} , {gym_code_key})".format(gym_code_key=gym_code_key, city_state_key=city_state_key))

        global cursor
        if cursor == None:
            connect()

        statement = "select json from gym_master where city_state_key = '{city_state_key}' and gym_code_key like '{gym_code_key}%' order by gym_code_key ".format(city_state_key=city_state_key, gym_code_key=gym_code_key)

        # print(statement)
        cursor.execute(statement)

        all_rows = cursor.fetchall()

        gym_list = []

        if len(all_rows) < 1:
            return None

        for row in all_rows:
            gym_list.append(json.loads(row[0]))

        return gym_list
    except Exception as error:
        print(error)

    return None

def get_gym_by_code(city_state_key, gym_code_key) -> []:
    try:
        print("get_gym_list_by_code({city_state_key} , {gym_code_key})".format(gym_code_key=gym_code_key, city_state_key=city_state_key))

        global cursor
        if cursor == None:
            connect()

        statement = "select json from gym_master where city_state_key = '{city_state_key}' and gym_code_key like '{gym_code_key}%' order by gym_code_key ".format(city_state_key=city_state_key, gym_code_key=gym_code_key)

        # print(statement)
        cursor.execute(statement)

        all_rows = cursor.fetchall()

        gym_list = []

        if len(all_rows) < 1:
            return None

        for row in all_rows:
            gym_list.append(json.loads(row[0]))

        return gym_list[0]
    except Exception as error:
        print(error)

    return None


def update_gym(gym_code_key, field_name, field_value):
    print("update_gym({gym_code_key} [ {field_name} = {field_value} ] )".format(gym_code_key=gym_code_key, field_name=field_name, field_value=field_value))
    try:
        global cursor
        if cursor == None:
            connect()

        statement = "update gym_master set {field_name} = '{field_value}' where gym_code_key = '{gym_code_key}' ".format(gym_code_key=gym_code_key, field_name=field_name, field_value=field_value)
        # print(statement)

        cursor.execute(statement)
        connection.commit()

        if field_name == 'GYM_CODE_KEY':
            update_json(field_value)
        else :
            update_json(gym_code_key)

    except Exception as error:
        print(error)


def update_json(gym_code_key):
    print("update_json({gym_code_key})".format(gym_code_key=gym_code_key))
    try:
        global cursor
        if cursor == None:
            connect()

        cursor.execute("select * from gym_master where gym_code_key like '{gym_code_key}%' ".format(gym_code_key=gym_code_key.upper()))

        col_names = [cn[0] for cn in cursor.description]

        all_rows = cursor.fetchall()

        row = all_rows[0]

        text = "{" \
            "\"" + col_names[0] + "\":\"" + row[0] + "\"," \
            "\"" + col_names[1] + "\":\"" + row[1] + "\"," \
            "\"" + col_names[2] + "\":\"" + row[2] + "\"," \
            "\"" + col_names[3] + "\":\"" + row[3] + "\"," \
            "\"" + col_names[4] + "\":\"" + row[4] + "\"," \
            "\"" + col_names[5] + "\":\"" + row[5] + "\"," \
            "\"" + col_names[6] + "\":\"" + row[6] + "\"," \
            "\"" + col_names[7] + "\":\"" + row[7] + "\"," \
            "\"" + col_names[8] + "\":\"" + row[8] + "\"," \
            "\"" + col_names[9] + "\":\"" + row[9] + "\"," \
            "\"" + col_names[10] + "\":\"" + row[10] + "\"," \
            "\"" + col_names[11] + "\":\"" + row[11] + "\"," \
            "\"" + col_names[12] + "\":\"" + row[12] + "\"," \
            "\"" + col_names[13] + "\":\"" + row[13] + "\"" \
            "}"

        statement = "UPDATE gym_master set json='{json}' where gym_code_key='{gym_code_key}'".format(json=text, gym_code_key=gym_code_key)

        # print(statement)

        cursor.execute(statement)
        connection.commit()

    except Exception as error:
        print(error)

    return


def convert_into_gym_info(gym_info):
    if gym_info:
        gym_info_adapter = {}

        gym_info_adapter['city_state'] = gym_info['city_state_key']
        gym_info_adapter['gym_code'] = gym_info['gym_code_key']
        gym_info_adapter['lat_long'] = gym_info['latitude']+","+gym_info['longitude']
        gym_info_adapter['gmap_link'] = gym_info['gmap_url']
        gym_info_adapter['gym_name'] = gym_info['gym_name']

        return gym_info_adapter

    return None

def main():
    set_db_name(SQLITE_DB)
    print(get_gym_list_by_code('NORTHHILLSCA','BIJI'))
    print(convert_into_gym_info(get_gym_list_by_code('NORTHHILLSCA','BIJI')[0]))

# main()

# print(get_gym_by_code('BURBANKCA','B'))
#


# update_gym('BIJI', 'GYM_CODE_KEY' , 'BIJI1' )
#
# print(get_gym_by_code('NORTHHILLSCA','BIJI1'))
#

#
# print(get_gym_by_code('NORTHHILLSCA','BIJI'))
#
# rows = get_gym_list_by_code("NORTHHILLSCA", "BIJI")
#
# print(rows[0]['GYM_CODE_KEY'])
#
# update_gym('BIJI', 'GYM_CODE_KEY' , 'BIJI1' )
#
# rows = get_gym_list_by_code("NORTHHILLSCA", "BIJI1")
# print(rows[0]['GYM_CODE_KEY'])
#
# update_gym('BIJI1', 'GYM_CODE_KEY' , 'BIJI' )
#
# rows = get_gym_list_by_code("NORTHHILLSCA", "BIJI")
# print(rows[0]['GYM_CODE_KEY'])