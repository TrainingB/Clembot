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

class CustomException(Exception):
    pass

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
                    "emoji1" : "role one",
                    "emoji1" : "role two",
                    "emoji1" : "role three"
                },
                "reaction-groups": {
                    "emoji1": "group one",
                    "emoji1": "group two",
                    "emoji1": "group three"
                },
                "options" : {
                    "exclusive": False,
                    "remove-roles" : True
                },
                "rsvp" : {
                    "status" : ["trainer_name"]
                }
            }
        }
    }

    options= {
        "exclusive": False,
        "remove-roles" : False,
        "manage-roles" : False,
        "display-rsvp" : False,
        "single-use" : False
    }


    toggle_option = ['single-use', 'exclusive' , 'remove-roles', 'display-rsvp', 'manage-roles']

    beep_mini_event = ("""**{member}** here are the commands for Mini Event management.

    **!mini-event create title description #channel** - send an embed post for mini-event in #channel.
    
    
    **!mini-event edit message_id new_title new_description image_url** - update the message.
    **!mini-event update-fields name value [name value]** - updates the message with fields with name value pair.
    **!mini-event remove-fields name** - to remove fields from the message.
        """)





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
                reference_id = self.utilities._uuid(reference_id)
                if reference_id not in self.bot.guild_dict[guild_id].setdefault('reaction-roles', {}).keys():
                    raise ValueError(f":id: {reference_id} is not registered for Reaction Role.")
                # await self.utilities._send_error_message(ctx.channel, f" :id: {reference_id} is not registered for Reaction Role.", ctx.author)

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
    async def _purge(self, ctx, message_count:int, message_id_to_stop: int = None):

        if message_count > 50:
            message_count = 50

        async for message in ctx.channel.history(limit=message_count):
            if message_id_to_stop and message.id == message_id_to_stop:
                break
            await message.delete()

    league_options = ['self-assign', 'manage-via-role' , 'remove-roles']

    @commands.group(pass_context=True, hidden=True, aliases=["league"])
    async def _league(self, ctx, title, body=None, channel: discord.TextChannel=None ):

        if not channel:
            channel = ctx.channel

        message = await self.utilities._send_embed(channel, body, title, {'Current Members' : [] })

        message_uuid = self.utilities._uuid(message.id)
        message.embeds[0].set_footer(text=f"[{message_uuid}]")

    @_league.command(pass_context=True, hidden=True, aliases=["register"])
    async def _league_register(self, ctx, title, channel: discord.TextChannel = None):
        await self.utilities._send_message(ctx.channel, f"League has been created!")

    @commands.command(pass_context=True, hidden=True, aliases=["say"])
    async def _say(self, ctx, title, body=None, channel: discord.TextChannel=None ):

        if not channel:
            channel = ctx.channel

        return await self.__send_message(channel, title, body)

    async def __send_message(self, channel, title, body=None):

        if not channel:
            channel = ctx.channel

        message = await self.utilities._send_embed(channel, body, title)

        message_uuid = self.utilities._uuid(message.id)
        message.embeds[0].set_footer(text=f"[{message_uuid}]")

        return message



    @commands.group(pass_context=True, hidden=True, aliases=["reaction-role", "rtr"])
    async def _reaction_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @commands.group(pass_context=True, hidden=True, aliases=["mini-event", "me"])
    async def _mini_event(self, ctx):

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

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["reset"])
    @checks.is_owner()
    async def _reaction_role_reset(self, ctx, reference_id):
        self.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(reference_id, {}).pop('emoji_role_map')
        self.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(reference_id, {}).pop('rsvp')
        self.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(reference_id, {}).pop('reaction-group')
        await self.utilities._send_message(ctx.channel,f"```{json.dumps(ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).get(reference_id), indent=2)}```")



    def __option_status(self, react_role_dict, option, default_value):
        react_role_dict.setdefault('options', {}).setdefault(option, default_value)
        return react_role_dict.get('options').get(option)

    # options = {
    #     "exclusive": False,
    #     "single-use": False
    # }

    def __register_message(self, message, channel, options):

        message_uuid = None
        if message:
            message_uuid = self.utilities._uuid(message.id)
            message_master = {
                "message_id": message.id,
                "channel_id": channel.id
            }
            self.bot.guild_dict[message.guild.id].setdefault('reaction-roles', {}).setdefault(message_uuid, {})['message_master'] = message_master
            self.bot.guild_dict[message.guild.id].setdefault('reaction-roles', {}).setdefault(message_uuid, {})['options'] = options
        return message_uuid

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["register"])
    async def _reaction_role_register(self, ctx, message_id: int, channel: discord.TextChannel=None ):

        options = {
            "exclusive": False,
            "single-use": False
        }

        try:
            if not channel:
                channel = ctx.channel
            message = await channel.get_message(id=message_id)
            if message:
                message_uuid = self.__register_message(message, channel, options)
                await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(message_uuid, channel.name, message_id, None, None), footer=f"[{message_uuid}]")

        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(ctx.channel, error, ctx.author)

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["deregister"])
    async def _reation_role_deregister(self, ctx, reference_id ):
        try:
            del ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {})[message_id]
        except Exception:
            pass
        await self.utilities._send_message(ctx.channel, f"Reaction to `{message_id}` will not assign roles anymore!", user=ctx.author)



    async def _reaction_role_add_reaction_pair(self, ctx, reference_id, emoji, role_or_group, tracking_type):
        try:

            tracking_group = 'emoji_role_map'
            if tracking_type == 'group':
                tracking_group = 'reaction-group'

            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)
            if not message:
                await self.utilities._send_error_message((ctx.channel, f"No message found with `{message.id}`"),message.author)

            emoji_id = self.utilities._normalize(emoji)

            await message.add_reaction(self.utilities._normalize(emoji))

            static_react_role_configuration = ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{}).setdefault(reference_id, {})
            new_static_react_role_configuration = {emoji_id: role_or_group}

            static_react_role_configuration.setdefault(tracking_group, {}).update(new_static_react_role_configuration)

            ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {})[reference_id] = static_react_role_configuration

            log_message = await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(reference_id, None, None, emoji, role_or_group))
            await asyncio.sleep(5)
            if log_message:
                await log_message.delete()


        except Exception as error:
            print(error)
            await self.utilities._send_error_message_and_cleanup(ctx.channel, error, ctx.author)



    @_reaction_role.command(pass_context=True, hidden=True, aliases=["add-role"])
    async def _reaction_role_add_role(self, ctx, reference_id, emoji, role):
        await self._reaction_role_add_reaction_pair(ctx, reference_id, emoji, role, 'role')


    @_reaction_role.command(pass_context=True, hidden=True, aliases=["add-group", "ag"])
    async def _reaction_role_add_group(self, ctx, reference_id, emoji, group):
        await self._reaction_role_add_reaction_pair(ctx, reference_id, emoji, group, 'group')

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["remove-role", "rr"])
    async def _reaction_role_remove_role(self, ctx, reference_id, emoji):
        await self._reaction_role_remove_reaction_pair(ctx, reference_id, emoji, 'role')

    @_reaction_role.command(pass_context=True, hidden=True, aliases=["remove-group", "rg"])
    async def _reaction_role_remove_group(self, ctx, reference_id, emoji):
        await self._reaction_role_remove_reaction_pair(ctx, reference_id, emoji, 'group')


    async def _reaction_role_remove_reaction_pair(self, ctx, reference_id, emoji, tracking_type):
        try:

            tracking_group = 'emoji_role_map'
            if tracking_type == 'group':
                tracking_group = 'reaction-group'

            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)
            if not message:
                await self.utilities._send_error_message((ctx.channel, f"No message found with `{message.id}`"), message.author)

            emoji_id = self.utilities._normalize(emoji)

            for reaction in message.reactions:
                if self.utilities._normalize(reaction.emoji) == emoji_id:
                    async for user_reacted in reaction.users():
                        await message.remove_reaction(self.utilities._normalize(emoji), user_reacted)

            ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{})[reference_id][tracking_group].pop(emoji_id, None)

            await self.utilities._send_embed(ctx.channel, f"Reaction has been removed successfully. `{message.id}`", "Reaction Removed",
                                             self._generate_addtional_fields(reference_id, channel.name, message.id, emoji, None))

        except Exception as error:
            print(error)


    @_mini_event.command(pass_context=True, hidden=True, aliases=["toggle"])
    async def _mini_event_toggle(self, ctx, reference_id, *options):
        try:
            if reference_id not in ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).keys():
                await self.utilities._send_error_message(ctx.channel, f" :id: {reference_id} is not registered for Reaction Role.", ctx.author)

            for option in options:
                if option in self.toggle_option:
                    static_react_role_configuration = ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles',{}).setdefault(reference_id, {})
                    existing_value = static_react_role_configuration.get('options',self.options).get(option)
                    ctx.bot.guild_dict[ctx.guild.id].setdefault('reaction-roles', {}).setdefault(reference_id, {}).setdefault('options', self.options)[option] = not existing_value
                    await self.utilities._send_embed(ctx.channel, None, None, self._generate_addtional_fields(reference_id, option=option, value=not existing_value))
                else:
                    await self.utilities._send_error_message(ctx.channel, f" available toggle options are: **{', '.join(list(self.options.keys()))}**", ctx.author)

            if option == 'display-rsvp':
                await self.__refresh_embed_fields(ctx.guild.id, ctx.channel, reference_id)

        except Exception as error:
            print(error)


    @_mini_event.command(pass_context=True, hidden=True, aliases=["help"])
    async def _mini_event_help(self, ctx):

        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.embed(title="Help - Mini Event Management", description=self.beep_mini_event.format(member=ctx.message.author.display_name), footer=footer)


    @_mini_event.command(pass_context=True, hidden=True, aliases=["create"])
    async def _mini_event_create(self, ctx, title, body=None, channel: discord.TextChannel = None):
        mini_event_options = {
            "exclusive": False,
            "single-use": False,
            "remove-roles" : False,
            "display-rsvp" : False,
            "manage-roles" : False
        }

        if not channel:
            channel = ctx.channel

        message = await self.__send_message(channel, title, body)

        message_uuid = self.__register_message(message, channel, mini_event_options)

        await self.__refresh_embed_fields(message.guild.id, channel, message_uuid)

        return message

    @_mini_event.command(pass_context=True, hidden=True, aliases=["remove"])
    @checks.is_owner()
    async def _mini_event_remove(self, ctx, reference_id):

        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)

            await message.delete()
            ctx.bot.guild_dict[ctx.guild.id]['reaction-roles'].pop(reference_id, None)
            await self.utilities._send_message(ctx.channel, f"Message [{reference_id}] has been removed.", user=ctx.author)

        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(channel, f"{error}", user=ctx.author)

    @_mini_event.command(pass_context=True, hidden=True, aliases=["clear-fields"])
    async def _reaction_role_clear_fields(self, ctx, reference_id):
        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)
            message.embeds[0].clear_fields()

            await message.edit(embed=message.embeds[0])

        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(channel, f"{error}", user=ctx.author)

    @_mini_event.command(pass_context=True, hidden=True, aliases=["update-fields", "add-fields"])
    async def _mini_event_update_fields(self, ctx, reference_id, *args):
        try:
            args_dict = dict(zip(args[::2], args[1::2]))
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)

            for index, field in enumerate(list(message.embeds[0].fields), start=0):
                if field.name in list(args_dict.keys()):
                    message.embeds[0].set_field_at(index, name=field.name, value=args_dict[field.name], inline=False)
                    args_dict.pop(field.name)

            for key in list(args_dict.keys()):
                message.embeds[0].add_field(name=key , value=args_dict[key])

            await message.edit(embed=message.embeds[0])
            await self.utilities._send_message(ctx.channel, f"Message has been updated.", user=ctx.author)
        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(channel, f"{error}", user=ctx.author)

    @_mini_event.command(pass_context=True, hidden=True, aliases=["remove-fields"])
    async def _mini_event_remove_fields(self, ctx, reference_id, *args):
        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)

            for index, field in enumerate(list(message.embeds[0].fields), start=0):
                if field.name in list(args):
                    message.embeds[0].remove_field(index)

            await message.edit(embed=message.embeds[0])
            await self.utilities._send_message(ctx.channel, f"Message has been updated.", user=ctx.author)
        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(channel, f"{error}", user=ctx.author)

    @_mini_event.command(pass_context=True, hidden=True, aliases=["add-image"])
    async def _mini_event_add_image(self, ctx, reference_id, url):
        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)
            if not url:
                url = message.embeds[0].url
            elif url == "None":
                url = None
            await self.__refresh_embed(ctx.guild.id, channel, reference_id, url=url)
        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(channel, f"{error}", user=ctx.author)

    @_mini_event.command(pass_context=True, hidden=True, aliases=["edit"])
    async def _mini_event_edit(self, ctx, reference_id, title=None, body=None, url=None ):
        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, ctx.guild.id)

            if not title:
                title = message.embeds[0].title
            if not body:
                body = message.embeds[0].description
            if not url:
                url = message.embeds[0].url
            elif url == "None":
                url = None

            await self.__refresh_embed(ctx.guild.id, channel, reference_id, title, body, url)
            await self.__refresh_embed_fields(ctx.guild.id, channel, reference_id)
            await self.utilities._send_message(ctx.channel, f"Message has been updated.", user=ctx.author)
        except Exception as error:
            await self.utilities._send_error_message_and_cleanup(channel, f"{error}", user=ctx.author)


    async def __refresh_embed_fields(self, guild_id, original_channel, reference_id):
        print(f"__refresh_embed_fields({reference_id})")
        try:
            channel, message = await self._fetch_channel_message_from_reference(reference_id, guild_id)

            static_react_role_configuration = self.bot.guild_dict[guild_id].setdefault('reaction-roles', {}).setdefault(reference_id, {})
            if static_react_role_configuration['options'].get('display-rsvp', False) == True:
                existing_fields = message.embeds[0].fields

                rsvp_roles_dict = dict(static_react_role_configuration['rsvp'])

                for index, field in enumerate(list(message.embeds[0].fields), start=0):
                    if field.name in list(rsvp_roles_dict.keys()):
                        if rsvp_roles_dict[field.name].__len__() > 0:
                            message.embeds[0].set_field_at(index, name=field.name, value=f'```{", ".join(rsvp_roles_dict[field.name])}```', inline=False)
                        else:
                            message.embeds[0].remove_field(index)
                        rsvp_roles_dict.pop(field.name)

                for key in list(rsvp_roles_dict.keys()):
                    if rsvp_roles_dict[key].__len__() > 0:
                        message.embeds[0].add_field(name=key, value=f'```{", ".join(rsvp_roles_dict[key])}```', inline=False)
            message.embeds[0].set_footer(text=f"Managed by ID: [{reference_id}]")
            await message.edit(embed=message.embeds[0])
        except Exception as error:
            print(error)


    async def __refresh_embed(self, guild_id, original_channel, message_or_reference_id, title=None, body=None, url=None ):
        print(f"__refresh_embed({message_or_reference_id})")
        try:
            if message_or_reference_id.isdigit():
                reference_id = self.utilities._uuid(message_or_reference_id)
            else:
                reference_id = message_or_reference_id

            channel, message = await self._fetch_channel_message_from_reference(reference_id, guild_id)

            if not title:
                title = message.embeds[0].title
            if not body:
                body = message.embeds[0].description
            if not url:
                url = message.embeds[0].url
                if not url:
                    url = message.embeds[0].image.url
            elif url == "None":
                url = None

            new_embed = discord.Embed(description=body, title=title, colour=message.embeds[0].colour.value)
            if url:
                new_embed.set_image(url=url)

            new_embed.set_footer(text=f"Managed by ID: [{reference_id}]")
            await message.edit(embed=new_embed)
        except Exception as error:
            print(error)


    @_reaction_role.command(pass_context=True, hidden=True, aliases=["refresh"])
    @checks.is_owner()
    async def _reaction_role_refresh(self, ctx, message_or_reference_id):

        await self.__refresh_embed_fields(ctx, ctx.guild.id, ctx.channel, message_or_reference_id)
        await ctx.message.delete()


    def _is_user_has_any_role(self, user, list_of_role_names):
        for already_assigned_role in user.roles:
            if already_assigned_role.name in list_of_role_names:
                return True
        return False

    def _is_user_has_role(self, user, role):
        if role in user.roles:
            return True
        return False

    async def _assign_role_to_user(self, user, role, channel, message):

        if role not in user.roles:
            await user.add_roles(role)
        else:
            raise CustomException({"message" : "User already has role assigned."})

        return

    async def handle_reaction(self, reaction, operation='add'):
        # print(f"handle_reaction_{operation} is called()")
        try:
            reference_id = self.utilities._uuid(reaction.message_id)

            channel, message = await self._fetch_channel_message_from_reference(reference_id, reaction.guild_id)
            guild = message.guild
            user = guild.get_member(reaction.user_id)

            emoji_id = self.utilities._normalize(reaction.emoji)
            static_react_role_dict = self.bot.guild_dict[reaction.guild_id].setdefault('reaction-roles',{}).setdefault(reference_id,{})

            is_exclusive = self.__option_status(static_react_role_dict, 'exclusive', False)
            is_remove_roles = self.__option_status(static_react_role_dict, 'remove-roles', False)
            is_display_rsvp = self.__option_status(static_react_role_dict, 'display-rsvp', False)
            is_manage_roles = self.__option_status(static_react_role_dict, 'manage-roles', False)

            role_to_be_assigned_name = static_react_role_dict.get('emoji_role_map',{}).get(emoji_id, None)
            if role_to_be_assigned_name:
                group_for_reaction = role_to_be_assigned_name
            else:
                group_for_reaction = static_react_role_dict.get('reaction-group',{}).get(emoji_id, None)

            static_react_role_dict.setdefault('rsvp', {})
            if is_display_rsvp and group_for_reaction:
                if operation == 'add':
                    if user.display_name not in static_react_role_dict.setdefault('rsvp', {}).setdefault(group_for_reaction, []):
                        static_react_role_dict['rsvp'].setdefault(group_for_reaction, []).append(user.display_name)
                else:
                    if user.display_name in static_react_role_dict.setdefault('rsvp', {}).setdefault(group_for_reaction, []):
                        static_react_role_dict['rsvp'].setdefault(group_for_reaction, []).remove(user.display_name)
                print(static_react_role_dict['rsvp'])
                await self.__refresh_embed_fields(guild.id, channel, reference_id)

            if not is_manage_roles:
                return

            role_to_be_assigned = None
            if role_to_be_assigned_name:
                role_to_be_assigned = discord.utils.get(message.guild.roles, name=static_react_role_dict['emoji_role_map'][emoji_id])
                if role_to_be_assigned:
                    pass
                else:
                    if group_for_reaction:
                        pass
                    else:
                        return await self.utilities._send_error_message_and_cleanup(channel, f"reaction is not setup for role assingation!", user=user)

            role_name_list = static_react_role_dict['emoji_role_map'].values()

            if is_exclusive:
                if self._is_user_has_any_role(user, role_name_list):
                    if operation == 'add':
                        return await self.utilities._send_error_message_and_cleanup(channel, f"You already have one of the exclusive role assigned. Please contact an admin if you want to switch roles!", user=user)
                    else :
                        return await self.utilities._send_error_message_and_cleanup(channel, f"removing exclusive role is not allowed. Please contact an admin.", user)

            log_message = None
            if role_to_be_assigned:
                if role_to_be_assigned not in user.roles:
                    if operation == 'add':
                        await user.add_roles(role_to_be_assigned)
                        log_message = await self.utilities._send_message(channel, f"you joined **{role_to_be_assigned.name}** {reaction.emoji}!", user=user)
                    else:
                        return await self.utilities._send_error_message_and_cleanup(channel, f"your reaction and role assignation was out of sync. *Please react again to make changes!*", user=user)
                else:
                    if is_remove_roles:
                        if operation == 'remove':
                            await user.remove_roles(role_to_be_assigned)
                            log_message = await self.utilities._send_message(channel,f"you left **{role_to_be_assigned.name}** {reaction.emoji}!", user=user)
                        else:
                            return await self.utilities._send_error_message_and_cleanup(channel, f"your reaction and role assignation was out of sync. *Please react again to make changes!*", user=user)
                    else:
                        log_message = await self.utilities._send_message(channel, f"you already have **{role_to_be_assigned.name}** {reaction.emoji}!", user=user)
            # else:
            #     log_message = await self.utilities._send_error_message(channel, f"The role **{static_react_role_dict['emoji_role_map'].get(emoji_id)}** associated with reaction {reaction.emoji} not found!", user=user)

            await asyncio.sleep(5)
            if log_message:
                await log_message.delete()
            return
        except Exception as error:
            log_message = await self.utilities._send_error_message(channel, f"handle_reaction() : {error}")
            await asyncio.sleep(5)
            if log_message:
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


