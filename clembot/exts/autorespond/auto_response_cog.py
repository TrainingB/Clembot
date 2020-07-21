import traceback

from discord.ext import commands

from clembot.core.bot import group
from clembot.core.logs import Logger
from clembot.exts.autorespond.auto_response import AutoResponse
from clembot.utilities.utils.embeds import Embeds

"""
create table auto_responses (
    guild_id bigint not null,
    channel_id bigint not null,
    respond_to text,
    respond_with text
);
"""


class AutoResponseCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_auto_responses())

    async def load_auto_responses(self):
        Logger.info("load_auto_responses()")
        ar_records = await AutoResponse.find_auto_responses(self.bot)
        for ar in ar_records:
            AutoResponse.cache(self.bot, AutoResponse.from_db_dict(self.bot, ar))

        print(len(AutoResponse.by_respond_to.keys()))


    def send_auto_response(self, message, respond_to):




        pass

    @group(pass_context=True, hidden=True, aliases=["auto-response", "ar"])
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
            Logger.error(f"{traceback.format_exc()}")


