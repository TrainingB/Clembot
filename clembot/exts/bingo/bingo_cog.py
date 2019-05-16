import json
import datetime
import os
from datetime import timedelta

import discord
from discord.ext import commands

from clembot.core.logs import init_loggers
from clembot.exts.bingo.BingoCardGenerator import BingoCardGenerator
from clembot.exts.bingo.bingogenerator import BingoDataGenerator
from clembot.exts.config.configmanager import ConfigManager
from clembot.exts.config.globalconfigmanager import GlobalConfigCache
from clembot.exts.utils.utilities import Utilities


class BingoCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()
        self.logger = init_loggers()
        self.MyConfigManager = ConfigManager(bot)
        self.MyBingoDataGenerator = BingoDataGenerator()
        self.MyBingoBoardGenerator = BingoCardGenerator()
        self.MyGlobalConfigCache = GlobalConfigCache(bot.dbi)


    @commands.command(pass_context=True, hidden=True, aliases=["bingo-card"])
    async def _bingo_card(self, ctx):
        self.logger.info("_bingo_card() called")
        command_option = "-new"
        is_option_new = False
        try:
            message = ctx.message
            args = message.content
            args_split = args.split()
            if args_split.__contains__(command_option):
                args_split.remove(command_option)
                is_option_new = True

            message = ctx.message
            author = ctx.message.author

            if len(ctx.message.mentions) > 0:
                author = ctx.message.mentions[0]
            self.logger.info("calling")
            event_title_map = await self.MyGlobalConfigCache.get_clembot_config("bingo-event-title")
            event_title_map = json.loads(event_title_map)
            self.logger.info(event_title_map)

            event_pokemon = await self._get_bingo_event_pokemon(message.guild.id, "bingo-event")

            self.logger.info(event_pokemon)
            if event_pokemon == None:
                return await self.utilities._send_error_message(message.channel,
                                                 "Beep Beep! **{member}** The bingo-event is not set yet. Please contact an admin to run **!set bingo-event pokemon**".format(
                                                     ctx.message.author.display_name))

            existing_bingo_card_record = await self.MyConfigManager.find_bingo_card(ctx.message.guild.id, author.id, event_pokemon)

            if is_option_new:
                existing_bingo_card_record = None

            if existing_bingo_card_record:
                bingo_card = json.loads(existing_bingo_card_record['bingo_card'])
                timestamp = existing_bingo_card_record['generated_at']
                file_url = existing_bingo_card_record['bingo_card_url']
            else:
                bingo_card = self.MyBingoDataGenerator.generate_card(event_pokemon)
                timestamp = (message.created_at + datetime.timedelta(
                    hours=self.guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))
                file_path = self.MyBingoBoardGenerator.generate_board(user_name=author.id, bingo_card=bingo_card,
                                                                 template_file="{0}.png".format(event_pokemon))
                repo_channel = await self.get_repository_channel(message)
                file_url_message = await repo_channel.send(file=discord.File(file_path),
                                                           content="Generated for : {user} at {timestamp}".format(
                                                               user=author.mention, timestamp=timestamp))
                file_url = file_url_message.attachments[0].url

            msg = 'Beep Beep! {0.author.mention} here is your Bingo Card; please take a screenshot for future use!'.format(
                message)

            embed_msg = "**!{0}!**".format(event_title_map.get(event_pokemon, "BingO"))
            embed = discord.Embed(title=embed_msg, colour=discord.Colour.gold())
            embed.set_image(url=file_url)
            embed.set_footer(
                text=f"Generated for : {author.display_name} at {timestamp}/ Requested by {ctx.author.display_name}")

            await message.channel.send(msg)

            await ctx.message.channel.send(embed=embed)

            if not existing_bingo_card_record:
                await self.MyConfigManager.save_bingo_card(ctx.message.guild.id, author.id, event_pokemon, bingo_card,
                                                      file_url, str(timestamp))
                os.remove(file_path)

        except Exception as error:
            print(error)
            # logger.info(error)
        return

    async def get_repository_channel(self, message):
        try:
            bingo_card_repo_channel = None

            if 'bingo_card_repo' in self.guild_dict[message.guild.id]:
                bingo_card_repo_channel_id = self.guild_dict[message.guild.id]['bingo_card_repo']
                if bingo_card_repo_channel_id:
                    bingo_card_repo_channel = self.bot.get_channel(bingo_card_repo_channel_id)

            if bingo_card_repo_channel == None:
                bingo_card_repo_category = None
                bingo_card_repo_channel = await message.guild.create_text_channel('bingo_card_repo', overwrites=dict(
                    message.channel.overwrites), category=bingo_card_repo_category)

            bingo_card_repo = {'bingo_card_repo': bingo_card_repo_channel.id}
            self.guild_dict[message.guild.id].update(bingo_card_repo)
            return bingo_card_repo_channel

        except Exception as error:
            self.logger.error(error)



    @commands.command(pass_context=True, hidden=True, aliases=["bingo"])
    async def _bingo_win(self, ctx):
        try:
            message = ctx.message
            self.logger.info("_bingo_win called")

            event_title_map_text = await self.MyGlobalConfigCache.get_clembot_config("bingo-event-title")
            event_title_map = json.loads(event_title_map_text)

            event_pokemon = await self._get_bingo_event_pokemon(message.guild.id, "bingo-event")

            timestamp = (message.created_at + datetime.timedelta(
                hours=self.guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))
            existing_bingo_card_record = await self.MyConfigManager.find_bingo_card(ctx.message.guild.id,
                                                                               ctx.message.author.id, event_pokemon)

            if existing_bingo_card_record:
                raid_embed = discord.Embed(
                    title=_("**{0} Shoutout!**".format(event_title_map.get(event_pokemon, "BingO"))), description="",
                    colour=discord.Colour.dark_gold())

                raid_embed.add_field(name="**Member:**",
                                     value=_("**{member}** called **bingo** at **{timestamp}**.").format(
                                         member=message.author.display_name, timestamp=timestamp), inline=True)
                raid_embed.set_image(url=existing_bingo_card_record['bingo_card_url'])
                raid_embed.set_thumbnail(url=_(
                    "https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=message.author,
                                                                                                 format="jpg")))

                msg = 'Beep Beep! {0.author.mention} please follow the guidelines below to complete your submission.'.format(
                    message)

                guidelines = f":one: Submit **2 photos** (use any collage app on your phone) similar to examples provided. \n:two: A screenshot of **9 event pokemon renamed**. See: https://goo.gl/nPcRr5 \n:three: A collage for **box # 2, 4, 6, 8 pokemon** showing height, weight, gender & CP requirements. \nSee: https://goo.gl/YrSSvM \n Here is {message.author.mention}'s bingo card for reference: "
                raid_embed.add_field(name="**Submission Guidelines**", value=guidelines)

                await message.channel.send(content=msg)
                await message.channel.send(embed=raid_embed)

            else:
                await message.channel.send(
                    "Beep Beep! {0} you will need to generate a bingo card first!".format(message.author.mention))

        except Exception as error:
            print(error)
            self.logger.info(error)
        return


    async def _get_bingo_event_pokemon(self, guild_id, config_key):
        bingo_event_pokemon =await self.MyGlobalConfigCache.get_clembot_config(config_key)
        return bingo_event_pokemon


def setup(bot):
    bot.add_cog(BingoCog(bot))
