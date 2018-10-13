import re
import discord
import os
import time_util
import json
from discord.ext import commands
from exts.utilities import Utilities
import checks
from random import *
import asyncio

import json

class ReactionRoleManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()


    # multi-use no unassignment is possible False re-use removes the role.
    # exclusive allows only one of the roles from the group


    reaction_roles_dict = {
        "reaction-roles" : {
            "message_uuid" : {
                "message_master" : {
                    "channel_id" : 0,
                    "message_id" : 0
                },
                "emoji_role_map" : {
                    "emoji1" :  "role one",
                    "emoji1"  : "role two",
                    "emoji1" : "role three"
                },
                "options" : {
                    "exclusive": False,
                    "remove-roles" : True
                }
            }
        }
    }

    options= {
        "exclusive": False,
        "remove-roles" : False
    }

    beep_react_role = ("""**{member}** here are the commands for Reaction Role management.

**!reaction-role register *message_id* #channel** - registers a message for reaction role.

**!reaction-role add *reference_id emoji role-name*** - adds a emoji reaction to the message and associates the role.
**!reaction-role remove *reference_id emoji*** - removes the emoji-role association.
**!react-role remove <group-name>** - to remove group from react-role configuration.

**!react-role add <group-name> <configuration-json>** - to add group from react-role configuration.
example:
```!react-role add region
{example}```

**!select <group-name>** - to trigger a reaction based role selection.

    """)




    async def _fetch_channel_message_from_reference(self, reference_id, guild_id):
        try:
            if reference_id not in self.bot.guild_dict[guild_id].setdefault('reaction-roles', {}).keys():
                raise ValueError(f":id: {reference_id} is not registered for Reaction Role.")
                # await self.utilities._send_error_message(ctx.channel, f" :id: {reference_id} is not registered for Reaction Role.", ctx.author)
            else:
                static_react_role_configuration = self.bot.guild_dict[guild_id].setdefault('reaction-roles',{}).setdefault(reference_id,{})

                message_id = static_react_role_configuration['message_master']['message_id']
                channel_id = static_react_role_configuration['message_master']['channel_id']

                channel = self.bot.get_channel(id=channel_id)
                message = await channel.get_message(id=message_id)

                return (channel, message)
        except Exception as error:
            raise ValueError(error)

    def _generate_addtional_fields(self, reference_id=None, channel_name=None, message_id=None, emoji=None, role=None, option=None, value=None ):
        additional_fields = {}
        if reference_id:
            additional_fields[':id: Reference Id'] = reference_id
        if channel_name:
            additional_fields[':tv: Channel'] = channel_name
        if message_id:
            additional_fields[':cloud: Message'] = message_id
        if emoji:
            additional_fields[':art: Emoji'] = emoji
        if role:
            additional_fields[':busts_in_silhouette: Role'] = role
        if option:
            additional_fields[f":gear: {option}"] = value
        return additional_fields


    @commands.command(pass_context=True, hidden=True, aliases=["purge"])
    async def _purge(self, ctx, message_count:int ):

        if int(message_count) > 50:
            message_count = 50

        async for message in ctx.channel.history(limit=message_count):
            await message.delete()

    @commands.command(pass_context=True, hidden=True, aliases=["say"])
    async def _say(self, ctx, title, body=None, channel: discord.TextChannel=None ):

        if not channel:
            channel = ctx.channel

        message = await self.utilities._send_embed(channel, body, title)

        message_uuid = self.utilities._uuid(message.id)

        await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(message_uuid))

    @commands.group(pass_context=True, hidden=True, aliases=["reaction-role", "rtr"])
    async def _reaction_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["purge"])
    @checks.is_owner()
    async def _reaction_role_purge(self, ctx):
        ctx.bot.guild_dict[ctx.guild.id]['reaction-roles'] = {}

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["status"])
    @checks.is_owner()
    async def _reaction_role_status(self, ctx, reference_id):
        await self.utilities._send_message(ctx.channel,f"```{json.dumps(ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).get(reference_id), indent=2)}```")


    @_reaction_role.command(pass_context=True, hidden=True, aliases=["register"])
    async def _reaction_role_register(self, ctx, message_id: int, channel: discord.TextChannel=None ):
        try:
            if not channel:
                channel = ctx.channel

            message = await channel.get_message(id=message_id)
            if message:
                message_uuid = self.utilities._uuid(message_id)
                message_master = {
                    "message_id": message_id,
                    "channel_id": channel.id
                }
                options = {
                    "exclusive" : False,
                    "single-use" : False
                }

                ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(message_uuid,{})['message_master'] = message_master
                ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(message_uuid, {})['options'] = options

                await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(message_uuid, channel.name, message_id, None, None) )

        except Exception as error:
            print(error)

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["deregister"])
    async def _reation_role_deregister(self, ctx, reference_id ):
        try:
            del ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {})[message_id]
        except Exception:
            pass
        await self.utilities._send_message(ctx.channel, f"Reaction to `{message_id}` will not assign roles anymore!", user=ctx.author)


    @_reaction_role.command(pass_context=True, hidden=True, aliases=["add-role"])
    async def _reaction_role_add_role(self, ctx, reference_id, emoji, role):

        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)
            if not message:
                await self.utilities._send_error_message((ctx.channel, f"No message found with `{message.id}`"),message.author)

            emoji_id = self.utilities._normalize(emoji)

            await message.add_reaction(self.utilities._normalize(emoji))

            static_react_role_configuration = ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{}).setdefault(reference_id, {})
            new_static_react_role_configuration = {emoji_id: role}

            static_react_role_configuration.setdefault('emoji_role_map', {}).update(new_static_react_role_configuration)

            ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {})[reference_id] = static_react_role_configuration

            await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(reference_id, None, None, emoji, role))
            # await self.utilities._send_message(ctx.channel,json.dumps(ctx.bot.guild_dict[ctx.guild.id]['reaction-roles'], indent=2))

        except Exception as error:
            print(error)

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["remove-role"])
    async def _reaction_role_remove_role(self, ctx, reference_id, emoji):

        try:

            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)
            if not message:
                await self.utilities._send_error_message((ctx.channel, f"No message found with `{message.id}`"), message.author)

            emoji_id = self.utilities._normalize(emoji)

            for reaction in message.reactions:
                if self.utilities._normalize(reaction.emoji) == emoji_id:
                    async for user_reacted in reaction.users():
                        await message.remove_reaction(self.utilities._normalize(emoji), user_reacted)

            del ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{})[message_id]['emoji_role_map'][emoji_id]

            await self.utilities._send_embed(ctx.channel, f"Reaction has been removed successfully. `{message.id}`", "Reaction Removed",
                                             self._generate_addtional_fields(reference_id, channel.name, message.id, emoji, None))

        except Exception as error:
            print(error)

    toggle_option = ['single-use', 'exclusive' , 'remove-roles']

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["toggle"])
    async def _reaction_role_toggle(self, ctx, reference_id, option):

        if option in self.options.keys():

            if reference_id not in ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{}).keys():
                await self.utilities._send_error_message(ctx.channel, f" :id: {reference_id} is not registered for Reaction Role.", ctx.author)
            else:
                static_react_role_configuration = ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{}).setdefault(reference_id, {})

                existing_value = static_react_role_configuration.get('options',self.options).get(option)

                ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(reference_id, {}).setdefault('options', self.options)[option] = not existing_value

                await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(reference_id, option=option, value=not existing_value))
        else:
            await self.utilities._send_error_message(ctx.channel, f" available toggle options are: **{', '.join(list(self.options.keys()))}**", ctx.author)

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["edit"])
    async def _reaction_role_edit(self, ctx, reference_id, title=None, body=None, url=None ):

        channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)

        if not title:
            title = message.embeds[0].title
        if not body:
            body = message.embeds[0].description
        if not url:
            url = message.embeds[0].url

        new_embed = discord.Embed(description=body, title=title, colour=message.embeds[0].colour.value, url=url)
        new_embed.set_image(url=url)
        await message.edit(embed=new_embed)

        await self.utilities._send_message(ctx.channel, f"Message has been updated.", user=ctx.author)

    async def handle_reaction_add(self, reaction):
        print("handle_reaction_add")
        try:
            reference_id = self.utilities._uuid(reaction.message_id)

            channel, message = await self._fetch_channel_message_from_reference(reference_id, reaction.guild_id)
            guild = message.guild
            user = guild.get_member(reaction.user_id)

            emoji_id = self.utilities._normalize(reaction.emoji)
            static_react_role_dict = self.bot.guild_dict[reaction.guild_id].setdefault('reaction-roles',{}).setdefault(reference_id,{})

            role_to_be_assigned = discord.utils.get(message.guild.roles, name=static_react_role_dict['emoji_role_map'][emoji_id])


            is_exclusive = static_react_role_dict['options']['exclusive']
            is_remove_roles = static_react_role_dict['options'].get('remove-roles', False)
            if is_exclusive:
                role_name_list = static_react_role_dict['emoji_role_map'].values()
                for already_assigned_role in user.roles:
                    if already_assigned_role.name in role_name_list:
                        log_message = await self.utilities._send_error_message(channel,
                                                                    f"You are already a member of **{already_assigned_role.name}**. Please contact an admin if you want to switch roles!",
                                                                    user=user)
                        await asyncio.sleep(5)
                        await log_message.delete()
                        return
            if role_to_be_assigned:
                is_role_changed = True
                if role_to_be_assigned not in user.roles:
                    await user.add_roles(role_to_be_assigned)
                    log_message = await self.utilities._send_message(channel, f"you joined **{role_to_be_assigned.name}** {reaction.emoji}!", user=user)
                else:
                    if is_remove_roles:
                        await user.remove_roles(role_to_be_assigned)
                        log_message = await self.utilities._send_error_message(channel,f"you left **{role_to_be_assigned.name}** {reaction.emoji}!", user=user)
                    else:
                        log_message = await self.utilities._send_message(channel, f"you already have **{role_to_be_assigned.name}** {reaction.emoji}!", user=user)
            else:
                log_message = await self.utilities._send_error_message(channel, f"The role **{static_react_role_dict['emoji_role_map'].get(emoji_id)}** associated with reaction {reaction.emoji} not found!", user=user)

            await asyncio.sleep(5)
            await log_message.delete()
            return
        except Exception as error:
            log_message = await self.utilities._send_error_message(channel, f"{error}", user=user)
            await asyncio.sleep(5)
            await log_message.delete()


    @classmethod
    async def _help(self, ctx):

        sample_text = json.dumps(self.sample_role_selection_dict, indent=2)
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - React Role Management", description=self.beep_react_role.format(member=ctx.message.author.display_name, example=sample_text), footer=footer))

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

def setup(bot):
    bot.add_cog(ReactionRoleManager(bot))


