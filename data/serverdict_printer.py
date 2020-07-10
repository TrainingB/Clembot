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

print(os.path.abspath('.'))

def process():
    with open(os.path.join(os.path.abspath('.'),'data','guilddict'), "rb") as fd:
        server_dict_old = pickle.load(fd)



    print(json.dumps(server_dict_old, default=datetime_handler, indent=4))

def main():

    process()
    print("finished")

main()