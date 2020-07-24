import asyncio
import json
import os
import traceback
from datetime import timedelta

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

import clembot.utilities.timezone.timehandler as TH
from clembot.config.constants import MyEmojis, Icons
from clembot.core.bot import command, group
from clembot.core.commands import Cog
from clembot.core.logs import Logger
from clembot.exts.gymmanager.gym import GymRepository, POILocationConverter
from clembot.exts.pkmn.raid_boss import RaidMaster, Pokemon
from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.exts.raid import raid_checks
from clembot.exts.raid.errors import NotARaidChannel, NotARaidReportChannel
from clembot.exts.raid.raid import ChannelMessage, Raid, RaidRepository, DiscordOperations
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
    """
    Loads Raid Manager Code
    """

    active_raids = {}

    def __init__(self, bot):
        self.bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()

        self.ArgParser = ArgParser(bot.dbi)
        self.gymRepository = GymRepository(self._dbi)
        RaidRepository.set_dbi(bot.dbi)

        self.bot.loop.create_task(self.pickup_raiddata())

    async def pickup_raiddata(self):
        Logger.info("pickup_raiddata()")
        await Pokemon.load(self.bot)
        for rcrd in await RaidRepository.find_raids():
            self.bot.loop.create_task(self.pickup_raid(rcrd))


    async def pickup_raid(self, rcrd):
        Logger.info(f"pickup_raid({rcrd.get('raid_id', None)})")
        raid = await Raid.from_db_dict(self.bot, rcrd)
        raid.monitor_task = raid.create_task_tuple(raid.monitor_status())


    raid_SYNTAX_ATTRIBUTE = ['command', 'pkmn', 'gym', 'timer', 'location']
    raidegg_SYNTAX_ATTRIBUTE = ['command', 'egg', 'gym', 'timer', 'location']



    @Cog.listener()
    async def on_command_error(self, ctx, error):
        """Method to handle Cog specific errors"""
        if isinstance(error, NotARaidChannel):
            await Embeds.error(ctx.channel, f'{ctx.prefix}{ctx.invoked_with} can be used in Raid Channel.', ctx.message.author)
        elif isinstance(error, NotARaidReportChannel):
            await Embeds.error(ctx.channel, f'Raid Reports are disabled in current channel.', ctx.message.author)


    async def expire_raid(self, raid):
        """
        Delete channels, update the messages.
        :param raid:
        :return:
        """
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


    @group(pass_context=True, hidden=True, aliases=["raid", "r"])
    @raid_checks.raid_report_enabled()
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
        if pokemon_or_level.isdigit():
            raid_type = "egg"
            p_level = int(pokemon_or_level)
            if p_level < 1 or p_level > 5:
                raise BadArgument("Invalid raid level")
        else:
            p_pkmn = await Pokemon.convert(ctx, pokemon_or_level)
            p_pokeform = await Pokemon.convert(ctx, pokemon_or_level)
            Logger.info(f"{p_pkmn} <=> {p_pokeform}")
            p_level = RaidMaster.get_level(p_pokeform)
            if not p_level:
                raise BadArgument(f"Last time I checked, {p_pokeform} didn't appear as a raid boss. If the information I have is outdated, contact an admin to add {p_pokeform} as a raid-boss.")

        if not p_level and not p_pkmn:
            raise BadArgument("Invalid raid level or Pokemon.")

        gym_time_split = gym_and_or_time.split()
        if gym_time_split[-1].isdigit():
            p_timer = int(gym_time_split.pop(-1))

        if len(gym_time_split) == 0:
            raise BadArgument("Raid location is not provided.")

        raid_location = await POILocationConverter.convert_from_text(ctx, " ".join(gym_time_split))

        raid = Raid(raid_id=raid_id, bot=self.bot, guild_id = ctx.guild.id,
                    author_id=ctx.message.author.id, raid_type=raid_type, level=p_level, timer=p_timer,
                    pkmn=p_pkmn, raid_location=raid_location, report_message=report_message, timezone=timezone )

        # create channel
        # respond in new channel that raid has been created
        # respond to raid report saying channel has been created

        new_raid_channel = await dscrd.create_channel(ctx, raid)
        raid.channel_id = new_raid_channel.id

        raid.raid_channel_id = new_raid_channel.id

        if raid.is_egg:
            raid_embed = await raid.egg_embed()
        else:
            raid_embed = await raid.raid_embed()

        raid.response_message = ChannelMessage.from_message(
            await dscrd.send_raid_response(raid, raid_embed, ref_channel=new_raid_channel))
        raid.channel_message = ChannelMessage.from_message(
            await dscrd.send_raid_channel_message(raid, raid_embed, raid_channel=new_raid_channel))

        if p_timer is not None:
            await Embeds.message(new_raid_channel, raid.timer_message)

        if raid_location.is_gym:
            roles_to_notify = [discord.utils.get(ctx.guild.roles, id=role_id)
                               for role_id in GuildNotificationAdapter.get_roles_to_notify(ctx.guild.id,
                                                                                           raid_location.gym.gym_code)]
            # TODO if roles_to_notify send notification

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


    @command(pass_context=True, hidden=True, aliases=["set-gym"])
    @raid_checks.raid_channel()
    async def cmd_set_gym(self, ctx, location: POILocationConverter):

        raid = RaidCog._get_raid_for_channel(ctx)

        raid.raid_location = location
        await raid.update()
        await Embeds.message(ctx.channel, f"Raid location has been updated.")


    @command(pass_context=True, hidden=True, aliases=["assume"])
    @raid_checks.raid_channel()
    async def cmd_assume(self, ctx, pkmn: Pokemon):
        # validate for assume is allowed or not
        # validate pkmn is a valid pokemon and belongs to egg_level
        # find raid-role from server and send notification

        raid = RaidCog._get_raid_for_channel(ctx)

        if pkmn.id in RaidMaster.get_boss_list(raid.level):
            raid.raid_boss = pkmn
            await raid.update()

            message = f'This egg will be assumed to be **{raid.raid_boss}** when it hatches!'
            await Embeds.message(ctx.channel, message)
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


    @command(pass_context=True, hidden=True, aliases=["timer"])
    @raid_checks.raid_channel()
    async def cmd_timer(self, ctx):
        raid = RaidCog._get_raid_for_channel(ctx)
        await Embeds.message(ctx.channel, raid.timer_message)


    @command(pass_context=True, hidden=True, aliases=["reset-start"])
    @raid_checks.raid_channel()
    async def cmd_reset_start(self, ctx):
        raid = RaidCog._get_raid_for_channel(ctx)
        raid.start_time = None
        await raid.update()
        await Embeds.message(ctx.channel, f"Suggested start time has been cleared.")


    @command(pass_context=True, hidden=True, aliases=["start"])
    @raid_checks.raid_channel()
    async def cmd_start(self, ctx, *time_as_text):

        raid = RaidCog._get_raid_for_channel(ctx)
        timezone = await ctx.guild_metadata('timezone')
        start_time = TH.convert_to_timestamp(" ".join(time_as_text), timezone)

        if not start_time:
            return await Embeds.error(ctx.channel, "I couldn't understand time format. Try again like this: `!start HH:MM AM/PM`")

        raid.start_time = start_time
        await raid.update()
        await Embeds.message(ctx.channel, f"suggested start time as **{raid.starts_at}**.", user=ctx.message.author)



    @command(pass_context=True, hidden=True, aliases=["timerset"])
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
            await Embeds.error(ctx.channel, f"I couldn't understand the time format. Try again like this: `!timerset 10`",
                               user=ctx.message.author)


    @group(pass_context=True, hidden=True, aliases=["boss"])
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


    @command(pass_context=True, hidden=True, aliases=["change-raid"])
    @raid_checks.raid_channel()
    async def cmd_change_raid(self, ctx, pokemon_or_level):
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
                raid.level = RaidMaster.get_level(p_pkmn)
                raid.raid_level_info = RaidMaster.from_cache(p_level)
                # set hatch_time just in case.
                raid.hatch_time = raid.hatch_time or raid.expiry_time - timedelta(minutes=self.raid_level_info.egg_timer).seconds

        if p_level or p_pkmn:
            await raid.update()
            await Embeds.message(ctx.channel, "The raid has been updated.\n Use `!timer` to check and `!timerset` to reset the timer if needed.")
        else:
            raise BadArgument("Invalid raid level or Pokemon.")


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
        if payload.user_id == self.bot.user.id:
            return

        emoji = str(payload.emoji)
        if emoji == MyEmojis.TRASH:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            payload_reaction = next(filter(lambda r: (r.emoji == payload.emoji.name), message.reactions), None)
            if payload_reaction and payload_reaction.me:
                await message.delete()


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
                # await channel.delete()





    @group(pass_context=True, hidden=True, aliases=["nest"])
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
        hide_preview = not nest_location.is_gym or await ctx.guild_metadata('nest.preview.hide') == 'true'
        if not hide_preview:
            nest_embed.set_image(url=nest_location.google_preview_url)
        nest_embed.set_footer(text=f"Reported by {message.author.display_name}", icon_url=Icons.avatar(message.author))
        await ctx.channel.send(embed=nest_embed)
        await asyncio.sleep(15)
        await ctx.message.delete()



def main():
    pass



if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")

