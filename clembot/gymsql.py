import os
import json
import sqlite3


DB_NAME = ""

script_path = os.path.dirname(os.path.realpath(__file__))

SQLITE_DB = "C:\\_MyDrive\\Codebase\\Discord\\Clembot\\database\\clembot_db"

connection = None
cursor = None
sqlite3.register_converter("json", json.loads)

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

def read_guild_city(guild_id):
    try:
        print("read_guild_city({guild_id})".format(guild_id=guild_id))

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select city_state from guild_channel_city where guild_id = {guild_id} and channel_id is null".format(guild_id=guild_id))

        all_rows = cursor.fetchall()

        if len(all_rows) < 1:
            return None

        return all_rows[0][0]
    except Exception as error:
        print(error)

    return None

def read_channel_city(guild_id, channel_id):
    try:
        print("read_channel_city({guild_id}, {channel_id})".format(guild_id=guild_id, channel_id=channel_id))

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select city_state from guild_channel_city where guild_id = {guild_id} and channel_id = {channel_id}".format(guild_id=guild_id, channel_id=channel_id))

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



#--SQL-- insert into guild_channel_city (guild_id, channel_id, city_state) select guild_id, channel_id, city_state from channel_city;


def save_guild_city(guild_id, city_state):

    try:
        print("save_guild_city({guild_id}, {city_state})".format(guild_id=guild_id,city_state=city_state))

        global cursor, connection
        if cursor == None:
            connect()

        # try updating first
        cursor.execute("update guild_channel_city set city_state = '{city_state}' where guild_id = {guild_id} and channel_id is null"
                     .format(guild_id=guild_id,city_state=city_state))
        # otherwise insert the new row
        cursor.execute("insert into guild_channel_city (guild_id, city_state ) "
                     "SELECT {guild_id}, '{city_state}'  where (select Changes() = 0)"
                     .format(guild_id=guild_id,city_state=city_state))

        connection.commit()
        return city_state
    except Exception as error:
        print(error)

    return None


def save_channel_city(guild_id, channel_id, city_state):

    try:
        print("save_channel_city({guild_id}, {channel_id}, {city_state})".format(guild_id=guild_id,channel_id=channel_id,city_state=city_state))

        global cursor, connection
        if cursor == None:
            connect()

        # try updating first
        cursor.execute("update guild_channel_city set city_state = '{city_state}' where guild_id = {guild_id} and channel_id = {channel_id}"
                     .format(guild_id=guild_id,channel_id=channel_id,city_state=city_state))
        # otherwise insert the new row
        cursor.execute("insert into guild_channel_city (guild_id, channel_id , city_state ) "
                     "SELECT {guild_id}, {channel_id}, '{city_state}'  where (select Changes() = 0)"
                     .format(guild_id=guild_id,channel_id=channel_id,city_state=city_state))

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

        statement = "select * from gym_master where city_state_key = ? and gym_code_key like ? order by gym_code_key "

        # print(statement)

        cursor.execute(statement, (city_state_key.upper(), gym_code_key.upper()+"%", ))

        all_rows = cursor.fetchall()
        col_names = [cn[0] for cn in cursor.description]

        gym_list = []

        if len(all_rows) < 1:
            return None

        for row in all_rows:
            gym_list.append(convert_row_to_dict(row, col_names))

        return gym_list
    except Exception as error:
        print(error)

    return []

def get_gym_by_code(city_state_key, gym_code_key):
    try:
        print("get_gym_by_code({city_state_key} , {gym_code_key})".format(gym_code_key=gym_code_key, city_state_key=city_state_key))

        return find_gym(city_state_key, gym_code_key)

    except Exception as error:
        print(error)

    return None


def convert_all_row_to_dict(row, col_names)-> {}:

    gym_info_dict = {}
    for i in range(0, len(col_names)):
        gym_info_dict[col_names[i]] = row[i]

    return gym_info_dict


