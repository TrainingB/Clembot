from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.exts.gymmanager.gym_manager_cog import Gym, GymAdapter, GymRepository
from clembot.exts.utils.utilities import TextUtil
from clembot.exts.utils.utilities import Utilities, EmbedUtil
from clembot.exts.utils.argparser import ArgParser
from clembot.core.logs import init_loggers
import asyncio
import time
from datetime import datetime, timedelta
import calendar
import discord
from discord.ext import commands

class MessageMetadata:

    def __init__(self, message: discord.Message=None, guild_id=None, channel_id=None, author_id=None, message_id=None):
        if message:
            self.message = message
            self.message_id = message.id
            self.guild_id = message.guild.id
            self.channel_id = message.channel.id
            self.author_id = message.author.id

        else:
            self.message_id = message_id
            self.guild_id = guild_id
            self.channel_id = channel_id
            self.author_id = author_id

    @classmethod
    def from_message(cls, message: discord.Message):
        return cls(message=message)

    @classmethod
    def from_data(cls, guild_id, channel_id, author_id, message_id):
        return cls(guild_id=guild_id, channel_id=channel_id, author_id=author_id, message_id=message_id)

    @property
    def channel_city(self):
        return ClemAdapter.get_channel_city(self.guild_id, self.channel_id)

    @property
    def guild_offset(self):
        return GuildTimeAdapter.get_offset(self.guild_id)


class ClemAdapter:

    @staticmethod
    def get_channel_city(guild_id, channel_id):
        return "BURBANKCA"


class MapsUtil:

    # Given an arbitrary string, create a Google Maps
    # query using the configured hints
    @staticmethod
    def google_url(details, channel_city):
        """loc_list = guild_dict[channel.guild.id]['city_channels'][channel.name].split()"""
        loc_list = channel_city.split()
        details_list = details.split()
        return f"https://www.google.com/maps/search/?api=1&query={'+'.join(details_list)}+{'+'.join(loc_list)}"


class RaidLocation:
    """Represent raid location a gym or a text phrase
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(raid_details)
        direction_description = f"{raid_details} [Click here for directions]({raid_gmaps_link})"
    """


    def __init__(self, gym: Gym=None, location: str=None, city: str=None, message_metadata: MessageMetadata=None):
        self.gym = gym
        self.message_metadata = message_metadata
        self.location = location
        self.city = city

    @classmethod
    def from_gym(cls, gym: Gym):
        return RaidLocation(gym=gym)

    @classmethod
    def from_text(cls, location: str, city: str):
        return RaidLocation(location=location, city=city)

    @property
    def name(self):
        if self.gym:
            return TextUtil.sanitize(self.gym.gym_display_name)
        return TextUtil.sanitize(self.location)

    @property
    def url(self):
        if self.gym:
            return self.gym.gym_url
        return MapsUtil.google_url(self.location, self.city)

    def __str__(self):
        return f"{self.name} ({self.url})"



