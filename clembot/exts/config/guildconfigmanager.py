import json
from discord.ext import commands

from clembot.core.logs import init_loggers
from clembot.exts.utils.utilities import Utilities


class GuildConfigCache(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()
        self._cache = {}

    def cache(self, guild_id):
        return self._cache.get(guild_id, {})

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

        self.logger.info(f'load_config()')

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
            self.logger.error(error)
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

            print(error)

def setup(bot):
    bot.add_cog(GuildConfigCache(bot))


