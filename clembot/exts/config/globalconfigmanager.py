from discord.ext import commands

from clembot.core.logs import init_loggers
from clembot.exts.utils.utilities import Utilities


class GlobalConfigCache(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()
        self._cache = {}


    def get_all_config(self):
        return self._cache


    async def get_clembot_config(self, config_name, reload=False):

        if reload or not self._cache:
            await self.load_config()

        if config_name in self._cache.keys():
            config_value = self._cache.get(config_name, None)
            return config_value

        return None

    async def load_config(self):

        self.logger.info(f'load_config()')

        cache = {}
        try:
            clembot_config_tbl = self.dbi.table('clembot_config')
            clembot_query = clembot_config_tbl.query().select()

            config_records = await clembot_query.get()

            for cr in config_records:
                cache[cr['config_name']] = cr['config_value']

            self._cache.clear()
            self._cache.update(cache)
        except Exception as error:
            self.logger.error(error)
        return None

    async def save_clembot_config(self, config_name, config_value):
        print("save_clembot_config ({0}, {1})".format(config_name, config_value))

        clembot_config_record = {
            "config_name": config_name,
            "config_value": config_value
        }
        table = self.dbi.table('clembot_config')

        existing_config_record = await table.query().select().where(config_name=config_name).get_first()

        if existing_config_record:
            update_query = table.update(config_value=config_value).where(config_name=config_name)
            await update_query.commit()
        else:
            insert_query = table.insert(**clembot_config_record)
            await insert_query.commit()

        await self.load_config()

def setup(bot):
    bot.add_cog(GlobalConfigCache(bot))


