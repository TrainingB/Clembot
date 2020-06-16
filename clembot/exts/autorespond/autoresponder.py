from discord.ext import commands

from clembot.utilities.utils.utilities import Utilities


class AutoResponder(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

    @commands.group(pass_context=True, hidden=True, aliases=["auto-response", "ar"])
    async def _command_auto_response(self, ctx):
        if ctx.invoked_subcommand is None:
            await Utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")


    @_command_auto_response.command(aliases=["add-image"])
    async def _command_auto_response_add_image(self, ctx, *, ar_message_text):
        ar_key, _, ar_message = ar_message_text.partition(' ')

        ctx.bot.guild_dict[ctx.guild.id].setdefault('auto-responses-image', {}).setdefault(ctx.channel.id,{})[ar_key] = ar_message

        await Utilities._send_message(ctx.channel, f"{ar_key} has been set correctly.", user=ctx.message.author)


    @_command_auto_response.command(aliases=["add"])
    async def _command_auto_response_add(self, ctx, *, ar_message_text):
        ar_key, _, ar_message = ar_message_text.partition(' ')

        ctx.bot.guild_dict[ctx.guild.id].setdefault('auto-responses', {}).setdefault(ctx.channel.id,{})[ar_key] = ar_message

        await Utilities._send_message(ctx.channel, f"{ar_key} has been set correctly.", user=ctx.message.author)


    @_command_auto_response.command(aliases=["clear-all"])
    async def _command_auto_response_clear_all(self, ctx):
        try:

            for guild_id in list(ctx.bot.guild_dict.keys()):
                for channel_id in list(ctx.bot.guild_dict[guild_id].get('auto-responses', {}).keys()):
                    if not ctx.bot.guild_dict[guild_id].get('auto-responses', {}).get(channel_id, None) :
                        print(ctx.bot.guild_dict[guild_id].get('auto-responses', {}).pop(channel_id,None))

                for channel_id in list(ctx.bot.guild_dict[guild_id].get('auto-responses-image', {}).keys()):
                    if not ctx.bot.guild_dict[guild_id].get('auto-responses-image', {}).get(channel_id, None) :
                        print(ctx.bot.guild_dict[guild_id].get('auto-responses-image', {}).pop(channel_id,None))

            await Utilities._send_message(ctx.channel, f"auto-responses are cleaned up.", user=ctx.message.author)
        except Exception as error:
            print(error)


