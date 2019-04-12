from context import Context
from discord.ext import commands
from cogs.dbi import DatabaseInterface
import logging

class Bot(commands.AutoShardedBot):
    """Custom Discord Bot class for Clembot"""

    # config_details = {
    #     "password": 'clembot',
    #     "hostname": '35.196.51.15',
    #     "username": 'postgres',
    #     "database": "bronzor-live"
    # }

    def __init__(self, **kwargs):
        print("init()")
        super().__init__(**kwargs)
        # self.dbi = DatabaseInterface(self.config_details)
        # self.loop.run_until_complete(self._db_connect())
        self.logger = logging.getLogger('clembot.Bot')

    # async def _db_connect(self):
    #     try:
    #         await self.dbi.start(loop=self.loop)
    #     except asyncpg.InvalidPasswordError:
    #         print(
    #             'The database login is incorrect. '
    #             'Please fix the config file and try again.')
    #         sys.exit(0)
    #     except asyncpg.InvalidCatalogNameError:
    #         db_name = self.config.db_details.get('database', 'meowth')
    #         print(
    #             f"The database '{db_name}' was not found. "
    #             "Please fix the config file and try again.")
    #         sys.exit(0)




    async def process_commands(self, message):
        """Processes commands that are registed with the bot and it's groups.

        Without this being run in the main `on_message` event, commands will
        not be processed.
        """
        if message.author.bot:
            return
        ctx = await self.get_context(message, cls=Context)
        if not ctx.command:
            return
        await self.invoke(ctx)