def convert_row_to_dict(row, col_names)-> {}:

    gym_info_dict = {}
    for i in range(0, len(col_names) - 1):
        gym_info_dict[col_names[i]] = row[i]

    return gym_info_dict

def convert_to_dict(row, col_names)-> {}:

    gym_info_dict = {}

    for onerow in row:
        gym_info_dict[onerow[0]] = onerow[1]

    return gym_info_dict


def find_gym(city_state_key, gym_code_key):
    try:
        print("find_gym({city_state_key} , {gym_code_key})".format(gym_code_key=gym_code_key.upper(), city_state_key=city_state_key.upper()))

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select * from gym_master where gym_code_key = ? and city_state_key = ? ", (gym_code_key.upper(), city_state_key.upper(),))

        all_rows = cursor.fetchall()

        col_names = [cn[0] for cn in cursor.description]

        gym_dict = {}

        if len(all_rows) > 0:
            gym_dict = convert_row_to_dict(all_rows[0], col_names)

        return gym_dict
    except Exception as error:
        print(error)

    return None

def update_gym_info(gym_info, gym_code=None):
    print(gym_info)

    try:
        global cursor
        if cursor == None:
            connect()
        parameter_list = []
        update_statement = "update gym_master set "
        for key, value in gym_info.items():
            print(key)
            print(value)
            update_statement = update_statement + " {key} = ? ,".format(key=key)
            parameter_list.append(value)

        update_statement = update_statement[:-1]
        update_statement = update_statement + " where gym_code_key = ? and city_state_key = ? "


        if gym_code:
            parameter_list.append(gym_code)
        else:
            parameter_list.append(gym_info['gym_code_key'])
        parameter_list.append(gym_info['city_state_key'])

        print(update_statement)
        print(parameter_list)


        cursor.execute(update_statement, parameter_list)
        connection.commit()
    except Exception as error:
        print(error)



def insert_gym_info(gym_info):
    print(gym_info)

    try:
        global cursor
        if cursor == None:
            connect()
        parameter_list = []
        insert_statement = "insert into gym_master ("
        for key, value in gym_info.items():
            insert_statement = insert_statement + " {key} ,".format(key=key)
            parameter_list.append(value)
            # print(value)

        insert_statement = insert_statement[:-1]
        insert_statement = insert_statement + ") values ("

        for key, value in gym_info.items():
            insert_statement = insert_statement + " ? ,".format(key=key)

        insert_statement = insert_statement[:-1]
        insert_statement = insert_statement  + " ) "

        print(insert_statement )
        print(parameter_list)

        cursor.execute(insert_statement, parameter_list)
        connection.commit()
    except Exception as error:
        print(error)


def delete_gym_info(city_state_key, gym_code_key):

    try:
        global cursor
        if cursor == None:
            connect()

        cursor.execute("delete from gym_master where gym_code_key = ? and city_state_key = ? ", (gym_code_key.upper(), city_state_key.upper(),))
        connection.commit()
    except Exception as error:
        print(error)





def update_gym(city_state_key, gym_code_key, field_name, field_value):
    print("update_gym({gym_code_key} [ {field_name} = {field_value} ] )".format(gym_code_key=gym_code_key.upper(), field_name=field_name, field_value=field_value))
    try:
        global cursor
        if cursor == None:
            connect()

        statement = "update gym_master set {field_name} = ? where gym_code_key = ? and city_state_key = ? ".format(field_name=field_name)
        # print(statement)

        cursor.execute(statement, (field_value,gym_code_key.upper(),city_state_key.upper()))
        connection.commit()

    except Exception as error:
        print(error)


