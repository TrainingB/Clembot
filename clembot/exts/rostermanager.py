import re
import discord
import os
import time_util
from discord.ext import commands
from exts.utilities import Utilities
from exts.utilities import RemoveComma
from random import *
from exts.pokemonform import PokemonForm

import json


class RosterManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()


    @commands.group(pass_context=True, hidden=True, aliases=["import"])
    async def _import(self, ctx):

        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @_import.command(aliases=["roster"])
    async def _import_roster(self, ctx):

    # !import roster #channel

        message = ctx.message

        channel_mentions = message.channel_mentions

        if len(channel_mentions) != 1:
            return await self.utilities._send_error_message(ctx.channel, f"correct usage is **!import roster #channel**", user=ctx.message.author)

        roster_from_channel = channel_mentions[0]
        roster = {}

        try:
            roster = ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][roster_from_channel.id]['roster']
        except Exception as error:
            pass

        if not roster:
            return await self.utilities._send_error_message(ctx.channel, f"no roster found in {roster_from_channel.mention}", user=ctx.message.author)

        change_roster = await self.utilities.ask_confirmation(ctx, message, "Are you sure to replace the current roster?", "Importing the roster..", "No Changes Made.", "Request timed out." )

        if change_roster:
            ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster'] = roster
            return await self.utilities._send_message(ctx.channel, f"roster successfully imported from {roster_from_channel.mention}", user=ctx.message.author)


    beep_notes = ("""**{member}** here are the commands for trade management. 

**!trade offer <pokemon>** - to add pokemon to your offers list.
**!trade request <pokemon>** - to add pokemon to your requests list.

**!trade clear <pokemon>** - to remove pokemon from your trade offer or request list.
**!trade clear all** - to clear your trade offer and request list.

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
    bot.add_cog(RosterManager(bot))


