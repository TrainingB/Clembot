import re
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from clembot.core import checks
from clembot.core.bot import group
from clembot.core.logs import Logger
from clembot.exts.badges.badge import Badge
from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.exts.profile.user_profile import UserProfile
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class CustomException(Exception):
    pass


class BadgeCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()



    recent_badges = {
        1001 : {
            "id" : 1001,
            "name" : "Hawaiian Surfer",
            "description" : "Solo Alolan Raichu without using legendary or duplicate Pokemon.",
            "emoji" : "<:hawaiiansurfer:537414385912643584>",
            "emoji_id": 537414385912643584,
            "image_url" : "https://cdn.discordapp.com/attachments/537333409635368980/537408014165082117/AlolaRaichu.png",
            "guild_id": 393545294337277970,
            "trainers_earned" : 0,
            "last_awarded_on" : None,
            "active" : True

        },
        1002 : {
            "id": 1002,
            "name" : "Han Solo",
            "description" : "Solo any level 3 raid boss without using legendary or duplicate pokemon.",
            "emoji" : "<:hansolo:537753744235036672>",
            "emoji_id" : 537753744235036672,
            "image_url" : "https://cdn.discordapp.com/attachments/537333409635368980/537752060230107136/SoloRaid1.png",
            "guild_id" : 393545294337277970,
            "trainers_earned" : 0,
            "last_awarded_on" : None,
            "active" : True
        }
    }


    def _extract_info(self, emoji):

        EMOJI_REGEX = "^<a?:(\w+):(\d+)>$"
        m = re.search(EMOJI_REGEX, emoji)
        if m:
            return {"id" : int(m.group(2)), "name" : m.group(1) }

        EMOJI_HACK_REGEX = "^(\w+)-(\d+)"
        m = re.search(EMOJI_HACK_REGEX, emoji)
        if m:
            return {"id": int(m.group(2)), "name": m.group(1)}

        return None



    def _get_emoji(self, emoji):
        emoji_data = self._extract_info(emoji)
        print(emoji_data)
        if emoji_data:
            emoji = self.bot.get_emoji(emoji_data['id'])
        elif emoji.isdigit():
            emoji = self.bot.get_emoji(emoji)
        else:
            emoji = ":medal:"
        return emoji

    def _is_custom_emoji(self, emoji):
        if isinstance(emoji, discord.Emoji):
            return True

        elif isinstance(emoji, discord.PartialEmoji):
            return True

        elif isinstance(emoji, str):
            return False

        return False



    beep_badge = ("""
        `!badge info badge_id` - to get the badge information
        `!badge profile @user` - to list badges for a user
        
        """)


    @group(pass_context=True, hidden=True, aliases=["badge"])
    async def cmd_badge(self, ctx):
        try:
            if ctx.invoked_subcommand is None:
                footer = "Tip: < > denotes required and [ ] denotes optional arguments."
                await ctx.embed(title="Help - Badge Management",
                                description=self.beep_badge.format(member=ctx.message.author.display_name),
                                footer=footer)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["info"])
    async def cmd_badge_info(self, ctx, badge_id:int):
        await self._badge_info(ctx, badge_id)


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["grant"])
    @checks.is_guild_owner()
    async def cmd_badge_grant(self, ctx, badge_id:int, user_or_role):

        current_badge = await Badge.find_first(self.bot, badge_id)

        if current_badge:
            if current_badge.is_admin_only:
                if not checks.is_owner_check(ctx):
                    return await Embeds.error(ctx.channel, f"It seems like you don't have access to manage/grant/revoke Badge {current_badge['name']}.", ctx.author)
            elif not current_badge.is_allowed_for_guild(ctx.guild.id):
                return await Embeds.error(ctx.channel, f"This badge is not associated with this guild.", ctx.author)

            if ctx.message.role_mentions:
                role = ctx.message.role_mentions[0]
                await self._badge_grant_to_users(ctx, current_badge, role.members)
            elif ctx.message.mentions:
                await self._badge_grant_to_users(ctx, current_badge, ctx.message.mentions)
            else:
                await Embeds.error(ctx.channel, f"Usage: `!badge grant badge_id @user`", ctx.author)
        else:
            await Embeds.error(ctx.channel, f"no badge found with id #{badge_id}.", ctx.author)


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["revoke"])
    @checks.is_guild_owner()
    async def cmd_badge_revoke(self, ctx, badge_id:int, user_or_role):
        try:
            current_badge = await Badge.find_first(self.bot, badge_id)

            if current_badge:
                if current_badge.is_admin_only:
                    if not checks.is_owner_check(ctx):
                        return await Embeds.error(ctx.channel, f"It seems like you don't have access to manage/grant/revoke Badge {current_badge['name']}.", ctx.author)
                elif not current_badge.is_allowed_for_guild(ctx.guild.id):
                    return await Embeds.error(ctx.channel, f"This badge is not associated with this guild.", ctx.author)

                if ctx.message.role_mentions:
                    role = ctx.message.role_mentions[0]
                    await self._badge_revoke_from_users(ctx, current_badge, role.members)
                elif ctx.message.mentions:
                    await self._badge_revoke_from_users(ctx, current_badge, ctx.message.mentions)
                else:
                    await Embeds.error(ctx.channel, f"Usage: `!badge revoke badge_id @user`", ctx.author)
            else:
                await Embeds.error(ctx.channel, f"no badge found with id #{badge_id}.", ctx.author)

            return
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["profile"])
    async def cmd_badge_profile(self, ctx, user:discord.Member = None ):
        try:
            if not user:
                user = ctx.author
            badge_info = ""
            badges = await self._get_global_and_guild_badges(ctx.guild.id, user)

            global_badge = '\n'.join([f"{badge['emoji']} {badge['name']} *(#{badge['badge_id']})*" for badge in badges if badge.is_admin_only or badge.is_global])
            guild_badge = '\n'.join([f"{badge['emoji']} {badge['name']} *(#{badge['badge_id']})*" for badge in badges if not badge.is_admin_only and not badge.is_global])

            fields = {
                f"**Global Badges**": global_badge,
                f"**Guild Badges**": guild_badge
            }
            return await ctx.embed(title="Badge Profile", icon=user.avatar_url,
                               description=f"{user.display_name} has earned the following badges:\n{badge_info}",
                                   fields=fields)

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["help"])
    async def cmd_badge_help(self, ctx):
        try:
            footer = "Tip: < > denotes required and [ ] denotes optional arguments."
            await ctx.embed(title="Help - Badge Management", description=self.beep_badge.format(member=ctx.message.author.display_name), footer=footer)
        except Exception as error:
            print (error)


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["list"])
    async def cmd_badge_list(self, ctx, badge_type=None):
        try:
            badge_details = ""
            badge_fields = {}
            if badge_type is None:
                badges = await Badge.find_by(self.bot, guild_id=ctx.guild.id)
            else:
                badges = await Badge.find_by(self.bot, badge_type=badge_type)

            for badge in badges:
                badge_fields.update({f"{badge['emoji']} {badge['name']} *(#{badge['badge_id']})*": f"{badge['description']}"})

            await ctx.embed(title="Available Badges", description="The following badges are available from this community", fields=badge_fields)

        except Exception as error:
            print (error)


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["test"])
    @checks.is_guild_owner()
    async def cmd_badge_test(self, ctx, emoji):
        try:
            emoji = self._get_emoji(emoji)
            if not emoji or emoji == ':medal:':
                return await self.utilities._send_error_message(ctx.channel, f"only custom emojis owned by community can be used to create badges.", ctx.author)

            await ctx.embed(title="Emoji Found", description=f"Emoji is available for the bot: {emoji}")

        except Exception as error:
            await ctx.embed(title="Error Occurred",description=f"{error}")



    @cmd_badge.command(pass_context=True, hidden=True, aliases=["create"])
    @checks.is_guild_owner()
    async def cmd_badge_create(self, ctx, emoji, name, description=None, badge_type=None):

        try:
            emoji = self._get_emoji(emoji)
            if not emoji or emoji == ':medal:':
                return await Embeds.error(ctx.channel, f"only custom emojis owned by community can be used to create badges.", ctx.author)


            existing_badge = await Badge.find_first_by(self.bot, guild_id=ctx.guild.id, emoji_id=emoji.id, name=name)
            if existing_badge:
                await Embeds.error(ctx.channel, f"either the Emoji {emoji} or the Name **{name}** has been used for another badge.", user=ctx.message.author)
                return await self._badge_info(ctx, existing_badge['badge_id'])

            badge_dict = {"name": name, "description": description,
                          "guild_id" : ctx.guild.id if badge_type is None else None,
                             "emoji_id" : emoji.id, "emoji": f"<:{emoji.name}:{emoji.id}>", "image_url": emoji.url._url,
                             "trainers_earned": 0, "last_awarded_on": None, "active": True, "badge_type": badge_type
            }

            new_badge = Badge(self.bot, badge_dict)
            await new_badge.insert()

            new_badge = await Badge.find_first_by(self.bot, emoji_id=emoji.id)

            await ctx.embed(
                            title="Badge Created",
                            thumbnail=emoji.url,
                            icon=self.bot.user.avatar_url,
                            description=f"{new_badge['emoji']} {new_badge['name']} *(#{new_badge['badge_id']})* has been added successfully."
                            )

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["update"])
    @checks.is_guild_owner()
    async def cmd_badge_update(self, ctx, badge_id:int, emoji, name, description=None, badge_type=None):

        try:
            emoji = self._get_emoji(emoji)
            if not emoji or emoji == ':medal:':
                return await Embeds.error(ctx.channel, f"only custom emojis owned by community can be used to create badges.", ctx.author)

            existing_badge = await Badge.find_first_by(self.bot, emoji_id=emoji.id)
            if existing_badge:

                if existing_badge.is_admin_only:
                    if not checks.is_owner_check(ctx):
                        return await Embeds.error(ctx.channel, f"It seems like you don't have access to manage/grant/revoke Badge {existing_badge['name']}.", ctx.author)
                elif not existing_badge.is_allowed_for_guild(ctx.guild.id):
                    return await Embeds.error(ctx.channel, f"Only global badges or local guild badges are assignable.", ctx.author)

                if not existing_badge['badge_id'] == badge_id:
                    return await Embeds.error(ctx.channel, f"either the Emoji {emoji} or the Name **{name}** has been used for another badge.", ctx.author)

            badge_dict = {"name": name, "description": description, "emoji_id": emoji.id,
                          "emoji": f"<:{emoji.name}:{emoji.id}>", "image_url": emoji.url._url,
                          "badge_type": badge_type
                          }
            existing_badge.update_dict(badge_dict)
            await existing_badge.update()

            await ctx.embed(
                            title="Badge Updated",
                            thumbnail=emoji.url,
                            icon=self.bot.user.avatar_url,
                            description=f"{existing_badge['emoji']} {existing_badge['name']} *(#{existing_badge['badge_id']})* has been updated successfully."
                            )

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @cmd_badge.command(pass_context=True, hidden=True, aliases=["delete"])
    @checks.is_guild_owner()
    async def cmd_badge_delete(self, ctx, badge_id:int ):

        try:
            existing_badge = await Badge.find_first_by(self.bot, badge_id=badge_id)
            if existing_badge:


                await self._remove_badge_id_from_all_user_profiles(badge_id)
                # await existing_badge.delete()

                emoji = self._get_emoji(existing_badge['emoji'])
                await ctx.embed(
                    title="Badge Removed",
                    thumbnail=emoji.url,
                    icon=self.bot.user.avatar_url,
                    description=f"{existing_badge['emoji']} {existing_badge['name']} *({existing_badge['badge_id']})* has been removed successfully."
                )

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    async def _badge_info(self, ctx, badge_id):
        try:
            current_badge = await Badge.find_first(self.bot, badge_id=badge_id)
            if current_badge:
                return await ctx.send(embed=current_badge.embed(ctx))
            else:
                return await Embeds.error(ctx.channel, f"no badge found with id {badge_id}.", user=ctx.author)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    async def _remove_badge_id_from_all_user_profiles(self, badge_id):

        table_names = ['user_profile', 'user_guild_profile']

        for table_name in table_names:
            query = f"update {table_name} set badge_id = (SELECT array_agg(single_badge_id) FROM unnest({table_name}.badge_id) AS single_badge_id WHERE $1 != single_badge_id ) where $2 = any(badge_id);"
            query_args = [badge_id, badge_id]
            await self.bot.dbi.execute_query(query, *query_args)


    async def _get_global_and_guild_badges(self, guild_id, user):

        user_profile = await UserProfile.find(self.bot, user.id)

        global_badges = user_profile['badge_id'] or []

        user_guild_profile = await UserGuildProfile.find(self.bot, user.id, guild_id)

        guild_badges = user_guild_profile['badge_id'] or []

        table = self.bot.dbi.table(Badge.TABLE_NAME)
        query = table.query().select().where(table['badge_id'].in_(global_badges + guild_badges))
        auto_response_list = await query.getjson()

        badges = [Badge(self.bot, rcrd) for rcrd in auto_response_list]

        return badges




    def _fetch_current_date(self):

        current_date = datetime.today()

        return current_date


    async def _badge_grant_to_users(self, ctx, badge: Badge, list_of_users):
        for user in list_of_users:
            try:
                emoji = self._get_emoji(badge['emoji'])
                existing_badges = await self._get_global_and_guild_badges(ctx.guild.id, user)
                if badge['badge_id'] in existing_badges:
                    await ctx.embed(
                        title="Badge Grant Failed",
                        thumbnail=emoji.url,
                        icon=self.bot.user.avatar_url,
                        colour=discord.Color.red(),
                        description=f"**{user.display_name}** already has the badge **{badge['emoji']} {badge['name']}**."
                    )
                    continue
                await self._add_badge_to_trainer_profile(user, badge, ctx.guild.id)
                current_date = self._fetch_current_date()
                badge['trainers_earned'] = badge['trainers_earned'] + 1
                badge['last_awarded_on'] = current_date
                await badge.update()

                await ctx.embed(
                    title="Badge Granted",
                    thumbnail=emoji.url,
                    icon=self.bot.user.avatar_url,
                    description=f"**{user.display_name}** has been granted **{badge['emoji']} {badge['name']}**."
                )

            except Exception as error:
                Logger.error(f"{traceback.format_exc()}")


    async def _add_badge_to_trainer_profile(self, user:discord.Member, badge: Badge, guild_id=None):

        guild_badge = badge['guild_id'] is not None

        if guild_badge:
            user_guild_profile = await UserGuildProfile.find(self.bot, user.id, guild_id)
            user_guild_profile['badge_id'] = badge.badge_id
            await user_guild_profile.update()
        else:
            user_profile = await UserProfile.find(self.bot, user.id)
            user_profile['badge_id'] = badge.badge_id
            await user_profile.update()


    async def _badge_revoke_from_users(self, ctx, badge: Badge, list_of_users):
        for user in list_of_users:
            try:

                emoji = self._get_emoji(badge['emoji'])
                existing_badges = await self._get_global_and_guild_badges(ctx.guild.id, user)
                if badge['badge_id'] not in existing_badges:
                    await ctx.embed(
                        title="Badge Revoke Failed",
                        thumbnail=emoji.url,
                        icon=self.bot.user.avatar_url,
                        colour=discord.Color.red(),
                        description=f"**{user.display_name}** doesn't have **{badge['emoji']} {badge['name']}**."
                    )
                    continue

                await self._remove_badge_from_trainer_profile(user, badge['badge_id'], ctx.guild.id)
                current_date = self._fetch_current_date()
                badge['trainers_earned'] = badge['trainers_earned'] - 1
                badge['last_awarded_on'] = current_date
                await badge.update()

                return await ctx.embed(
                    title="Badge Revoked",
                    thumbnail=emoji.url,
                    icon=self.bot.user.avatar_url,
                    description=f"**{badge['emoji']} {badge['name']}** has been revoked from **{user.display_name}**."
                )

            except Exception as error:
                Logger.error(f"{traceback.format_exc()}")


    async def _remove_badge_from_trainer_profile(self, user: discord.Member, badge_to_remove: Badge, guild_id=None):

        guild_badge = badge_to_remove['guild_id'] is not None

        if guild_badge:
            user_guild_profile = await UserGuildProfile.find(self.bot, user.id, guild_id)
            badge_list = user_guild_profile['badge_id']
            badge_list = [badge_id for badge_id in badge_list if badge_id != badge_to_remove.badge_id]
            user_guild_profile['badge_id'] = None
            user_guild_profile['badge_id'] = badge_list
            await user_guild_profile.update()
        else:
            user_profile = await UserProfile.find(self.bot, user.id)
            badge_list = user_profile['badge_id']
            badge_list = [badge_id for badge_id in badge_list if badge_id != badge_to_remove.badge_id]
            user_profile['badge_id'] = None
            user_profile['badge_id'] = badge_list
            await user_profile.update()