# def update_json(city_state_key, gym_code_key):
#     print("update_json({city_state_key} , {gym_code_key})".format(city_state_key=city_state_key,gym_code_key=gym_code_key))
#     try:
#         global cursor
#         if cursor == None:
#             connect()
#
#         statement = "UPDATE gym_master set JSON = '{' || ' \"region_code_key\":"' ||region_code_key || '",' ||' \"city_state_key\":"' ||city_state_key || '",' ||' \"gym_code_key\":"' ||gym_code_key || '",' ||' \"original_gym_name\":"' ||original_gym_name || '",' ||' \"gym_name\":"' ||gym_name || '",' ||' \"latitude\":"' ||latitude || '",' ||' \"longitude\":"' ||longitude || '",' ||' \"gym_location_city\":"' ||gym_location_city || '",' ||' \"gym_location_state\":"' ||gym_location_state || '",' ||' \"gmap_url\":"' ||gmap_url || '",' ||' \"gym_image\":"' ||gym_image || '"}'  where city_state_key=? AND gym_code_key=? "
#
#         print(statement)
#
#         # statement = "select * from gym_master where gym_code_key = '{gym_code_key}' and city_state_key = ? ".format(gym_code_key=gym_code_key.upper())
#         # cursor.execute(statement, (city_state_key, gym_code_key))
#         #
#         # col_names = [cn[0] for cn in cursor.description]
#         #
#         # all_rows = cursor.fetchall()
#         #
#         # row = all_rows[0]
#         #
#         # text = "{" \
#         #     "\"" + col_names[0] + "\":\"" + row[0] + "\"," \
#         #     "\"" + col_names[1] + "\":\"" + row[1] + "\"," \
#         #     "\"" + col_names[2] + "\":\"" + row[2] + "\"," \
#         #     "\"" + col_names[3] + "\":\"" + row[3] + "\"," \
#         #     "\"" + col_names[4] + "\":\"" + row[4] + "\"," \
#         #     "\"" + col_names[5] + "\":\"" + row[5] + "\"," \
#         #     "\"" + col_names[6] + "\":\"" + row[6] + "\"," \
#         #     "\"" + col_names[7] + "\":\"" + row[7] + "\"," \
#         #     "\"" + col_names[8] + "\":\"" + row[8] + "\"," \
#         #     "\"" + col_names[9] + "\":\"" + row[9] + "\"," \
#         #     "\"" + col_names[10] + "\":\"" + row[10] + "\"," \
#         #     "\"" + col_names[11] + "\":\"" + row[11] + "\"," \
#         #     "\"" + col_names[12] + "\":\"" + row[12] + "\"," \
#         #     "\"" + col_names[13] + "\":\"" + row[13] + "\"" \
#         #     "}"
#         #
#         # statement = "UPDATE gym_master set json=? where gym_code_key = ? and city_state_key = ? ".format(json=text)
#
#         # print(statement)
#
#         cursor.execute(statement, (gym_code_key, city_state_key,))
#         connection.commit()
#
#     except Exception as error:
#         print(error)
#
#     return


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



def read_guild_configuration(guild_id, channel_id=None) -> {}:

    try:
        print("read_guild_configuration({guild_id}, {channel_id})".format(guild_id=guild_id, channel_id=channel_id))

        global cursor
        if cursor == None:
            connect()

        statement = "select configuration from guild_channel_configuration where guild_id = '{guild_id}' and channel_id ".format(guild_id=guild_id)

        if channel_id:
            statement = statement + "= {channel_id}".format(channel_id=channel_id)
        else:
            statement = statement + " is null "

        statement = statement + " ORDER BY ROWID ASC LIMIT 1 "

        result_row = cursor.execute(statement).fetchone()

        if result_row:
            configuration = json.loads(result_row[0])
            return configuration

        return None

    except Exception as error:
        print(error)

    return None

