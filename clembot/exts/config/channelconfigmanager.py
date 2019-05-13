from discord.ext import commands

from clembot.core.logs import init_loggers
from clembot.exts.config.configmanager import ConfigManager
from clembot.exts.utils.utilities import Utilities


class ChannelConfigCache(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()
        self.ConfigManager = ConfigManager(bot)
        self.MyGuildConfigCache = bot.MyGuildConfigCache
        self._cache = {}

    async def load_channel_config(self):

        try:
            self.logger.info(f'load_channel_config()')
            guild_channel_config_tbl = self.dbi.table('guild_channel_config')
            guild_channel_query = guild_channel_config_tbl.query().select()

            channel_config_record = await guild_channel_query.get()
            cache = {}

            for ccr in channel_config_record:
                cache.setdefault(ccr['guild_id'], {}).setdefault(ccr['channel_id'], {})[ccr['config_name']] = ccr['config_value']

            self._cache.clear()
            self._cache.update(cache)

        except Exception as error:
            self.logger.error(error)

        return None

    async def get_channel_config(self, guild_id, channel_id, config_name, reload=False):

        if reload or not self._cache:
            await self.load_channel_config()

        if config_name in self._cache.setdefault(guild_id, {}).setdefault(channel_id, {}).keys():
            config_value = self._cache.get(guild_id).get(channel_id).get(config_name)
            return config_value

        return None


    async def save_channel_config(self, guild_id, channel_id, config_name, config_value):
        try:
            print(f"save_channel_config ({guild_id}, {channel_id}, {config_name} = {config_value} )")

            channel_config_record = {
                "guild_id" : guild_id,
                "channel_id" : channel_id,
                "config_name": config_name,
                "config_value": config_value
            }
            table = self.dbi.table('guild_channel_config')

            existing_config_record = await table.query().select().where(guild_id=guild_id, channel_id=channel_id, config_name=config_name).get_first()

            if existing_config_record:
                update_query = table.update(config_value=config_value).where(guild_id=guild_id, channel_id=channel_id, config_name=config_name)
                await update_query.commit()
            else:
                insert_query = table.insert(**channel_config_record)
                await insert_query.commit()

            await self.load_channel_config()
        except Exception as error:

            print(error)

    async def _get_config_by(self, config_name, **kwargs):
        self.logger.info(f'get_config_by( {config_name}, {kwargs})')
        try:

            guild_channel_config_tbl = self.dbi.table('guild_channel_config')
            kwargs.update(config_name=config_name)

            guild_channel_query = guild_channel_config_tbl.query().select().where(**kwargs)

            config_record = await guild_channel_query.get_first()
            if config_record:
                config_value = dict(config_record)['config_value']
                if config_value:
                    return config_value
        except Exception as error:
            self.logger.error(error)
        return None

    async def get_city_for_channel(self, guild_id, channel_id=None, parent_channel_id=None) -> str :
        try:
            print(f"get_city_for_channel({guild_id}, {channel_id}, {parent_channel_id})")
            city_for_channel = await self._get_config_by('city', guild_id=guild_id, channel_id=channel_id)

            if not city_for_channel:
                if parent_channel_id:
                    city_for_channel = await self._get_config_by('city', guild_id=guild_id, channel_id=parent_channel_id)

            if not city_for_channel:
                city_for_channel = await self.MyGuildConfigCache.get_guild_config(guild_id=guild_id, config_name='city')
            return city_for_channel

        except Exception as error:
            print(error)
            self.logger.info(error)
            return None

    async def get_city_for_channel_only(self, guild_id, channel_id=None, parent_channel_id=None) -> str :
        try:
            print(f"get_city_for_channel_only({guild_id}, {channel_id}, {parent_channel_id})")
            city_for_channel = await self.ConfigManager._get_config_by('city', guild_id=guild_id, channel_id=channel_id)

            if not city_for_channel:
                city_for_channel = await self.ConfigManager._get_config_by('city', guild_id=guild_id, parent_channel_id=parent_channel_id)
            return city_for_channel

        except Exception as error:
            print(error)
            self.logger.info(error)
            return None


    async def save_channel_city(self, guild_id, channel_id, city_state):
        print("save_channel_city()")
        try:
            await self.save_channel_config(guild_id, channel_id, 'city', city_state)
            new_channel_city =  await self.get_city_for_channel(guild_id=guild_id, channel_id=channel_id)
            return new_channel_city
        except Exception as error:
            print(error)
            return None


def setup(bot):
    bot.add_cog(ChannelConfigCache(bot))

