import re
import discord
import os
import time_util
from discord.ext import commands
from exts.utilities import Utilities
from exts.utilities import RemoveComma
from random import *
import asyncio
import os,sys,inspect
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import gymsql

import json


class GymManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()
        self.pokemon_forms = []
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        self.pokemon_forms = data['pokemon_forms']

    def _read_channel_city(self, message):
        city = gymsql.read_channel_city(guild_id=message.guild.id, channel_id=message.channel.id)
        if city == None:
            try:
                parent_city_id = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id].get('reportcity', 0)
                city = gymsql.read_channel_city(guild_id=message.guild.id, channel_id=parent_city_id)
            except Exception:
                pass
            if city == None:
                city = gymsql.read_guild_city(guild_id=message.guild.id)
        if city:
            return city
        return None

    # @commands.group(pass_context=True, hidden=True, aliases=["foo"])
    # async def _foo(self, ctx, *, gym_code=None):
    #
    #     if ctx.invoked_subcommand is None:
    #         return await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
    #
    #
    #
    # @_foo.command(aliases=["bar"])
    # @commands.has_permissions(manage_channels=True)
    # async def _d(self, ctx, *, gym_list_in_json_text):
    #     return await self.utilities._send_message(ctx.channel, f"Beep Beep! BAR **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")


