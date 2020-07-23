import asyncio

import discord
import pydash as _
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config.constants import Icons
from clembot.core import checks
from clembot.core.bot import group
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.utilities.utils.embeds import Embeds


class FeatureManagementCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    FEATURES = ['raid', 'wild', 'nest', 'research', 'trade', 'rocket']
    CITY_FEATURES = ['raid', 'wild', 'nest', 'research', 'trade', 'rocket']


    @group(pass_context=True, aliases=["feature"])
    @checks.is_guild_admin()
    async def cmd_feature(self, ctx):
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                return await self.cmd_feature_status(ctx)

            raise BadArgument("`!feature` can be used with `status, enable, disable`")


    @cmd_feature.command(pass_context=True, aliases=["abort"])
    @checks.is_guild_admin()
    @wrap_error
    async def cmd_abort(self, ctx):
        channel_id = ctx.channel.id
        if ChannelMetadata.config_in_progress(channel_id):
            ChannelMetadata.end_configuration(channel_id)
            return await Embeds.message(ctx.channel, "Aborting current configuration!")

        raise Exception("No configuration found in progress.")


    @cmd_feature.command(pass_context=True, aliases=["status"])
    @checks.is_guild_admin()
    @wrap_error
    async def cmd_feature_status(self, ctx):
        channel_id = ctx.channel.id
        report_channel_dict = await ChannelMetadata.find(ctx.bot, channel_id, ctx.guild.id)
        return await ctx.send(embed=ChannelMetadata.embed(ctx, report_channel_dict))


    @cmd_feature.command(pass_context=True, aliases=["disable"])
    @checks.is_guild_admin()
    @wrap_error
    async def cmd_feature_disable(self, ctx, *features):
        """
        Disable features in the channel.
        """
        try:
            channel_id = ctx.channel.id
            if ChannelMetadata.config_in_progress(channel_id):
                raise BadArgument("It seems like another configuration is already in progress. \nType `cancel` or `!abort` to abort the current configuration and re-start.")

            requested_features = [feature for feature in features if feature in FeatureManagementCog.FEATURES]
            if not requested_features:
                raise BadArgument(f"valid features are: `{', '.join(FeatureManagementCog.FEATURES)}`.")

            ChannelMetadata.begin_configuration(channel_id)
            report_channel_dict = await ChannelMetadata.find(ctx.bot, channel_id, ctx.guild.id)

            for feature in requested_features:
                report_channel_dict[feature] = False

            await ChannelMetadata.update(ctx.bot, report_channel_dict)
            ChannelMetadata.end_configuration(channel_id)
            return await ctx.send(embed=ChannelMetadata.success_embed(ctx, report_channel_dict))

        except BadArgument as ba:
            raise ba
        except Exception as error:
            ChannelMetadata.end_configuration(channel_id)
            Logger.error(error)
            raise error


    @cmd_feature.command(pass_context=True, aliases=["enable"])
    @checks.is_guild_admin()
    @wrap_error
    async def cmd_feature_enable(self, ctx, *features):
        """
        Enable features in the channel.
        """
        try:
            channel_id = ctx.channel.id
            if ChannelMetadata.config_in_progress(channel_id):
                raise BadArgument("It seems like another configuration is already in progress. \nType `cancel` or `!feature abort` to abort the current configuration and re-start.")

            requested_features = [feature for feature in features if feature in FeatureManagementCog.FEATURES]
            if not requested_features:
                raise BadArgument(f"valid features are: `{', '.join(FeatureManagementCog.FEATURES)}`.")


            ChannelMetadata.begin_configuration(channel_id)
            report_channel_dict = await ChannelMetadata.find(ctx.bot, channel_id, ctx.guild.id)

            Logger.info(report_channel_dict)


            if not _.is_empty(_.intersection(requested_features, FeatureManagementCog.CITY_FEATURES)):
                if not report_channel_dict.get('city'):
                    report_channel_dict = await self.set_location(ctx, channel_id, report_channel_dict)

            if 'raid' in requested_features:
                report_channel_dict = await self.enable_raid(ctx, channel_id, report_channel_dict)

            for feature in ['wild', 'nest', 'rocket', 'trade', 'research']:
                if feature in requested_features:
                    report_channel_dict[feature] = True

            if not ChannelMetadata.config_in_progress(channel_id):
                return await ctx.send(embed=ChannelMetadata.failure_embed(ctx, report_channel_dict))

            await ChannelMetadata.update(ctx.bot, report_channel_dict)
            ChannelMetadata.end_configuration(channel_id)
            return await ctx.send(embed=ChannelMetadata.success_embed(ctx, report_channel_dict))
        except BadArgument as ba:
            raise ba
        except Exception as error:
            ChannelMetadata.end_configuration(channel_id)





    async def set_location(self, ctx, channel_id, channel_dict):

        city = channel_dict.get('city')

        if city:
            # await Utilities.ask_confirmation(ctx, ctx.message, f'The current city is set as {city}.')
            return
        content = 'All location based features need a city to be setup for the channel. ' \
                  'What would you like it to be set to? \n(ex: LASVEGASNV for Las Vegas, Nevada)'
        prompt_embed = Embeds.make_embed(header="Enable Raid Configuration - City", header_icon=Icons.configure,
                                         title="Please setup the city for the channel.",
                                         msg_color=discord.Color.blue(),
                                         footer="Note: type 'cancel' to cancel the configuration.",
                                         content=content)

        def is_text(msg):
            return True

        response = await self.ask_for_input(ctx, prompt_embed, is_text)
        if response == "cancel":
            ChannelMetadata.end_configuration(channel_id)
            raise BadArgument("Configuration cancelled.")

        channel_dict['city'] = response.replace(" ", "").upper()

        return channel_dict



    async def enable_raid(self, ctx, channel_id, channel_dict):

        content = "**none** - if you don't want them categorized, \n"\
                  "**same** - if you want them in the same category as the reporting channel, \n"\
                  "**level** - if you want them categorized by level, \n" \
                  "**some** - if you want them to go under a different category. "

        prompt_embed = Embeds.make_embed(header="Enable Raid Configuration", header_icon=Icons.configure,
                                         msg_color=discord.Color.blue(),
                                         title="How would you like me to categorize the raid channels I create?",
                                         content=content, footer="Note: type 'cancel' to cancel the configuration."
                                         )

        def is_valid_category(text):
            if text in ["none", "same", "level", "some"]:
                return True
            return False


        response = (await self.ask_for_input(ctx, prompt_embed, is_valid_category)).lower()
        if response == "cancel":
            ChannelMetadata.end_configuration(channel_id)
            return channel_dict
        if response == "none":
            channel_dict['category'] = None
        elif response == "same":
            channel_dict['category'] = str(ctx.channel.category.id) if ctx.channel.category else None
        elif response == "some":
            prompt_embed = Embeds.make_embed(header="Enable Raid Configuration - Category selection",
                                             msg_color=discord.Color.blue(),
                                             header_icon=Icons.configure, title="Enter the category name or id for this channel?",
                                             footer="Note: type 'cancel' to cancel the configuration.")
            def is_category_exists(ui):
                term = int(ui.strip()) if ui.strip().isdigit() else ui.strip()
                category = ctx.get.category(term)
                return category is not None

            response = await self.ask_for_input(ctx, prompt_embed, is_category_exists)
            if response == "cancel":
                ChannelMetadata.end_configuration(channel_id)
                return channel_dict
            channel_dict['category'] = response

        elif response == "level":
            content="""Pokemon Go currently has six levels of raids. 
            Please provide the names of the categories you would like each level of raid to appear in. 
            Use the following order: 1, 2, 3, 4, 5, EX
            You do not need to use different categories for each level, but they do need to be pre-existing categories. 
            Separate each category name with a comma."""

            prompt_embed = Embeds.make_embed(header="Enable Raid Configuration - Categories by level selection",
                                             header_icon=Icons.configure, content=content,
                                             msg_color=discord.Color.blue(),
                                             footer="Note: type 'cancel' to cancel the configuration.")


            def is_all_valid_category(ui):
                valid = True
                for category_id in ui.split(","):
                    category = ctx.get.category(int(category_id.strip()) if category_id.strip().isdigit() else category_id.strip())
                    valid = valid and category is not None
                return valid

            response = await self.ask_for_input(ctx, prompt_embed, is_all_valid_category)
            if response == "cancel":
                ChannelMetadata.end_configuration(channel_id)
                return channel_dict

            level = ['1', '2', '3', '4', '5', 'EX']

            level_cat = { level[i] : (response.split(",")[i]).strip() for i in range(len(level))}
            channel_config = channel_dict.get('config') or {}
            channel_config['categories'] = level_cat
            channel_dict['config'] = channel_config
            channel_dict['category'] = None
        channel_dict['raid'] = True
        return channel_dict



    async def ask_for_input(self, ctx, prompt_embed, validate_response):
        """
        returns cancel if configuration is cancelled.
        """
        def check(msg):
            return msg.author == ctx.message.author and msg.channel == ctx.channel

        await ctx.send(embed=prompt_embed)

        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                await Embeds.error(ctx.channel, 'Too late! Aborting configuration!')
                return "cancel"
            except Exception as error:
                break
            response_content = response.content.strip()
            if ChannelMetadata.config_in_progress(ctx.channel.id):
                if response_content == "cancel" or validate_response(response_content):
                    return response_content
                else:
                    await Embeds.error(ctx.channel, 'I could not interpret your response. Try again!')
                    continue
        return "cancel"


