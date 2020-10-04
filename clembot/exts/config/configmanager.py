import json
import re

import discord
from discord.ext import commands

from clembot.core.logs import init_loggers
from clembot.exts.utils.utilities import Utilities


class ConfigManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()

    # async def _get_config_by(self, config_name, **kwargs):
    #     self.logger.info(f'get_config_by( {config_name}, {kwargs})')
    #     try:
    #         guild_channel_config_tbl = self.dbi.table('guild_channel_config')
    #         kwargs.update(config_name=config_name)
    #
    #         guild_channel_query = guild_channel_config_tbl.query().select().where(**kwargs)
    #
    #         config_record = await guild_channel_query.get_first()
    #         if config_record:
    #             config_value = dict(config_record)['config_value']
    #             if config_value:
    #                 return config_value
    #     except Exception as error:
    #         self.logger.error(error)
    #     return None
    #
    # async def _save_config(self, config_name, config_value, guild_id, channel_id):
    #
    #     guild_channel_config_record = {
    #         "guild_id": guild_id,
    #         "config_name": config_name,
    #         "config_value": config_value
    #     }
    #
    #     if channel_id:
    #         guild_channel_config_record.update(channel_id=channel_id)
    #
    #     table = self.dbi.table('guild_channel_config')
    #
    #
    #     existing_config_record = await self._get_config_by(config_name, guild_id=guild_id, channel_id=channel_id)
    #
    #     if existing_config_record:
    #         update_query = table.update(config_value=config_value).where(channel_id=channel_id, guild_id=guild_id, config_name='city')
    #         await update_query.commit()
    #     else:
    #         insert_query = table.insert(**guild_channel_config_record)
    #         await insert_query.commit()
    #
    #     return None
    #
    # async def read_channel_configuration(self, guild_id, channel_id) -> {}:
    #
    #     try:
    #         result = await self._get_config_by('global', guild_id=guild_id, channel_id=channel_id)
    #
    #         if result:
    #             configuration = json.loads(result)
    #             return configuration
    #
    #     except Exception as error:
    #         print(error)
    #
    #     return None
    #
    # async def save_channel_configuration(self, guild_id, configuration, channel_id) -> {}:
    #
    #     try:
    #         print(f"save_guild_configuration({guild_id}, {channel_id}, {configuration})")
    #
    #         await self._save_config('global', json.dumps(configuration), guild_id=guild_id, channel_id=channel_id)
    #         return configuration
    #
    #     except Exception as error:
    #         print(error)
    #
    #     return None

    async def find_bingo_card(self, guild_id, user_id, event):

        try:
            print(f"find_bingo_card({guild_id}, {user_id}, {event})")

            guild_user_event_bingo_card_table = self.dbi.table('guild_user_event_bingo_card')

            bingo_card_query = guild_user_event_bingo_card_table.query().select().where(guild_id=guild_id, user_id=user_id, event=event)

            bingo_record = await bingo_card_query.get_first()
            if bingo_record:
                return bingo_record
        except Exception as error:
            print(error)

        return None

    async def save_bingo_card(self, guild_id, user_id, event, bingo_card, bingo_card_url, generated_at):
        print("save_bingo_card ({0}, {1}, {2})".format(guild_id, user_id, event))
        try:

            guild_user_event_bingo_card_record = {
                "guild_id": guild_id,
                "user_id": user_id,
                "event":event,
                "bingo_card": json.dumps(bingo_card),
                "bingo_card_url": bingo_card_url,
                "generated_at": generated_at
            }

            table = self.dbi.table('guild_user_event_bingo_card')

            existing_bingo_card = await table.query().select().where(guild_id=guild_id, user_id=user_id, event=event).get_first()

            if existing_bingo_card:
                update_query = table.update(bingo_card=json.dumps(bingo_card), bingo_card_url=bingo_card_url, generated_at=generated_at).where(user_id=user_id, guild_id=guild_id, event=event)
                await update_query.commit()
            else:
                insert_query = table.insert(**guild_user_event_bingo_card_record)
                await insert_query.commit()

        except Exception as error:
            print(error)

        return

    @commands.command(pass_context=True, hidden=True, aliases=["list-servers"])
    async def _list_servers(self, ctx):
        recipient = {}
        recipient_text = ""

        for guild in ctx.bot.guilds:
            recipient[guild.name] = guild.owner.mention
            recipient_text += f"\n**{guild.name} [{len(guild.members)}]** - {guild.owner.name} {guild.owner.mention}"

        await self.utilities._send_message(ctx.channel, recipient_text)

    #
    # @commands.group(pass_context=True, hidden=True, aliases=["config"])
    # async def _config(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await self.utilities._send_message(ctx.channel,
    #                                            f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
    #
    # @_config.group(pass_context=True, hidden=True, aliases=["set"])
    # async def _config_set(self, ctx, key, value=None):
    #     if value:
    #         if key == 'timezone':
    #
    #             await self._save_config('timezone', value, ctx.guild.id)
    #
    #             new_timezone = await self._get_config_by('timezone', guild_id=ctx.guild.id)
    #
    #             # ctx.bot.guild_dict[ctx.guild.id]['offset'] = int(value)
    #             await self.utilities._send_message(ctx.channel, f"**Timezone** is set to **{new_timezone}**", user=ctx.author)
    #     else:
    #         await self.utilities._send_error_message(ctx.channel, f"no changes made!", user=ctx.author)
    #
    #
    # @_config.group(pass_context=True, hidden=True, aliases=["get"])
    # async def _config_get(self, ctx, key):
    #     if key == 'global':
    #
    #         configuration = await self.read_channel_configuration(ctx.guild.id, None)
    #
    #         await self.utilities._send_message(ctx.channel, f"**{configuration}**", user=ctx.author)
    #
    #
    #
    # @commands.command(pass_context=True, hidden=True, aliases=["list-servers"])
    # async def _list_servers(self, ctx):
    #     recipient = {}
    #     recipient_text = ""
    #
    #     for guild in ctx.bot.guilds:
    #         recipient[guild.name] = guild.owner.mention
    #         recipient_text += f"\n**{guild.name} [{len(guild.members)}]** - {guild.owner.name} {guild.owner.mention}"
    #
    #     await self.utilities._send_message(ctx.channel, recipient_text)
    #
    #
    # @commands.group(pass_context=True, hidden=True, aliases=["setx"])
    # async def _setx(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
    #
    #
    # @commands.group(pass_context=True, hidden=True, aliases=["set-config"])
    # async def _set_config(self, ctx):
    #     if ctx.invoked_subcommand is None:
    #         await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")
    #
    # @_setx.group(pass_context=True, hidden=True, aliases=["channel"])
    # async def _set_channel_config(self, ctx, * , key_and_json_text):
    #     try:
    #         await self.utilities._send_message(ctx.channel, key_and_json_text)
    #
    #         key, _, json_text = key_and_json_text.replace('\n', ' ').partition(' ')
    #
    #         if len(json_text) < 1:
    #             return await self.utilities._send_message(ctx.channel, f"No json provided!")
    #
    #         json_body = json.loads(json_text)
    #
    #         new_configuration = {}
    #         new_configuration[key] = json_body
    #
    #         configuration = await self.read_channel_configuration(ctx.message.guild.id, ctx.message.channel.id)
    #
    #         if configuration:
    #             configuration.update(new_configuration)
    #         else:
    #             configuration = new_configuration
    #
    #         configuration = gymsql.save_channel_configuration(guild_id=ctx.message.guild.id,
    #                                                           channel_id=ctx.message.channel.id, configuration=configuration)
    #
    #         if configuration:
    #             await self.utilities._send_message(ctx.channel, configuration)
    #         else:
    #             await self.utilities._send_error_message(ctx.channel, "Beep Beep! I couldn't set the configuration successfully.")
    #     except Exception as error:
    #         print(error)
    #
    # @_setx.group(pass_context=True, hidden=True, aliases=["guild"])
    # async def _set_guild_config(self, ctx, * , key_and_json_text):
    #     try:
    #         await self.utilities._send_message(ctx.channel, key_and_json_text)
    #
    #         key, _, json_text = key_and_json_text.replace('\n', ' ').partition(' ')
    #
    #         if len(json_text) < 1:
    #             return await self.utilities._send_message(ctx.channel, f"No json provided!")
    #
    #         new_configuration = {}
    #         configuration = await self.read_channel_configuration(ctx.message.guild.id, None)
    #
    #         if json_text == "remove":
    #             del configuration[key]
    #         else:
    #             json_body = json.loads(json_text)
    #             new_configuration[key] = json_body
    #
    #
    #             if configuration:
    #                 configuration.update(new_configuration)
    #             else:
    #                 configuration = new_configuration
    #
    #         configuration = gymsql.save_channel_configuration(guild_id=ctx.message.guild.id,
    #                                                           channel_id=None, configuration=configuration)
    #
    #         if configuration:
    #             await self.utilities._send_message(ctx.channel, configuration)
    #         else:
    #             await self.utilities._send_error_message(ctx.channel, "Beep Beep! I couldn't set the configuration successfully.")
    #     except Exception as error:
    #         print(error)
    #
    #
    #
    #
    #
    # @_setx.command(aliases=["regional"])
    # async def _setx_regional(self, ctx, raid_boss = None):
    #
    # # !import roster #channel
    #
    #     message = ctx.message
    #     if raid_boss:
    #         regional = re.sub("[\@]", "", raid_boss.lower())
    #         # regional = get_name(regional).lower() if regional.isdigit() else regional
    #
    #         if regional:
    #             if regional in ctx.bot.raidlist:
    #                 ctx.bot.guild_dict[message.channel.guild.id].setdefault("configuration", {}).setdefault("settings", {})["regional"] = regional
    #                 return await self.utilities._send_message(ctx.channel, f"{raid_boss} is set as a regional raid boss.", user=ctx.message.author)
    #             else:
    #                 return await self.utilities._send_error_message(ctx.channel, f" {regional} doesn't appear as a raid boss.", user=ctx.message.author)
    #     del ctx.bot.guild_dict[message.channel.guild.id].setdefault("configuration", {}).setdefault("settings", {})["regional"]
    #     return await self.utilities._send_error_message(ctx.channel, f"Regional raid boss has been cleared.", user=ctx.message.author)
    #



def setup(bot):
    bot.add_cog(ConfigManager(bot))


