import os
import pickle
import discord
import tempfile
import json
import datetime

server_dict_new = {}

def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")



with open('../data/guilddict', "rb") as fd:
	server_dict_old = pickle.load(fd)



print(json.dumps(server_dict_old, default=datetime_handler, indent=4))
