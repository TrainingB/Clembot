import asyncio
import json
import os
import traceback
from datetime import timedelta

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

import clembot.utilities.timezone.timehandler as TH
from clembot.config import config_template
from clembot.config.constants import MyEmojis, Icons
from clembot.core.bot import command, group
from clembot.core.commands import Cog
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.core.utils import notify_for
from clembot.exts.config import channel_checks

from clembot.exts.gymmanager.gym import GymRepository, POILocationConverter
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.exts.pkmn.raid_boss import RaidLevelMaster, RaidLevelConverter
from clembot.exts.pokebattler.pokebattler import PokeBattler
from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.exts.raid import raid_checks
from clembot.exts.raid.errors import NotARaidChannel, NotARaidPartyChannel

from clembot.exts.raid.raid import ChannelMessage, Raid, RaidRepository, DiscordOperations, RemoteRaid
from clembot.utilities.utils import snowflake
from clembot.utilities.utils.argparser import ArgParser
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class RaidTimerTooLongError(ValueError):
    pass


class GuildTimeAdapter:
    GUILD_TIMEZONE = 'America/New_York'
    BOT_TIMEZONE = 'America/Los_Angeles'

    @classmethod
    def get_guild_timezone(cls):
        return cls.BOT_TIMEZONE


class GuildNotificationAdapter:

    @classmethod
    def get_roles_to_notify(cls, guild_id, gym_code):
        role_id_list = []

        return role_id_list


class NoRaidForChannelError(ValueError):
    pass


