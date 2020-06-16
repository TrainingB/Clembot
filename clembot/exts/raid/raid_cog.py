import asyncio
import json
import os
from datetime import timedelta

import discord
from discord.ext import commands

import clembot.utilities.timezone.timehandler as TH

from clembot.core.commands import Cog
from clembot.core.logs import Logger
from clembot.exts.config import ChannelConfigCache
from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.exts.gymmanager.gym import Gym, GymRepository, POILocation, POILocationConverter
from clembot.exts.raid import raid_checks
from clembot.exts.raid.errors import NotARaidChannel, NotARaidReportChannel
from clembot.exts.raid.raid import ChannelMessage, Raid, RaidRepository, DiscordOperations
from clembot.utilities.utils import snowflake
from clembot.utilities.utils.argparser import ArgParser

from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities

from clembot.exts.pkmn.pokemon import PokemonConverter, PokemonCache


async def get_gym_by_code_message(dbi, gym_code, message):
    return await get_gym_info_wrapper(dbi, message, gym_code)


async def get_gym_info_wrapper(dbi, message, gym_code) -> Gym:

    city_state = await ChannelMetadata.city({dbi: dbi}, message.channel.id)

    gym = await GymRepository(dbi).to_gym_by_code_city(gym_code.upper(), city_state)

    Logger.info(f"get_gym_info_wrapper {city_state, gym_code} : {gym}")

    return gym


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

        await PokemonCache.load_cache_from_dbi(self.bot.dbi)
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
        # elif isinstance(error, MeetupDisabled):
        #     await ctx.error('Meetup command disabled in current channel.')
        # elif isinstance(error, InvalidTime):
        #     await ctx.error(f'Invalid time for {ctx.prefix}{ctx.invoked_with}')
        # elif isinstance(error, GroupTooBig):
        #     await ctx.error('This group is too big for the raid!')
        # elif isinstance(error, NotRaidChannel):
        #     await ctx.error(f'{ctx.prefix}{ctx.invoked_with} must be used in a Raid Channel!')
        # elif isinstance(error, NotTrainChannel):
        #     await ctx.error(f'{ctx.prefix}{ctx.invoked_with} must be used in a Train Channel!')
        # elif isinstance(error, RaidNotActive):
        #     await ctx.error(f'Raid must be active to use {ctx.prefix}{ctx.invoked_with}')

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
                        print(error)

                    channel = self.bot.get_channel(raid_channel_id)
                    if channel:
                        await channel.delete()
                        Logger.info(f"Channel deleted: {channel.name}")

        except Exception as error:
            Logger.error(error)


    @commands.group(pass_context=True, hidden=True, aliases=["info"])
    @raid_checks.raid_channel()
    async def cmd_info(self, ctx):
        try:
            raid = RaidCog._get_raid_for_channel(ctx)
            await Embeds.message(ctx.channel, f"Reported at: {raid.reported_at} Hatches at: {raid.hatches_at} Expires At: {raid.expires_at}")
            await Embeds.message(ctx.channel, json.dumps(raid.__getstate__(), indent=2))

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)
        pass

    @commands.group(pass_context=True, hidden=True, aliases=["raid", "r"])
    @raid_checks.raid_report_enabled()
    async def cmd_raid(self, ctx, pokemon):
        """

        !raid 4 gym 12 -> reports a level 4 raid at gym and egg will hatch in 12 minutes
        !raid absol gym 43 -> reports a absol raid at gym which will expire in 43 minutes
        """
        try:
            city = await ctx.guild_setting(key='city')
            timezone = await ctx.guild_setting(key='timezone')
            Logger.info(f"_command_raid({ctx.message.content}) for {city} {timezone}")
            raid_id = next(snowflake.create())

            report_message = f"{ctx.message.channel.id}-{ctx.message.id}"

            dscrd = DiscordOperations(self.bot)

            raid_type = "raid"
            if pokemon.isdigit():
                raid_type = "egg"


            syntax = self.raid_SYNTAX_ATTRIBUTE
            if raid_type == "egg":
                syntax = self.raidegg_SYNTAX_ATTRIBUTE

            argument_text = ctx.message.clean_content.lower()
            parameters = await self.ArgParser.parse_arguments(argument_text, syntax, {'gym': get_gym_by_code_message},
                                                              {'message': ctx.message, 'dbi': ctx.bot.dbi }, ctx)
            Logger.info(f"[{argument_text}] => {parameters}")

            p_length, p_level, p_pkmn, p_gym, p_timer, p_others = [parameters.get(var_name, None) for var_name in
                                                                   ['length', 'egg', 'pkmn', 'gym', 'timer', 'others']]

            if p_length < 3:
                return await Embeds.error(ctx.message.channel, f"Not enough information to create raid.")

            if p_level is None and p_pkmn is None and len(p_others) > 0:
                for word in p_others:
                    try:
                        p_pkmn = await PokemonConverter.convert(word, ctx, word)
                        break
                    except:
                        continue

            if p_level is None and p_pkmn is None:
                return await Embeds.error(ctx.message.channel, f"Not enough information to create raid.")


            raid_location = POILocation.from_gym(p_gym) if p_gym else POILocation.from_location_city(
                ' '.join(str(elem) for elem in p_others), city)

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

            if p_gym:
                roles_to_notify = [discord.utils.get(ctx.guild.roles, id=role_id)
                                   for role_id in GuildNotificationAdapter.get_roles_to_notify(ctx.guild.id,
                                                                                               p_gym.gym_code)]
                # TODO if roles_to_notify send notification

            await raid.insert()
            self.bot.loop.create_task(raid.monitor_status())
            Logger.info(raid)

        except Exception as error:
            Logger.error('error', error)



    @commands.group(pass_context=True, hidden=True, aliases=["assume"])
    @raid_checks.raid_channel()
    async def cmd_assume(self, ctx, pkmn: PokemonConverter):
        # validate for assume is allowed or not
        # validate pkmn is a valid pokemon and belongs to egg_level
        # find raid-role from server and send notification

        raid = RaidCog._get_raid_for_channel(ctx)

        raid.raid_boss = pkmn
        await raid.update()

        message = f'This egg will be assumed to be **{raid.raid_boss}** when it hatches!'
        await Embeds.message(ctx.channel, message)


    async def egg_to_raid(self, raid: Raid, pkmn):
        raid_channel = raid.channel_message.message.channel
        raid_channel_name = raid_channel.name
        #
        #
        #
        # Logger.info(f"--- egg_to_raid({raid}) : {raid_channel_name} into {pkmn}")
        # # fetch egg_report
        # # fetch raid_message
        # # fetch author
        #
        # # TODO: validate pokemon for spelling, raid-boss-level
        #
        # raid.timer = 45
        # raid.raid_type = 'raid'
        # new_channel_name = raid.channel_name
        #
        #
        # try:
        #     await raid_channel.edit(name=new_channel_name)
        # except Exception as e:
        #     print(e)
        #
        # try:
        #     await raid.report_message.message.edit(new_content="Egg has hatched")
        # except Exception as e:
        #     print(e)
        #
        # try:
        #     await raid.channel_message.message.edit(new_content="Egg has hatched")
        # except Exception as e:
        #     print(e)
        #
        # await raid.update()

        # TODO: create new embed in raid-channel
        # TODO: trainer dict and send notification
        # self._bot.loop.create_task(self.expiry_check(raid.id))





    @staticmethod
    def _get_raid_for_channel(ctx) -> Raid:
        raid = Raid.by_channel.get(ctx.channel.id, None)
        if raid:
            return raid
        else:
            raise NoRaidForChannelError(f"Raid not found for channel {ctx.channel.mention}.")


    @commands.group(pass_context=True, hidden=True, aliases=["timer"])
    @raid_checks.raid_channel()
    async def cmd_timer(self, ctx):
        try:
            raid = RaidCog._get_raid_for_channel(ctx)
            await Embeds.message(ctx.channel, raid.timer_message)

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["start"])
    @raid_checks.raid_channel()
    async def cmd_start(self, ctx, *time_as_text):
        try:
            raid = RaidCog._get_raid_for_channel(ctx)
            timezone = await ctx.guild_setting('timezone')
            start_time = TH.convert_to_timestamp(" ".join(time_as_text), timezone)

            if not start_time:
                return await Embeds.error(ctx.channel, "I couldn't understand time format. Try again like this: `!start HH:MM AM/PM`")

            raid.start_time = start_time
            await raid.update()
            await Embeds.message(ctx.channel, f"**B** suggested start time as **{raid.starts_at}**.")

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["timerset"])
    @raid_checks.raid_channel()
    async def cmd_timerset(self, ctx, timer):
        try:
            raid = RaidCog._get_raid_for_channel(ctx)

            Logger.info(f"timerset({raid.cuid}, {timer})")
            if timer.isdigit():
                expire_in_minutes = int(timer)
                raid.update_time(TH.current_epoch(second_precision=False) + timedelta(minutes=expire_in_minutes).seconds)
                await raid.update()
                await Embeds.message(ctx.channel, raid.timer_message)
            else:
                # TODO: handle time input?
                await Embeds.error(ctx.channel, f"I couldn't understand the time format. Try again like this: `!timerset 10`",
                                   user=ctx.message.author)

            # await Embeds.message(ctx.channel, f"Reported at: {raid.reported_at} Hatches at: {raid.hatches_at} Expires At: {raid.expires_at}")
        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["boss"])
    @raid_checks.raid_channel()
    async def cmd_boss(self, ctx, boss: PokemonConverter):
        try:
            raid = RaidCog._get_raid_for_channel(ctx)

            if TH.is_in_future(raid.hatch_time):
                return await Embeds.error(ctx.channel, f"Please wait until the egg has hatched before changing it to an open raid!",
                                          user=ctx.message.author)

            if raid.pkmn:
                return await Embeds.error(ctx.channel, f"Raid boss has already been assigned to this channel.",
                                          user=ctx.message.author)

            await raid.report_hatch(boss)

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)




    @commands.group(pass_context=True, hidden=True, aliases=["clean-up"])
    async def cmd_clean(self, ctx):

        query = self._dbi.table("raid_report").query().where(guild_id=ctx.guild.id).order_by("raid_report_id", True)

        results = await query.getjson()

        for raid in results:
            channel_id = raid['channel_id']

            channel = discord.utils.get(ctx.guild.channels, id=channel_id)
            if channel:
                print(f"{channel.name} ({channel_id})")
                # await channel.delete()

        print(f"_command_xclean() finished!")




    def get_pokemon_image_url(self, pokedex_number):
        # url = icon_list.get(str(pokedex_number))
        url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/pkmn/{0}_.png?cache={1}".format(
            str(pokedex_number).zfill(3), 25)
        if url:
            return url
        else:
            return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=pokedex_number)


    @commands.group(pass_context=True, hidden=True, aliases=["nest"])
    async def cmd_nest(self, ctx, pokemon: PokemonConverter, *location_args):
        """
        !nest chimchar MESC
        !nest pikachu somewhere closer
        !nest aron some park http://google-url.com
        """
        try:
            message = ctx.message
            if len(location_args) > 0:
                nest_location = await POILocationConverter.convert_from_text(ctx, *location_args)
            else:
                return await Embeds.error(ctx.channel, f"The correct usage are: ```!nest pokemon location```", user = ctx.message.author)
            Logger.info(f"{ctx.message.content} => {pokemon} | {nest_location.embed_label} ")

            # await EmbedUtil.message(ctx.channel, f"{pokemon} | {nest_location.embed_label}")

            embed_title = ":map: **A new nest has been reported!**"
            raid_img_url = pokemon.preview_url

            # embed_desription = _("**Pokemon :** {pokemon}\n**Nest Reported at :** {location}\n").format(pokemon=pokemon.label.capitalize(), location=nest_location.name)

            nest_embed = discord.Embed(title=embed_title, description="", colour=discord.Colour.gold(), timestamp=TH.datetime.utcnow())

            nest_embed.add_field(name="**Pokemon**", value=pokemon.label.capitalize(), inline=True)
            nest_embed.add_field(name="**Where**", value=nest_location.embed_label, inline=True)
            nest_embed.set_thumbnail(url=raid_img_url)
            hide_preview = not nest_location.is_gym or await ctx.guild_setting('nest.preview.hide') == 'true'
            if not hide_preview:
                nest_embed.set_image(url=nest_location.google_preview_url)
            nest_embed.set_footer(text=f"Reported by {message.author.display_name}", icon_url=f"https://cdn.discordapp.com/avatars/{message.author.id}/{message.author.avatar}.jpg?size=32")
            await ctx.channel.send(embed=nest_embed)

        except Exception as error:
            Logger.info("{0} while processing message.".format(error))

        finally:
            await asyncio.sleep(15)
            try:
                await ctx.message.delete()
            except:
                pass




def main():
    pass



if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")