def save_guild_configuration(guild_id, configuration, channel_id=None ) -> {}:

    try:
        print("save_guild_configuration({guild_id}, {channel_id}, {configuration})".format(guild_id=guild_id, channel_id=channel_id, configuration=configuration))

        global cursor, connection
        if cursor == None:
            connect()

        statement = "update guild_channel_configuration set configuration = ? where guild_id = '{guild_id}' and channel_id ".format(guild_id=guild_id, channel_id=channel_id)
        if channel_id:
            statement = statement + "= '{channel_id}'".format(channel_id=channel_id)
        else:
            statement = statement + " is null "
        print(statement)
        # try updating first
        json_string = json.dumps(configuration)
        cursor.execute(statement, (json_string,))
        # otherwise insert the new row

        if channel_id:
            cursor.execute("insert into guild_channel_configuration (guild_id, channel_id , configuration ) "
                       "SELECT '{guild_id}', '{channel_id}', ?  where (select Changes() = 0)".format(guild_id=guild_id, channel_id=channel_id) , (json_string,))
        else:
            cursor.execute("insert into guild_channel_configuration (guild_id, configuration ) "
                           "SELECT '{guild_id}', ?  where (select Changes() = 0)".format(guild_id=guild_id), (json_string,))


        connection.commit()
        return configuration
    except Exception as error:
        print(error)

    return None

def main():
    gyms_lookup_test()

def gyms_test():
    set_db_name(SQLITE_DB)
    # print(get_gym_list_by_code('NORTHHILLSCA', 'BIJI'))
    # print(convert_into_gym_info(get_gym_list_by_code('NORTHHILLSCA', 'BIJI')[0]))

def configuration_test():
    configuration = {}
    configuration['region_prefix'] = "SO"

    save_guild_configuration(guild_id=1, channel_id=1, configuration=configuration)

    print(read_guild_configuration(guild_id=1,channel_id=1))

    channel_configuration={}
    channel_configuration['add_region_prefix'] = "true"

    save_guild_configuration(guild_id=1, configuration=channel_configuration)

    print(read_guild_configuration(guild_id=1))

    print(read_guild_configuration(guild_id=2))


def print_list(dict_list):
    for d in dict_list:
        print(d)


def gyms_lookup_test():

    set_db_name(SQLITE_DB)
    # print_list(get_gym_list_by_code('SPRINGFIELDIL', 'RIPA'))
    #
    # print(get_gym_by_code('SPRINGFIELDIL', 'RIPA'))



# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Bulbasaur Bingo Save
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#
# create table guild_user_bingo_card (
# id integer primary key,
# guild_id integer,
# user_id integer,
# bingo_card text,
# bingo_card_url text,
# generated_at text
# );

def find_bingo_card(guild_id, user_id, event):

    try:
        print("find_bingo_card({0}, {1}, {2})".format(guild_id, user_id, event))

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select * from guild_user_event_bingo_card where guild_id = ? and user_id = ? and event = ? order by id desc", (guild_id, user_id, event, ))

        all_rows = cursor.fetchall()

        col_names = [cn[0] for cn in cursor.description]

        bingo_card_dict = {}

        if len(all_rows) > 0:
            bingo_card_dict = convert_all_row_to_dict(all_rows[0], col_names)

        return bingo_card_dict
    except Exception as error:
        print(error)

    return None

def save_bingo_card(guild_id, user_id, event, bingo_card, bingo_card_url, generated_at):
    print("save_bingo_card ({0}, {1}, {2})".format(guild_id,user_id,event))
    try:
        global cursor
        if cursor == None:
            connect()
        parameter_list = []

        bingo_card_text = json.dumps(bingo_card)

        cursor.execute("update guild_user_event_bingo_card set bingo_card = ? , bingo_card_url = ?, generated_at = ? where guild_id = ? and user_id = ? and event = ?", (bingo_card_text, bingo_card_url, generated_at, guild_id, user_id, event,))

        insert_statement = "insert into guild_user_event_bingo_card (guild_id, user_id, event, bingo_card, bingo_card_url, generated_at ) SELECT  ? , ? , ?, ? ,? , ? where (select Changes() = 0) "

        cursor.execute(insert_statement, (guild_id, user_id, event, bingo_card_text, bingo_card_url, generated_at,))
        connection.commit()
    except Exception as error:
        print(error)


    return


