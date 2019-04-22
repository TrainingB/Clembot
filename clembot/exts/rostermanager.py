import re
import discord
import os
from clembot.core import time_util
from clembot.core import checks
from discord.ext import commands
from exts.utilities import Utilities
from exts.utilities import RemoveComma
from random import *
from exts.pokemonform import PokemonForm
import asyncio
import json
import copy

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
            roster = copy.deepcopy(ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][roster_from_channel.id]['roster'])
        except Exception as error:
            pass

        if not roster:
            return await self.utilities._send_error_message(ctx.channel, f"no roster found in {roster_from_channel.mention}", user=ctx.message.author)

        change_roster = await self.utilities.ask_confirmation(ctx, message, "Are you sure to replace the current roster?", "Importing the roster..", "No Changes Made.", "Request timed out." )

        if change_roster:
            ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster'] = roster
            return await self.utilities._send_message(ctx.channel, f"roster successfully imported from {roster_from_channel.mention}", user=ctx.message.author)



    @commands.command(pass_context=True, hidden=True, aliases=["rosterx"])
    @checks.raidpartychannel()
    async def _rosterx(self, ctx):

        # message = await self.utilities._send_message(ctx.channel, "New roster under construction.", user=ctx.message.author)

        message = await self.print_roster(ctx, ctx.message)
        description_1 = message.embeds[0].description
        description_2 = "Message 2"


        try:

            await message.add_reaction('\u2b05')
            await message.add_reaction('\u27a1')
            await message.add_reaction('\u23f9')
        except Exception as error:
            print(error)

        try:
            is_timed_out = False
            while True:
                reaction, user = await ctx.bot.wait_for('reaction_add', check=(lambda r, u: u.id == ctx.message.author.id and r.message.id == message.id) , timeout=20)

                if reaction.emoji == '\u23f9':
                    await message.remove_reaction(reaction.emoji, user)
                    await message.remove_reaction('\u27a1', ctx.bot.user)
                    await message.remove_reaction('\u2b05', ctx.bot.user)
                    await message.remove_reaction('\u23f9', ctx.bot.user)
                    return
                elif reaction.emoji == '\u2b05':
                    await message.edit(embed=discord.Embed(description=description_1, title=message.embeds[0].title, footer=message.embeds[0].footer ))
                elif reaction.emoji == '\u27a1':
                    await message.edit(embed=discord.Embed(description=description_2))

                await message.remove_reaction(reaction.emoji, user)

        except asyncio.TimeoutError:
            await message.remove_reaction('\u27a1', ctx.bot.user)
            await message.remove_reaction('\u2b05', ctx.bot.user)
            await message.remove_reaction('\u23f9', ctx.bot.user)

        except Exception as error:
            print(error)

    async def print_roster(self, ctx, message, roster_message=None):

        roster = ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster']

        if len(roster) < 1:
            await message.channel.send(content=_(
                "Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
            return

        roster_index = roster[0]['index']

        roster_msg = self.get_roster_with_highlight(roster, roster_index)

        raid_party_image_url = "https://media.discordapp.net/attachments/419935483477622793/450201828802560010/latest.png"

        raid_img_url = raid_party_image_url
        # "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png".format(str(raid_number))

        if roster_index:
            current_roster = roster[0]
            embed_title = _("Raid Party is at Location#{index}. Click here for directions!").format(
                index=self.utilities.emojify_numbers(roster_index))
            raid_party_image_url = current_roster['gmap_link']
        else:
            embed_title = "Raid Party has not started yet!!"
            raid_party_image_url = ""

        raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title),
                                   url=raid_party_image_url, description=roster_msg)
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name),
                              icon_url=message.author.avatar_url)
        raid_embed.set_thumbnail(url=raid_img_url)

        if roster_message:
            return await message.channel.send(
                content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention,
                                                                         roster_message=roster_message),
                embed=raid_embed)
        else:
            return await message.channel.send(
                content=_("Beep Beep! {member} here is the raid party roster: ").format(member=message.author.mention),
                embed=raid_embed)



    def get_roster_with_highlight(self, roster, highlight_roster_loc):
        roster_msg = ""

        try:
            for roster_loc in roster:
                if highlight_roster_loc == roster_loc['index']:
                    marker = "**"
                else:
                    marker = ""
                eta = roster_loc.get('eta', "")
                if eta:
                    eta = " [{eta}]".format(eta=eta)
                else:
                    eta = ""
                if len(roster_msg) > 1900:
                    roster_msg += "\n and more!"
                    break
                else:
                    roster_msg += _("\n{marker1}{number} [{gym}]({link}) - {pokemon}{eta}{marker2}").format(
                        number=self.utilities.emojify_numbers(roster_loc['index']), pokemon=roster_loc['pokemon'].capitalize(),
                        gym=roster_loc['gym_name'], link=roster_loc['gmap_link'], eta=eta, marker1=marker,
                        marker2=marker)

        except Exception as error:
            print(error)

        return roster_msg

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