class RaidCog(commands.Cog):
    active_raids = {}

    def __init__(self, bot):
        self.bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()

        self.ArgParser = ArgParser(bot.dbi)
        self.gymRepository = GymRepository(self._dbi)
        RaidRepository.set_dbi(bot.dbi)

        self.bot.loop.create_task(self.load_raid_reports())

    async def load_raid_reports(self):
        Logger.info("load_raid_reports()")
        await Pokemon.load(self.bot)
        for rcrd in await RaidRepository.find_raids():
            self.bot.loop.create_task(self.load_raid_report(rcrd))


    async def load_raid_report(self, rcrd):
        Logger.info(f"load_raid_report({rcrd.get('raid_id', None)})")
        raid = await Raid.from_db_dict(self.bot, rcrd)
        raid.monitor_task = raid.create_task_tuple(raid.monitor_status())


    raid_SYNTAX_ATTRIBUTE = ['command', 'pkmn', 'gym', 'timer', 'location']
    raidegg_SYNTAX_ATTRIBUTE = ['command', 'egg', 'gym', 'timer', 'location']



    @Cog.listener()
    async def on_command_error(self, ctx, error):
        """Method to handle Cog specific errors"""
        if isinstance(error, NotARaidChannel):
            await Embeds.error(ctx.channel, f'{ctx.prefix}{ctx.invoked_with} can be used in Raid channel.', ctx.message.author)
        elif isinstance(error, NotARaidPartyChannel):
            await Embeds.error(ctx.channel, f'{ctx.prefix}{ctx.invoked_with} can be used in Raid party channel.', ctx.message.author)

    async def expire_raid(self, raid):
        try:
            raid_channel_id, raid_channel = raid.channel_message.channel_id, raid.channel_message.message.channel
            raid_channel_name = raid_channel.name
            Logger.info(f"--- expire_raid({raid.expires_at}) : {raid_channel_name}")

            channel = self.bot.get_channel(raid_channel_id)

            # TODO : Handle if channel is archived!

            if not channel and not self.bot.is_closed():
                # If discord channel is missing, delete the raid.
                try:
                    Logger.info(f"Deleting {raid}")
                    await raid.delete()
                except Exception as error:
                    Logger.error(error)
                return
            else:
                already_expired = not raid.active
                Logger.info(f"Channel expired: {channel.name}")
                if not already_expired:
                    raid.active = False

                if raid.type == "egg":
                    if not already_expired:
                        raid.type = 'raid'
                        await raid_channel.edit(name=raid.channel_name)
                        # TODO: Change channel name
                        # TODO: Send hatch message
                        # TODO: Set new end time, mark raid as active
                        # TODO: Sent expiry message
                        delete_time = raid.expiry_time - TH.current_epoch()
                        pass

                else:
                    if not already_expired:
                        raid.type = 'expired'
                        await raid_channel.edit(name=raid.channel_name)
                        # TODO: Send expired message will be deleted in 5 minutes.
                        delete_time = raid.expiry_time - TH.current_epoch() + timedelta(seconds=45).seconds

                if delete_time:
                    await asyncio.sleep(delete_time)


                if not raid.active and not self.bot.is_closed():
                    try:
                        raid.delete()
                    except Exception as error:
                        Logger.error(f"{traceback.format_exc()}")

                    channel = self.bot.get_channel(raid_channel_id)
                    if channel:
                        await channel.delete()
                        Logger.info(f"Channel deleted: {channel.name}")

        except Exception as error:
            Logger.error(error)


    @command(pass_context=True, hidden=True, aliases=["info"])
    @raid_checks.raid_channel()
    async def cmd_info(self, ctx):

        raid = RaidCog._get_raid_for_channel(ctx)
        await Embeds.message(ctx.channel, f"Reported at: {raid.reported_at} Hatches at: {raid.hatches_at} Expires At: {raid.expires_at}")
        await Embeds.message(ctx.channel, json.dumps(raid.get_raid_dict(), indent=2))


    @command(pass_context=True, category='Bot Info', aliases=["raidegg"])
    @channel_checks.raid_report_enabled()
    async def cmd_raidegg(self, ctx):
        await Embeds.message(ctx.channel,
                             f"Ahh I see you've got some Clembot experience. Things are different now.\nNow you can report either raid or egg both using just `!raid` or `!r`")


    @group(pass_context=True, aliases=["raid", "r"], category='Bot Info')
    @channel_checks.raid_report_enabled()
    async def cmd_raid(self, ctx, pokemon_or_level, *, gym_and_or_time):
        """
        Reports a raid
        **Arguments**
        *pokemon_or_level* - pokemon or level. For pokemon if specifying forms, use - as separator
        *gym_and_or_time* - specify raid location can be a predefined gym code or can be any text to identify the location. You can include minutes remaining as a last parameter.

        **Usage**
        `!raid 4 gym 12` -> reports a level 4 raid at gym and egg will hatch in 12 minutes
        `!raid alola-raichu gym 43` -> reports a absol raid at gym which will expire in 43 minutes
        """

        city = await ctx.city()
        timezone = await ctx.timezone()
        Logger.info(f"cmd_raid({ctx.message.content}) for {city} {timezone}")
        raid_id = next(snowflake.create())

        report_message = f"{ctx.message.channel.id}-{ctx.message.id}"

        dscrd = DiscordOperations(self.bot)
        p_level, p_pkmn, p_timer = None, None, None
        raid_type = "raid"



        p_level = RaidLevelConverter.to_level(pokemon_or_level)

        if p_level is not None:
            raid_type = "egg"
        else:
            p_pkmn = await Pokemon.convert(ctx, pokemon_or_level)
            p_pokeform = await Pokemon.convert(ctx, pokemon_or_level)
            Logger.info(f"{p_pkmn} <=> {p_pokeform}")
            p_level = RaidLevelMaster.get_level(p_pokeform)
            if p_level is None:
                new_raid_boss = f"Last time I checked, **{p_pokeform}** didn't appear as a raid boss. Please contact an admin to add **{p_pokeform}** as a raid-boss. Anyway, what is the raid boss level?"
                reaction_dict = {
                    "1⃣": "1",
                    "2⃣": "2",
                    "3⃣": "3",
                    "4⃣": "4",
                    "5⃣": "5",
                    "🇲" : "M",
                    "🇪" : "E"
                }

                p_level = await Utilities.ask_via_reactions(ctx, ctx.message, new_raid_boss, "Got it!", "I need to know the raid boss level.", "Too late!", reaction_dict, None)
                if not p_level:
                    raise BadArgument("Raid level information not available!")

        if not p_level and not p_pkmn:
            raise BadArgument("Invalid raid level or Pokemon.")

        gym_time_split = gym_and_or_time.split()
        if gym_time_split[-1].isdigit():
            p_timer = int(gym_time_split.pop(-1))

        if len(gym_time_split) == 0:
            raise BadArgument("Raid location is not provided.")

        raid_location = await POILocationConverter.convert_from_text(ctx, " ".join(gym_time_split))

        raid = Raid(raid_id=raid_id, bot=self.bot, guild_id=ctx.guild.id, author_id=ctx.message.author.id,
                    report_message=report_message, raid_type=raid_type, level=p_level, raid_location=raid_location,
                    pkmn=p_pkmn, timer=p_timer, timezone=timezone)

        # create channel
        # respond in new channel that raid has been created
        # respond to raid report saying channel has been created

        new_raid_channel = await dscrd.create_channel(ctx, raid)
        raid.channel_id = new_raid_channel.id

        raid.raid_channel_id = new_raid_channel.id

        message_content = f"{MyEmojis.INFO} Raid reported in {ctx.channel.mention}! Coordinate here!"

        if raid.is_egg:
            raid_embed = await raid.egg_embed()
        else:
            raid_embed = await raid.raid_embed()

            role = await notify_for(self.bot, ctx.guild, raid.raid_boss.id)
            if role:
                message_content = f"{role.mention} raid reported by {ctx.message.author.mention} in {ctx.channel.mention}. Coordinate here!"


        actual_repsonse_message = await ctx.channel.send(content=f"{MyEmojis.INFO} Coordinate the raid in {new_raid_channel.mention}", embed=raid_embed)
        actual_channel_message = await new_raid_channel.send(content=message_content, embed=raid_embed)

        raid.response_message = ChannelMessage.from_message(actual_repsonse_message)
        raid.channel_message = ChannelMessage.from_message(actual_channel_message)

        if p_timer is not None:
            await Embeds.message(new_raid_channel, raid.timer_message)

        if raid_location.is_gym:
            roles_to_notify = [discord.utils.get(ctx.guild.roles, id=role_id)
                               for role_id in GuildNotificationAdapter.get_roles_to_notify(ctx.guild.id,
                                                                                           raid_location.gym.gym_code)]
            # TODO if roles_to_notify send notification


        for emoji in raid.actions :
            await actual_repsonse_message.add_reaction(emoji)
        await actual_channel_message.add_reaction(MyEmojis.POKE_BATTLER)

        await raid.insert()

        # TODO: record raid report for leader-board
        user_guild_profile = await UserGuildProfile.find(self.bot, user_id=ctx.message.author.id, guild_id=ctx.guild.id)
        user_guild_profile.record_report('eggs' if raid.is_egg else 'raids')
        await user_guild_profile.update()

        self.bot.loop.create_task(raid.monitor_status())
        Logger.info(raid)


    @command(pass_context=True, hidden=True, aliases=["record"])
    async def cmd_raid_record(self, ctx, type, leaderboard='lifetime'):
        user_guild_profile = await UserGuildProfile.find(self.bot, user_id=ctx.message.author.id, guild_id=ctx.guild.id)
        user_guild_profile.record_report(type, leaderboard)
        await user_guild_profile.update()

        await Embeds.message(ctx.channel, f"**{leaderboard}** : {user_guild_profile.leaderboard_status(leaderboard)}")





    @command(pass_context=True, aliases=["assume"], category='Bot Info')
    @raid_checks.raid_channel()
    async def cmd_assume(self, ctx, pkmn: Pokemon):
        # validate for assume is allowed or not
        # validate pkmn is a valid pokemon and belongs to egg_level
        # find raid-role from server and send notification

        raid = RaidCog._get_raid_for_channel(ctx)

        if pkmn.id in RaidLevelMaster.get_boss_list(raid.level):
            raid.raid_boss = pkmn
            await raid.update()

            role = await notify_for(self.bot, ctx.guild, pkmn.id)
            if role:
                message_content = f"This egg will be assumed to be {role.mention} when it hatches!"
                await ctx.send(content=message_content)
            else:
                message_content = f'This egg will be assumed to be **{raid.raid_boss}** when it hatches!'
                await Embeds.message(ctx.channel, message_content)
        else:
            err_message = f"**{pkmn.label}** doesn't appear in level {raid.level} raids."
            await Embeds.error(ctx.channel, err_message)


    @staticmethod
    def _get_raid_for_channel(ctx) -> Raid:
        raid = Raid.by_channel.get(ctx.channel.id, None)
        if raid:
            return raid
        else:
            raise NoRaidForChannelError(f"Raid not found for channel {ctx.channel.mention}.")


    @command(pass_context=True, aliases=["timer"], category='Bot Info')
    @raid_checks.raid_channel()
    async def cmd_timer(self, ctx, timer=None):
        """
        Returns/Sets the current timer for the raid

        **Usage:**
        **!timer** - returns the current timer for the raid.
        **!timer min-left** - set the remaining timer for the raid.
        """
        raid = RaidCog._get_raid_for_channel(ctx)
        if timer is None:
            return await Embeds.message(ctx.channel, raid.timer_message)

        if timer.isdigit():
            expire_in_minutes = int(timer)

            if expire_in_minutes > raid.max_timer:
                raise BadArgument(f"You can set timer upto {raid.max_timer} minutes.")
            raid.update_time(TH.current_epoch(second_precision=False) + timedelta(minutes=expire_in_minutes).seconds)
            await raid.update()
            await Embeds.message(ctx.channel, raid.timer_message)
        else:
            # TODO: handle time input?
            await Embeds.error(ctx.channel, f"I couldn't understand the time format. Try again like this: `!timer 10`",
                               user=ctx.message.author)




    @command(pass_context=True, category='Bot Info', aliases=["start"])
    @raid_checks.raid_channel()
    async def cmd_start(self, ctx, *time_as_text):
        """
        Sets up/clears the suggested start time.

        **Usage:**
        **!start HH:MM AM/PM** - suggests a start time for the raid.
        **!start reset** - removes the suggested start time, if any.


        """
        raid = RaidCog._get_raid_for_channel(ctx)
        timezone = await ctx.guild_profile('timezone')

        if time_as_text == "reset":
            raid = RaidCog._get_raid_for_channel(ctx)
            raid.start_time = None
            await raid.update()
            await Embeds.message(ctx.channel, f"Suggested start time has been cleared.")

        else:
            start_time = TH.convert_to_timestamp(" ".join(time_as_text), timezone)

            if not start_time:
                return await Embeds.error(ctx.channel, "I couldn't understand time format. Try again like this: `!start HH:MM AM/PM`")

            raid.start_time = start_time
            await raid.update()
            await Embeds.message(ctx.channel, f"suggested start time as **{raid.starts_at}**.", user=ctx.message.author)






    @group(pass_context=True, category='Bot Info', aliases=["boss"])
    @raid_checks.raid_channel()
    async def cmd_boss(self, ctx, boss: Pokemon):
        raid = RaidCog._get_raid_for_channel(ctx)

        if TH.is_in_future(raid.hatch_time):
            return await Embeds.error(ctx.channel, f"Please wait until the egg has hatched before changing it to an open raid!",
                                      user=ctx.message.author)

        if raid.pkmn:
            return await Embeds.error(ctx.channel, f"Raid boss has already been assigned to this channel.",
                                      user=ctx.message.author)

        await raid.report_hatch(boss)

    @group(pass_context=True, category='Bot Info', aliases=["change"])
    @raid_checks.raid_channel()
    async def cmd_change(self, ctx):
        """
        Changes raid-level/raid-boss/gym for a raid.
        **Usgae:**

        **!change raid 4** - changes the raid channel status to egg with raid level 4
        **!change raid pokemon** - changes the current raid-boss in the raid channel.
        **!change gym gym-code** - changes the gym in the raid channel.
        """

        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                return await Embeds.message(ctx.channel, f"Use **help change** to see the usage.")


    @cmd_change.command(pass_context=True, category='Bot Info', aliases=["raid"])
    @raid_checks.raid_channel()
    @wrap_error
    async def cmd_change_raid(self, ctx, pokemon_or_level):
        """
        Changes the raid level or raid boss for the current raid.

        **Usgae:**

        **!change-raid 4** - changes the raid channel status to egg with raid level 4
        **!change-raid pokemon** - changes the current raid-boss in the raid channel.

        **Note:**  Use **!timer** to check/set the time remaining correctly.
        """
        raid = RaidCog._get_raid_for_channel(ctx)

        p_level = None
        p_pkmn = None
        if pokemon_or_level.isdigit():
            p_level = int(pokemon_or_level)
            if p_level < 1 or p_level > 5:
                raise BadArgument("Invalid raid level")
            raid.raid_type = "egg"
            raid.level = p_level
            raid.pkmn = None

        else:
            p_pkmn = await Pokemon.convert(ctx, pokemon_or_level)
            if p_pkmn:
                raid.pkmn = p_pkmn
                raid.raid_type = "raid"
                raid.level = RaidLevelMaster.get_level(p_pkmn)
                raid.raid_level_info = RaidLevelMaster.from_cache(p_level)
                # set hatch_time just in case.
                raid.hatch_time = raid.hatch_time or raid.expiry_time - timedelta(minutes=(config_template.development_timer or self.raid_level_info.egg_timer)).seconds

        if p_level or p_pkmn:
            if raid.poke_battler_id is not None:
                PokeBattler.update_raid_party(raid.poke_battler_id, PokeBattler.pb_raid_level(raid.level), raid.pkmn.pokemon_form_id if raid.pkmn is not None else None)

            await raid.update()
            await Embeds.message(ctx.channel, "The raid has been updated.\n Use `!timer` to check/set the timer if needed.")
        else:
            raise BadArgument("Invalid raid level or Pokemon.")


    @cmd_change.command(pass_context=True, category='Bot Info', aliases=["gym"])
    @raid_checks.raid_channel()
    @wrap_error
    async def cmd_change_gym(self, ctx, location: POILocationConverter):
        """
        Changes the gym for the raid channel

        **Usage:**
        **!change gym gym-code**
        """
        raid = RaidCog._get_raid_for_channel(ctx)

        raid.raid_location = location
        await raid.update()
        await Embeds.message(ctx.channel, f"Raid location has been updated.")



    @command(pass_context=True, category='Bot Info', aliases=["raids"])
    @channel_checks.raid_report_enabled()
    async def cmd_raids(self, ctx):

        list_of_raid_id = await RaidRepository.find_raids_reported_in_channel(self.bot, ctx.message.channel.id)


        list_of_raid_detail = []

        if len(list_of_raid_id) > 0:
            for raid_id in list_of_raid_id:
                raid = await Raid.from_cache(ctx, raid_id)
                list_of_raid_detail.append(f"{raid.summary}")
        else:
            list_of_raid_detail.append("No active raid report(s).")

        raid_list_msg = await ctx.send(embed=Embeds.make_embed(header="Current Raid(s):", content="\n\n".join(list_of_raid_detail), msg_color=ctx.message.author.color))
        await raid_list_msg.add_reaction('🗑️')


    @command(pass_context=True, hidden=True, aliases=["refresh-raid"])
    @raid_checks.raid_channel()
    async def cmd_raid_refresh(self, ctx):
        raid = RaidCog._get_raid_for_channel(ctx)

        chm_channel, chm_message = await ChannelMessage.from_text(self.bot, raid.channel_message)
        if chm_channel and chm_channel.name != raid.channel_name:
            try:
                Logger.info("updating channel name")
                await chm_channel.edit(name=raid.channel_name)
                Logger.info("updated channel name")
            except Exception as error:
                Logger.error(error)

        await Embeds.message(ctx.channel,"The raid has been updated.")



    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """If user reacted 🗑 where I added 🗑 already, delete the message."""
        Logger.info(f"{str(payload.emoji)} added by {payload.member.nick}")
        if payload.user_id == self.bot.user.id:
            return

        emoji = str(payload.emoji)
        if emoji == MyEmojis.TRASH:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            payload_reaction = next(filter(lambda r: (r.emoji == payload.emoji.name), message.reactions), None)
            if payload_reaction and payload_reaction.me:
                await message.delete()

        if emoji == MyEmojis.POKE_BATTLER:
            try:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                payload_reaction = next(filter(lambda r: (r.emoji.id == payload.emoji.id), message.reactions), None)
                if payload_reaction and payload_reaction.me:

                    raid = Raid.by_message_id.get(message.id)
                    if raid is not None:
                        # create PBRP if already not present
                        if raid.poke_battler_id is None:
                            pb_raid_id = PokeBattler.create_raid_party(PokeBattler.pb_raid_level(raid.level), raid.pkmn.pokemon_form_id if raid.pkmn is not None else None)
                            raid.poke_battler_id = pb_raid_id
                            await raid.update()

                        # add the user to the raid party
                        user = self.bot.get_user(payload.user_id)
                        PokeBattler.add_user_to_raid_party(raid.poke_battler_id, user)
                        await Embeds.message(raid.channel, f"{user.display_name} has joined pokebattler raid party [#{raid.poke_battler_id}]({PokeBattler.get_raid_party_url(raid.poke_battler_id)}).", icon=MyEmojis.POKE_BATTLER)
            except Exception as error:
                Logger.info(f"{error}")
                
        if emoji == MyEmojis.REMOTE:
            
            try:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                payload_reaction = next(filter(lambda r: (r.emoji.id == payload.emoji.id), message.reactions), None)
                if payload_reaction and payload_reaction.me:
        
                    raid = Raid.by_message_id.get(message.id)
                    if raid is not None:
                        # add the user to the raid party
                        # user = self.bot.get_user(payload.user_id)
                        await raid.add_rsvp(member_id=payload.user_id, status='ir', count=1)
                        chnl, msg = await ChannelMessage.from_text(self.bot, raid.channel_message)
                        await raid.send_remote_rsvp_embed(msg, "")
                        
            except Exception as error:
                print(error)
                pass



    @command(pass_context=True, hidden=True)
    async def embed(self, ctx, header=None, title=None, content=None,
                    header_icon=None):
        """Build and post an embed in the current channel.

        Note: Always use quotes to contain multiple words within one argument.
        """
        try:
            embed = Embeds.make_embed(header=header, header_icon=header_icon, title=title, content=content)

            await ctx.send(embed=embed)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @group(pass_context=True, hidden=True, aliases=["clean-up"])
    async def cmd_clean(self, ctx):

        query = self._dbi.table("raid_report").query().where(guild_id=ctx.guild.id).order_by("raid_report_id", True)

        results = await query.getjson()

        for raid in results:
            channel_id = raid['channel_id']

            channel = discord.utils.get(ctx.guild.channels, id=channel_id)
            if channel:
                print(f"{channel.name} ({channel_id})")
                await channel.delete()


    @group(pass_context=True, category='Bot Info', aliases=["weather"])
    async def cmd_weather(self, ctx):
        """
        Provides a list of support weather values
        """
        additional_fields = {
            'Supported Weather Values' : [False, f'**{", ".join(self.weather_list)}**']
        }

        embed = Embeds.make_embed(header="Weather", fields=additional_fields)
        return await ctx.send(embed=embed)


    @command(pass_context=True, category='Bot Info', aliases=["counters"])
    @raid_checks.raid_channel()
    async def cmd_counters(self, ctx, *, args=None):
        """Simulate a Raid battle with Pokebattler. Only usable in raid channels. Uses current boss if not provided.

        **Usage:**

        **!counters** - fetches the raid counters for current raid boss in channel.
        **!counters [weather]** - fetches weather optimized raid counters.

        If the egg isn't hatched you can use:

        **!counters [pokemon] [weather]**

        See **!weather** for acceptable values for weather.
        """
        # If [user] is a valid Pokebattler user id, Clembot will simulate the Raid with that user's Pokebox.
        #         and weather by default.

        raid = RaidCog._get_raid_for_channel(ctx)
        pkmn = None
        weather = None
        if args:
            args_split = args.split(" ")

            pkmn = Pokemon.to_pokemon(args_split[0]) if len(args_split) >= 1 else None

            if pkmn is None:
                weather = args_split[0] if len(args_split) >= 1 else None
            else:
                weather = args_split[1] if len(args_split) >=2 else None


        if pkmn is None:
            if raid.is_egg:
                raise BadArgument("Enter a pokemon which appears in raids, or wait for this egg to hatch.")
            else:
                pkmn = raid.raid_boss

        await self.fetch_counters(ctx, pkmn.id, raid.level, weather=weather)

    weather_list = ['none', 'extreme', 'clear', 'sunny', 'rainy', 'partlycloudy', 'cloudy', 'windy', 'snowy', 'foggy']

    async def fetch_counters(self, ctx, pkmn, level, user=None, weather=None):

        img_url = Pokemon.to_pokemon(pkmn).preview_url

        url = f"https://fight.pokebattler.com/raids/defenders/{pkmn.replace('-', '_').upper()}/levels/{PokeBattler.pb_raid_level(level)}/attackers/"
        if user:
            url += "users/{user}/".format(user=user)
            userstr = "user #{user}'s".format(user=user)
        else:
            url += "levels/30/"
            userstr = "Level 30"
        if not weather:
            weather = "NO_WEATHER"
        else:

            match_list = ['NO_WEATHER', 'NO_WEATHER', 'CLEAR', 'CLEAR', 'RAINY',
                          'PARTLY_CLOUDY', 'OVERCAST', 'WINDY', 'SNOW', 'FOG']
            index = self.weather_list.index(weather)
            weather = match_list[index]
        url += "strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=OVERALL&"
        url += "weatherCondition={weather}&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE".format(
            weather=weather)
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    data = await resp.json()

            title_url = url.replace('https://fight', 'https://www')
            colour = ctx.guild.me.colour
            hyperlink_icon = 'https://i.imgur.com/fn9E5nb.png'
            pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'
            data = data['attackers'][0]
            raid_cp = data['cp']
            atk_levels = '30'
            ctrs = data['randomMove']['defenders'][-6:]
            index = 1

            def clean(txt):
                return txt.replace('_', ' ').title()

            title = '{pkmn} | {weather}'.format(pkmn=pkmn.title(), weather=clean(weather))
            stats_msg = "**CP:** {raid_cp}\n".format(raid_cp=raid_cp)
            stats_msg += "**Weather:** {weather}\n".format(weather=clean(weather))
            stats_msg += "**Attacker Level:** {atk_levels}".format(atk_levels=atk_levels)
            ctrs_embed = discord.Embed(colour=colour)
            ctrs_embed.set_author(name=title, url=title_url, icon_url=hyperlink_icon)
            ctrs_embed.set_thumbnail(url=img_url)
            ctrs_embed.set_footer(text='Results courtesy of Pokebattler', icon_url=pbtlr_icon)
            for ctr in reversed(ctrs):
                ctr_name = clean(ctr['pokemonId'])
                moveset = ctr['byMove'][-1]
                moves = "{move1} | {move2}".format(move1=clean(moveset['move1'])[:-5], move2=clean(moveset['move2']))
                name = "#{index} - {ctr_name}".format(index=index, ctr_name=ctr_name)
                ctrs_embed.add_field(name=name, value=moves)
                index += 1
            ctrs_embed.add_field(name="Results with {userstr} attackers".format(userstr=userstr),
                                 value="[See your personalized results!](https://www.pokebattler.com/raids/{pkmn})".format(
                                     pkmn=pkmn.replace('-', '_').upper()))
            await ctx.channel.send(embed=ctrs_embed)


    @group(pass_context=True, category='Bot Info', aliases=["nest"])
    @channel_checks.nest_report_enabled()
    async def cmd_nest(self, ctx, pokemon: Pokemon, *location_args):
        """
        !nest chimchar MESC
        !nest pikachu somewhere closer
        !nest aron some park http://google-url.com
        """

        message = ctx.message
        if len(location_args) > 0:
            nest_location = await POILocationConverter.convert_from_text(ctx, *location_args)
        else:
            return await Embeds.error(ctx.channel, f"The correct usage are: ```!nest pokemon location```", user = ctx.message.author)
        Logger.info(f"{ctx.message.content} => {pokemon} | {nest_location.gym_embed_label} ")

        # await EmbedUtil.message(ctx.channel, f"{pokemon} | {nest_location.embed_label}")

        embed_title = ":map: **A new nest has been reported!**"
        raid_img_url = pokemon.preview_url

        # embed_desription = _("**Pokemon :** {pokemon}\n**Nest Reported at :** {location}\n").format(pokemon=pokemon.label.capitalize(), location=nest_location.name)

        nest_embed = discord.Embed(title=embed_title, description="", colour=discord.Colour.gold(), timestamp=TH.datetime.utcnow())

        nest_embed.add_field(name="**Pokemon**", value=pokemon.label, inline=True)
        nest_embed.add_field(name="**Where**", value=nest_location.gym_embed_label, inline=True)
        nest_embed.set_thumbnail(url=raid_img_url)
        # hide_preview = not nest_location.is_gym or await ctx.guild_profile('hide-nest-preview') == 'true'
        # if not hide_preview:
        #     nest_embed.set_image(url=nest_location.google_preview_url)
        nest_embed.set_footer(text=f"Reported by {message.author.display_name}", icon_url=Icons.avatar(message.author))
        await ctx.channel.send(embed=nest_embed)
        await asyncio.sleep(15)
        await ctx.message.delete()


    @command(pass_context=True, hidden=True, aliases=["set-gym"])
    @raid_checks.raid_channel()
    async def cmd_set_gym(self, ctx, location: POILocationConverter):
        """
        Changes the gym for the raid channel

        **Usage:**
        **!set-gym gym-code**
        """
        raid = RaidCog._get_raid_for_channel(ctx)

        raid.raid_location = location
        await raid.update()
        await Embeds.message(ctx.channel, f"Raid location has been updated.")


    @command(pass_context=True, hidden=True, aliases=["change-raid"])
    @raid_checks.raid_channel()
    async def cmd_change_raid_old(self, ctx, pokemon_or_level):
        """
        Changes the raid level or raid boss for the current raid.

        **Usgae:**

        **!change-raid 4** - changes the raid channel status to egg with raid level 4
        **!change-raid pokemon** - changes the current raid-boss in the raid channel.

        **Note:**  Use **!timer** to check/set the time remaining correctly.
        """
        raid = RaidCog._get_raid_for_channel(ctx)

        p_level = None
        p_pkmn = None
        if pokemon_or_level.isdigit():
            p_level = int(pokemon_or_level)
            if p_level < 1 or p_level > 5:
                raise BadArgument("Invalid raid level")
            raid.raid_type = "egg"
            raid.level = p_level
            raid.pkmn = None

        else:
            p_pkmn = await Pokemon.convert(ctx, pokemon_or_level)
            if p_pkmn:
                raid.pkmn = p_pkmn
                raid.raid_type = "raid"
                raid.level = RaidLevelMaster.get_level(p_pkmn)
                raid.raid_level_info = RaidLevelMaster.from_cache(p_level)
                # set hatch_time just in case.
                raid.hatch_time = raid.hatch_time or raid.expiry_time - timedelta(minutes=(config_template.development_timer or self.raid_level_info.egg_timer)).seconds

        if p_level or p_pkmn:
            if raid.poke_battler_id is not None:
                PokeBattler.update_raid_party(raid.poke_battler_id, PokeBattler.pb_raid_level(raid.level), raid.pkmn.pokemon_form_id if raid.pkmn is not None else None)

            await raid.update()
            await Embeds.message(ctx.channel, "The raid has been updated.\n Use `!timer` to check/reset the timer if needed.")
        else:
            raise BadArgument("Invalid raid level or Pokemon.")


    @command(pass_context=True, hidden=True, category='Bot Info', aliases=["timerset"])
    @raid_checks.raid_channel()
    async def cmd_timerset(self, ctx, timer):

        raid = RaidCog._get_raid_for_channel(ctx)


        if timer.isdigit():
            expire_in_minutes = int(timer)

            if expire_in_minutes > raid.max_timer:
                raise BadArgument(f"You can set timer upto {raid.max_timer} minutes.")
            raid.update_time(TH.current_epoch(second_precision=False) + timedelta(minutes=expire_in_minutes).seconds)
            await raid.update()
            await Embeds.message(ctx.channel, raid.timer_message)
        else:
            # TODO: handle time input?
            await Embeds.error(ctx.channel, f"I couldn't understand the time format. Try again like this: `!timer 10`",
                               user=ctx.message.author)
    
    
    @group(pass_context=True, aliases=["remote", "rr"], category='Bot Info')
    @channel_checks.raid_report_enabled()
    async def cmd_remote_raid(self, ctx, pokemon_or_level, time_remaining=None):
        """
        Reports a raid
        **Arguments**
        *pokemon_or_level* - pokemon or level. For pokemon if specifying forms, use - as separator
        *gym_and_or_time* - specify raid location can be a predefined gym code or can be any text to identify the location. You can include minutes remaining as a last parameter.
    
        **Usage**
        `!raid 4 gym 12` -> reports a level 4 raid at gym and egg will hatch in 12 minutes
        `!raid alola-raichu gym 43` -> reports a absol raid at gym which will expire in 43 minutes
        """
        
        city = await ctx.city()
        timezone = await ctx.timezone()
        Logger.info(f"cmd_raid({ctx.message.content}) for {city} {timezone}")
        raid_id = next(snowflake.create())
        
        report_message = f"{ctx.message.channel.id}-{ctx.message.id}"
        
        dscrd = DiscordOperations(self.bot)
        p_level, p_pkmn, p_timer = None, None, None
        raid_type = "raid"
        
        p_level = RaidLevelConverter.to_level(pokemon_or_level)
        
        if p_level is not None:
            raid_type = "egg"
        else:
            p_pkmn = await Pokemon.convert(ctx, pokemon_or_level)
            p_pokeform = await Pokemon.convert(ctx, pokemon_or_level)
            Logger.info(f"{p_pkmn} <=> {p_pokeform}")
            p_level = RaidLevelMaster.get_level(p_pokeform)
            if p_level is None:
                new_raid_boss = f"Last time I checked, **{p_pokeform}** didn't appear as a raid boss. Please contact an admin to add **{p_pokeform}** as a raid-boss. Anyway, what is the raid boss level?"
                reaction_dict = {
                    "1⃣": "1",
                    "2⃣": "2",
                    "3⃣": "3",
                    "4⃣": "4",
                    "5⃣": "5",
                    "🇲": "M",
                    "🇪": "E"
                }
                
                p_level = await Utilities.ask_via_reactions(ctx, ctx.message, new_raid_boss, "Got it!",
                                                            "I need to know the raid boss level.", "Too late!",
                                                            reaction_dict, None)
                if not p_level:
                    raise BadArgument("Raid level information not available!")
        
        if not p_level and not p_pkmn:
            raise BadArgument("Invalid raid level or Pokemon.")
        
        
        if time_remaining and time_remaining.isdigit():
            p_timer = int(time_remaining)
        
        
        raid = RemoteRaid(raid_id=raid_id, bot=self.bot, guild_id=ctx.guild.id, author_id=ctx.message.author.id,
                    report_message=report_message, raid_type=raid_type, level=p_level,
                    pkmn=p_pkmn, timer=p_timer, timezone=timezone)
        
        # create channel
        # respond in new channel that raid has been created
        # respond to raid report saying channel has been created
        
        new_raid_channel = await dscrd.create_private_channel(ctx, raid)
        raid.channel_id = new_raid_channel.id
        
        raid.raid_channel_id = new_raid_channel.id
        
        message_content = f"{MyEmojis.INFO} Raid reported! Coordinate here!"
        
        if raid.is_egg:
            raid_embed = await raid.egg_embed()
        else:
            raid_embed = await raid.raid_embed()
            
            role = await notify_for(self.bot, ctx.guild, raid.raid_boss.id)
            if role:
                message_content = f"{role.mention} raid reported by {ctx.message.author.mention} in {ctx.channel.mention}. Coordinate here!"
        
        actual_repsonse_message = await ctx.channel.send(
            content=f"{MyEmojis.INFO} Tap {MyEmojis.REMOTE} if you are interested in remote invite (first 5 only).", embed=raid_embed)
        actual_channel_message = await new_raid_channel.send(content=message_content, embed=raid_embed)
        
        raid.response_message = ChannelMessage.from_message(actual_repsonse_message)
        raid.channel_message = ChannelMessage.from_message(actual_channel_message)
        
        if p_timer is not None:
            await Embeds.message(new_raid_channel, raid.timer_message)
        
        for emoji in raid.actions:
            await actual_repsonse_message.add_reaction(emoji)
        await actual_channel_message.add_reaction(MyEmojis.POKE_BATTLER)
        
        await raid.insert()
        
        # TODO: record raid report for leader-board
        user_guild_profile = await UserGuildProfile.find(self.bot, user_id=ctx.message.author.id, guild_id=ctx.guild.id)
        user_guild_profile.record_report('eggs' if raid.is_egg else 'raids')
        await user_guild_profile.update()
        
        self.bot.loop.create_task(raid.monitor_status())
        Logger.info(raid)


def main():
    pass



if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")

