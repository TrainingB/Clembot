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


class RecoveryManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()
        self.pokemon_forms = []
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        self.pokemon_forms = data['pokemon_forms']


    @commands.command(pass_context=True, hidden=True, aliases=["recover1-rsvp"])
    @commands.has_permissions(manage_channels=True)
    async def _recover_1rsvp(self, ctx):



        return

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
    bot.add_cog(RecoveryManager(bot))


