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

class Badge:
    def __init__(self, emoji=None, name=None):
        self.emoji=None
        self.image_url=None
        self.id=None
        self.description=None
        self.name=None


class BadgeManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
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

        return None



    def _get_emoji(self, emoji):
        emoji_data = self._extract_info(emoji)
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



    beep_badge = ("""**{member}** here are the commands for badge management.

**!badge create emoji name description** - to create a badge from custom emoji

**!badge info badge_id** - to get the badge information
**!badge update badge_id emoji name description** - to update a badge details


""")



    def _save_badge(self, guild_id, badge_data):
        badge_id_to_look_for = badge_data['id']

        self.bot.guild_dict[guild_id].setdefault('badges', {})[badge_id_to_look_for] = badge_data
        return

    def _delete_badge(self, guild_id, badge_id):
        badge = self.bot.guild_dict[guild_id].setdefault('badges', {}).pop(badge_id)
        return badge


    def _get_badge(self, guild_id, badge_id):
        current_badge = self.bot.guild_dict[guild_id].setdefault('badges', {}).get(badge_id, self.recent_badges.get(badge_id, None))
        return current_badge

    def _find_badge(self, guild_id, emoji_id=None, name=None, badge_id=None):
        badges = self.bot.guild_dict[guild_id].setdefault('badges', {})
        if badges:
            for badge_key in badges.keys():
                badge = badges[badge_key]
                if emoji_id and badge['emoji_id']==emoji_id :
                    return badge
                if name and badge['name'] == name:
                    return badge
                if badge_id and badge['id'] == badge_id:
                    return badge
        return None


    @commands.group(pass_context=True, hidden=True, aliases=["badge"])
    async def _badge(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @_badge.command(pass_context=True, hidden=True, aliases=["help"])
    async def _badge_help(self, ctx):
        try:
            footer = "Tip: < > denotes required and [ ] denotes optional arguments."
            await ctx.embed(title="Help - Badge Management", description=self.beep_badge.format(member=ctx.message.author.display_name), footer=footer)
        except Exception as error:
            print (error)

    @_badge.command(pass_context=True, hidden=True, aliases=["list"])
    async def _badge_list(self, ctx):
        try:
            badge_details = ""
            badge_fields = {}

            badges = self.bot.guild_dict[ctx.guild.id].setdefault('badges', {})
            if badges:
                for badge_key in badges.keys():
                    badge = badges[badge_key]
                    badge_fields.update({f"{badge['emoji']} {badge['name']} (#{badge['id']})" : f"{badge['description']}"})

            await ctx.embed(title="Available Badges", description="The following badges are available from this community", fields=badge_fields)

        except Exception as error:
            print (error)



    @_badge.command(pass_context=True, hidden=True, aliases=["create"])
    async def _badge_create(self, ctx, emoji, name, description=None):

        try:
            emoji = self._get_emoji(emoji)
            if emoji == ':medal:':
                return await self.utilities._send_error_message(ctx.channel, f"only custom emojis owned by community can be used to create badges.", ctx.author)

            if self._find_badge(ctx.guild.id, emoji.id, name):
                return await self.utilities._send_error_message(ctx.channel, f"either the Emoji {emoji} or the Name **{name}** has been used for another badge.", ctx.author)

            new_badge_id = gymsql.find_clembot_config('next-badge-id')
            gymsql.save_clembot_config('next-badge-id', new_badge_id+1)

            current_badge = {"id": new_badge_id, "name": name, "description": description, "guild_id" : ctx.guild.id,
                             "emoji_id" : emoji.id, "emoji": f"<:{emoji.name}:{emoji.id}>", "image_url": emoji.url,
                             "trainers_earned": 0, "last_awarded_on": None, "active": True
                             }

            self._save_badge(ctx.guild.id, current_badge)

            await ctx.embed(
                            title="Badge Created",
                            thumbnail=emoji.url,
                            icon=self.bot.user.avatar_url,
                            description=f"{current_badge['emoji']} {current_badge['name']} ({current_badge['id']}) has been added successfully."
                            )

        except Exception as error:
            print(error)

    @_badge.command(pass_context=True, hidden=True, aliases=["update"])
    async def _badge_update(self, ctx, badge_id:int, emoji, name, description=None):

        try:
            emoji = self._get_emoji(emoji)
            if emoji == ':medal:':
                return await self.utilities._send_error_message(ctx.channel, f"only custom emojis owned by community can be used to create badges.", ctx.author)

            existing_badge = self._find_badge(ctx.guild.id, emoji.id, name)
            if existing_badge:
                if existing_badge['id'] != badge_id:
                    return await self.utilities._send_error_message(ctx.channel, f"either the Emoji {emoji} or the Name **{name}** has been used for another badge.", ctx.author)

            current_badge = {"id": badge_id, "name": name, "description": description, "guild_id" : ctx.guild.id,
                             "emoji_id" : emoji.id, "emoji": f"<:{emoji.name}:{emoji.id}>", "image_url": emoji.url,
                             "trainers_earned": 0, "last_awarded_on": None, "active": True
                             }

            self._save_badge(ctx.guild.id, current_badge)

            await ctx.embed(
                            title="Badge Updated",
                            thumbnail=emoji.url,
                            icon=self.bot.user.avatar_url,
                            description=f"{current_badge['emoji']} {current_badge['name']} ({current_badge['id']}) has been updated successfully."
                            )

        except Exception as error:
            print(error)


    @_badge.command(pass_context=True, hidden=True, aliases=["delete"])
    async def _badge_delete(self, ctx, badge_id:int ):

        try:
            existing_badge = self._find_badge(ctx.guild.id, badge_id=badge_id)
            if existing_badge:
                removed_badge = self._delete_badge(ctx.guild.id, badge_id)
                emoji = self._get_emoji(removed_badge['emoji'])
                await ctx.embed(
                    title="Badge Removed",
                    thumbnail=emoji.url,
                    icon=self.bot.user.avatar_url,
                    description=f"{removed_badge['emoji']} {removed_badge['name']} ({removed_badge['id']}) has been removed successfully."
                )

        except Exception as error:
            print(error)

    @_badge.command(pass_context=True, hidden=True, aliases=["info"])
    async def _badge_info(self, ctx, badge_id:int):

        try:
            current_badge = self._get_badge(ctx.guild.id, badge_id)

            if current_badge:

                badge_fields = { "Distributed By": self.bot.get_guild(current_badge['guild_id']).name, "Trainer(s) Earned":  f"{current_badge['trainers_earned']}"}

                footer = "Badge Status : Inactive"
                if current_badge['active']:
                    footer = "Badge Status : Active"

                if current_badge['last_awarded_on']:
                    footer = f"{footer} | Last awarded on: {current_badge['last_awarded_on']}"

                await ctx.embed(title=f"#{current_badge['id']} - {current_badge['name']}", description=f"*{current_badge['description']}*",
                                thumbnail=current_badge['image_url'], fields = badge_fields, footer=footer,
                                footer_icon=self.bot.get_guild(current_badge['guild_id']).icon_url, inline=True)
            else:
                return await self.utilities._send_error_message(ctx.channel, f"no badge found with id {badge_id}.", ctx.author)
        except Exception as error:
            print(error)


def setup(bot):
    bot.add_cog(BadgeManager(bot))





