import re
import discord
import os
import time_util
from discord.ext import commands
from exts.utilities import Utilities
from random import *


import json

class TeamManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()
        self.pokemon_forms = []
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        self.pokemon_forms = data['pokemon_forms']

    async def ask(self, message, destination, user_list=None, *, react_list=['✅', '❎']):
        if user_list and type(user_list) != __builtins__.list:
            user_list = [user_list]

        def check(reaction, user):
            if user_list and type(user_list) is __builtins__.list:
                return (user.id in user_list) and (reaction.message.id == message.id) and (reaction.emoji in react_list)
            elif not user_list:
                return (user.id != message.guild.me.id) and (reaction.message.id == message.id) and (reaction.emoji in react_list)

        for r in react_list:
            await asyncio.sleep(0.25)
            await message.add_reaction(r)
        try:
            reaction, user = await Clembot.wait_for('reaction_add', check=check, timeout=60)
            return reaction, user
        except asyncio.TimeoutError:
            await message.clear_reactions()
            return

    async def ask_confirmation(self, message, rusure_message, yes_message, no_message, timed_out_message):
        author = message.author
        channel = message.channel

        reaction_list = ['✅', '❎']
        # reaction_list = ['❔', '✅', '❎']

        rusure = await channel.send(_("Beep Beep! {message}".format(message=rusure_message)))
        await rusure.add_reaction("✅")  # checkmark
        await rusure.add_reaction("❎")  # cross

        def check(react, user):
            if user.id != author.id:
                return False
            return True

        # res = await Clembot.wait_for_reaction(reaction_list, message=rusure, check=check, timeout=60)
        try:
            reaction, user = await Clembot.wait_for('reaction_add', check=check, timeout=10)
        except asyncio.TimeoutError:
            await rusure.delete()
            confirmation = await channel.send(_("Beep Beep! {message}".format(message=timed_out_message)))
            await asyncio.sleep(3)
            await confirmation.delete()
            return False

        if reaction.emoji == "❎":
            await rusure.delete()
            confirmation = await channel.send(_("Beep Beep! {message}".format(message=no_message)))
            await asyncio.sleep(3)
            await confirmation.delete()
            return False
        elif reaction.emoji == "✅":
            await rusure.delete()
            confirmation = await channel.send(_("Beep Beep! {message}".format(message=yes_message)))
            await asyncio.sleep(3)
            await confirmation.delete()
            return True

    @commands.command(pass_context=True, hidden=True, aliases=["teams"])
    async def _teams(self, ctx):


        team_message = await ctx.send("Please select your team by clicking your team icon.")
        print(ctx.message.author.roles)

        print(ctx.bot.config['team_dict'])
        print(ctx.bot.config['team_dict'].keys())

        for team_emoji in ctx.bot.config['team_dict'].keys():
            for emoji in ctx.bot.emojis:
                if emoji.name == team_emoji:
                    await team_message.add_reaction(emoji)


        # for role in ctx.message.author.roles:
        #     if role.name in ctx.bot.config['team_dict'].keys() :
        #         await self.utilities._send_error_message(ctx.channel, f"Already a member of {role.name}!")





    beep_notes = ("""**{member}** here are the commands for trade management. 

**!trade offer <pokemon>** - to add pokemon to your offers list.
**!trade request <pokemon>** - to add pokemon to your requests list.

**!trade clear <pokemon>** - to remove pokemon from your trade offer or request list.

**!trade list** - brings up pokemon in your trade offer/request list.
**!trade list @user** - brings up pokemon in user's trade offer/request list.

**!trade search <pokemon>** - brings up a list of 10 users who are offering pokemon with their pokemon request as well.

**Note:** *<pokemon> can only be the name of the pokemon. The qualifiers like shiny, perfect, mini or anything else will be ignored.*

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
    bot.add_cog(TeamManager(bot))


