import re
import discord
import time_util
from discord.ext import commands
from random import *

import json

class TradeManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict


    @commands.group(pass_context=True, hidden=True, aliases=["trade"])
    async def _trade(self, ctx):

        if ctx.invoked_subcommand is None:
            await self._send_message(ctx.channel, "trade has been called ")

    @_trade.command(aliases=["clear"])
    async def _trade_clear(self, ctx):
        ctx.bot.guild_dict[ctx.guild.id]['trade_dict'] = {}

    @_trade.command(aliases=["status"])
    async def _trade_status(self, ctx, *pokemon):
        try:

            trade_dict = ctx.bot.guild_dict[ctx.guild.id].setdefault('trade_dict', {})

            await self._send_message(ctx.channel, json.dumps(trade_dict, indent=2))
        except Exception as error:
            print(error)

    @_trade.command(aliases=["offer","have"])
    async def _trade_offer(self, ctx, *pokemon):

        pokemon_list = [e for e in pokemon if e in ctx.bot.pkmn_info['pokemon_list'] ]

        pokemon_offer_trade_dict={}

        for pokemon_offer in pokemon_list:

            pokemon_offer_trade_dict = ctx.bot.guild_dict[ctx.guild.id].setdefault('trade_dict', {}).get(pokemon_offer, {})

            if pokemon_offer_trade_dict:
                pokemon_offer_trade_dict['trainer_id'].append(ctx.message.author.id)
            else:

                trade_id = '%04x' % randrange(16 ** 4)
                pokemon_offer_trade_dict['trade_id'] = trade_id
                pokemon_offer_trade_dict.setdefault('trainer_id',[]).append(ctx.message.author.id)


                ctx.bot.guild_dict[ctx.guild.id]['trade_dict'][pokemon_offer] = pokemon_offer_trade_dict

        await self._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['trade_dict'], indent=2))


    @_trade.command(aliases=["request","want"])
    async def _trade_request(self, ctx, *pokemon):

        pokemon_list = [e for e in pokemon if e in ctx.bot.pkmn_info['pokemon_list'] ]

        if ctx.invoked_subcommand is None:
            await self._send_message(ctx.channel, "Beep Beep! **{member}** is looking for following Pokemon : {pokemon_list}".format(member=ctx.message.author.display_name, pokemon_list=", ".join(pokemon_list)))


    @_trade.command(aliases=["search"])
    async def _trade_search(self, ctx, *pokemon):

        pokemon_list = [e for e in pokemon if e in ctx.bot.pkmn_info['pokemon_list'] ]

        for pokemon_search in pokemon_list:
            available = ctx.bot.guild_dict[ctx.guild.id]['trade_dict'].get(pokemon_search)

            text = "!@{}{}\n".format(available['trainer_id'], available['trade_id'])

            await self._send_message(ctx.channel, text)

        if ctx.invoked_subcommand is None:
            await self._send_message(ctx.channel, "Beep Beep! **{member}** Here is your search result for : {pokemon_list}".format(member=ctx.message.author.display_name, pokemon_list=", ".join(pokemon_list)))


    async def _send_error_message(self, channel, description):

        color = discord.Colour.red()
        error_embed = discord.Embed(description="{0}".format(description), colour=color)
        return await channel.send(embed=error_embed)

    async def _send_message(self, channel, description):
        try:

            error_message = "The output contains more than 2000 characters."
            if len(description) >= 2000:
                discord.Embed(description="{0}".format(error_message), colour=color)

            color = discord.Colour.green()
            message_embed = discord.Embed(title="Trade",   description="{0}".format(description), colour=color)

            return await channel.send(embed=message_embed)
        except Exception as error:
            print(error)


    beep_notes = ("""**{member}** here are the commands for notes management. 

**!notes ** - to list all the notes from a channel.
**!notes add <note>** - to add a note to the current channel.
**!notes clear** - to clear the note(s) for the current channel.

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
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - Note(s) Management", description=self.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


def setup(bot):
    bot.add_cog(TradeManager(bot))


