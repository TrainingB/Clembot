import json
import os
import traceback

import discord
from discord.ext import commands

from clembot.core.bot import group, command
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.exts.bingo.bingo_card_manager import BingoCardManager
from clembot.exts.bingo.bingo_card_writer import BingoCardWriter
from clembot.exts.bingo.bingo_data_generator import BingoDataGenerator
from clembot.exts.config.globalconfigmanager import GlobalConfigCache
from clembot.exts.config.guild_metadata import GuildMetadata
from clembot.utilities.timezone import timehandler as TH
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class BingoCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.utilities = Utilities()
        self.MyBingoCardManager = BingoCardManager(bot.dbi)
        self.MyGlobalConfigCache = GlobalConfigCache(bot.dbi)

    @command(pass_context=True, hidden=True, aliases=["bingo-card"])
    async def cmd_bingo_card_original(self, ctx):
        await self.cmd_bingo_card(ctx)

    @group(pass_context=True, hidden=True, aliases=["bingo"])
    async def cmd_bingo(self, ctx):
        if ctx.invoked_subcommand is None:
            await self._bingo_win(ctx)


    @cmd_bingo.command(pass_context=True, hidden=True, aliases=["card"])
    @wrap_error
    async def cmd_bingo_card(self, ctx):
        command_option = "-new"
        is_option_new = False

        message = ctx.message
        args = message.content
        args_split = args.split()
        if args_split.__contains__(command_option):
            args_split.remove(command_option)
            is_option_new = True

        message = ctx.message
        card_for = ctx.message.author

        if len(ctx.message.mentions) > 0:
            card_for = ctx.message.mentions[0]

        event_title = (await ctx.guild_profile("bingo-event-title")) or (
            await self.MyGlobalConfigCache.get_clembot_config("bingo-event-title"))
        event_pokemon = (await ctx.guild_profile("bingo-event-pokemon")) or (
            await self.MyGlobalConfigCache.get_clembot_config("bingo-event-pokemon"))

        if event_pokemon is None:
            raise Exception(f"The bingo-event is not set yet. Please contact an admin.")

        if is_option_new:
            existing_bingo_card_record = None
        else:
            existing_bingo_card_record = await self.MyBingoCardManager.find_bingo_card(ctx.message.guild.id,
                                                                                       card_for.id, event_pokemon)
        file_path = None
        if existing_bingo_card_record:
            bingo_card = json.loads(existing_bingo_card_record['bingo_card'])
            timestamp = existing_bingo_card_record['generated_at']
            file_url = existing_bingo_card_record['bingo_card_url']
        else:
            bingo_card = BingoDataGenerator.generate_card(event_pokemon)
            timezone = await ctx.guild_profile('timezone')
            timestamp = TH.as_local_time(TH.epoch(message.created_at, 'UTC'), timezone)
            file_path = BingoCardWriter.generate_board(user_name=card_for.id, bingo_card=bingo_card,
                                                       template_file="{0}.png".format(event_pokemon))
            repo_channel = await self.get_repository_channel(ctx, message)
            file_url_message = await repo_channel.send(file=discord.File(file_path),
                                                       content="Generated for : {user} at {timestamp}".format(
                                                           user=card_for.mention, timestamp=timestamp))
            file_url = file_url_message.attachments[0].url

        msg = f'Beep Beep! {card_for.mention} here is your Bingo Card; please take a screen-shot for future use!'

        embed_msg = "**{0}**".format(event_title)
        embed = discord.Embed(title=embed_msg, colour=discord.Colour.gold())
        embed.set_image(url=file_url)
        embed.set_author(name=f'Bingo card for {card_for.display_name}',
                         icon_url='https://cdn.discordapp.com/attachments/707860518416941078/715487100111421510/icons8-squared-menu-96.png')
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name} @ {timestamp}")

        await message.channel.send(msg)

        await ctx.message.channel.send(embed=embed)

        if not existing_bingo_card_record:
            await self.MyBingoCardManager.save_bingo_card(ctx.message.guild.id, card_for.id, event_pokemon,
                                                          bingo_card,
                                                          file_url, str(timestamp))
            if file_path:
                os.remove(file_path)


    @wrap_error
    async def get_repository_channel(self, ctx, message):

        bingo_card_repo_channel_id = await GuildMetadata.bingo_card_repo(self.bot, ctx.message.guild.id)

        if bingo_card_repo_channel_id:
            bingo_card_repo_channel = self.bot.get_channel(int(bingo_card_repo_channel_id))

        else:
            bingo_card_repo_category = None
            bingo_card_repo_channel = await message.guild.create_text_channel('bingo_card_repo', overwrites=dict(
                message.channel.overwrites), category=bingo_card_repo_category)

            await ctx.guild_profile(key='bingo-card-repo', value=bingo_card_repo_channel.id)

        return bingo_card_repo_channel

    @wrap_error
    async def _bingo_win(self, ctx):
        message = ctx.message

        event_title = (await ctx.guild_profile("bingo-event-title")) or (
            await self.MyGlobalConfigCache.get_clembot_config("bingo-event-title"))
        event_pokemon = (await ctx.guild_profile("bingo-event-pokemon")) or (
            await self.MyGlobalConfigCache.get_clembot_config("bingo-event-pokemon"))
        timezone = await ctx.guild_profile('timezone')
        timestamp = TH.as_local_time(TH.epoch(message.created_at, 'UTC'),timezone)
        existing_bingo_card_record = await self.MyBingoCardManager.find_bingo_card(ctx.message.guild.id,
                                                                                   ctx.message.author.id,
                                                                                   event_pokemon)

        if existing_bingo_card_record:
            raid_embed = discord.Embed(
                title=f"**{event_title} Shoutout!**", description="",
                colour=discord.Colour.dark_gold())

            raid_embed.add_field(name="**Member:**",
                                 value=f"**{message.author.display_name}** called **bingo** at **{timestamp}**.", inline=False)
            raid_embed.set_image(url=existing_bingo_card_record['bingo_card_url'])
            raid_embed.set_thumbnail(
                url=f"https://cdn.discordapp.com/avatars/{message.author.id}/{message.author.avatar}.jpg")

            msg = 'Beep Beep! {0.author.mention} please follow the guidelines below to complete your submission.'.format(
                message)

            guidelines = f":one: Submit **2 photos** (use any collage app on your phone) similar to examples provided. \n:two: A screenshot of **9 event pokemon renamed**. See: https://goo.gl/nPcRr5 \n:three: A collage for **box # 2, 4, 6, 8 pokemon** showing height, weight, gender & CP requirements. \nSee: https://goo.gl/YrSSvM \n Here is {message.author.mention}'s bingo card for reference: "
            raid_embed.add_field(name="**Submission Guidelines**", value=guidelines)

            await message.channel.send(content=msg)
            await message.channel.send(embed=raid_embed)

        else:
            await message.channel.send(
                "Beep Beep! {0} you will need to generate a bingo card first!".format(message.author.mention))



    async def _get_bingo_event_pokemon(self, guild_id, config_key):
        bingo_event_pokemon = await self.MyGlobalConfigCache.get_clembot_config(config_key)
        return bingo_event_pokemon
