import asyncio
import copy
import json

import discord
from discord.ext import commands

from clembot.core import checks
from clembot.core.logs import Logger
from clembot.exts.pkmn.pokemon import PokemonCache
from clembot.exts.raid.raid import RaidRepository, RaidParty, RosterLocation
from clembot.exts.raid.raid_cog import NoRaidForChannelError
from clembot.utilities.utils import snowflake
from clembot.utilities.utils.embeds import Embeds, Emojis
from clembot.utilities.utils.utilities import Utilities


class RaidPartyCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()

        self.bot.loop.create_task(self.pickup_raidpartydata())


    async def pickup_raidpartydata(self):
        Logger.info("pickup_raidpartydata()")

        await PokemonCache.load_cache_from_dbi(self.bot.dbi)
        for rcrd in await RaidRepository.find_raid_parties():
            self.bot.loop.create_task(self.pickup_raidparty(rcrd))


    async def pickup_raidparty(self, rcrd):
        Logger.info(f"pickup_raidparty({rcrd.get('raid_party_id', None)})")
        raid_party = await RaidParty.from_db_dict(self.bot, rcrd)
        print(raid_party);
        # raid.monitor_task = raid.create_task_tuple(raid.monitor_status())

    @staticmethod
    def _get_raid_for_channel(ctx) -> RaidParty:
        raid_party = RaidParty.by_channel.get(ctx.channel.id, None)
        if raid_party is not None:
            return raid_party
        else:
            raise NoRaidForChannelError(f"Raid not found for channel {ctx.channel.mention}.")


    @commands.group(pass_context=True, hidden=True, aliases=["raidparty", "rp", "raid-party"])
    async def cmd_raidparty(self, ctx, party_title):
        """

        :param ctx:
        :param pokemon:
        :return:
        """

        city = await ctx.guild_metadata(key='city')
        timezone = await ctx.guild_metadata(key='timezone')
        raid_party_id = next(snowflake.create())

        try:
            raid_party_channel = await ctx.guild.create_text_channel(party_title, overwrites=dict(ctx.channel.overwrites),
                                                category=ctx.guild.get_channel(ctx.channel.category_id))
        except discord.Forbidden:
                raise commands.BotMissingPermissions(['Manage Channels'])

        raid_party = RaidParty(raid_party_id=raid_party_id, bot=self.bot, guild_id=ctx.guild.id,
                               channel_id=raid_party_channel.id, author_id=ctx.message.author.id, city=city,
                               timezone=timezone, roster_begins_at=0)
        await raid_party.insert()
        await Embeds.message(ctx.channel, f"Raid Party has been created, organize in {raid_party_channel.mention}")


        Logger.info(raid_party)


    @commands.command(pass_context=True, hidden=True, aliases=["roster"])
    async def cmd_raidparty_roster(self, ctx):
        try:
            raid_party = RaidPartyCog._get_raid_for_channel(ctx)

            embed = await raid_party.embed()

            return await ctx.channel.send(embed=embed)

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)
        pass

    @commands.command(pass_context=True, hidden=True, aliases=["rinfo"])
    async def cmd_raidparty_info(self, ctx):
        try:
            raid_party = RaidPartyCog._get_raid_for_channel(ctx)
            await Embeds.message(ctx.channel, json.dumps(raid_party.to_dict(), indent=2))

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)
        pass

    @commands.command(pass_context=True, hidden=True, aliases=["where"])
    async def cmd_raidparty_where(self, ctx, location_number: int):
        try:
            raid_party = RaidPartyCog._get_raid_for_channel(ctx)
            roster_location = raid_party[location_number]
            if roster_location:
                embed = roster_location.raid_location_embed()
                return await ctx.channel.send(embed=embed)

            return await Embeds.error(ctx.channel, f"The roster doesn't have location {location_number}.", user=ctx.message.author)


        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)
        pass

    @commands.command(pass_context=True, hidden=True, aliases=["move"])
    async def cmd_raidparty_move(self, ctx):
        try:
            raid_party = RaidPartyCog._get_raid_for_channel(ctx)

            await raid_party.move()

            success_message = f"{Emojis.info} Raid party is moving to next location."
            await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)
        pass


    @commands.command(pass_context=True, hidden=True, aliases=["add"])
    async def cmd_raidparty_add(self, ctx):
        try:
            raid_party = RaidPartyCog._get_raid_for_channel(ctx)

            city = await ctx.channel_setting(ctx.channel.id, 'city')
            if city is None:
                city = raid_party.city
                await Embeds.message(ctx.channel, f"The city for this channel is set to {city}")
                await ctx.channel_setting(ctx.channel.id, 'city', city)

            roster_location = await RosterLocation.from_command_text(ctx, ctx.message.content)
            await raid_party.append(roster_location)

            success_message = f"{Emojis.info} Location {raid_party.current_location_index} has been added to the roster."
            await RaidPartyCog.show_roster_with_message(ctx, success_message, raid_party)

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @staticmethod
    async def show_roster_with_message(ctx, message, raid_party):
        embed = await raid_party.embed()
        await ctx.channel.send(content=message, embed=embed)


    @commands.group(pass_context=True, hidden=True, aliases=["import"])
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



    @commands.command(pass_context=True, hidden=True, aliases=["rosterx"])
    @checks.raidpartychannel()
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
            print(error)

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
            print(error)

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
            print(error)

        return roster_msg

    beep_notes = ("""**{member}** here are the commands for trade management. 

**!trade offer <pokemon>** - to add pokemon to your offers list.
**!trade request <pokemon>** - to add pokemon to your requests list.

**!trade clear <pokemon>** - to remove pokemon from your trade offer or request list.
**!trade clear all** - to clear your trade offer and request list.

**!trade list** - brings up pokemon in your trade offer/request list.
**!trade list @user** - brings up pokemon in user's trade offer/request list.
**!trade list pokemon** - filters your trade offer/request list by sepcified pokemon.

**!trade search <pokemon>** - brings up a list of 10 users who are offering pokemon with their pokemon request as well.

**<pokemon> - can be one or more pokemon or pokedex# separated by space.**

""")

    def get_beep_embed(self, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - Trade Management", description=self.beep_notes.format(member=ctx.message.author.display_name), footer=footer))

#
# @Clembot.command(pass_context=True, hidden=True)
# @checks.raidpartychannel()
# async def raidover(ctx):
#
#     try:
#         channel = ctx.message.channel
#         message = ctx.message
#         started_by = guild_dict[message.guild.id]['raidchannel_dict'][channel.id]['started_by']
#
#         if ctx.message.author.id == started_by:
#
#             clean_channel = await ask_confirmation(ctx.message, "Are you sure to delete the channel?", "The channel will be deleted shortly.", "No changes done!", "Request Timed out!")
#             if clean_channel:
#                 await asyncio.sleep(30)
#                 try:
#                     report_channel = Clembot.get_channel(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['reportcity'])
#                     reportmsg = await report_channel.fetch_message(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['raidreport'])
#                     expiremsg = _("**This raidparty is over!**")
#                     await reportmsg.edit(embed=discord.Embed(description=expiremsg, colour=channel.guild.me.colour))
#                 except Exception as error:
#                     pass
#                 await ctx.message.channel.delete()
#
#
#         else:
#             await _send_error_message(channel, _("Beep Beep! Only raid reporter can clean up the channel!"))
#     except Exception as error:
#         Logger.info(error)
#
#
# @Clembot.command(pass_context=True, hidden=True)
# @checks.raidpartychannel()
# async def update(ctx):
#     try:
#         roster = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
#         if len(roster) <= 0:
#             await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
#             return
#
#         args = ctx.message.clean_content[len("!update"):]
#         args_split = args.lower().split()
#
#         location_number = 0
#         if len(args_split) > 0:
#             if args_split[0].isdigit():
#                 location_number = int(args_split[0])
#
#         if location_number == 0:
#             await ctx.message.channel.send( content=_("Beep Beep! I couldn't understand the location #."))
#             return
#
#         del args_split[0]
#
#         roster_loc = None
#         for roster_loc_at in roster:
#             if roster_loc_at['index'] == location_number:
#                 roster_loc = roster_loc_at
#                 break
#
#         if roster_loc is None:
#             await ctx.message.channel.send( content=_("Beep Beep! Location {location} doesn't exist on the roster!".format(location=emojify_numbers(location_number))))
#             return
#
#         # if len(args_split) > 1:
#         #     await ctx.message.channel.send( content=_("Beep Beep! That's too much to update... use `!update <location#> <pokemon-name or gymmanager-code or google map link>`"))
#         #     return
#
#         arg = args_split[0].lower()
#         # gym_info = gymutil.get_gym_info(arg, city_state=get_city_list(ctx.message))
#         gym = await get_gym_info_wrapper(ctx.message, gym_code=arg)
#
#         if gym:
#             roster_loc['gym_name'] = gym.gym_name
#             roster_loc['gym_code'] = gym.gym_code
#             roster_loc['lat_long'] = f"{gym.latitude},{gym.longitude}"
#             roster_loc['gmap_link'] = gym.gym_url
#             roster_loc['eta'] = None
#             args_split.remove(arg.lower())
#
#         elif arg in pkmn_info['pokemon_list']:
#             roster_loc['pokemon'] = arg
#             args_split.remove(arg.lower())
#         else:
#             gmap_link = extract_link_from_text("".join(args_split))
#             if gmap_link:
#                 roster_loc['gmap_link'] = gmap_link
#                 roster_loc['gym_name'] = "location " + str(roster_loc['index'])
#                 roster_loc['gym_code'] = "location " + str(roster_loc['index'])
#                 roster_loc['lat_long'] = extract_lat_long_from(gmap_link)
#             else:
#                 time_as_text = " ".join(args_split)
#                 eta = convert_into_time(time_as_text, False)
#                 if eta:
#                     roster_loc['eta'] = time_as_text
#                 else:
#                     await ctx.message.channel.send( content=_("Beep Beep! I am not sure what to update;... use `!update <location#> <pokemon-name | gym-code | google map link | eta>` "))
#                     return
#
#         await print_roster_with_highlight(ctx.message, location_number, "Beep Beep! Location {location} has been updated.".format(location=emojify_numbers(location_number)))
#         return
#
#     except Exception as error:
#         await ctx.message.channel.send( content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))
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
# @Clembot.command(pass_context=True, hidden=True, aliases= ["next"])
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
