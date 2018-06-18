from discord.ext import commands
import discord
from clembot import checks

class Utilities:
    def __init__(self, bot):
        self.bot = bot
    #
    # async def _send_error_message(channel, description):
    #
    #     color = discord.Colour.red()
    #     error_embed = discord.Embed(description="{0}".format(description), colour=color)
    #     return await channel.send(embed=error_embed)
    #
    # async def _send_message(channel, description):
    #     try:
    #
    #         error_message = "The output contains more than 2000 characters."
    #         if len(description) >= 2000:
    #             discord.Embed(description="{0}".format(error_message), colour=color)
    #
    #         color = discord.Colour.green()
    #         message_embed = discord.Embed(description="{0}".format(description), colour=color)
    #
    #         return await channel.send(embed=message_embed)
    #     except Exception as error:
    #         print(error)
    #
    #
    # @commands.command(name='embed')
    # @checks.serverowner_or_permissions(manage_message=True)
    # async def _embed(self, ctx, title, content=None, colour=None,
    #                  icon_url=None, image_url=None, thumbnail_url=None,
    #                  plain_msg=''):
    #     """Build and post an embed in the current channel.
    #
    #     Note: Always use quotes to contain multiple words within one argument.
    #     """
    #     await ctx.embed(title=title, description=content, colour=colour,
    #                     icon=icon_url, image=image_url,
    #                     thumbnail=thumbnail_url, plain_msg=plain_msg)

    async def _send_error_message(self, channel, description):

        color = discord.Colour.red()
        error_embed = discord.Embed(description="{0}".format(description), colour=color)
        return await channel.send(embed=error_embed)

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
    bot.add_cog(Utilities(bot))