class Raid:

    def __init__(self, raid_type=None, level=None, timer=None, pkmn = None, bot=None,
                 gym: Gym=None, location=None, raid_location :RaidLocation=None,
                 guild_id=None, channel_id=None, reporter_id=None, message_id=None, raid_report_message_id=None,
                 message_metadata: MessageMetadata=None, raid_dict: dict={} ):


        self.reported_time = GuildTimeAdapter.fetch_current_guild_time(guild_id=guild_id)
        if message_metadata:
            self.message_metadata = message_metadata
        else:
            self.message_metadata = MessageMetadata.from_data(guild_id=guild_id, channel_id=channel_id, author_id=reporter_id, message_id=None)

        self.level = level
        self.raid_type = raid_type
        self.timer = timer if timer is not None else 45
        if raid_location:
            self.raid_location = raid_location
        else:
            if gym:
                self.raid_location = RaidLocation.from_gym(gym)
            else:
                self.raid_location = RaidLocation.from_text(location, self.message_metadata.channel_city)

        self.bot = bot
        self.pkmn = pkmn
        self.raid_dict = raid_dict


    @property
    def guild_id(self):
        return self.message_metadata.guild_id

    @property
    def reported_at(self):
        return ClemTime.as_readable_time(self.reported_time)

    @property
    def expires_at(self):
        return ClemTime.as_readable_time(self.reported_time, timedelta(minutes=self.timer))


    def to_legacy_dict(self):
        legacy_dict = dict(self.raid_dict)
        legacy_dict.update({
            'reportcity': self.message_metadata.channel_id,
            # 'trainer_dict': {},
            # 'exp': fetch_current_time(message.channel.guild.id) + timedelta(minutes=egg_timer),  # One hour from now
            # 'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
            # 'active': True,
            # 'raidmessage': raidmessage.id,
            # 'raidreport': raidreport.id,
            'address': self.raid_location.name,
            # 'type': 'egg',
            # 'pokemon': '',
            'egglevel': self.level,
            # 'suggested_start': False
            'source': 'new-raid'
        })
        return legacy_dict


    def __str__(self):
        timer = f" expiring at [{self.expires_at}]" if self.timer is not None else ""

        value = f"[{self.reported_at}] #{self.channel_name}{timer}({self.url})"

        return value

    @classmethod
    def from_raid_command(cls, text):


        return cls()

    @property
    def state(self):
        return ""
        # if self.hatch and time.time() < self.hatch:
        #     return ""
        # elif not self.pkmn:
        #     return "hatched-"
        # elif time.time() < self.end:
        #     return ""
        # else:
        #     return "expired-"

    @property
    def raid_boss(self):
        if self.level:
            return f"level-{self.level}-egg-"
        else:
            return f"{self.pkmn}-"
        #
        # if self.hatch and time.time() < self.hatch:
        #     return f"level-{self.level}-egg-"
        # elif time.time() < self.end:
        #     return f"{self.pkmn}-"


    @property
    def channel_name(self):
        if self.raid_location:
            location = self.raid_location.name
        else:
            location = "channel_name()"
        channel_name = f"{self.state}{self.raid_boss}{location}"

        return channel_name.lower()

    @property
    def url(self):
        return self.raid_location.url


class ClemTime:

    clem_offset = -7

    @classmethod
    def set_offset(cls, offset):
        cls.clem_offset = offset


    @staticmethod
    def convert_to_epoch(current_time) -> float:
        return calendar.timegm(current_time.utctimetuple())


    @staticmethod
    def as_readable_time(timestamp: float=time.time(), after: timedelta=timedelta(minutes=0)) -> str:
        """Returns time in HH:MM format, can also add after minutes"""
        new_timestamp = datetime.fromtimestamp(timestamp) + after
        return new_timestamp.strftime("%H:%M")


    @staticmethod
    def current_time_by(offset) -> float:
        """Returns time by provided utc offset, if not provided return Bot Time"""
        if offset is None:
            return ClemTime.current_bot_time()

        real_utc_time = datetime.utcnow() - timedelta(hours=ClemTime.clem_offset)
        current_time = real_utc_time + timedelta(hours=offset)
        return ClemTime.convert_to_epoch(current_time)


    @staticmethod
    def current_bot_time() -> float:
        """Returns time in clem-timezone"""
        current_time = datetime.utcnow()
        return ClemTime.convert_to_epoch(current_time)


class GuildTimeAdapter:

    @staticmethod
    def fetch_current_guild_time(guild_id):
        # do something with the guild_id to compute offset
        offset = -4 if guild_id == 1 else None
        return ClemTime.current_time_by(offset=offset)

    @staticmethod
    def get_offset(guild_id):
        offset = -4 if guild_id == 1 else None
        return offset


def test():

    current_bot_time = ClemTime.current_bot_time()
    print(f"Current Bot Time: {ClemTime.as_readable_time(current_bot_time)}")


    nyc_time = GuildTimeAdapter.fetch_current_guild_time(1)
    print(f"NYC Time: {ClemTime.as_readable_time(nyc_time)}")

    local_time = GuildTimeAdapter.fetch_current_guild_time(2)
    print(f"Local Time: {ClemTime.as_readable_time(local_time)}")



    current_bot_time = ClemTime.current_bot_time()
    print(f"Current Bot Time: {ClemTime.as_readable_time(current_bot_time)}")


    nyc_time = GuildTimeAdapter.fetch_current_guild_time(1)
    print(f"NYC Time: {ClemTime.as_readable_time(nyc_time)}")

    local_time = GuildTimeAdapter.fetch_current_guild_time(2)
    print(f"Local Time: {ClemTime.as_readable_time(local_time)}")



