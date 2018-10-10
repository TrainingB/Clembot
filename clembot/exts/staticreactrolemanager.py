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

class StaticReactRoleManager:

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

    @commands.command(pass_context=True, hidden=True, aliases=["purge"])
    async def _purge(self, ctx, message_count:int ):

        if int(message_count) > 50:
            message_count = 50

        async for message in ctx.channel.history(limit=message_count):
            await message.delete()

    @commands.group(pass_context=True, hidden=True, aliases=["react-to-role", "rtr"])
    async def _react_to_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")



    # toggle-single-use TRUE deletes the reaction after use, no unassignment is possible FALSE re-use removes the role.
    # toggle-exclusive  TRUE allows only one role selection,
    # toggle

    toggle_option = ['single-use', 'exclusive' ]

    @_react_to_role.command(pass_context=True, hidden=True, aliases=["toggle"])
    async def _react_to_role_toggle_options(self, ctx, channel: discord.TextChannel, message_id, option):

        options = {
            "single-use" : false,
            "exclusive" : false
        }

       


    # !react-to-role add channel title body
    @_react_to_role.command(pass_context=True, hidden=True, aliases=["add-message"])
    async def _react_to_role_add(self, ctx, title, body=None, channel: discord.TextChannel=None ):
        message = await self.utilities._send_embed(channel, body, title)
        await self.utilities._send_message(ctx.channel, f"Message has been posted with `{message.id}`")

    @_react_to_role.command(pass_context=True, hidden=True, aliases=["remove-message"])
    async def _react_to_role_remove(self, ctx, message_id ):
        try:
            del ctx.bot.guild_dict[ctx.guild.id].setdefault('static-react-roles', {})[message_id]
        except Exception:
            pass
        await self.utilities._send_message(ctx.channel, f"Reaction to `{message_id}` will not assign roles anymore!", user=ctx.author)

    @_react_to_role.command(pass_context=True, hidden=True, aliases=["edit-message"])
    async def _react_to_role_edit_message(self, ctx, channel: discord.TextChannel, message_id, title=None, body=None ):

        message = await channel.get_message(id=message_id)
        if not title:
            title = message.embeds[0].title
        if not body:
            body = message.embeds[0].description

        await message.edit(embed=discord.Embed(description=body, title=title, colour=message.embeds[0].colour.value))

        await self.utilities._send_message(ctx.channel, f"Message has been updated.", ctx.author)


    @_react_to_role.command(pass_context=True, hidden=True, aliases=["message-status"])
    async def _react_to_role_status(self, ctx, message_id):

        await self.utilities._send_message(ctx.channel,json.dumps(ctx.bot.guild_dict[ctx.guild.id]['static-react-roles'].setdefault(message_id,{}), indent=2))

    # !react-to-role add-role message_id role emoji
    @_react_to_role.command(pass_context=True, hidden=True, aliases=["add-role"])
    async def _react_to_role_add_role(self, ctx, channel: discord.TextChannel , message_id, emoji, role ):
        try:
            react_to_role_message_id = '%06x' % randrange(16 ** 6)

            message = await channel.get_message(id=message_id)
            if not message:
                await self.utilities._send_error_message((ctx.channel, f"No message found with `{message.id}`"), message.author)

            emoji_id = self.utilities._normalize(emoji)

            await message.add_reaction(self.utilities._normalize(emoji))

            additional_fields = {}
            additional_fields [':id: Reference Id'] = react_to_role_message_id
            additional_fields[':tv: Channel'] = channel
            additional_fields[':cloud: Message'] = message_id

            await self.utilities._send_embed(ctx.channel, f"Message has been posted with `{message.id}`", None, additional_fields)


            static_react_role_configuration = ctx.bot.guild_dict[ctx.guild.id].setdefault('static-react-roles', {}).setdefault(message_id,{})
            new_static_react_role_configuration = { emoji_id : role }

            static_react_role_configuration.setdefault('emoji_role_dict',{}).update(new_static_react_role_configuration)

            ctx.bot.guild_dict[ctx.guild.id].setdefault('static-react-roles',{})[message_id] = static_react_role_configuration

            await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['static-react-roles'], indent=2))

        except Exception as error:
            print(error)

    @_react_to_role.command(pass_context=True, hidden=True, aliases=["remove-role"])
    async def _react_to_role_remove_role(self, ctx, channel: discord.TextChannel , message_id, emoji):

        try:
            react_to_role_message_id = '%06x' % randrange(16 ** 6)

            message = await channel.get_message(id=message_id)
            if not message:
                await self.utilities._send_error_message((ctx.channel, f"No message found with `{message.id}`"), message.author)

            emoji_id = self.utilities._normalize(emoji)



            for reaction in message.reactions:
                if self.utilities._normalize(reaction.emoji) == emoji_id:
                    async for user_reacted in reaction.users():
                        await message.remove_reaction(self.utilities._normalize(emoji), user_reacted)

            additional_fields = {}
            additional_fields [':id: Reference Id'] = react_to_role_message_id
            additional_fields[':tv: Channel'] = channel
            additional_fields[':cloud: Message'] = message_id
            additional_fields[':art: Message'] = emoji

            del ctx.bot.guild_dict[ctx.guild.id].setdefault('static-react-roles',{})[message_id]['emoji_role_dict'][emoji_id]

            await self.utilities._send_embed(ctx.channel, f"Reaction has been removed successfully. `{message.id}`", "Reaction Removed", additional_fields)

            await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['static-react-roles'], indent=2))

        except Exception as error:
            print(error)
    async def handle_reaction_add(self, reaction):
        try:
            static_react_role_dict = self.bot.guild_dict[reaction.guild_id].get('static-react-roles', {}).get(str(reaction.message_id), {})
            if static_react_role_dict:

                channel = self.bot.get_channel(reaction.channel_id)
                message = await channel.get_message(reaction.message_id)
                guild = message.guild
                user = guild.get_member(reaction.user_id)

                emoji_id = self.utilities._normalize(reaction.emoji)

                role_to_be_assigned = discord.utils.get(message.guild.roles, name=static_react_role_dict['emoji_role_dict'][emoji_id])
                if role_to_be_assigned:
                    is_role_changed = True
                    if role_to_be_assigned not in user.roles:
                        await user.add_roles(role_to_be_assigned)
                        log_message = await self.utilities._send_message(channel, f"Beep Beep! **{user.display_name}**, you joined **{role_to_be_assigned.name}** {reaction.emoji}!")
                    else:
                        log_message = await self.utilities._send_message(channel,f"Beep Beep! **{user.display_name}**, you already have **{role_to_be_assigned.name}** {reaction.emoji}!")
                else:
                    log_message = await self.utilities._send_error_message(channel, f", I couldn't find **{emoji_role_dict.get(reaction.emoji)}**!", user)

                await asyncio.sleep(10)
                await log_message.delete()
                return
        except Exception as error:
            print(error)
    #
    #
    # @commands.group(pass_context=True, hidden=True, aliases=["react-role", "rr"])
    # async def _react_role(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
    #
    #
    # @_react_role.command(aliases=["list"])
    # async def _react_role_list(self, ctx, filter_text=None):
    #     await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['react-roles'], indent=2))
    #
    # def _get_react_role_list(self, ctx):
    #     return ctx.bot.guild_dict[ctx.guild.id]['react-roles'].keys()
    #
    # @_react_role.command(aliases=["add"])
    # async def _react_role_add(self, ctx, *, command_and_json_text):
    #
    #     group_name, _, json_text = command_and_json_text.replace('\n',' ').partition(' ')
    #
    #     if len(json_text) < 1:
    #         sample_text = json.dumps(self.sample_role_selection_dict, indent=2)
    #         return await self.utilities._send_message(ctx.channel, f"```!react-role add group-name \n{sample_text}```")
    #
    #     react_role_configuration = {}
    #     react_role_configuration = json.loads(json_text)
    #     emoji_role_dict = {}
    #
    #     for key, value in react_role_configuration['emoji_role_dict'].items():
    #         new_key = self.serialize(ctx.guild, key)
    #         emoji_role_dict[new_key]= value
    #
    #     react_role_configuration['emoji_role_dict'] = emoji_role_dict
    #
    #     ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles',{})[group_name] = react_role_configuration
    #
    #     await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['react-roles'], indent=2))
    #
    #
    # @_react_role.command(aliases=["remove"])
    # async def _react_role_remove(self, ctx, group_name):
    #
    #     ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {})[group_name] = {}
    #     await self.utilities._send_message(ctx.channel, f", group-name **{group_name}** has been removed from react-role configurations.",user=ctx.message.author)
    #
    # @_react_role.command(pass_context=True, hidden=True, aliases=["debug"])
    # async def _react_role_debug(self, ctx, emoji):
    #     try:
    #
    #         to_save = self.serialize(ctx.guild, emoji)
    #         await self.utilities._send_message(ctx.channel, f"To Save: `{to_save}`")
    #
    #         for_reaction = self.emojify(ctx.guild, to_save)
    #         message = await self.utilities._send_message(ctx.channel, f"For Reaction: {for_reaction}")
    #
    #         emoji_to_add = self.emojify(ctx.guild, to_save)
    #         await message.add_reaction(emoji_to_add)
    #
    #         reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60, check=lambda r, u: u.id == ctx.message.author.id)
    #
    #         from_reaction = self.demojify(ctx.guild, str(reaction))
    #         await self.utilities._send_message(ctx.channel, f"From Reaction: {from_reaction}")
    #
    #     except Exception as error:
    #         print(error)
    #
    #
    #
    # @commands.command(pass_context=True, hidden=True, aliases=["select"])
    # async def _select_react_role(self, ctx, group_name=None):
    #     try:
    #         available_groups = ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {}).keys()
    #
    #         if group_name == None:
    #             help_embed = self.utilities.get_help_embed("Select roles via reactions.", "!select *group-name*", "Available Groups ", available_groups, "message")
    #             return await ctx.channel.send(embed = help_embed)
    #
    #
    #         group_dict = ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {}).get(group_name, {})
    #
    #         if group_dict:
    #
    #             exclusive = group_dict.get('exclusive', False)
    #             if exclusive == 'true':
    #                 return await self._assign_exclusive_role_via_reaction(ctx, None, ctx.message.author, emoji_role_dict=group_dict['emoji_role_dict'])
    #             else:
    #                 return await self._assign_role_via_reaction(ctx, None, ctx.message.author, emoji_role_dict=group_dict['emoji_role_dict'])
    #
    #         available_groups_text = ", ".join(available_groups)
    #         return await self.utilities._send_error_message(ctx.channel, f", Only available selections are **{available_groups_text}**", ctx.message.author)
    #
    #     except Exception as error:
    #         return await self.utilities._send_error_message(ctx.channel, f", Some error has occured!", ctx.message.author)
    #         print(error)
    #
    #
    # async def _assign_exclusive_role_via_reaction(self, ctx, message, original_user, emoji_role_dict=None):
    #
    #     timeout_duration = 60
    #
    #     for role_name in emoji_role_dict.values():
    #         role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name = role_name)
    #         if role_to_be_assigned:
    #             if role_to_be_assigned in original_user.roles:
    #                 return await self.utilities._send_error_message(ctx.channel, f"You are already a member of **{role_to_be_assigned.name}**. Please contact an admin if you want to switch roles!", original_user)
    #
    #     if not message:
    #         message_text = "\n"
    #         for emoji, role in emoji_role_dict.items():
    #             message_text += f"\n{self.printable(ctx.guild, emoji)} - **{role}**"
    #         message = await self.utilities._send_message(ctx.channel, f"React to this message to select the role(s).{message_text}", footer=f"Click \u23f9 to stop. This message will be auto deleted in {timeout_duration} seconds.", user=original_user)
    #
    #     for emoji in emoji_role_dict.keys():
    #         try:
    #             await message.add_reaction(self.emojify(ctx.guild, emoji))
    #         except Exception as error:
    #             print(error)
    #
    #     await message.add_reaction('\u23f9')
    #     try:
    #         reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60, check=lambda r, u: u.id == original_user.id and r.message.id == message.id)
    #         if reaction.emoji == '\u23f9':
    #             await message.remove_reaction(reaction.emoji, user)
    #             timeout_message = await self.utilities._send_error_message(ctx.channel, f", No changes were made!", original_user)
    #             delete_message = await self.utilities._send_error_message(ctx.channel, "Cleaning up messages...", original_user)
    #             await asyncio.sleep(5)
    #             await message.delete()
    #             await asyncio.sleep(5)
    #             await delete_message.delete()
    #             return
    #
    #         await message.remove_reaction(reaction.emoji, user)
    #         role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name=emoji_role_dict.get(self.demojify(ctx.guild,str(reaction.emoji))))
    #         await original_user.add_roles(role_to_be_assigned)
    #
    #         await self.utilities._send_message(ctx.channel, f"Beep Beep! **{original_user.display_name}**, you joined **{role_to_be_assigned.name}** {reaction}!")
    #         await asyncio.sleep(3)
    #         await message.delete()
    #         return
    #
    #     except asyncio.TimeoutError:
    #         nochange_timeout_message = await self.utilities._send_error_message(ctx.channel, f", No changes were made!", original_user)
    #         timeout_message = await self.utilities._send_error_message(ctx.channel, f", the request has timed out.", original_user)
    #         await asyncio.sleep(3)
    #         await message.delete()
    #         await asyncio.sleep(5)
    #         await timeout_message.delete()
    #
    #     except Exception as error:
    #         print(error)
    #     return
    #
    #
    #
    #
    #
    #
    # async def _assign_role_via_reaction(self, ctx, message, original_user, emoji_role_dict = None, exclusive=False):
    #     is_role_changed = False
    #     timeout_duration = 20
    #
    #     if not message:
    #         message_text = ""
    #         for emoji, role in emoji_role_dict.items():
    #             message_text += f"\n{self.printable(ctx.guild, emoji)} - **{role}**"
    #
    #         message = await self.utilities._send_embed(ctx.channel, description=f"**{original_user.display_name}** React to this message to make your selection(s). \n{message_text}", footer=f"Click \u23f9 to stop. This message will be auto deleted after {timeout_duration} second of inactivity.")
    #
    #     for emoji in emoji_role_dict.keys():
    #         try:
    #             await message.add_reaction(self.emojify(ctx.guild, emoji))
    #         except Exception as error:
    #             print(error)
    #
    #
    #     await message.add_reaction('\u23f9')
    #
    #     try:
    #         is_timed_out = False
    #         while True:
    #             reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout_duration, check=lambda r, u: u.id == original_user.id and r.message.id == message.id)
    #
    #             if reaction.emoji == '\u23f9':
    #                 await message.remove_reaction(reaction.emoji, user)
    #                 if not is_role_changed:
    #                     timeout_message = await self.utilities._send_error_message(ctx.channel,f", No changes were made!",original_user)
    #                 else:
    #                     delete_message = await self.utilities._send_error_message(ctx.channel, "Cleaning up messages...", original_user)
    #                     await asyncio.sleep(5)
    #                     return await delete_message.delete()
    #                 await asyncio.sleep(5)
    #                 await message.delete()
    #
    #
    #             await message.remove_reaction(reaction.emoji, user)
    #             role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name=emoji_role_dict.get(self.demojify(ctx.guild, str(reaction.emoji))))
    #             if role_to_be_assigned:
    #                 is_role_changed = True
    #                 if role_to_be_assigned in original_user.roles:
    #                     await original_user.remove_roles(role_to_be_assigned)
    #                     await self.utilities._send_error_message(ctx.channel, f", you left **{role_to_be_assigned.name}** {reaction}!",original_user)
    #                 else:
    #                     await original_user.add_roles(role_to_be_assigned)
    #                     await self.utilities._send_message(ctx.channel, f"Beep Beep! **{original_user.display_name}**, you joined **{role_to_be_assigned.name}** {reaction}!")
    #             else:
    #                 await self.utilities._send_error_message(ctx.channel, f", I couldn't find **{emoji_role_dict.get(reaction.emoji)}**!", original_user)
    #
    #     except asyncio.TimeoutError:
    #         if not is_role_changed:
    #             timeout_message = await self.utilities._send_error_message(ctx.channel, f", No changes were made!", original_user)
    #
    #     except Exception as error:
    #         print(error)
    #
    #     await asyncio.sleep(3)
    #     await message.delete()
    #
    #     return
    #
    #

#
# beep_react_role = ("""**{member}** here are the commands for trade management.
#
# **!react-role list** - brings up all the react-role configuration.
# **!react-role remove <group-name>** - to remove group from react-role configuration.
#
# **!react-role add <group-name> <configuration-json>** - to add group from react-role configuration.
# example:
# ```!react-role add region
# {example}```
#
# **!select <group-name>** - to trigger a reaction based role selection.
#
# """)

    # def get_beep_embed(self, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):
    #
    #     if mode == "message":
    #         color = discord.Colour.green()
    #     else:
    #         color = discord.Colour.red()
    #
    #     help_embed = discord.Embed(title=title, description=f"{description}", colour=color)
    #
    #     help_embed.set_footer(text=footer)
    #     return help_embed

    @classmethod
    async def _help(self, ctx):

        sample_text = json.dumps(self.sample_role_selection_dict, indent=2)
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - React Role Management", description=self.beep_react_role.format(member=ctx.message.author.display_name, example=sample_text), footer=footer))

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

def setup(bot):
    bot.add_cog(StaticReactRoleManager(bot))


