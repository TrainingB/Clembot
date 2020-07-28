import json

import discord
import pytz
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config.constants import Icons, MyEmojis, GUILD_METADATA_KEY, GUILD_CONFIG_KEY, GLOBAL_CONFIG_KEY, \
    CHANNEL_METADATA_KEY
from clembot.core import checks
from clembot.core.bot import group
from clembot.core.checks import is_guild_admin, is_guild_mod
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.exts.config.globalconfigmanager import GlobalConfigCache
from clembot.exts.pkmn.spelling import SpellHelper
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class ConfigCog(commands.Cog):

    _cache = dict()
    by_guild = dict()


    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        TimezoneSpellHelper.set_dictionary(list(pytz.all_timezones))
        self.global_config_cache = GlobalConfigCache(dbi=self.dbi, bot=bot)



    @group(pass_context=True, aliases=["configure"])
    @is_guild_admin()
    async def cmd_configure(self, ctx):

        not_emoji = ":white_large_square:"
        is_emoji = ":white_check_mark:"
        guild_config = await ctx.guild_profile()


        guild_config_complete = False
        prefix = guild_config.get('prefix', None)
        city = guild_config.get('city', None)
        timezone = guild_config.get('timezone', None)

        if prefix and city and timezone:
            guild_config_complete = True

        if city:
            city_label = f'{is_emoji} City'
        else:
            city_label = f'{not_emoji} City'
            city =f'Set city using `!config city city_state`.\n||Ex: `!config city BURBANKCA`||'


        if timezone:
            timezone_label = f'{is_emoji} Timezone'
        else:
            timezone_label = f'{not_emoji} Timezone'
            timezone =f'Set timezone using `!config timezone`. \nList of timezone is available `!timezone country_code`\n||Ex: `!config timezone America/Los_Angeles`||'

        response_config = {
            f'{is_emoji} Prefix' : [False, prefix],
            f'{city_label}' : [False, city],
            f'{timezone_label}' : [False, timezone]
        }

        if guild_config_complete:
            response_config.update({f'{is_emoji} Guild configuration' : 'For enabling features in channels, use `!feature` in respective channels.'})

        await ConfigCog.send_guild_config_embed(ctx, response_config)






    @group(pass_context=True, aliases=["timezone"])
    async def cmd_timezone(self, ctx, country_code):

        # timezone = '\n'.join([tz for tz in list(pytz.all_timezones)])
        try:
            timezone_list = pytz.country_timezones(country_code)
            country_name = f" ({pytz.country_names[country_code]})"
            timezones = '\n'.join([tz for tz in timezone_list if tz in pytz.common_timezones])
        except KeyError:
            timezone_list = []
            country_name = ""
            timezones = 'No timezone found. Are you sure you provided a valid ISO 3166 country code?'

        response_message = await ctx.send(embed=Embeds.make_embed(header=f"Available Timezones for {country_code}{country_name}",
                                               header_icon=Icons.TIMEZONE,
                                               msg_color=discord.Color.blue(),
                                               content=f"{timezones} \n\n ||You can tap 🗑️ to delete this message.||",
                                                footer="Timezone info from Olson database"))

        await response_message.add_reaction(MyEmojis.TRASH)


    @group(pass_context=True, hidden=True, aliases=["config"])
    @is_guild_admin()
    async def cmd_config(self, ctx):

        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                return await self.cmd_config_guild(ctx)

            raise BadArgument("`!config` can be used with `guild, timezone, city`")


    @cmd_config.command(pass_context=True, hidden=True, aliases=["timezone"])
    @wrap_error
    @is_guild_admin()
    async def cmd_config_timezone(self, ctx, timezone):

        if timezone in pytz.all_timezones:
            await ctx.guild_profile(key='timezone', value=timezone)
            config = await ctx.guild_profile(key='timezone')
            return await Embeds.message(ctx.message.channel, f"**timezone** is set to **{config}**")

        raise BadArgument(f"**{timezone}** didn't resolve to a valid timezone. \nYou can see a list for a valid timezone for a country ISO 3166 country code using `!timezone country_code`")


    @cmd_config.command(pass_context=True, hidden=True, aliases=["city"])
    @wrap_error
    @is_guild_admin()
    async def cmd_config_city(self, ctx, *city):
        if city:
            city_state = ''.join(city).upper()
            await ctx.guild_profile(key='city', value=city_state)
            config = await ctx.guild_profile(key='city')
            return await Embeds.message(ctx.message.channel, f"**city** is set to **{config}**")
        else:
            raise BadArgument("Please specify city and state, in all caps, without spaces.")


    @cmd_config.command(pass_context=True, hidden=True, aliases=["guild"])
    @wrap_error
    @is_guild_admin()
    async def cmd_config_guild(self, ctx, config_name=None, config_value=None):

        if config_name and config_name not in GUILD_CONFIG_KEY and config_name not in GUILD_METADATA_KEY:
            return await Embeds.error(ctx.message.channel, "No such configuration exists.")

        config = await ctx.guild_profile(key=config_name, value=config_value)
        if config_name:
            if config_value:
                config = await ctx.guild_profile(key=config_name)
            else:
                config = await ctx.guild_profile(key=config_name, delete=True)
            await Embeds.message(ctx.message.channel, f"**{config_name}** is set to **{config}**")
        else:
            await ConfigCog.send_guild_config_embed(ctx, config)


    @cmd_config.command(pass_context=True, hidden=True, aliases=["channel"])
    @wrap_error
    @is_guild_mod()
    async def cmd_config_channel(self, ctx, config_name=None, config_value=None):

        if config_name and config_name not in CHANNEL_METADATA_KEY:
            return await Embeds.error(ctx.message.channel, "No such configuration exists.")

        config = await ctx.channel_profile(channel_id=ctx.message.channel.id, key=config_name, value=config_value)
        if config_name:
            if config_value:
                config = await ctx.channel_profile(channel_id=ctx.message.channel.id, key=config_name)
            else:
                config = await ctx.channel_profile(channel_id=ctx.message.channel.id, key=config_name, delete=True)

        await Embeds.message(ctx.message.channel, f"**{config_name}** is set to **{config}**")



    @staticmethod
    async def send_guild_config_embed(ctx, config):

        embed = Embeds.make_embed(header="Guild Configuration",
                        fields=config, msg_color=discord.Color.blue(),
                        inline=True)

        return await ctx.send(embed=embed)

    @staticmethod
    async def send_global_config_embed(ctx, config):

        embed = Embeds.make_embed(header="Clembot Global Configuration",
                        fields={k[0]:k[1] for k in config.items() if k[0] in GLOBAL_CONFIG_KEY and k[1] is not None or ''},
                        msg_color=discord.Color.blue(),
                        inline=True)

        return await ctx.send(embed=embed)



    @cmd_config.command(pass_context=True, hidden=True, aliases=["global"])
    @wrap_error
    @checks.is_bot_owner()
    async def cmd_config_global(self, ctx, config_name=None, config_value=None):
        await self.global_config_cache.load_config()
        if config_name and config_name not in GLOBAL_CONFIG_KEY:
            return await Embeds.error(ctx.message.channel, "No such configuration exists.")

        if config_value:
            await self.global_config_cache.save_clembot_config(config_name, config_value)

        if config_name:
            if config_value:
                config = await self.global_config_cache.get_clembot_config(config_name)
            await Embeds.message(ctx.message.channel, f"**{config_name}** is set to **{config}**")
        else:
            config = self.global_config_cache.get_all_config()
            await ConfigCog.send_global_config_embed(ctx, config)



    async def get_guild_config(self, guild_id, config_name, reload=False):

        if reload or not self._cache:
            await self.load_config()

        if config_name:
            if config_name == 'global':
                if config_name in self._cache.setdefault(guild_id, {}).keys():
                    global_config_value = self._cache.get(guild_id).get(config_name, None)
                    return json.loads(global_config_value)
            else:
                if config_name in self._cache.setdefault(guild_id, {}).keys():
                    config_value = self._cache.get(guild_id).get(config_name)
                    return config_value
        else:
            return self._cache.get(guild_id)


        return None


    async def load_config(self):

        Logger.info(f'load_config()')

        cache = {}
        try:
            config_tbl = self.dbi.table('guild_config')
            query = config_tbl.query().select()

            config_records = await query.get()

            for cr in config_records:
                if cr['config_name'] == 'global':
                    cache.setdefault(cr['guild_id'], {})[cr['config_name']] = cr['config_value']
                else:
                    cache.setdefault(cr['guild_id'], {})[cr['config_name']] = cr['config_value']

            self._cache.clear()
            self._cache.update(cache)
        except Exception as error:
            Logger.error(error)
        return None

    async def save_guild_config(self, guild_id, config_name, config_value):
        try:
            print(f"save_guild_config ({guild_id}, {config_name} = {config_value} )")

            guild_config_record = {
                "guild_id" : guild_id,
                "config_name": config_name,
                "config_value": config_value
            }
            table = self.dbi.table('guild_config')

            existing_config_record = await table.query().select().where(guild_id=guild_id, config_name=config_name).get_first()

            if existing_config_record:

                if config_name == 'global':
                    existing_dict = json.loads(existing_config_record['config_value'])
                    config_dict = json.loads(config_value)
                    existing_dict.update(config_dict)
                    update_query = table.update(config_value=json.dumps(existing_dict)).where(guild_id=guild_id, config_name=config_name )
                else:
                    update_query = table.update(config_value=config_value).where(guild_id=guild_id, config_name=config_name)

                await update_query.commit()
            else:
                insert_query = table.insert(**guild_config_record)
                await insert_query.commit()

            await self.load_config()
        except Exception as error:

            Logger.error(error)


class TimezoneSpellHelper(SpellHelper):

    pass