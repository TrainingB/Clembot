from discord.ext import commands
import discord

class Utilities:
    def __init__(self):
        return

    numbers = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:", "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:"}

    def emojify_numbers(self, number):
        number_emoji = ""

        reverse = "".join(reversed(str(number)))

        for digit in reverse[::-1]:

            emoji = self.numbers.get(digit)
            if not emoji:
                emoji = ":regional_indicator_"+digit.lower()+":"

            number_emoji = number_emoji + emoji

        return number_emoji

    async def _send_error_message(self, channel, description):

        color = discord.Colour.red()
        error_embed = discord.Embed(description="{0}".format(description), colour=color)
        return await channel.send(embed=error_embed)

    @classmethod
    async def _send_message(self, channel, description):
        try:

            error_message = "The output contains more than 2000 characters."
            if len(description) >= 2000:
                discord.Embed(description="{0}".format(error_message), colour=color)

            color = discord.Colour.green()
            message_embed = discord.Embed(description="{0}".format(description), colour=color)

            return await channel.send(embed=message_embed)
        except Exception as error:
            print(error)

    @commands.command(name="export")
    async def _export(self, ctx):

        return await self._send_message(ctx.channel, "Beep Beep! **{}**, This feature is under-development!".format(ctx.message.author.display_name))

        print("_export() called!")


        raid_dict = ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id]

        channel_mentions = ctx.message.raw_channel_mentions

        if len(channel_mentions) < 1:
            await self._send_error_message(ctx.channel, "Beep Beep! **{}**, Please provide the channel reference to export the details!".format(ctx.message.author.display_name))





def setup(bot):
    bot.add_cog(Utilities())
