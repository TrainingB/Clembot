import asyncio
import json

import discord
from discord.ext import commands

from clembot.core.bot import group, command
from clembot.core.utils import emojify
from clembot.utilities.utils.utilities import Utilities


class ReactRoleManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

    sample_role_selection_dict = {
        "emoji_role_dict" : {
            "emoji1" :  "role one",
            "emoji1"  : "role two",
            "emoji1" : "role three"
        }
    }


    @group(pass_context=True, hidden=True, aliases=["react-role", "rr"])
    async def _react_role(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")


    @_react_role.command(aliases=["list"])
    async def _react_role_list(self, ctx, filter_text=None):
        await self.utilities._send_message(ctx.channel, json.dumps(ctx.bot.guild_dict[ctx.guild.id]['react-roles'], indent=2))

    def _get_react_role_list(self, ctx):
        return ctx.bot.guild_dict[ctx.guild.id]['react-roles'].keys()

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
    async def _react_role_debug(self, ctx, *emoji_list):
        for emoji in emoji_list:
            try:
                new_emoji = self._new_serialize(emoji)
                this_message=await self.utilities._send_message(ctx.channel, f"New To Save: `{new_emoji}`")
                await this_message.add_reaction(new_emoji)

            except Exception as error:
                Logger.error(f"{traceback.format_exc()}")
                continue


    @command(pass_context=True, hidden=True, aliases=["select"])
    async def _select_react_role(self, ctx, group_name=None):
        try:
            available_groups = ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {}).keys()

            if group_name == None:
                help_embed = self.utilities.get_help_embed("Select roles via reactions.", "!select *group-name*", "Available Groups ", available_groups, "message")
                return await ctx.channel.send(embed = help_embed)


            group_dict = ctx.bot.guild_dict[ctx.guild.id].setdefault('react-roles', {}).get(group_name, {})

            if group_dict:

                exclusive = group_dict.get('exclusive', False)
                if exclusive == 'true':
                    return await self._assign_exclusive_role_via_reaction(ctx, None, ctx.message.author, emoji_role_dict=group_dict['emoji_role_dict'])
                else:
                    return await self._assign_role_via_reaction(ctx, None, ctx.message.author, emoji_role_dict=group_dict['emoji_role_dict'])

            available_groups_text = ", ".join(available_groups)
            return await self.utilities._send_error_message(ctx.channel, f", Only available selections are **{available_groups_text}**", ctx.message.author)

        except Exception as error:
            return await self.utilities._send_error_message(ctx.channel, f", Some error has occured!", ctx.message.author)
            Logger.error(f"{traceback.format_exc()}")


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
            message = await self.utilities._send_message(ctx.channel, f"React to this message to select the role(s).{message_text}", footer=f"Click \u23f9 to stop. This message will be auto deleted in {timeout_duration} seconds.", user=original_user)

        for emoji in emoji_role_dict.keys():
            try:
                await message.add_reaction(emojify(self.numbers_text, self.one_to_ten, ctx.guild, emoji))
            except Exception as error:
                Logger.error(f"{traceback.format_exc()}")

        await message.add_reaction('\u23f9')
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60, check=lambda r, u: u.id == original_user.id and r.message.id == message.id)
            if reaction.emoji == '\u23f9':
                await message.remove_reaction(reaction.emoji, user)
                timeout_message = await self.utilities._send_error_message(ctx.channel, f", No changes were made!", original_user)
                delete_message = await self.utilities._send_error_message(ctx.channel, "Cleaning up messages...", original_user)
                await asyncio.sleep(5)
                await message.delete()
                await asyncio.sleep(5)
                await delete_message.delete()
                return

            await message.remove_reaction(reaction.emoji, user)
            role_to_be_assigned = discord.utils.get(ctx.message.guild.roles, name=emoji_role_dict.get(self.demojify(ctx.guild,str(reaction.emoji))))
            await original_user.add_roles(role_to_be_assigned)

            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{original_user.display_name}**, you joined **{role_to_be_assigned.name}** {reaction}!")
            await asyncio.sleep(3)
            await message.delete()
            return

        except asyncio.TimeoutError:
            nochange_timeout_message = await self.utilities._send_error_message(ctx.channel, f", No changes were made!", original_user)
            timeout_message = await self.utilities._send_error_message(ctx.channel, f", the request has timed out.", original_user)
            await asyncio.sleep(3)
            await message.delete()
            await asyncio.sleep(5)
            await timeout_message.delete()

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")
        return






    async def _assign_role_via_reaction(self, ctx, message, original_user, emoji_role_dict = None, exclusive=False):
        is_role_changed = False
        timeout_duration = 20

        if not message:
            message_text = ""
            for emoji, role in emoji_role_dict.items():
                message_text += f"\n{self.printable(ctx.guild, emoji)} - **{role}**"

            message = await self.utilities._send_embed(ctx.channel, description=f"**{original_user.display_name}** React to this message to make your selection(s). \n{message_text}", footer=f"Click \u23f9 to stop. This message will be auto deleted after {timeout_duration} second of inactivity.")

        for emoji in emoji_role_dict.keys():
            try:
                await message.add_reaction(emojify(self.numbers_text, self.one_to_ten, ctx.guild, emoji))
            except Exception as error:
                Logger.error(f"{traceback.format_exc()}")


        await message.add_reaction('\u23f9')

        try:
            is_timed_out = False
            while True:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout_duration, check=lambda r, u: u.id == original_user.id and r.message.id == message.id)

                if reaction.emoji == '\u23f9':
                    await message.remove_reaction(reaction.emoji, user)
                    if not is_role_changed:
                        timeout_message = await self.utilities._send_error_message(ctx.channel,f", No changes were made!",original_user)
                    else:
                        delete_message = await self.utilities._send_error_message(ctx.channel, "Cleaning up messages...", original_user)
                        await asyncio.sleep(5)
                        return await delete_message.delete()
                    await asyncio.sleep(5)
                    await message.delete()


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
                timeout_message = await self.utilities._send_error_message(ctx.channel, f", No changes were made!", original_user)

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

        await asyncio.sleep(3)
        await message.delete()

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


