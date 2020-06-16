import json
import datetime
import os

import discord
from discord.ext import commands

from clembot.core.logs import Logger
from clembot.exts.bingo.bingocardwriter import BingoCardWriter
from clembot.exts.bingo.bingogenerator import BingoDataGenerator
from clembot.exts.bingo.bingocardmanager import BingoCardManager
from clembot.exts.config.globalconfigmanager import GlobalConfigCache
from clembot.utilities.utils.utilities import Utilities
from clembot.utilities.utils.embeds import Embeds


class BingoCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.MyBingoCardManager = BingoCardManager(bot.dbi)
        self.MyBingoDataGenerator = BingoDataGenerator()
        self.MyBingoBoardGenerator = BingoCardWriter()
        self.MyGlobalConfigCache = GlobalConfigCache(bot.dbi)


    @commands.command(pass_context=True, hidden=True, aliases=["bingo-card"])
    async def cmd_bingo_card_original(self, ctx):
        return await Embeds.error(ctx.channel, f"This command has been migrated to `!bingo card`.", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["bingo"])
    async def cmd_bingo(self, ctx):
        if ctx.invoked_subcommand is None:
            await self._bingo_win(ctx)


    @cmd_bingo.command(pass_context=True, hidden=True, aliases=["card", "bingo-card"])
    async def cmd_bingo_card(self, ctx):
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
            event_title_map = await self.MyGlobalConfigCache.get_clembot_config("bingo-event-title")
            event_title_map = json.loads(event_title_map)
            Logger.info(event_title_map)

            event_pokemon = await self._get_bingo_event_pokemon(message.guild.id, "bingo-event")

            Logger.info(event_pokemon)
            if event_pokemon is None:
                return await Embeds.error(message.channel, f"The bingo-event is not set yet. Please contact an admin to run **!set bingo-event pokemon**", user=message.author)



            if is_option_new:
                existing_bingo_card_record = None
            else:
                existing_bingo_card_record = await self.MyBingoCardManager.find_bingo_card(ctx.message.guild.id,
                                                                                           author.id, event_pokemon)

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

            msg = f'Beep Beep! {author.mention} here is your Bingo Card; please take a screen-shot for future use!'

            embed_msg = "**{0}**".format(event_title_map.get(event_pokemon, "BingO"))
            embed = discord.Embed(title=embed_msg, colour=discord.Colour.gold())
            embed.set_image(url=file_url)
            embed.set_author(name=f'Bingo card for {author.display_name}', icon_url='https://cdn.discordapp.com/attachments/707860518416941078/715487100111421510/icons8-squared-menu-96.png')
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}")

            await message.channel.send(msg)

            await ctx.message.channel.send(embed=embed)

            if not existing_bingo_card_record:
                await self.MyBingoCardManager.save_bingo_card(ctx.message.guild.id, author.id, event_pokemon, bingo_card,
                                                              file_url, str(timestamp))
                if file_path:
                    os.remove(file_path)

        except Exception as error:
            print(error)
        return


    async def get_repository_channel(self, message):
        try:
            bingo_card_repo_channel = None

            if 'bingo_card_repo' in self.guild_dict[message.guild.id]:
                bingo_card_repo_channel_id = self.guild_dict[message.guild.id]['bingo_card_repo']
                if bingo_card_repo_channel_id:
                    bingo_card_repo_channel = self.bot.get_channel(bingo_card_repo_channel_id)

            if bingo_card_repo_channel is None:
                bingo_card_repo_category = None
                bingo_card_repo_channel = await message.guild.create_text_channel('bingo_card_repo', overwrites=dict(
                    message.channel.overwrites), category=bingo_card_repo_category)

            bingo_card_repo = {'bingo_card_repo': bingo_card_repo_channel.id}
            self.guild_dict[message.guild.id].update(bingo_card_repo)
            return bingo_card_repo_channel

        except Exception as error:
            Logger.error(error)


    async def _bingo_win(self, ctx):
        try:
            Logger.info("_bingo_win()")
            message = ctx.message


            event_title_map_text = await self.MyGlobalConfigCache.get_clembot_config("bingo-event-title")
            event_title_map = json.loads(event_title_map_text)

            event_pokemon = await self._get_bingo_event_pokemon(message.guild.id, "bingo-event")

            timestamp = (message.created_at + datetime.timedelta(
                hours=self.guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))
            existing_bingo_card_record = await self.MyBingoCardManager.find_bingo_card(ctx.message.guild.id,
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
            Logger.info(error)
        return


    async def _get_bingo_event_pokemon(self, guild_id, config_key):
        bingo_event_pokemon =await self.MyGlobalConfigCache.get_clembot_config(config_key)
        return bingo_event_pokemon

