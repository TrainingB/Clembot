import sys, os
import platform
import asyncpg
import pkg_resources
from enum import Enum
import discord
from discord.ext import commands
from discord.utils import cached_property

from dateutil.relativedelta import relativedelta


from clembot.config import config_template
from clembot.core.context import Context
from clembot.core.data_manager import DatabaseInterface, DataManager
from clembot.core.logs import Logger
import datetime

from clembot.exts.config.guild_metadata import GuildMetadata


class ExitCodes(Enum):
    SHUTDOWN = 0
    CRITICAL = 1
    RESTART = 26

class Bot(commands.AutoShardedBot):
    """Custom Discord Bot class for Clembot"""

    def __init__(self, **kwargs):
        Logger.info("bot initialized.")
        self.default_prefix = config_template.default_prefix
        self.owner = config_template.bot_users['owner']
        self.dbi = DatabaseInterface.get_instance() # DatabaseInterface(**config_template.db_config_details)
        self.data_manager = DataManager(self.dbi)

        self.debug = kwargs.pop('debug')
        self.launch_time = None
        self.shutdown_mode = ExitCodes.CRITICAL
        self.core_dir = os.path.dirname(os.path.realpath(__file__))
        self.bot_dir = os.path.dirname(self.core_dir)
        self.ext_dir = os.path.join(self.bot_dir, "exts")
        self.preload_extensions = config_template.preload_extensions
        self.req_perms = discord.Permissions(config_template.bot_permissions)
        kwargs = dict(owner_id=self.owner,
                      command_prefix=self.dbi.prefix_manager,
                      status=discord.Status.dnd, **kwargs)
        super().__init__(**kwargs)
        self.loop.run_until_complete(self._db_connect())

    async def _db_connect(self):
        Logger.info("_db_connect()")

        try:
            await self.dbi.start(loop=self.loop)
        except asyncpg.InvalidPasswordError:
            Logger.info('The database login is incorrect. Please fix the config file.')
            sys.exit(0)

        except asyncpg.InvalidCatalogNameError:
            db_name = config_template.db_details.get('database', 'clembot')
            Logger.info(f'The database {db_name} not found. Please fix the config file.')
            sys.exit(0)

        prefix_table = self.dbi.table('guild_prefix')
        results = await prefix_table.query.get()
        self.prefixes = dict(results)
        return True

    @property
    def uptime(self):
        return relativedelta(datetime.datetime.utcnow(), self.launch_time)


    @property
    def uptime_str(self):
        """Shows info about Clembot"""
        ut = self.uptime
        ut.years, ut.months, ut.days, ut.hours, ut.minutes
        if ut.years >= 1:
            uptime = "{yr}y {mth}m {day}d {hr}:{min}".format(yr=ut.years, mth=ut.months, day=ut.days, hr=ut.hours,
                                                             min=ut.minutes)
        elif ut.months >= 1:
            uptime = "{mth}m {day}d {hr}:{min}".format(mth=ut.months, day=ut.days, hr=ut.hours, min=ut.minutes)
        elif ut.days >= 1:
            uptime = "{day} days {hr} hrs {min} mins".format(day=ut.days, hr=ut.hours, min=ut.minutes)
        elif ut.hours >= 1:
            uptime = "{hr} hrs {min} mins {sec} secs".format(hr=ut.hours, min=ut.minutes, sec=ut.seconds)
        else:
            uptime = "{min} mins {sec} secs".format(min=ut.minutes, sec=ut.seconds)

        return uptime


    @cached_property
    def invite_url(self):
        invite_url = discord.utils.oauth_url(self.user.id,
                                             permissions=self.req_perms)
        return invite_url


    async def shutdown(self, *, restart=False):
        """Shutdown the bot"""
        if not restart:
            self.shutdown_mode = ExitCodes.SHUTDOWN
        else:
            self.shutdown_mode = ExitCodes.RESTART

        await self.logout()
        await self.dbi.stop()


    async def process_commands(self, message):
        """Processes commands that are registered with the bot and it's groups.

        Without this being run in the main `on_message` event, commands will
        not be processed.
        """
        if message.author.bot:
            return
        ctx = await self.get_context(message, cls=Context)
        if not ctx.command:
            return
        try:
            await self.invoke(ctx)
        except Exception as error:
            print(error)


    @cached_property
    def version(self):
        return pkg_resources.get_distribution("meowth").version

    @cached_property
    def py_version(self):
        return platform.python_version()

    @cached_property
    def dpy_version(self):
        return pkg_resources.get_distribution("discord.py").version

    @cached_property
    def platform(self):
        return platform.platform()


    async def on_guild_join(self, guild):
        d = {
            'guild_id': guild.id,
            'prefix': '!'
        }
        await GuildMetadata.insert(self, d)

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_ready(self):
        Logger.info("on_ready()")
        if not self.launch_time:
            self.launch_time = datetime.datetime.utcnow()

        # load extensions marked for preload in config
        for ext in self.preload_extensions:
            self.load_extension(ext)

        print("Clembot is back on!")

    async def on_shard_ready(self, shard_id):
        await self.change_presence(status=discord.Status.online, shard_id=shard_id, activity=discord.Game(name="Pokemon Go"))
        print(f'Shard {shard_id} is ready.')

    def get(self, iterable, **attrs):
        """A helper that returns the first element in an iterable that meets
        all the attributes passed in `attrs`.
        """
        return discord.utils.get(iterable, **attrs)

# def command(*args, **kwargs):
#     def decorator(func):
#         category = kwargs.get("category")
#         func.command_category = category
#         result = commands.command(*args, **kwargs)(func)
#         return result
#     return decorator
#
# def group(*args, **kwargs):
#     def decorator(func):
#         category = kwargs.get("category")
#         func.command_category = category
#         result = commands.group(*args, **kwargs)(func)
#         return result
#     return decorator