import re
import discord
import os
import time_util
import json
from discord.ext import commands
from exts.utilities import Utilities
from random import *
import asyncio

import json

class ReactRoleManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()

    sample_role_selection_dict = {
        "emoji_role_dict" : {
            "emoji1" :  "role one",
            "emoji1"  : "role two",
            "emoji1" : "role three"
        },
        "exclusive" : "false",
    }

    numbers_text = ["zero","one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    one_to_ten = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']


    def serialize(self, guild, emoji):
        emoji_array = [guild_emoji.name for guild_emoji in guild.emojis if guild_emoji.name == emoji or str(guild_emoji) == emoji]

        if len(emoji_array) > 0:
            return emoji_array[0]

        if emoji in self.numbers_text:
            emoji = self.numbers_text.index(emoji)
            emoji = f'{emoji}\u20e3'

        if emoji.isdigit():
            emoji = f'{emoji}\u20e3'

        if emoji in self.one_to_ten:
            return emoji

        return None

    def demojify(self, guild, emoji_string):

        if emoji_string in self.one_to_ten:
            return emoji_string

        emoji = emoji_string.replace('<','').replace('>','').split(":")[1]

        return emoji

    # convert input to standard emoji format
    def emojify(self, guild, normalized_emoji):

        emoji_array = [':%s:%s' %(guild_emoji.name,guild_emoji.id) for guild_emoji in guild.emojis if guild_emoji.name == normalized_emoji or str(guild_emoji) == normalized_emoji]

        if len(emoji_array) > 0:
            return emoji_array[0]

        if normalized_emoji in self.numbers_text:
            normalized_emoji = self.numbers_text.index(normalized_emoji)
            normalized_emoji = f'{emoji}\u20e3'

        if normalized_emoji.isdigit():
            normalized_emoji = f'{emoji}\u20e3'

        if normalized_emoji in self.one_to_ten:
            return normalized_emoji

        return None

    def printable(self, guild, emoji_text):
        if emoji_text in self.one_to_ten:
            return emoji_text

        emoji_array = ['<:%s:%s>' % (guild_emoji.name, guild_emoji.id) for guild_emoji in guild.emojis if guild_emoji.name == emoji_text or str(guild_emoji) == emoji_text]

        if len(emoji_array) > 0:
            return emoji_array[0]



    # bot.guild_dict[ctx.guild.id]['react-roles']

    @commands.group(pass_context=True, hidden=True, aliases=["react-role", "rr"])
    async def _react_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")


    @_react_role.command(aliases=["list"])
    async def _react_role_list(self, ctx, filter_text=None):
        await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['react-roles'], indent=2))

    @_react_role.command(aliases=["add"])
    async def _react_role_add(self, ctx, *, command_and_json_text):

        group_name, _, json_text = command_and_json_text.replace('\n',' ').partition(' ')

        if len(json_text) < 1:
            sample_text = json.dumps(self.sample_role_selection_dict, indent=2)
            return await self.utilities._send_message(ctx.channel, f"```!react-role add group-name \n{sample_text}```")

        react_role_configuration = {}
        react_role_configuration = json.loads(json_text)
        emoji_role_dict = {}

        for key, value in react_role_configuration['emoji_role_dict'].items():
            new_key = self.serialize(ctx.guild, key)
            emoji_role_dict[new_key]= value

        react_role_configuration['emoji_role_dict'] = emoji_role_dict

        ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles',{})[group_name] = react_role_configuration

        await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['react-roles'], indent=2))


    @_react_role.command(aliases=["remove"])
    async def _react_role_remove(self, ctx, group_name):

        ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {})[group_name] = {}
        await self.utilities._send_message(ctx.channel, f", group-name **{group_name}** has been removed from react-role configurations.",user=ctx.message.author)

    @_react_role.command(pass_context=True, hidden=True, aliases=["debug"])
    async def _react_role_debug(self, ctx, emoji):
        try:

            to_save = self.serialize(ctx.guild, emoji)
            await self.utilities._send_message(ctx.channel, f"To Save: `{to_save}`")

            for_reaction = self.emojify(ctx.guild, to_save)
            message = await self.utilities._send_message(ctx.channel, f"For Reaction: {for_reaction}")

            emoji_to_add = self.emojify(ctx.guild, to_save)
            await message.add_reaction(emoji_to_add)

            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60, check=lambda r, u: u.id == ctx.message.author.id)

            from_reaction = self.demojify(ctx.guild, str(reaction))
            await self.utilities._send_message(ctx.channel, f"From Reaction: {from_reaction}")

        except Exception as error:
            print(error)



    @commands.command(pass_context=True, hidden=True, aliases=["select"])
    async def _select_react_role(self, ctx, group_name=None):
        try:
            if group_name == None:
                help_embed = self.utilities.get_help_embed("Select roles via reactions.", "!select *group-name*", "Available Groups ", ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {}).keys(), "message")
                return await ctx.channel.send(embed = help_embed)


            group_dict = ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {}).get(group_name, {})

            if group_dict:

                exclusive = group_dict.get('exclusive', False)
                if exclusive == 'true':
                    return await self._assign_exclusive_role_via_reaction(ctx, None, ctx.message.author, emoji_role_dict=group_dict['emoji_role_dict'])
                else:
                    return await self._assign_role_via_reaction(ctx, None, ctx.message.author, emoji_role_dict=group_dict['emoji_role_dict'])

            return await self.utilities._send_error_message(ctx.channel, f", No ReactRoles are defined for **{group_name}**", ctx.message.author)

        except Exception as error:
            return await self.utilities._send_error_message(ctx.channel, f", Some error has occured!", ctx.message.author)
            print(error)


    async def _assign_exclusive_role_via_reaction(self, ctx, message, original_user, emoji_role_dict=None):

        timeout_duration = 60

        for role_name in emoji_role_dict.values():
            role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name = role_name)
            if role_to_be_assigned:
                if role_to_be_assigned in original_user.roles:
                    return await self.utilities._send_error_message(ctx.channel, f"You are already a member of **{role_to_be_assigned.name}**. Please contact an admin if you want to switch roles!", original_user)

        if not message:
            message_text = "\n"
            for emoji, role in emoji_role_dict.items():
                message_text += f"\n{self.printable(ctx.guild, emoji)} - **{role}**"
            message = await self.utilities._send_message(ctx.channel, f"React to this message to select the role(s).{message_text}", footer=f"Click \u23f9 to stop. This message will be auto deleted in {timeout_duration} seconds.")

        for emoji in emoji_role_dict.keys():
            try:
                await message.add_reaction(self.emojify(ctx.guild, emoji))
            except Exception as error:
                print(error)

        await message.add_reaction('\u23f9')
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60, check=lambda r, u: u.id == original_user.id and r.message.id == message.id)
            if reaction.emoji == '\u23f9':
                await message.remove_reaction(reaction.emoji, user)
                await self.utilities._send_error_message(ctx.channel, "The role selection was cancelled.", original_user)
                await asyncio.sleep(5)
                await message.delete()


            await message.remove_reaction(reaction.emoji, user)
            role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name=emoji_role_dict.get(self.demojify(ctx.guild,str(reaction.emoji))))
            await original_user.add_roles(role_to_be_assigned)

            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{original_user.display_name}**, you joined **{role_to_be_assigned.name}** {reaction}!")
            await asyncio.sleep(3)
            await message.delete()

        except asyncio.TimeoutError:
            timeout_message = await self.utilities._send_error_message(ctx.channel, f"the request has timed out. You can type **!teams** to pick up a team.", original_user)
            await asyncio.sleep(3)
            await message.delete()

        except Exception as error:
            print(error)
        return






    async def _assign_role_via_reaction(self, ctx, message, original_user, emoji_role_dict = None, exclusive=False):
        is_role_changed = False
        timeout_duration = 20

        if not message:
            message_text = ""
            for emoji, role in emoji_role_dict.items():
                message_text += f"\n{self.printable(ctx.guild, emoji)} - **{role}**"

            message = await self.utilities._send_embed(ctx.channel, description=f"React to this message to make your selection(s). {message_text}", footer=f"Click \u23f9 to stop. This message will be auto deleted after {timeout_duration} second of inactivity.")

        for emoji in emoji_role_dict.keys():
            try:
                await message.add_reaction(self.emojify(ctx.guild, emoji))
            except Exception as error:
                print(error)


        await message.add_reaction('\u23f9')

        try:
            is_timed_out = False
            while True:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout_duration, check=lambda r, u: u.id == original_user.id and r.message.id == message.id)

                if reaction.emoji == '\u23f9':
                    await message.remove_reaction(reaction.emoji, user)
                    await self.utilities._send_error_message(ctx.channel, "The role selection has been terminated.", original_user)
                    await asyncio.sleep(5)
                    return await message.delete()

                await message.remove_reaction(reaction.emoji, user)
                role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name=emoji_role_dict.get(self.demojify(ctx.guild, str(reaction.emoji))))
                if role_to_be_assigned:
                    is_role_changed = True
                    if role_to_be_assigned in original_user.roles:
                        await original_user.remove_roles(role_to_be_assigned)
                        await self.utilities._send_error_message(ctx.channel, f", you left **{role_to_be_assigned.name}** {reaction}!",original_user)
                    else:
                        await original_user.add_roles(role_to_be_assigned)
                        await self.utilities._send_message(ctx.channel, f"Beep Beep! **{original_user.display_name}**, you joined **{role_to_be_assigned.name}** {reaction}!")
                else:
                    await self.utilities._send_error_message(ctx.channel, f", I couldn't find **{emoji_role_dict.get(reaction.emoji)}**!", original_user)

        except asyncio.TimeoutError:
            if not is_role_changed:
                timeout_message = await self.utilities._send_error_message(ctx.channel, f"The role selection process is complete.", original_user)
            await asyncio.sleep(3)
            await message.delete()

        except Exception as error:
            print(error)


        return




    beep_react_role = ("""**{member}** here are the commands for trade management. 

**!react-role list** - brings up all the react-role configuration.
**!react-role remove <group-name>** - to remove group from react-role configuration.

**!react-role add <group-name> <configuration-json>** - to add group from react-role configuration.
example: 
```!react-role add region 
{example}```

**!select <group-name>** - to trigger a reaction based role selection.

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

        sample_text = json.dumps(self.sample_role_selection_dict, indent=2)
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - React Role Management", description=self.beep_react_role.format(member=ctx.message.author.display_name, example=sample_text), footer=footer))


def setup(bot):
    bot.add_cog(ReactRoleManager(bot))


