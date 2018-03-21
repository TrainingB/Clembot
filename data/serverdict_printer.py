import os
import pickle
import discord
import tempfile
import json

server_dict_new = {}

with open('../data/guilddict', "rb") as fd:
	server_dict_old = pickle.load(fd)



print(server_dict_old)