#
#             if gym_code == None:
#                 return await self.utilities._send_error_message(message.channel, "Beep Beep... **{member}** I need at-least one character for lookup!".format(member=message.author.display_name))
#             else:
#                 return await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
#
#
#
#         city = self._read_channel_city(message)
#         # gym_message_output = ""
#         # try:
#         #
#         #     list_of_gyms = await _get_gym_info_list(message, gym_code)
#         #
#         #     if len(list_of_gyms) < 1:
#         #         await self.utilities._send_error_message(message.channel, "Beep Beep... **{member}** I could not find any gym starting with **{gym_code}** for **{city}**!".format(member=message.author.display_name, city=city, gym_code=gym_code))
#         #         return
#         #
#         #     gym_message_output = "Beep Beep! **{member}** Here is a list of gyms for **{city}** :\n\n".format(member=message.author.display_name, city=city)
#         #
#         #     for gym_info in list_of_gyms:
#         #         new_gym_info = "**{gym_code}** - {gym_name}\n".format(gym_code=gym_info.get('gym_code_key').ljust(6), gym_name=gym_info.get('gym_name'))
#         #
#         #         if len(gym_message_output) + len(new_gym_info) > 1990:
#         #             await self.utilities._send_message(message.channel, gym_message_output)
#         #             gym_message_output = ""
#         #
#         #         gym_message_output += new_gym_info
#         #
#         #     if gym_message_output:
#         #         await self.utilities._send_message(message.channel, gym_message_output)
#         #     else:
#         #         await self.utilities._send_error_message(message.channel, "Beep Beep... **{member}** No matches found for **{gym_code}** in **{city}**!".format(member=message.author.display_name, gym_code=gym_code, city=city))
#         # except Exception as error:
#         #     print(error)
#         # await self.utilities._send_error_message(message.channel, "Beep Beep...**{member}** No matches found for **{gym_code}** in **{city}**!".format(member=message.author.display_name, gym_code=gym_code, city=city))
#
#     @commands.group(pass_context=True, hidden=True, aliases=["abc"])
#     async def _abc(self, ctx, gym_code=None):
#         if ctx.invoked_subcommand is None:
#             await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
#
#     @_abc.command(pass_context=True, hidden=True, aliases=["d"])
#     @commands.has_permissions(manage_channels=True)
#     async def _d(self, ctx, *, gym_list_in_json_text):
#         await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
#
    @commands.command(pass_context=True, hidden=True, aliases=["import-gym"])
    @commands.has_permissions(manage_channels=True)
    async def _import_gym(self, ctx, *, gym_list_in_json_text):
        try:

            gym_info_1 = {}
            gym_info_1['Name'] = 'Gym Name'
            # gym_info_1['OriginalName'] = 'Gym Original Name (if different)'
            gym_info_1['Latitude'] = 00.00000
            gym_info_1['Longitude'] = 00.00000
            gym_info_1['CityState'] = 'CITY,STATE'
            gym_info_list = [gym_info_1]

            if len(gym_list_in_json_text) < 1:
                return await self.utilities._send_message(ctx.message.channel, "Beep Beep! **{member}**, please provide gym information is following format. \n```!import-gym \n{gym_info}```\n You can use https://www.csvjson.com/csv2json to convert CSV to JSON.".format(member=ctx.message.author.display_name, gym_info=json.dumps(gym_info_list, indent=4)))

            gym_info_list = json.loads(gym_list_in_json_text)

            list_of_msg = []

            for gym_info_1 in gym_info_list:

                gym_name_words = gym_info_1['Name'].upper().split(' ')
                words_1 = words_2 = words_3 = ''
                words_1 = gym_name_words[0]
                if len(gym_name_words) >= 2:
                    words_2 = gym_name_words[1]

                if len(gym_name_words) >= 3:
                    words_3 = gym_name_words[2]

                gym_code_key = words_1[:2] + words_2[:2] + words_3[:2]

                city, state = gym_info_1['CityState'].split(",")

                gmap_url = "https://www.google.com/maps/place/{0},{1}".format(gym_info_1['Latitude'], gym_info_1['Longitude'])

                gym_info_to_save = {}
                gym_info_to_save['city_state_key'] = city + state
                gym_info_to_save['gym_code_key'] = gym_code_key
                gym_info_to_save['gym_name'] = gym_info_1['Name']
                gym_info_to_save['original_gym_name'] = gym_info_1.get('OriginalName', gym_info_1['Name'])
                gym_info_to_save['gmap_url'] = gmap_url
                gym_info_to_save['latitude'] = gym_info_1['Latitude']
                gym_info_to_save['longitude'] = gym_info_1['Longitude']
                gym_info_to_save['region_code_key'] = city + state
                gym_info_to_save['word_1'] = words_1[:2]
                gym_info_to_save['word_2'] = words_2[:2]
                gym_info_to_save['word_3'] = words_3[:2]
                gym_info_to_save['gym_location_city'] = city
                gym_info_to_save['gym_location_state'] = state

                message_text = "Beep Beep! **{0}**, Gym **{1}** has been added successfully.".format(ctx.message.author.display_name, gym_info_to_save['original_gym_name'])

                gym_info_already_saved = gymsql.find_gym(city + state, gym_code_key)
                if gym_info_already_saved:
                    message_text = "Beep Beep! **{0}**, Gym **{1}** already exists for **{2}**.".format(ctx.message.author.display_name, gym_info_to_save['original_gym_name'], city + state)
                    confirmation_msg = await self.utilities._send_error_message(ctx.message.channel, message_text)
                else:
                    gymsql.insert_gym_info(gym_info_to_save)
                    confirmation_msg = await self.utilities._send_message(ctx.message.channel, message_text)

                list_of_msg.append(confirmation_msg)



            await asyncio.sleep(15)
            await ctx.message.delete()

        except Exception as error:
            return await self.utilities._send_error_message(ctx.message.channel, error)
            print(error)


    beep_notes = ("""**{member}** here are the commands for trade management.

**!trade offer <pokemon>** - to add pokemon to your offers list.
**!trade request <pokemon>** - to add pokemon to your requests list.

**!trade clear <pokemon>** - to remove pokemon from your trade offer or request list.

**!trade list** - brings up pokemon in your trade offer/request list.
**!trade list @user** - brings up pokemon in user's trade offer/request list.
**!trade list pokemon** - filters your trade offer/request list by sepcified pokemon.

**!trade search <pokemon>** - brings up a list of 10 users who are offering pokemon with their pokemon request as well.

**<pokemon> - can be one or more pokemon or pokedex# separated by space.**

""")

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


