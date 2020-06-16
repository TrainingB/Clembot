import json

from discord.ext import commands

from clembot.core.logs import Logger
from clembot.utilities.utils.utilities import Utilities
from clembot.utilities.utils.embeds import Embeds


class GuildConfigCog(commands.Cog):
    """Caches the guild config as well
    prefix - !
    city - city of the guild, for gym search
    timezone - as text to handle pytz time (America/Los_Angeles)

    nest.preview.hide = true ( hides maps preview in nest )

    """
    _cache = dict()

    _guild_config_key = ["prefix", "city", "timezone", "nest.preview.hide"]
    _channel_config_key = ["city"]

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()


    @commands.group(pass_context=True, hidden=True, aliases=["config"])
    async def _command_config(self, ctx):
        try:
            if ctx.invoked_subcommand is None:
                return await Embeds.error(ctx.channel,
                                          f"**{ctx.invoked_with}** can be only used with options **guild, channel**.",
                                          user=ctx.message.author)
        except Exception as error:
            Logger.error(error)


    @_command_config.command(pass_context=True, hidden=True, aliases=["guild"])
    async def _command_config_guild(self, ctx, config_name=None, config_value=None):

        if config_name and config_name not in GuildConfigCog._guild_config_key:
            return await Embeds.error(ctx.message.channel, "No such configuration exists.")

        config = await ctx.guild_setting(key=config_name, value=config_value)
        if config_name:
            if config_value:
                config = await ctx.guild_setting(key=config_name)
            await Embeds.message(ctx.message.channel, f"**{config_name}** is set to **{config}**")
        else:
            await GuildConfigCog.send_guild_config_embed(ctx, config)


    @staticmethod
    async def send_guild_config_embed(ctx, config):

        await ctx.embed("Guild Configuration",
                        fields = {k['config_name']:k['config_value'] for k in config if k['config_name'] in GuildConfigCog._guild_config_key},
                        inline=True)















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