def find_clembot_config(config_key):
    print("find_clembot_config ({0})".format(config_key))

    try:
        global cursor
        if cursor == None:
            connect()

        cursor.execute("select config_value from clembot_config where config_key = ? order by id desc", (config_key, ))

        all_rows = cursor.fetchall()

        col_names = [cn[0] for cn in cursor.description]

        if len(all_rows) > 0:

            try :
                value = json.loads(all_rows[0][0])
            except Exception as error:
                value = all_rows[0][0]
                pass

            return value

    except Exception as error:
        print(error)

    return None


def find_all_clembot_config():
    print("find_all_clembot_config()")

    try:

        global cursor
        if cursor == None:
            connect()

        cursor.execute("select config_key , config_value from clembot_config order by id desc", ())

        all_rows = cursor.fetchall()

        col_names = [cn[0] for cn in cursor.description]

        config_dict = {}

        if len(all_rows) > 0:
            config_dict.update(convert_to_dict(all_rows, col_names))

        return config_dict

    except Exception as error:
        print(error)

    return None

def save_clembot_config(config_key, config_value):
    print("save_clembot_config ({0}, {1})".format(config_key, config_value))
    try:
        global cursor
        if cursor == None:
            connect()
        parameter_list = []

        cursor.execute("update clembot_config set config_value = ? where config_key = ? ", (config_value, config_key, ))

        insert_statement = "insert into clembot_config (config_key, config_value ) SELECT  ? , ? where (select Changes() = 0) "

        cursor.execute(insert_statement, (config_key, config_value,))
        connection.commit()
    except Exception as error:
        print(error)

    return




#

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

#
# print(find_gym('SPRINGFIELDIL','CEILPU'))
#
# update_json('SPRINGFIELDIL','CEILPU')


# print(get_gym_list_by_code('BURBANKCA' , 'POROFO'))


def test_update(text):

    print(find_gym('BURBANKCA', 'GRMA'))

    gym_info = json.loads(text)

    gym_info['gym_code_key'] = 'NEWNEW'

    # insert_gym_info(gym_info)

    print(find_gym('BURBANKCA', 'NEWNEW'))



def test_bingo_card():

    print(find_bingo_card(393545294337277970,289657500167438336))

    bingo_card = find_bingo_card(393545294337277970,289657500167438336)

    if bingo_card:
        bingo_card_dict = json.loads(bingo_card['bingo_card'])

        print(bingo_card['bingo_card'])

        print(bingo_card_dict['2'])

# test_update('{"city_state_key": "BURBANKCA","gmap_url": "https://www.google.com/maps?q=34.164256,-118.292803","gym_code_key": "GRMA","gym_image": "https://lh4.ggpht.com/HPzAb_J2iuzAsmXue0B9mBpKwjo-g5zUWIbB_4v75WJC6oEo0MOD0RnaIlZyDaZAFM1xkefEx5ek4G4bk3w","gym_location_city": "BURBANK","gym_location_state": "CA","gym_name": "Griffith Manor Park (Ex-eligible)","latitude": "34.164256","longitude": "-118.292803","original_gym_name": "Griffith Manor Park","region_code_key": "BAG","word_1": "GR","word_2": "MA","word_3": "PA"}')


def test_config():
    # byte_array = json.dumps(["bulbasaur","mareep"])
    #
    # save_clembot_config("bingo-event", byte_array)
    # save_clembot_config("test-key","test-value")
    #
    # print(find_clembot_config("bingo-event"))
    # print(find_clembot_config("test-key"))
    #
    # byte_array = find_clembot_config("bingo-event")
    #
    # print(byte_array)
    # print(byte_array[0])

    map = find_clembot_config("bingo-event-title")
    print(map)



def main():
    set_db_name(SQLITE_DB)
    test_config()

    print(find_all_clembot_config())

#main()