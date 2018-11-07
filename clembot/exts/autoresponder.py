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

class AutoResponder:

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

    @commands.group(pass_context=True, hidden=True, aliases=["auto-response", "ar"])
    async def _autoresponse(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @_autoresponse.command(aliases=["add-image"])
    async def _autoresponse_add_image(self, ctx, *, ar_message_text):
        ar_key, _, ar_message = ar_message_text.partition(' ')

        ctx.bot.guild_dict[ctx.guild.id].setdefault('auto-responses-image', {}).setdefault(ctx.channel.id,{})[ar_key] = ar_message

        await self.utilities._send_message(ctx.channel, f"{ar_key} has been set correctly.", user=ctx.message.author)

    @_autoresponse.command(aliases=["add"])
    async def _autoresponse_add(self, ctx, *, ar_message_text):
        ar_key, _, ar_message = ar_message_text.partition(' ')

        ctx.bot.guild_dict[ctx.guild.id].setdefault('auto-responses', {}).setdefault(ctx.channel.id,{})[ar_key] = ar_message

        await self.utilities._send_message(ctx.channel, f"{ar_key} has been set correctly.", user=ctx.message.author)

    @_autoresponse.command(aliases=["clear-all"])
    async def _autoresponse_clear_all(self, ctx):
        try:

            for guild_id in list(ctx.bot.guild_dict.keys()):
                for channel_id in list(ctx.bot.guild_dict[guild_id].get('auto-responses', {}).keys()):
                    if not ctx.bot.guild_dict[guild_id].get('auto-responses', {}).get(channel_id, None) :
                        print(ctx.bot.guild_dict[guild_id].get('auto-responses', {}).pop(channel_id,None))

                for channel_id in list(ctx.bot.guild_dict[guild_id].get('auto-responses-image', {}).keys()):
                    if not ctx.bot.guild_dict[guild_id].get('auto-responses-image', {}).get(channel_id, None) :
                        print(ctx.bot.guild_dict[guild_id].get('auto-responses-image', {}).pop(channel_id,None))

            await self.utilities._send_message(ctx.channel, f"auto-responses are cleaned up.", user=ctx.message.author)
        except Exception as error:
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
    bot.add_cog(AutoResponder(bot))