def test1():

    raid = Raid(level=3, location="somewhere", timer=16)
    print(raid)

    raid3 = Raid(pkmn="Machamp", location="here", timer=19, guild_id=1)
    print(raid3)

    raid3 = Raid(pkmn="Medicham", location="here", guild_id=1)
    print(raid3)


    raid3 = Raid(pkmn="Groudon", location="here", guild_id=2)
    print(raid3)


async def test2():

    gym = await GymAdapter.to_gym_by_code_city('MESC', 'BURBANKCA')

    raid2 = Raid(level=3, gym=gym, timer=12)
    print(raid2)





dbi = None

async def initialize():
    global dbi
    dbi = DatabaseInterface()
    await dbi.start()
    GymRepository.set_dbi(dbi)

async def cleanup():
    global dbi
    await dbi.stop()


def async_db_wrapper(function_to_run):
    print("async_db_wrapper()")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize())
        loop.run_until_complete(function_to_run())
        loop.run_until_complete(cleanup())
    except Exception as error:
        print(error)



def main():
    test()
    test1()
    # async_db_wrapper(test2)

# main()


# def main():
#     try:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(initialize())
#         loop.run_until_complete(test_condition())
#         loop.run_until_complete(cleanup())
#
#     except Exception as error:
#         print(error)


    # guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
    #     'reportcity': message.channel.id,
    #     'trainer_dict': {},
    #     'exp': fetch_current_time(message.channel.guild.id) + timedelta(minutes=get_raid_timer(None, entered_raid)),  # raid timer minutes from now
    #     'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
    #     'active': True,
    #     'raidmessage' : raidmessage.id,
    #     'raidreport' : raidreport.id,
    #     'address': raid_details,
    #     'type': 'raid',
    #     'pokemon': entered_raid,
    #     'egglevel': -1,
    #     'suggested_start': False,
    #     'counters_dict' : {},
    #     'weather' : None,
    #     'moveset' : 0,
    #     'countersmessage' : None
    #     }



class RaidCog(commands.Cog):
    """
    Loads Raid Manager Code
    """

    def __init__(self, bot):
        self._bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()
        self.ArgParser = ArgParser()
        # self.CityManager = ChannelConfigCache(bot)
        # NewGymManager.set_dbi(self._dbi)
        # CityConfigAdapter.set_dbi(self._dbi)

    raid_SYNTAX_ATTRIBUTE = ['command', 'pokemon', 'gym_info', 'timer', 'location']
    raidegg_SYNTAX_ATTRIBUTE = ['command', 'egg', 'gym_info', 'timer', 'location']

    @commands.group(pass_context=True, hidden=True, aliases=["xraid"])
    async def _command_raid(self, ctx):
        try:

            self.logger.info(f"_command_raid({ctx.message.content})")
            argument_text = ctx.message.clean_content.lower()
            parameters = await self.ArgParser.parse_arguments(argument_text, self.raidegg_SYNTAX_ATTRIBUTE, {}, {'message': ctx.message})
            self.logger.info(f"[{argument_text}] => {parameters}")


            if parameters['length'] <= 2:
                await EmbedUtil.message(ctx.channel, "")



            message_metadata = MessageMetadata.from_message(ctx.message)
            raid = Raid(level = parameters['egg'], raid_location=raid_location, message_metadata=message_metadata)

            self.logger.info(raid)




        except Exception as error:
            self.logger.error(error)





def setup(bot):
    bot.add_cog(RaidCog(bot))


# # ------------- new Raid() object
# message_metadata = MessageMetadata.from_message(message)
# raid_location = RaidLocation(gym=gym, location=raid_details, message_metadata=message_metadata)
# raid = Raid(level=egg_level, timer=egg_timer, pkmn='', raid_location=raid_location, message_metadata=message_metadata,
#             raid_dict=guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id])
#
# print(raid)
# print(guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id])
# print(raid.to_legacy_dict())
# # ------------- new Raid() object
