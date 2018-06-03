import os
import pickle
import discord
import tempfile
import json
import copy

server_dict_new = {}

with open(os.path.join('guilddict'), "rb") as fd:
	old_guild_dict = pickle.load(fd)


print(old_guild_dict)

for guild_id in old_guild_dict:

	for author_id in old_guild_dict[guild_id]['trainers']:
		print(old_guild_dict[guild_id]['trainers'][author_id])

		leaderboard_status = copy.deepcopy(old_guild_dict[guild_id]['trainers'][author_id])

		leaderboard_status['lifetime']={}
		if 'wild_reports' in leaderboard_status:
			leaderboard_status['lifetime']['wild_reports'] = leaderboard_status['wild_reports']

		if 'raid_reports' in leaderboard_status:
			leaderboard_status['lifetime']['raid_reports'] = leaderboard_status['raid_reports']

		if 'egg_reports' in leaderboard_status:
			leaderboard_status['lifetime']['egg_reports'] = leaderboard_status['egg_reports']

		if 'research_reports' in leaderboard_status:
			leaderboard_status['lifetime']['research_reports'] = leaderboard_status['research_reports']


		old_guild_dict[guild_id]['trainers'][author_id] = leaderboard_status


		print(old_guild_dict[guild_id]['trainers'][author_id])


with tempfile.NamedTemporaryFile('wb', dir=os.path.dirname(os.path.join('guilddict')), delete=False) as tf:
	pickle.dump(old_guild_dict, tf, -1)
	tempname = tf.name
try:
	os.remove(os.path.join('guilddict_leaderboard_backup'))
except OSError as e:
	pass
try:
	os.rename(os.path.join('guilddict'), os.path.join('guilddict_leaderboard_backup'))
except OSError as e:
	if e.errno != errno.ENOENT:
		raise
os.rename(tempname, os.path.join('guilddict'))


print('Dictionary converted successfully.')