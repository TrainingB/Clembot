from discord.ext import commands

from clembot.utilities.utils.utilities import Utilities


class RemoveComma(commands.Converter):
    async def convert(self, ctx, argument):
        return argument.replace(",", " ").strip()


class HandleAngularBrackets(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.__contains__("<") or argument.__contains__(">"):
            await Utilities._send_error_message(ctx.channel,f"Beep Beep! **{ctx.message.author.display_name}**, **< >** just represents the placeholder. You can provide the values directly!")
        return argument.replace("<", "").replace(">", "").strip()