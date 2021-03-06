import asyncio
import copy
import json
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config.constants import MyEmojis
from clembot.core import checks
from clembot.core.bot import group, command
from clembot.core.checks import AccessDenied
from clembot.core.logs import Logger
from clembot.exts.config import channel_checks
from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.exts.raid import raid_checks
from clembot.exts.raid.raid import RaidRepository, RaidParty, RosterLocation, ChannelMessage
from clembot.exts.raid.raid_cog import NoRaidForChannelError
from clembot.utilities.utils import snowflake
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class RaidPartyCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()

        self.bot.loop.create_task(self.load_raid_parties())


    async def load_raid_parties(self):
        Logger.info("load_raid_parties()")

        await Pokemon.load(self.bot)
        for rcrd in await RaidRepository.find_raid_parties():
            self.bot.loop.create_task(self.load_raid_party(rcrd))


    async def load_raid_party(self, rcrd):
        Logger.info(f"load_raid_party({rcrd.get('raid_party_id', None)})")
        await RaidParty.from_db_dict(self.bot, rcrd)


    @staticmethod
    def get_raid_party_for_channel(ctx) -> RaidParty:
        raid_party = RaidParty.by_channel.get(ctx.channel.id, None)
        if raid_party is not None:
            return raid_party
        else:
            raise NoRaidForChannelError(f"Raid not found for channel {ctx.channel.mention}.")


    @command(pass_context=True, category='Bot Info', aliases=["raidparty", "rp", "raid-party"])
    @channel_checks.raid_report_enabled()
    async def cmd_raidparty(self, ctx, *party_title):
        """
        **!raid-party channel-name** - creates a raid party channel.

        **Organizer commands:**
        **!add pokemon-or-egg gym-or-location [eta]** - adds a location into the roster
        **!update location# [pokemon-or-egg] [gym-or-location] [eta]** - updates the pokemon or location or eta for location #
        **!remove location#** - to remove specified location from roster
        **!move** - moves raid party to the next location in roster
        **!reset** - to clean up the roster
        **!raid-over** - to delete the channel (only channel-creator can do this)

        **Participant commands:**
        **!roster** - lists the roster
        **!where** - to see the current location of raid party
        **!next** - to see the next location of raid party

        """

        city = await ctx.city()
        timezone = await ctx.guild_profile(key='timezone')
        raid_party_id = next(snowflake.create())

        try:
            raid_party_channel = await ctx.guild.create_text_channel('-'.join(party_title), overwrites=dict(ctx.channel.overwrites),
                                                category=ctx.guild.get_channel(ctx.channel.category_id))

            raid_party_message = await Embeds.message(ctx.channel, f"Raid Party has been created, organize in {raid_party_channel.mention}")

        except discord.Forbidden:
                raise commands.BotMissingPermissions(['Manage Channels'])

        raid_party = RaidParty(raid_party_id=raid_party_id, bot=self.bot, guild_id=ctx.guild.id,
                               response_message_id=raid_party_message.id, report_channel_id = ctx.channel.id,
                               channel_id=raid_party_channel.id, author_id=ctx.message.author.id, city=city,
                               timezone=timezone, roster_begins_at=0)
        await raid_party.insert()



    @command(pass_context=True, category='Bot Info', aliases=["raid-city", "rc"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_city(self, ctx, city=None):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        if city is not None:
            if raid_party.is_started_by(ctx.message.author.id) or checks._check_is_moderator(ctx):
                await ctx.channel_profile(channel_id=ctx.message.channel.id, key='city', value=city)
                ChannelMetadata.evict(ctx.channel.id)
            else:
                raise AccessDenied("This operation is allowed only for person who started this raid-party.")

        channel_city = await ChannelMetadata.city(self.bot, ctx.channel.id)

        await Embeds.message(ctx.channel, f"The city for this channel is set to **{channel_city}**.")


    @command(pass_context=True, category='Bot Info', aliases=["raid-over", "raidover"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_over(self, ctx):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        if raid_party.is_started_by(ctx.message.author.id) or checks._check_is_moderator(ctx):
            clean_channel = await Utilities.ask_confirmation(ctx, ctx.message, "Are you sure to delete the channel?", "The channel will be deleted shortly.", "No changes done!", "Request Timed out!")
            if clean_channel:
                try:
                    report_channel, report_message = await ChannelMessage.from_id(ctx.bot, raid_party.report_channel_id, raid_party.response_message_id)
                    expire_msg = f"**This raid party is over!**"
                    await report_message.edit(embed=discord.Embed(description=expire_msg))
                except Exception as error:
                    pass
                await asyncio.sleep(30)
                await ctx.message.channel.delete()
        else:
            raise AccessDenied("This operation is allowed only for person who started this raid-party.")



    @command(pass_context=True, category='Bot Info', aliases=["roster"])
    @raid_checks.raid_party_channel()
    async def cmd_raidparty_roster(self, ctx):
        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        embed = await raid_party.embed()

        return await ctx.channel.send(embed=embed)



    @command(pass_context=True, category='Bot Info', aliases=["rinfo"])
    @raid_checks.raid_party_channel()
    async def cmd_raidparty_info(self, ctx):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)
        await Embeds.message(ctx.channel, json.dumps(raid_party.to_dict(), indent=2))


    @command(pass_context=True, category='Bot Info', aliases=["where"])
    @raid_checks.raid_party_channel()
    async def cmd_raidparty_where(self, ctx, location_number: int = None):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)
        location_number = location_number or raid_party.current_location
        roster_location = raid_party[location_number]
        if roster_location:
            embed = roster_location.raid_location_embed()
            return await ctx.channel.send(embed=embed)

        return await Embeds.error(ctx.channel, f"The roster doesn't have location {location_number}.", user=ctx.message.author)


    @command(pass_context=True, category='Bot Info', aliases=["move"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_party_move(self, ctx):
        try:
            raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

            await raid_party.move()

            success_message = f"{MyEmojis.INFO} Raid party is moving to next location."
            if raid_party.empty:
                success_message = f"{MyEmojis.INFO} The roster has no locations now."

            await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)
        pass


    @command(pass_context=True, category='Bot Info', aliases=["add"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_party_add(self, ctx, *pkmn_location_eta):
        """
        **!add pokemon-or-egg gym-code-or-location eta**
        **Example**
        **!add Pikachu MESC 12:45** - adds Pikachu at MEtallic SCulpture for eta 12:45 to the roster
        **!add egg some-gym** - adds egg at some-gym to the roster
        """
        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        roster_location = await RosterLocation.from_command_text(ctx, ' '.join(pkmn_location_eta))

        if roster_location.poi_location is None:
            raise BadArgument(f"I need a location.")

        await raid_party.append(roster_location)

        success_message = f"{MyEmojis.INFO} Location {raid_party.current_location_index} has been added to the roster."
        await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)


    @command(pass_context=True, category='Bot Info', aliases=["remove"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_party_remove(self, ctx, location_number:int):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        if len(raid_party.roster) <=0 :
            raise BadArgument("Raid party doesn't have any location on the roster.")

        if not raid_party[location_number]:
            raise BadArgument(f"Location {Utilities.emojify_numbers(location_number)} doesn't exist on the roster!")


        del raid_party[location_number]
        await raid_party.update()

        success_message = f"{MyEmojis.INFO} Location {raid_party.current_location_index} has been removed to the roster."
        await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)

    @command(pass_context=True, category='Bot Info', aliases=["reset"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_party_reset(self, ctx):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        if len(raid_party.roster) <=0 :
            raise BadArgument("Raid party doesn't have any location on the roster.")

        reset = await Utilities.ask_confirmation(ctx, ctx.message, "Are you sure to clear the roster?", "The roster will be cleared shortly.", "No changes done!", "Request Timed out!")
        if reset:
            await raid_party.reset()
            success_message = f"{MyEmojis.INFO} The roster has been cleared."
            await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)



    @command(pass_context=True, category='Bot Info', aliases=["update"])
    @raid_checks.raid_party_channel()
    async def cmd_raid_party_update(self, ctx, location_number:int, *pkmn_gym_or_eta):

        raid_party = RaidPartyCog.get_raid_party_for_channel(ctx)

        if len(raid_party.roster) <=0 :
            raise BadArgument("Raid party doesn't have any location on the roster.")

        roster_location = await RosterLocation.from_command_text(ctx, ' '.join(pkmn_gym_or_eta), True)

        if location_number == 0:
            raise BadArgument ("I couldn't understand the location #.")

        if roster_location is None:
            raise BadArgument("I am not sure what to update;... use `!update <location#> <pokemon-name | gym-code | google map link | eta>`")

        if not raid_party[location_number]:
            raise BadArgument(f"Location {Utilities.emojify_numbers(location_number)} doesn't exist on the roster!")


        raid_party[location_number].raid_boss = roster_location.raid_boss or raid_party[location_number].raid_boss
        raid_party[location_number].poi_location = roster_location.poi_location or raid_party[location_number].poi_location
        raid_party[location_number].eta = roster_location.eta or raid_party[location_number].eta
        await raid_party.update()

        success_message = f"{MyEmojis.INFO} Location {location_number} has been updated."
        await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)





    @staticmethod
    async def show_roster_with_message(ctx, message, raid_party):
        embed = await raid_party.embed()
        await ctx.channel.send(content=message, embed=embed)


    @group(pass_context=True, category='Bot Info', aliases=["import"])
    async def _import(self, ctx):

        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")


    @_import.command(aliases=["roster"])
    async def _import_roster(self, ctx):

    # !import roster #channel

        message = ctx.message

        channel_mentions = message.channel_mentions

        if len(channel_mentions) != 1:
            return await self.utilities._send_error_message(ctx.channel, f"correct usage is **!import roster #channel**", user=ctx.message.author)

        roster_from_channel = channel_mentions[0]
        roster = {}

        try:
            roster = copy.deepcopy(ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][roster_from_channel.id]['roster'])
        except Exception as error:
            pass

        if not roster:
            return await self.utilities._send_error_message(ctx.channel, f"no roster found in {roster_from_channel.mention}", user=ctx.message.author)

        change_roster = await self.utilities.ask_confirmation(ctx, message, "Are you sure to replace the current roster?", "Importing the roster..", "No Changes Made.", "Request timed out." )

        if change_roster:
            ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster'] = roster
            return await self.utilities._send_message(ctx.channel, f"roster successfully imported from {roster_from_channel.mention}", user=ctx.message.author)



    @command(pass_context=True, category='Bot Info', aliases=["rosterx"])
    @raid_checks.raid_channel()
    async def _rosterx(self, ctx):

        # message = await self.utilities._send_message(ctx.channel, "New roster under construction.", user=ctx.message.author)

        message = await self.print_roster(ctx, ctx.message)
        description_1 = message.embeds[0].description
        description_2 = "Message 2"


        try:

            await message.add_reaction('\u2b05')
            await message.add_reaction('\u27a1')
            await message.add_reaction('\u23f9')
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

        try:
            is_timed_out = False
            while True:
                reaction, user = await ctx.bot.wait_for('reaction_add', check=(lambda r, u: u.id == ctx.message.author.id and r.message.id == message.id) , timeout=20)

                if reaction.emoji == '\u23f9':
                    await message.remove_reaction(reaction.emoji, user)
                    await message.remove_reaction('\u27a1', ctx.bot.user)
                    await message.remove_reaction('\u2b05', ctx.bot.user)
                    await message.remove_reaction('\u23f9', ctx.bot.user)
                    return
                elif reaction.emoji == '\u2b05':
                    await message.edit(embed=discord.Embed(description=description_1, title=message.embeds[0].title, footer=message.embeds[0].footer ))
                elif reaction.emoji == '\u27a1':
                    await message.edit(embed=discord.Embed(description=description_2))

                await message.remove_reaction(reaction.emoji, user)

        except asyncio.TimeoutError:
            await message.remove_reaction('\u27a1', ctx.bot.user)
            await message.remove_reaction('\u2b05', ctx.bot.user)
            await message.remove_reaction('\u23f9', ctx.bot.user)

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

    async def print_roster(self, ctx, message, roster_message=None):

        roster = ctx.bot.guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster']

        if len(roster) < 1:
            await message.channel.send(content=_(
                "Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
            return

        roster_index = roster[0]['index']

        roster_msg = self.get_roster_with_highlight(roster, roster_index)

        raid_party_image_url = "https://media.discordapp.net/attachments/419935483477622793/450201828802560010/latest.png"

        raid_img_url = raid_party_image_url
        # "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png".format(str(raid_number))

        if roster_index:
            current_roster = roster[0]
            embed_title = _("Raid Party is at Location#{index}. Click here for directions!").format(
                index=self.utilities.emojify_numbers(roster_index))
            raid_party_image_url = current_roster['gmap_link']
        else:
            embed_title = "Raid Party has not started yet!!"
            raid_party_image_url = ""

        raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title),
                                   url=raid_party_image_url, description=roster_msg)
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name),
                              icon_url=message.author.avatar_url)
        raid_embed.set_thumbnail(url=raid_img_url)

        if roster_message:
            return await message.channel.send(
                content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention,
                                                                         roster_message=roster_message),
                embed=raid_embed)
        else:
            return await message.channel.send(
                content=_("Beep Beep! {member} here is the raid party roster: ").format(member=message.author.mention),
                embed=raid_embed)



    def get_roster_with_highlight(self, roster, highlight_roster_loc):
        roster_msg = ""

        try:
            for roster_loc in roster:
                if highlight_roster_loc == roster_loc['index']:
                    marker = "**"
                else:
                    marker = ""
                eta = roster_loc.get('eta', "")
                if eta:
                    eta = " [{eta}]".format(eta=eta)
                else:
                    eta = ""
                if len(roster_msg) > 1900:
                    roster_msg += "\n and more!"
                    break
                else:
                    roster_msg += _("\n{marker1}{number} [{gym}]({link}) - {pokemon}{eta}{marker2}").format(
                        number=self.utilities.emojify_numbers(roster_loc['index']), pokemon=roster_loc['pokemon'].capitalize(),
                        gym=roster_loc['gym_name'], link=roster_loc['gmap_link'], eta=eta, marker1=marker,
                        marker2=marker)

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

        return roster_msg




#

#

# @Clembot.command(pass_context=True, hidden=True)
# @checks.raidpartychannel()
# async def pathshare(ctx):
#     try:
#
#         args = ctx.message.clean_content
#         args_split = args.split()
#         del args_split[0]
#
#         pathshare_url = args_split[0]
#
#         guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['pathshare_url'] = pathshare_url
#         guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['pathshare_user'] = ctx.message.author.id
#
#         await ctx.message.channel.send(_("Beep Beep! Pathshare URL has been set to {url}!".format(url=pathshare_url)))
#     except Exception as error:
#         Logger.info(error)
#
#
#
# @Clembot.command(pass_context=True, hidden=True)
# async def makeitraidparty(ctx):
#     message = ctx.message
#
#     guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id] = {
#         'reportcity': message.channel.id,
#         'trainer_dict': {},
#         'exp': None,  # No expiry
#         'manual_timer': False,
#         'active': True,
#         'raidmessage': None,
#         'type': 'raidparty',
#         'pokemon': None,
#         'egglevel': -1,
#         'suggested_start': False,
#         'roster': [],
#         'roster_index': None,
#         'started_by' : message.author.id
#     }
#
#     await message.channel.send( content=_("Beep Beep! It's a raid party channel now!"))
#
#     return
#
#
# @Clembot.command(pass_context=True, hidden=True)
# @checks.raidpartychannel()
# async def reset(ctx):
#     message = ctx.message
#
#     guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id] = {
#         'reportcity': message.channel.id,
#         'trainer_dict': {},
#         'exp': None,  # No expiry
#         'manual_timer': False,
#         'active': True,
#         'raidmessage': None,
#         'type': 'raidparty',
#         'pokemon': None,
#         'egglevel': -1,
#         'suggested_start': False,
#         'roster': [],
#         'roster_index': None
#     }
#
#     await message.channel.send( content=_("Beep Beep! The roster has been cleared!"))
#
#     return
#
#
#
# @Clembot.command(pass_context=True, category='Bot Info', aliases= ["next"])
# @checks.raidpartychannel()
# async def _next_location(ctx):
#     roster = guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
#
#     if len(roster) < 1:
#         await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
#         return
#     roster_index = roster[0]['index']
#
#     if len(roster) < 2:
#         status_message = _("Raid party is at **{current}/{total}** location. Next location doesn't exist on roster!").format(current=roster_index, total=roster_index)
#         await ctx.message.channel.send( content=_("Beep Beep! {status_message}").format(status_message=status_message))
#         return
#
#     roster_index = roster[1]['index']
#
#     roster_message = _("Raid Party will be headed next to location {location_number} on the roster!").format(location_number=emojify_numbers(roster_index))
#
#     await print_roster_with_highlight(ctx.message, roster_index, roster_message)
#     return
#
