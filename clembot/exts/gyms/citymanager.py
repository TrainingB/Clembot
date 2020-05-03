from discord.ext import commands

from clembot.core.logs import init_loggers
from clembot.exts.utils.utilities import Utilities
from clembot.core import checks


class CityManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()
        self.guild_dict = bot.guild_dict
        self.MyGuildConfigCache = bot.MyGuildConfigCache
        self.MyChannelConfigCache = bot.MyChannelConfigCache
        self._cache = {}

    @commands.command(pass_context=True, hidden=True, aliases=["get-city"])
    async def get_city(self, ctx):
        await self._get_city(ctx)

    @commands.command(pass_context=True, hidden=True, aliases=["set-city"])
    async def _set_city(self, ctx, city_state):
        city_state = city_state.upper()

        await self.MyChannelConfigCache.save_channel_city(ctx.message.guild.id, ctx.message.channel.id, city_state)

        await self._get_city(ctx)

    @commands.command(pass_context=True, hidden=True, aliases=["set-guild-city"])
    @checks.guildowner_or_permissions(manage_guild=True)
    async def _set_guild_city(self, ctx, city_state):

        city_state = city_state.upper()

        await self.MyGuildConfigCache.save_guild_config(ctx.message.guild.id, 'city', city_state)
        await self._get_guild_city(ctx.message)

    @commands.command(pass_context=True, hidden=True, aliases=["get-guild-city"])
    @checks.guildowner_or_permissions(manage_guild=True)
    async def get_guild_city(self, ctx):
        await self._get_guild_city(ctx.message)


    async def _get_city(self, ctx):
        content = "Beep Beep! Reporting City for this channel / guild has not been set."

        channel_city = await self.get_city_for_channel(ctx.guild.id, ctx.message.channel.id)

        if channel_city:
            content = f"Beep Beep! **{ctx.message.author.display_name}** Reporting City for this channel is **{channel_city}**."

        return await self.utilities._send_message(ctx.message.channel, content)

    async def _get_guild_city(self, message):
        guild_city = await self.MyGuildConfigCache.get_guild_config(message.guild.id, 'city')
        content = f"Beep Beep! **{message.author.display_name}** Reporting City for this guild is **{guild_city}**."

        return await self.utilities._send_message(message.channel, content)



    async def get_city_for_channel(self, guild_id, channel_id=None, parent_channel_id=None) -> str :
        try:

            city_for_channel = await self.MyChannelConfigCache.get_channel_config(guild_id=guild_id, channel_id=channel_id, config_name='city')

            if not city_for_channel:
                if parent_channel_id:
                    city_for_channel = await self.MyChannelConfigCache.get_channel_config(guild_id=guild_id, channel_id=parent_channel_id, config_name='city')

            if not city_for_channel:
                city_for_channel = await self.MyGuildConfigCache.get_guild_config(guild_id=guild_id, config_name='city')
            return city_for_channel

        except Exception as error:
            self.logger.info(error)
            return None

    async def get_city_for_channel_only(self, guild_id, channel_id, parent_channel_id=None) -> str :
        try:
            self.logger.info(f"read_channel_city({guild_id}, {channel_id}, {parent_channel_id})")
            city_for_channel = await self.MyChannelConfigCache.get_channel_config(guild_id=guild_id, channel_id=channel_id, config_name='city')

            if not city_for_channel:
                city_for_channel = await self.MyChannelConfigCache.get_channel_config(guild_id=guild_id, channel_id=parent_channel_id, config_name='city')
            return city_for_channel

        except Exception as error:
            print(error)
            self.logger.info(error)
            return None

    # async def save_channel_city(self, guild_id, channel_id, city_state):
    #     print("save_channel_city()")
    #     try:
    #         await self.MyChannelConfigCache.save_channel_config('city', city_state, guild_id, channel_id)
    #         new_channel_city =  await self.MyChannelConfigCache.get_channel_config('city', guild_id=guild_id, channel_id=channel_id)
    #         return new_channel_city
    #     except Exception as error:
    #         print(error)
    #         return None

def setup(bot):
    bot.add_cog(CityManager(bot))

