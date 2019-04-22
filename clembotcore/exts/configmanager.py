import json
import re

import discord
from discord.ext import commands
from exts.utilities import Utilities

from clembotcore.core import gymsql


class ConfigManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.raidlist = bot.raidlist
        self.utilities = Utilities()



    @commands.group(pass_context=True, hidden=True, aliases=["config"])
    async def _config(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel,
                                               f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @_config.group(pass_context=True, hidden=True, aliases=["set"])
    async def _config_set(self, ctx, key, value=None):
        if value:
            if key == 'timezone':
                ctx.bot.guild_dict[ctx.guild.id]['offset'] = int(value)
                await self.utilities._send_message(ctx.channel, f"**Timezone** is set to **{ctx.bot.guild_dict[ctx.guild.id]['offset']}**", user=ctx.author)
        else:
            await self.utilities._send_error_message(ctx.channel, f"no changes made!", user=ctx.author)



    @commands.command(pass_context=True, hidden=True, aliases=["list-servers"])
    async def _list_servers(self, ctx):
        recipient = {}
        recipient_text = ""

        for guild in ctx.bot.guilds:
            recipient[guild.name] = guild.owner.mention
            recipient_text += f"\n**{guild.name} [{len(guild.members)}]** - {guild.owner.name} {guild.owner.mention}"

        await self.utilities._send_message(ctx.channel, recipient_text)


    @commands.group(pass_context=True, hidden=True, aliases=["setx"])
    async def _setx(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")


    @commands.group(pass_context=True, hidden=True, aliases=["set-config"])
    async def _set_config(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @_setx.group(pass_context=True, hidden=True, aliases=["channel"])
    async def _set_channel_config(self, ctx, * , key_and_json_text):
        try:
            await self.utilities._send_message(ctx.channel, key_and_json_text)

            key, _, json_text = key_and_json_text.replace('\n', ' ').partition(' ')

            if len(json_text) < 1:
                return await self.utilities._send_message(ctx.channel, f"No json provided!")

            json_body = json.loads(json_text)

            new_configuration = {}
            new_configuration[key] = json_body

            configuration = gymsql.read_guild_configuration(ctx.message.guild.id, ctx.message.channel.id)

            if configuration:
                configuration.update(new_configuration)
            else:
                configuration = new_configuration

            configuration = gymsql.save_guild_configuration(guild_id=ctx.message.guild.id,
                                                            channel_id=ctx.message.channel.id, configuration=configuration)

            if configuration:
                await self.utilities._send_message(ctx.channel, configuration)
            else:
                await self.utilities._send_error_message(ctx.channel, "Beep Beep! I couldn't set the configuration successfully.")
        except Exception as error:
            print(error)

    @_setx.group(pass_context=True, hidden=True, aliases=["guild"])
    async def _set_guild_config(self, ctx, * , key_and_json_text):
        try:
            await self.utilities._send_message(ctx.channel, key_and_json_text)

            key, _, json_text = key_and_json_text.replace('\n', ' ').partition(' ')

            if len(json_text) < 1:
                return await self.utilities._send_message(ctx.channel, f"No json provided!")

            new_configuration = {}
            configuration = gymsql.read_guild_configuration(ctx.message.guild.id, None)

            if json_text == "remove":
                del configuration[key]
            else:
                json_body = json.loads(json_text)
                new_configuration[key] = json_body


                if configuration:
                    configuration.update(new_configuration)
                else:
                    configuration = new_configuration

            configuration = gymsql.save_guild_configuration(guild_id=ctx.message.guild.id,
                                                            channel_id=None, configuration=configuration)

            if configuration:
                await self.utilities._send_message(ctx.channel, configuration)
            else:
                await self.utilities._send_error_message(ctx.channel, "Beep Beep! I couldn't set the configuration successfully.")
        except Exception as error:
            print(error)





    @_setx.command(aliases=["regional"])
    async def _setx_regional(self, ctx, raid_boss = None):

    # !import roster #channel

        message = ctx.message
        if raid_boss:
            regional = re.sub("[\@]", "", raid_boss.lower())
            # regional = get_name(regional).lower() if regional.isdigit() else regional

            if regional:
                if regional in ctx.bot.raidlist:
                    ctx.bot.guild_dict[message.channel.guild.id].setdefault("configuration", {}).setdefault("settings", {})["regional"] = regional
                    return await self.utilities._send_message(ctx.channel, f"{raid_boss} is set as a regional raid boss.", user=ctx.message.author)
                else:
                    return await self.utilities._send_error_message(ctx.channel, f" {regional} doesn't appear as a raid boss.", user=ctx.message.author)
        del ctx.bot.guild_dict[message.channel.guild.id].setdefault("configuration", {}).setdefault("settings", {})["regional"]
        return await self.utilities._send_error_message(ctx.channel, f"Regional raid boss has been cleared.", user=ctx.message.author)



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
    bot.add_cog(ConfigManager(bot))


