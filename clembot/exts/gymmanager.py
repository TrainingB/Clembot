import re
import discord
import os
import time_util
import json
import asyncio

from random import *

from discord.ext import commands
from exts.utilities import Utilities
from exts.utilities import RemoveComma
import os,sys,inspect

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import gymsql
from logs import init_loggers


class GymManager:

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()
        self.pokemon_forms = []
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        self.pokemon_forms = data['pokemon_forms']
        self.logger = init_loggers()

    async def query_channel_city(self, *conditions, **kwargs):
        try:
            guild_channel_city_tbl = self.dbi.table('guild_channel_city')
            guild_channel_query = guild_channel_city_tbl.query().select().where(**kwargs)
            city_rcrd = await guild_channel_query.get_first()
            if city_rcrd:
                city = dict(city_rcrd)['city_state']
                if city:
                    return city
        except Exception as error:
            print(error)
        return None

    async def get_city_for_channel(self, guild_id, channel_id, parent_channel_id=None) -> str :
        try:
            self.logger.info(f"read_channel_city(, {guild_id}, {channel_id}, {parent_channel_id}")
            city_for_channel = await self.query_channel_city(guild_id=guild_id, channel_id=channel_id)

            if not city_for_channel:
                if parent_channel_id:
                    city_for_channel = await self.query_channel_city(guild_id=guild_id, channel_id=parent_channel_id)

            if not city_for_channel:
                city_for_channel = await self.query_channel_city(self.dbi.table('guild_channel_city')['channel_id'].is_null_(), guild_id=guild_id)
            return city_for_channel

        except Exception as error:
            print(error)
            self.logger.info(error)
            return None


    @commands.group(pass_context=True, hidden=True, aliases=["xgym"])
    async def _gym(self, ctx):
        print("xgym()")
        await self.utilities._send_message(ctx.channel,f"subcommand_passed = {ctx.subcommand_passed} , invoked_with = {ctx.invoked_with}, invoked_subcommand = {ctx.invoked_subcommand}")

        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                return await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

            gym_list = await self.find_gyms_for_city(ctx, ctx.subcommand_passed)
            await self.utilities._send_embed(channel=ctx.channel, description=json.dumps(gym_list, indent=2))

    @_gym.command(pass_context=True, hidden=True, aliases=["find"])
    async def _gym_find(self, ctx, gym_code):
        return await self.find_gyms_for_city(ctx, gym_code)

    @_gym.command(pass_context=True, hidden=True, aliases=["add"])
    async def _gym_add(self, ctx, *, gym_info=None):
        print("_gym_add()")
        try:
            sample_gym_info = {
                "Name" : "Gym New Name",
                "Latitude" : 00.00000,
                "Longitude" : 00.00000,
                "CityState" : "CITY,STATE"
            }

            gym_info_list = [sample_gym_info]

            args = ctx.message.clean_content.split()

            if gym_info is None:
                return await self.utilities._send_message(ctx.message.channel,
                                           "Beep Beep! **{member}**, please provide gym information is following format. \n```!gym add \n{gym_info}```\n You can use https://www.csvjson.com/csv2json to convert CSV to JSON.".format(
                                               member=ctx.message.author.display_name,
                                               gym_info=json.dumps(gym_info_list, indent=4)))

            # gym_info_text = gym_info.clean_content

            gym_info_list = json.loads(gym_info)

            list_of_msg = []

            for sample_gym_info in gym_info_list:

                gym_name_words = sample_gym_info['Name'].upper().split(' ')
                words_1 = words_2 = words_3 = ''
                words_1 = gym_name_words[0]
                if len(gym_name_words) >= 2:
                    words_2 = gym_name_words[1]

                if len(gym_name_words) >= 3:
                    words_3 = gym_name_words[2]

                gym_code_key = words_1[:2] + words_2[:2] + words_3[:2]

                city, state = sample_gym_info['CityState'].split(",")

                gmap_url = "https://www.google.com/maps/place/{0},{1}".format(sample_gym_info['Latitude'],
                                                                              sample_gym_info['Longitude'])

                gym_info_to_save = {
                    "city_state_key" : city + state
                    ,"gym_code_key" : gym_code_key
                    ,"gym_name" : sample_gym_info['Name']
                    ,"original_gym_name" : sample_gym_info.get('OriginalName', sample_gym_info['Name'])
                    ,"gmap_url" : gmap_url
                    ,"latitude" : str(sample_gym_info['Latitude'])
                    ,"longitude" : str(sample_gym_info['Longitude'])
                    ,"region_code_key" : city + state
                    ,"word_1" : words_1[:2]
                    ,"word_2" : words_2[:2]
                    ,"word_3" : words_3[:2]
                    ,"gym_location_city" : city
                    ,"gym_location_state" : state
                }
                message_text = "Beep Beep! **{0}**, Gym **{1}** has been added successfully.".format(
                    ctx.message.author.display_name, gym_info_to_save['original_gym_name'])

                gym_info_already_saved = await self.find_gyms_for_city(ctx.message, gym_code_key, gym_info_to_save['city_state_key'])

                # gymsql.find_gym(city + state, gym_code_key)
                if gym_info_already_saved:
                    message_text = "Beep Beep! **{0}**, Gym **{1}** already exists for **{2}**.".format(ctx.message.author.display_name, gym_info_to_save['original_gym_name'], city + state)
                    confirmation_msg = await self.utilities._send_error_message(ctx.message.channel, message_text)
                else:
                    table = self.dbi.table('gym_master')
                    table.insert(**gym_info_to_save)
                    await table.insert.commit()

                    confirmation_msg = await self.utilities._send_message(ctx.message.channel, message_text)

                list_of_msg.append(confirmation_msg)

            # self.dbi.table('gym_master').query().insert().where(gym_master['original_gym_name'].ilike(f'%{gym_code}%'),city_state_key=city)




            await asyncio.sleep(15)
            await ctx.message.delete()

        except Exception as error:
            print(error)
            return await _send_error_message(ctx.message.channel, error)
            logger.info(error)

        return




    async def _query_gym_master_by_gym_code(self, gym_code, city=None):
        gym_master = self.dbi.table('gym_master')
        gym_code_query = gym_master.query().select().where(gym_code_key=gym_code, city_state_key=city)
        list_of_gym = await gym_code_query.getjson()
        return list_of_gym

    async def _query_gym_master(self, gym_code_or_name, city=None):
        try:
            gym_code_or_name = gym_code_or_name.upper()

            if gym_code_or_name:

                gym_master = self.dbi.table('gym_master')
                gym_code_query = gym_master.query().select().where(gym_master['gym_code_key'].like(f'%{gym_code_or_name}%'), city_state_key=city)

                list_of_gym = await gym_code_query.getjson()
                print(f"_query_gym_master({gym_code_or_name}, {city}) : {len(list_of_gym)} record(s) found!")
                if len(list_of_gym) == 0:
                    gym_name_query = self.dbi.table('gym_master').query().select().where(gym_master['original_gym_name'].ilike(f'%{gym_code_or_name}%'),city_state_key=city)
                    list_of_gym = await gym_name_query.getjson()
                return list_of_gym

        except Exception as error:
            print(error)

        return None

    async def find_gym_by_gym_code(self, gym_code, city=None):
        list_of_gym = await self._query_gym_master_by_gym_code(gym_code, city)

        if len(list_of_gym) == 1:
            return list_of_gym[0]
        else :
            print(f"find_gym_by_gym_code({gym_code},{city}) : {len(list_of_gym)} records found!")
        return None

    async def find_gym_list_by(self, gym_code_or_name, city=None):
        return await self._query_gym_master(gym_code_or_name, city)




    def get_beep_embed(self, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - Trade Management", description=self.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


def setup(bot):
    bot.add_cog(GymManager(bot))

