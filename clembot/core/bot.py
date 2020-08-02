import datetime
import os
import platform
import sys
import traceback
from enum import Enum

import asyncpg
import discord
import pkg_resources
from dateutil.relativedelta import relativedelta
from discord.ext import commands
from discord.utils import cached_property

from clembot.config import config_template
from clembot.core.context import Context
from clembot.core.data_manager import DatabaseInterface, DataManager
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.utilities.utils import pagination


class ExitCodes(Enum):
    SHUTDOWN = 0
    CRITICAL = 1
    RESTART = 26

class Bot(commands.AutoShardedBot):
    """Custom Discord Bot class for Clembot"""

    def __init__(self, **kwargs):
        Logger.info("bot initialized.")
        self.default_prefix = config_template.default_prefix
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
        kwargs = dict(owner_id=config_template.bot_users['owner'],
                      command_prefix=self.dbi.prefix_manager,
                      status=discord.Status.online, **kwargs)
        super().__init__(**kwargs)
        self.owner_id = config_template.bot_users['owner']
        self.owner = self.get_user(self.owner_id)
        self.trusted_users = config_template.bot_users['trusted_users']
        self.loop.run_until_complete(self._db_connect())
        self.auto_responses = {}

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

        prefix_table = self.dbi.table('guild_config')
        results = await prefix_table.query.select('guild_id', 'prefix').getjson()
        if results:
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

        # if not a valid command
        if not ctx.command:
            # Auto-Respond Code
            key = message_key(ctx, message)
            if key in ctx.bot.auto_responses:
                auto_response = ctx.bot.auto_responses.get(key)
                await ctx.send(auto_response)

        try:
            await self.invoke(ctx)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


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
        guild_metadata_table = self.dbi.table('guild_config')
        d = {
            'guild_id': guild.id,
            'prefix': '!'
        }
        guild_metadata_table_insert = guild_metadata_table.insert.row(**d)

        await guild_metadata_table_insert.commit()



    async def on_message(self, message):
        await self.process_commands(message)

    async def on_ready(self):
        Logger.info("on_ready()")
        if not self.launch_time:
            self.launch_time = datetime.datetime.utcnow()

        # load extensions marked for preload in config
        for ext in self.preload_extensions:
            try:
                self.load_extension(ext)
            except Exception as error:
                import traceback
                print(traceback.format_exc())

        print("Clembot is back on!")

    async def on_shard_ready(self, shard_id):
        await self.change_presence(status=discord.Status.online, shard_id=shard_id, activity=discord.Game(name="Pokemon Go"))
        print(f'Shard {shard_id} is ready.')

    def get(self, iterable, **attrs):
        """A helper that returns the first element in an iterable that meets
        all the attributes passed in `attrs`.
        """
        return discord.utils.get(iterable, **attrs)


    def get_cog_commands(self, cog_name):

        cog = self.get_cog(cog_name)

        return cog.get_commands()

    async def send_cmd_help(self, ctx, **kwargs):
        """Function to invoke help output for a command.

        Parameters
        -----------
        ctx: :class:`discord.ext.commands.Context`
            Context object from the originally invoked command.
        per_page: :class:`int`
            Number of entries in the help embed page. 12 is default.
        title: :class:`str`
            Title of the embed message.
        """
        try:
            if ctx.invoked_subcommand:
                kwargs['title'] = kwargs.get('title', 'Sub-Command Help')
                p = await pagination.Pagination.from_command(
                    ctx, ctx.invoked_subcommand, **kwargs)
            else:
                kwargs['title'] = kwargs.get('title', 'Command Help')
                p = await pagination.Pagination.from_command(
                    ctx, ctx.command, **kwargs)
            await p.paginate()
        except discord.DiscordException as exc:
            await ctx.send(exc)

def command(*args, **kwargs):
    def decorator(func):
        category = kwargs.get("category")
        examples = kwargs.get("examples")
        func.command_category = category
        func.examples = examples
        error_wrapped_func = wrap_error(func)
        result = commands.command(*args, **kwargs)(error_wrapped_func)
        return result
    return decorator

def group(*args, **kwargs):
    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        examples = kwargs.get("examples")
        func.examples = examples
        error_wrapped_func = wrap_error(func)
        result = commands.group(*args, **kwargs)(error_wrapped_func)
        return result
    return decorator

def message_key(ctx, message):
    prefix = ctx.bot.prefixes.get(message.guild.id, config_template.default_prefix)
    content_without_prefix = message.content.replace(prefix, '')
    return f'{message.guild.id}___{message.channel.id}___{content_without_prefix}'


