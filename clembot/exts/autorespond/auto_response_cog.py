from discord.ext import commands

from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities

"""
create table auto_responses (
    guild_id bigint not null,
    channel_id bigint not null,
    respond_to text,
    respond_with text
);
"""


class AutoResponse:

    by_respond_to = dict()

    def __init__(self, bot, guild_id, channel_id, respond_to, respond_with, image=False, auto_respond_id=None):
        self.bot = bot
        self.id = auto_respond_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.respond_to = respond_to
        self.respond_with = respond_with
        self.image = image

    @property
    def key(self):
        return f"{self.guild_id}___{self.channel_id}___{self.respond_to}"

    def get_state(self):
        db_dict = {
            'guild_id' : self.guild_id,
            'channel_id' : self.channel_id,
            'respond_to' : self.respond_to,
            'respond_with' : self.respond_with,
            'image' : self.image
        }
        return db_dict



    @classmethod
    def from_db_dict(cls, bot, db_dict):
        p_id, p_guild_id, p_channel_id, p_respond_to, p_respond_with, p_image = ([db_dict.get(key) for key in ['id', 'guild_id', 'channel_id', 'respond_to', 'respond_with', 'image']])

        return cls(bot, p_guild_id, p_channel_id, p_respond_to, p_respond_with, p_image, p_id)

    @classmethod
    def from_cache(cls, guild_id, channel_id, respond_to):

        key = f"{guild_id}___{channel_id}___{respond_to}"

        auto_response = cls.by_respond_to[key]

        return auto_response


    @classmethod
    def cache(cls, auto_response):
        cls.by_respond_to[auto_response.key] = auto_response


    @classmethod
    def evict(cls, auto_response):
        cls.by_respond_to.pop(auto_response.key, None)


    async def insert(self):
        auto_response_table = self.bot.dbi.table('auto_responses')
        auto_response_table_insert = auto_response_table.insert(**self.get_state())
        await auto_response_table_insert.commit()
        AutoResponse.cache(auto_response=self)


    async def update(self):
        auto_response_table = self.bot.dbi.table('auto_responses')
        auto_response_table_update = auto_response_table.update(**self.get_state()).where(id=self.id)
        await auto_response_table_update.commit()
        AutoResponse.cache(auto_response=self)

    async def delete(self):
        """Deletes the raid record from DB and evicts from cache."""
        auto_response_table = self.bot.dbi.table('auto_responses')
        auto_response_table_delete = auto_response_table.query().where(id=self.id)
        await auto_response_table_delete.delete()
        AutoResponse.evict(auto_response=self)





class AutoResponseCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_auto_responses())

    async def load_auto_responses(self):
        Logger.info("pickup_raiddata()")

        await PokemonCache.load_cache_from_dbi(self.bot.dbi)
        for rcrd in await RaidRepository.find_raids():
            self.bot.loop.create_task(self.pickup_raid(rcrd))

    @commands.group(pass_context=True, hidden=True, aliases=["auto-response", "ar"])
    async def cmd_auto_response(self, ctx):
        if ctx.invoked_subcommand is None:
            await Embeds.error(ctx.channel, f"**!{ctx.invoked_with}** can be used with `add, add-image or clear-all`.", user=ctx.message.author)


    @cmd_auto_response.command(aliases=["add-image"])
    async def cmd_auto_response_add_image(self, ctx, *, ar_message_text):
        ar_key, _, ar_message = ar_message_text.partition(' ')

        auto_response = AutoResponse(ctx.bot, ctx.guild_id, ctx.channel_id, ar_key, ar_message, True)

        await auto_response.insert()

        await Embeds.message(ctx.channel, f"{ar_key} has been set correctly.", user=ctx.message.author)


    @cmd_auto_response.command(aliases=["add"])
    async def cmd_auto_response_add(self, ctx, *, ar_message_text):
        ar_key, _, ar_message = ar_message_text.partition(' ')

        auto_response = AutoResponse(ctx.bot, ctx.guild.id, ctx.channel.id, ar_key, ar_message, False)

        await auto_response.insert()

        await Embeds.message(ctx.channel, f"{ar_key} has been set correctly.", user=ctx.message.author)


    @cmd_auto_response.command(aliases=["clear-all"])
    async def cmd_auto_response_clear_all(self, ctx):
        try:

            for channel_id in AutoResponse.by_channel.keys():

                auto_response = AutoResponse.by_channel[channel_id]
                await auto_response.delete()

            await Embeds.message(ctx.channel, f"auto-responses are cleaned up.", user=ctx.message.author)

        except Exception as error:
            print(error)


