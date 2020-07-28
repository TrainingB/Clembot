import asyncio
import json
import re
import traceback
from datetime import timedelta
from enum import Enum
from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config import config_template
from clembot.config.constants import Icons, MyEmojis
from clembot.core.logs import Logger
from clembot.core.time_util import convert_into_time
from clembot.exts.gymmanager.gym import POILocation, POILocationConverter
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.exts.pkmn.raid_boss import RaidMaster
from clembot.exts.profile.user_profile import UserProfile

from clembot.utilities.timezone import timehandler as TH
import pydash as _

from clembot.utilities.utils import parse_emoji
from clembot.utilities.utils.embeds import Embeds, color
from clembot.utilities.utils.snowflake import CUIDGenerator, Snowflake
from clembot.utilities.utils.utilities import TextUtil
from clembot.utilities.utils.utilities import Utilities

fcounter = 0

def get_counter():
    global fcounter
    fcounter = fcounter + 1
    return fcounter



MyUtilities = Utilities()




class ChannelMessage:
    """Represents a message identifier (channel_id, message_id)"""

    @classmethod
    def from_message(cls, message):
        """returns channel_id-message_id"""
        return f"{message.channel.id}-{message.id}"

    @classmethod
    async def from_text(cls, bot, arg):
        """returns Channel & Message from - separated IDs"""
        channel_id, message_id = [int(a) for a in arg.split('-')]

        channel = bot.get_channel(channel_id)
        if not channel:
            return None, None

        try:
            message = await channel.fetch_message(message_id)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")
            return channel, None

        return channel, message


class RosterLocation:

    def __init__(self, raid_boss = Union[Pokemon, str], poi_location: POILocation=None, eta=None):
        self.raid_boss = raid_boss
        self.poi_location = poi_location
        self.eta = eta

    def to_dict(self):
        state_dict = {
            'raid_boss': self.raid_boss if isinstance(self.raid_boss, str) else self.raid_boss.id,
            'poi' : self.poi_location.to_dict(),
            'eta' : self.eta,
        }
        return state_dict

    @classmethod
    async def from_dict(cls, bot, state):
        p_raid_boss, p_eta, p_poi = ([state.get(attr, None) for attr in ['raid_boss', 'eta', 'poi']])

        raid_boss = "egg" if p_raid_boss == "egg" else Pokemon.to_pokemon(p_raid_boss)
        poi_location = await POILocation.from_dict(bot, p_poi)

        return cls(raid_boss=raid_boss, poi_location=poi_location, eta=p_eta)

    @classmethod
    async def from_command_text(cls, ctx, text, update_mode=False):
        args = text.split()

        if len(args) == 0:
            raise BadArgument("No information found about egg/boss location and/or eta.")

        if args[0] == 'egg':
            pkmn_or_egg = 'egg'
        else:
            try:
                pkmn_or_egg = (await Pokemon.convert(ctx, args[0]))
            except BadArgument as error:
                if not update_mode:
                    raise error
                else:
                    pkmn_or_egg = None
            if pkmn_or_egg:
                del args[0]

        eta=None
        if len(args) > 0:
            eta = args[-1]
            if convert_into_time(eta, require_am_pm=False) is None:
                eta = None
            else:
                del args[-1]

        poi_location = None
        if len(args) > 0:
            poi_location = await POILocationConverter.convert(ctx, ' '.join(args))

        return cls(raid_boss=pkmn_or_egg, poi_location=poi_location, eta=eta)

    @property
    def raid_for(self):
        if isinstance(self.raid_boss, Pokemon):
            return self.raid_boss.label
        return self.raid_boss

    @property
    def raid_at(self):
        if self.poi_location:
            return self.poi_location.gym_embed_label

    def raid_location_embed(self):
        return (RosterLocationEmbed.from_roster_location(self)).embed




class RSVPEnabled:

    embed_options = ['description', 'timer', 'rsvp']

    status_map = {
        "i" : "interested",
        "ir" : "interested remotely",
        "ii" : "interested in remote invite",
        "h" : "here",
        "hr" : "here remotely",
        "c" : "coming",
        "cr": "coming",
        "x" : "cancel"
    }

    STATUS_MESSAGE = {
        "i": {"title": "Interested", "message": "interested"},
        "ir": {"title": f"Interested {MyEmojis.REMOTE}", "message": f"interested remotely"},
        "ii": {"title": f"Interested {MyEmojis.INVITE}", "message":  f"interested in raid invite.\nIf you've told me your IGN `!list` would display it next to your name so others can invite you."},
        "h": {"title": "At the raid", "message": "at the raid"},
        "hr": {"title":f"At the raid {MyEmojis.REMOTE}", "message": "at the raid remotely"},
        "c": {"title": "On the way", "message": "on the way"},
        "cr": {"title": "On the way", "message": "on the way remotely"},
        "x": {"title": "No status", "message": "no status"}
    }


    def __init__(self, bot, trainer_dict=dict()):
        self.bot = bot
        self.trainer_dict = trainer_dict

    async def add_rsvp(self, member_id: str, status, count=None):

        member_id = str(member_id)
        if not count:
            count = 1

        self.trainer_dict.setdefault(member_id, {})
        self.trainer_dict[member_id]['status'] = status
        self.trainer_dict[member_id]['count'] = count

        await self.update()


    async def cancel_rsvp(self, member_id: str):
        member_id = str(member_id)
        member = self.trainer_dict.pop(member_id, None)
        await self.update()
        return member


    def validate_count(self, count_value):

        try:
            count = int(count_value)
        except Exception as error:
            raise ValueError(
                "I can't understand how many are in your group, please use a number to specify the party size.")

        if 1 <= count <= 20:
            return count
        else:
            raise ValueError("Group size is limited between 1-20.")


    USERS_PATTERN = '<@!?(\d{17,19})>'

    @staticmethod
    def from_mention(text: str):
        new_text = text.replace("<","").replace(">","").replace("!","").replace("@","")
        return new_text


    async def handle_rsvp(self, message, status):
        """
        '!xc <@!415421645214449664> <@!159985870458322944> <@!289657500167438336> 5'
        """

        arguments = message.content.split()[1:]
        party_status = {}
        mention_count_dict = {}

        if len(arguments) == 0:
            party_status[str(message.author.mention)] = 1
        elif message.mentions:
            # create a dictionary like a, 1, b, c, 2 => { a: 1, 1: 1, b: 1, c: 2}

            words = iter(arguments)
            word = next(words)

            while word:
                try:
                    prev_word = word
                    word = next(words)
                    if word.isdigit():
                        mention_count_dict[prev_word] = int(word)
                    else:
                        mention_count_dict[prev_word] = 1
                except StopIteration:
                    mention_count_dict[prev_word] = 1
                    break

            # only leave mention_id in keys, discard other elements of dictionary
            party_status =  { key: mention_count_dict[key] for key in mention_count_dict.keys() if re.search(self.USERS_PATTERN, key) }

        elif len(arguments) == 1:
            party_status[str(message.author.mention)] = self.validate_count(arguments[0])


        try:
            Logger.info(party_status)
            total_trainer_rsvp = 0
            if status == 'x':
                for mention, party_size in party_status.items():
                    removed_user = await self.cancel_rsvp(member_id=Raid.from_mention(mention))
                    if removed_user is None:
                        embed_msg = f"{mention} had no status to cancel."
                        await Embeds.error(message.channel, embed_msg)
                    else:
                        embed_msg = f"{mention}'s status has been cancelled."
                        await Embeds.message(message.channel, embed_msg)
                embed_msg = ""
            else:
                for user_id, party_size in party_status.items():
                    await self.add_rsvp(member_id=Raid.from_mention(user_id), status=status, count=party_size)
                    total_trainer_rsvp += party_size

                with_trainers = "" if total_trainer_rsvp == 1 else " with a total of {trainer_count} trainers".format(trainer_count=total_trainer_rsvp)
                is_or_are = "is" if len(party_status) == 1 else "are"
                embed_msg = f"{', '.join([mention for mention in party_status.keys()])} {is_or_are} {RSVPEnabled.STATUS_MESSAGE[status].get('message', None)}{with_trainers}"

            await self.send_rsvp_embed(message, description=embed_msg, options=self.embed_options)

        except ValueError as value_error:
            await Embeds.error(message.channel, f"{value_error}", user=message.author)

        except Exception as error:
            Logger.info(error)

    async def send_rsvp_embed(self, message, description=None, options=['description', 'timer', 'i', 'c', 'h']):

        embed_message = await message.channel.send(embed=await self.rsvp_embed_by_options(message, options=options,
                                                                           description=description))
        await embed_message.add_reaction('🗑️')

    async def rsvp_embed_by_options(self, message, options=None, description=None):
        additional_fields = {}
        footer = None
        for option in options:
            if option == 'timer':
                _type, _action, _at = self.type_action_at()
                footer = f"{_type.capitalize()} {_action} {_at}"

            if option == 'rsvp':

                int_label = f"Interested {MyEmojis.INTERESTED} / {MyEmojis.REMOTE} / {MyEmojis.INVITE}"
                int_status = f"{self.size_by_status('i')} / {self.size_by_status('ir')} / {self.size_by_status('ii')}"
                additional_fields[int_label] = int_status

                coming_label = f"On the way {MyEmojis.COMING} / {MyEmojis.REMOTE}"
                coming_status = f"{self.size_by_status('c')} / {self.size_by_status('cr')}"
                additional_fields[coming_label] = coming_status

                here_label = f"At the raid {MyEmojis.HERE} / {MyEmojis.REMOTE}"
                here_status = f"{self.size_by_status('h')} / {self.size_by_status('hr')}"
                additional_fields[here_label] = here_status

            elif option in ['i','ir','ii']:
                int_label = f"Interested {MyEmojis.INTERESTED} {self.size_by_status('i')} / {MyEmojis.REMOTE} {self.size_by_status('ir')} / {MyEmojis.INVITE} {self.size_by_status('ii')}"
                int_status = ""

                trainer_names = await self.trainers_by_status(message, 'i')
                if trainer_names:
                    int_status += f"{MyEmojis.INTERESTED} {trainer_names}\n"

                trainer_names = await self.trainers_by_status(message, 'ir')
                if trainer_names:
                    int_status += f"{MyEmojis.REMOTE} {trainer_names}\n"

                trainer_names = await self.trainers_by_status(message, 'ii')
                if trainer_names:
                    int_status += f"{MyEmojis.INVITE} {trainer_names}\n"

                additional_fields[int_label] = int_status

            elif option in ['c','cr']:
                int_label = f"On the way {MyEmojis.COMING} {self.size_by_status('c')} / {MyEmojis.REMOTE} {self.size_by_status('cr')}"
                int_status = ""

                trainer_names = await self.trainers_by_status(message, 'c')
                if trainer_names:
                    int_status += f"{MyEmojis.COMING} {trainer_names}\n"

                trainer_names = await self.trainers_by_status(message, 'cr')
                if trainer_names:
                    int_status += f"{MyEmojis.REMOTE} {trainer_names}\n"
                additional_fields[int_label] = int_status

            elif option in ['h','hr']:
                int_label = f"At the raid {MyEmojis.HERE} {self.size_by_status('h')} / {MyEmojis.REMOTE} {self.size_by_status('hr')}"
                int_status = ""

                trainer_names = await self.trainers_by_status(message, 'h')
                if trainer_names:
                    int_status += f"{MyEmojis.HERE} {trainer_names}\n"

                trainer_names = await self.trainers_by_status(message, 'hr')
                if trainer_names:
                    int_status += f"{MyEmojis.REMOTE} {trainer_names}\n"
                additional_fields[int_label] = int_status



        return Embeds.make_embed(header="RSVP Status", msg_color=discord.Color.gold(), fields=additional_fields, footer=footer, content=description)

    async def trainers_by_status(self, message, status, mentions=False, delimiter=', '):

        name_list = []
        for trainer in self.trainer_dict.keys():
            if self.trainer_dict[trainer]['status'] == status:
                user = message.channel.guild.get_member(int(trainer))
                if mentions:
                    name_list.append(user.mention)
                else:
                    user_name = user.nick if user.nick else user.name

                    if status == 'ii':
                        ign = await UserProfile.find_ign(self.bot, user.id)
                        if ign:
                            user_name = f"{user_name} ({ign})"

                    count = self.trainer_dict[trainer]['count']
                    if count > 1:
                        name_list.append("**{trainer} ({count})**".format(trainer=user_name, count=count))
                    else:
                        name_list.append("**{trainer}**".format(trainer=user_name))

        if len(name_list) > 0:
            return MyUtilities.trim_to(delimiter.join(name_list), 950, delimiter)

        return None

    def size_by_status(self, status):
        count = 0

        for trainer in self.trainer_dict.values():
            if trainer['status'] == status:
                count += int(trainer['count'])

        return count




class RaidParty(RSVPEnabled):
    """
    Also serves as raidparty_cache
    """
    by_channel = dict()
    by_id = dict()
    embed_options = ['description', 'rsvp']

    def __init__(self, raid_party_id=None, bot=None, guild_id=None, channel_id=None, author_id = None,
                 city=None, timezone=None, roster= [] , roster_begins_at = 0, trainer_dict=dict()):
        super().__init__(bot=bot, trainer_dict=trainer_dict)
        self.id = raid_party_id
        self.bot = bot
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.author_id = author_id
        self.raid_type = "raidparty"
        self.city = city
        self.timezone = timezone
        self.snowflake = Snowflake()
        self.roster = roster
        self.roster_begins_at = roster_begins_at
        self.trainer_dict = trainer_dict

    @property
    def current_location(self):
        return self.roster[self.physical_index(self.roster_begins_at)]

    @property
    def current_location_index(self):
        return self.roster_begins_at

    def physical_index(self, i):
        return i - self.roster_begins_at

    def __getitem__(self, i: int) -> RosterLocation:
        """Get"""
        if self.roster_begins_at <= i <= self.roster_begins_at + self.__len__():
            return self.roster[self.physical_index(i)]
        return None

    def __setitem__(self, i: int, o: RosterLocation) -> None:
        """Update"""
        if self.physical_index(i) > len(self.roster):
            return
        self.roster[self.physical_index(i)] = o

    def __delitem__(self, i: int) -> None:
        """Remove"""
        del self.roster[self.physical_index(i)]
        print(f"{self.__repr__()} (after REMOVE {i})")

    def __len__(self) -> int:
        return len(self.roster)

    def __contains__(self, __x: RosterLocation) -> bool:
        return __x in self.roster


    async def append(self, roster_location: RosterLocation):
        self.roster.append(roster_location)
        if self.roster_begins_at == 0:
            self.roster_begins_at = 1
        await self.update()

    async def add_location(self, roster_location):
        await self.append(roster_location)

    def remove_location(self, location_number):
        self.__delitem__(location_number)

    async def move(self):
        if len(self) == 0:
            raise ValueError("No next location available on the roster!")
        self.remove_location(self.roster_begins_at)
        self.roster_begins_at += 1
        await self.update()



    async def embed(self):
        return (RaidPartyEmbed.from_raid_party(self)).embed

    @property
    def guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self):
        return self.guild.get_channel(self.channel_id)


    def to_dict(self):
        """Returns the raid_dict column value for the raid"""
        state_dict = {
            'raid_type' : self.raid_type,
            'author_id': self.author_id,
            'timezone': self.timezone,
            'city' : self.city,
            'roster_begins_at': self.roster_begins_at,
            'roster': [rl.to_dict() for rl in self.roster],
        }

        if len(self.trainer_dict) > 0:
            state_dict['trainer_dict'] = self.trainer_dict

        return state_dict

    def __setstate__(self, state):
        return None


    def get_state(self):
        """Returns the DB representation of the raid report"""
        state = self.to_dict()
        db_state = {
            'raid_party_id': self.id,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'raid_party_dict': json.dumps(state)
        }
        return db_state


    @classmethod
    def cache(cls, raid_party):
        cls.by_channel[raid_party.channel_id] = raid_party
        cls.by_id[raid_party.id] = raid_party

    @classmethod
    def evict(cls, raid_party):
        cls.by_channel.pop(raid_party.channel_id, None)
        cls.by_id.pop(raid_party.id, None)

    @classmethod
    async def from_cache(cls, ctx, raid_id=None):
        if raid_id:
            raid = cls.by_id.get(raid_id, None)
            if not raid:
                RaidRepository.set_dbi(ctx.bot.dbi)
                raid_from_db = await RaidRepository.find_raid_by_id(raid_id)
                raid = await Raid.from_db_dict(ctx.bot, raid_from_db)
                if not raid:
                    return None
                return raid
        else:
            raid = cls.by_channel.get(ctx.channel.id, None)
            if not raid:
                RaidRepository.set_dbi(ctx.bot.dbi)
                raid_from_db = await RaidRepository.find_raid_for_channel(ctx.guild.id, ctx.channel.id)
                raid = await Raid.from_db_dict(ctx.bot, raid_from_db)
                if not raid:
                    return None
                return raid


    @classmethod
    async def from_db_dict(cls, bot, db_dict):
        """
        :param bot:
        :param db_dict:
        :return: Raid object, also caches the object
        """
        guild_id, channel_id, raid_party_id, raid_party_dict_text \
            = [db_dict.get(attr, None) for attr in ['guild_id', 'channel_id', 'raid_party_id', 'raid_party_dict']]

        raid_party_dict = json.loads(raid_party_dict_text)

        roster_dict, trainer_dict = [raid_party_dict.get(attr, {}) for attr in
               ['roster', 'trainer_dict']]

        roster_dict = json.loads(roster_dict) if isinstance(roster_dict, str) else roster_dict

        roster = [await RosterLocation.from_dict(bot, rl) for rl in roster_dict]

        p_raid_type, p_author_id, p_timezone, p_city, p_roster_begins_at = [raid_party_dict.get(attr, None) for attr in
                                                 ['raid_type', 'author_id', 'timezone', 'city', 'roster_begins_at']]

        raid_party = RaidParty(raid_party_id=raid_party_id, bot=bot, guild_id=guild_id, channel_id=channel_id,
                    author_id=p_author_id, timezone=p_timezone, city=p_city,
                    roster=roster, roster_begins_at=p_roster_begins_at, trainer_dict=trainer_dict)

        RaidParty.cache(raid_party)
        return raid_party

    @property
    def cuid(self):
        return CUIDGenerator.cuid(self.id)


    def __str__(self):
        value = f"{self.cuid}"
        return value




    async def insert(self):
        raid_table = self.bot.dbi.table('raid_party_report')
        raid_table_insert = raid_table.insert(**self.get_state())
        await raid_table_insert.commit()
        RaidParty.cache(raid_party=self)


    async def update(self):
        raid_table = self.bot.dbi.table('raid_party_report')
        raid_table_update = raid_table.update(raid_party_dict=json.dumps(self.to_dict())).where(raid_party_id=self.id)
        await raid_table_update.commit()
        RaidParty.cache(raid_party=self)
        # await self.update_messages()
        Logger.info(f"[{self.cuid}] => raid_party update() finished!")

    async def delete(self):
        """Deletes the raid record from DB and evicts from cache."""
        raid_table = self.bot.dbi.table('raid_party_report')
        raid_table_delete = raid_table.query().where(raid_party_id=self.id)
        self.bot.loop.create_task(raid_table_delete.delete())
        RaidParty.evict(raid_party=self)
        Logger.info(f"[{self.cuid}] => raid delete() finished!")

    async def add_rsvp(self, member_id: str, status, count=None):

        member_id = str(member_id)
        if not count:
            count = 1

        self.trainer_dict.setdefault(member_id, {})
        self.trainer_dict[member_id]['status'] = status
        self.trainer_dict[member_id]['count'] = count

        await self.update()


    async def cancel_rsvp(self, member_id: str):
        member_id = str(member_id)
        member = self.trainer_dict.pop(member_id, None)
        await self.update()
        return member


    def validate_count(self, count_value):

        try:
            count = int(count_value)
        except Exception as error:
            raise ValueError(
                "I can't understand how many are in your group, please use a number to specify the party size.")

        if 1 <= count <= 20:
            return count
        else:
            raise ValueError("Group size is limited between 1-20.")


    USERS_PATTERN = '<@!?(\d{17,19})>'

    @staticmethod
    def from_mention(text: str):
        new_text = text.replace("<","").replace(">","").replace("!","").replace("@","")
        return new_text


    async def handle_rsvp(self, message, status):
        """
        '!xc <@!415421645214449664> <@!159985870458322944> <@!289657500167438336> 5'
        """

        arguments = message.content.split()[1:]
        party_status = {}
        mention_count_dict = {}

        if len(arguments) == 0:
            party_status[str(message.author.mention)] = 1
        elif message.mentions:
            # create a dictionary like a, 1, b, c, 2 => { a: 1, 1: 1, b: 1, c: 2}

            words = iter(arguments)
            word = next(words)

            while word:
                try:
                    prev_word = word
                    word = next(words)
                    if word.isdigit():
                        mention_count_dict[prev_word] = int(word)
                    else:
                        mention_count_dict[prev_word] = 1
                except StopIteration:
                    mention_count_dict[prev_word] = 1
                    break

            # only leave mention_id in keys, discard other elements of dictionary
            party_status =  { key: mention_count_dict[key] for key in mention_count_dict.keys() if re.search(self.USERS_PATTERN, key) }

        elif len(arguments) == 1:
            party_status[str(message.author.mention)] = self.validate_count(arguments[0])


        try:
            Logger.info(party_status)
            total_trainer_rsvp = 0
            if status == 'cancel':
                for mention, party_size in party_status.items():
                    removed_user = await self.cancel_rsvp(member_id=Raid.from_mention(mention))
                    if removed_user is None:
                        embed_msg = f"{mention} had no status to cancel."
                        await Embeds.error(message.channel, embed_msg)
                    else:
                        embed_msg = f"{mention}'s status has been cancelled."
                        await Embeds.message(message.channel, embed_msg)
                embed_msg = ""
            else:
                for user_id, party_size in party_status.items():
                    await self.add_rsvp(member_id=Raid.from_mention(user_id), status=status, count=party_size)
                    total_trainer_rsvp += party_size

                with_trainers = "" if total_trainer_rsvp == 1 else " with a total of {trainer_count} trainers".format(trainer_count=total_trainer_rsvp)
                is_or_are = "is" if len(party_status) == 1 else "are"
                embed_msg = f"{', '.join([mention for mention in party_status.keys()])} {is_or_are} {_.get(RSVPEnabled.STATUS_MESSAGE, f'{status}.message')}{with_trainers}"

            await self.send_rsvp_embed(message, description=embed_msg, options=self.embed_options)

        except ValueError as value_error:
            await Embeds.error(message.channel, f"{value_error}", user=message.author)

        except Exception as error:
            Logger.info(error)


    async def send_rsvp_embed(self, message, description=None, options=['rsvp', 'interested', 'coming', 'here', 'remote']):

        return await message.channel.send(embed=await self.rsvp_embed_by_options(message, options=options,
                                                                           description=description))
    #
    # def rsvp_embed_by_options(self, message, options=None, description=None):
    #     additional_fields = {}
    #
    #     for option in options:
    #         if option == 'timer':
    #             _type, _action, _at = self.type_action_at()
    #             additional_fields[f"{_type} {_action}".capitalize()] = _at
    #
    #             # TODO: handle suggested start time
    #             # TODO: handle ex-raid
    #             # raid_time_value = fetch_channel_expire_time(message.channel.id).strftime("%I:%M %p (%H:%M)")
    #             # raid_time_label = "Raid Expires At"
    #             # if rc_d['type'] == 'egg':
    #             #     raid_time_label = "Egg Hatches At"
    #             #     if rc_d['egglevel'] == 'EX':
    #             #         raid_time_value = fetch_channel_expire_time(message.channel.id).strftime(
    #             #             "%B %d %I:%M %p (%H:%M)")
    #         #
    #         #     start_time = fetch_channel_start_time(message.channel.id)
    #         #     start_time_label = "None"
    #         #     if start_time:
    #         #         raid_time_label = raid_time_label + " / Suggested Start Time"
    #         #         raid_time_value = raid_time_value + " / " + start_time.strftime("%I:%M %p (%H:%M)")
    #         #
    #         #     additional_fields[raid_time_label] = raid_time_value
    #
    #         if option == 'rsvp':
    #             aggregated_label = "Interested / On the way / At the raid"
    #             aggregated_status = f"{self.size_by_status('maybe')} / {self.size_by_status('omw')} / {self.size_by_status('waiting')}"
    #
    #             additional_fields[aggregated_label] = aggregated_status
    #         elif option == 'interested':
    #             trainer_names = self.trainers_by_status(message, "maybe")
    #             if trainer_names:
    #                 additional_fields['Interested'] = trainer_names
    #         elif option == 'coming':
    #             trainer_names = self.trainers_by_status(message, "omw")
    #             if trainer_names:
    #                 additional_fields['On the way'] = trainer_names
    #         elif option == 'here':
    #             trainer_names = self.trainers_by_status(message, "waiting")
    #             if trainer_names:
    #                 additional_fields['At the raid'] = trainer_names
    #         elif option == 'remote':
    #             trainer_names = self.trainers_by_status(message, "remote")
    #             if trainer_names:
    #                 additional_fields['Remote'] = trainer_names
    #
    #
    #     footer = None
    #
    #     return Embeds.make_embed(content=description, fields=additional_fields, footer=footer)

    # def _generate_rsvp_embed(self, message):
    #     embed_msg = ""
    #
    #     embed = discord.Embed(description=embed_msg, colour=discord.Colour.gold())
    #
    #     embed.add_field(name="**Interested / On the way / At the raid**", value="{maybe} / {omw} / {waiting}".format(
    #         waiting=self.size_by_status("waiting"),
    #         omw=self.size_by_status("omw"),
    #         maybe=self.size_by_status("maybe")), inline=True)
    #
    #     maybe = self.trainers_by_status(message, "maybe")
    #     if maybe:
    #         embed.add_field(name="**Interested**", value=maybe)
    #
    #     omw = self.trainers_by_status(message, "omw")
    #     if omw:
    #         embed.add_field(name="**On the way**", value=omw)
    #
    #     waiting = self.trainers_by_status(message, "waiting")
    #     if waiting:
    #         embed.add_field(name="**At the raid**", value=waiting)
    #
    #     return embed


    def trainers_by_status(self, message, status, mentions=False):

        name_list = []
        for trainer in self.trainer_dict.keys():
            if self.trainer_dict[trainer]['status'] == status:
                user = message.channel.guild.get_member(int(trainer))
                if mentions:
                    name_list.append(user.mention)
                else:
                    user_name = user.nick if user.nick else user.name
                    count = self.trainer_dict[trainer]['count']
                    if count > 1:
                        name_list.append("**{trainer} ({count})**".format(trainer=user_name, count=count))
                    else:
                        name_list.append("**{trainer}**".format(trainer=user_name))

        if len(name_list) > 0:
            return MyUtilities.trim_to(', '.join(name_list), 950, ', ')

        return None

    def size_by_status(self, status):
        count = 0

        for trainer in self.trainer_dict.values():
            if trainer['status'] == status:
                count += int(trainer['count'])

        return count



    async def handle_group_start(self):

        users_starting = {}

        for trainer_id in self.trainer_dict:
            if self.trainer_dict[trainer_id]['status'] in ["h", "hr", "ir"]:
                trainer = self.bot.get_user(int(trainer_id))
                users_starting[trainer_id] = trainer.mention

        if len(users_starting) > 0:
            embed_message = f"The group of trainers waiting at location {self.current_location_index} are starting. Trainers {', '.join(users_starting.values())}, please make sure you sync-up with other players."
            await Embeds.message(self.channel, description=embed_message)
        else:
            embed_message = f"How can you start when there is nobody waiting at the location?"
            await Embeds.error(self.channel, description=embed_message)





class Raid (RSVPEnabled):
    """
    Also serves as raid_cache
    """
    by_channel = dict()
    by_id = dict()

    def __init__(self, raid_id=None, bot=None, guild_id=None, channel_id=None, author_id = None,
                 report_message: str = None,
                 raid_type=None, level=None,
                 raid_location: POILocation=None, pkmn :Pokemon=None, timer=None,
                 reported_time=None, hatch_time=None, expiry_time=None, start_time=None,
                 response_message: str = None, channel_message: str = None, timezone=None,
                 trainer_dict=dict()):
        """
        From command:
            Raid(bot, report_message, raid_type, level, raid_location, timer, pokemon )
            Raid(bot, raid_report_id, reported_time, expiry_time, report_message, response_message, channel_message
                        raid_type, level, raid_location, pokemon )

        :param bot: needed for dbi & dpy operations
        :param raid_type:
        :param level:
        :param report_message: [!raid 4 somewhere 12] - MessageMetadata
        :param raid_location: raid location information ( can contain gym or location )
        :param pkmn:
        :param timer:

        :param manual_timer_set: if the timer was provided.
        :param response_message: [A raid has been reported, co-ordinate in #channel] - MessageMetadata
        :param channel_message: [A raid has been reported, co-ordinate here] - MessageMetadata
        """
        super().__init__(bot=bot, trainer_dict=trainer_dict)
        self.id = raid_id
        self.bot = bot
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.author_id = author_id

        # new raid report
        self.report_message = report_message
        self.raid_type = raid_type
        self.level = level
        self.pkmn = pkmn
        if not self.pkmn:
            self.verify_level()
        self.raid_location = raid_location
        # TODO: Connect guild timezone
        self.timezone = timezone

        # fetched from DB, post creation
        self.response_message = response_message
        self.channel_message = channel_message

        self.hatch_time = hatch_time
        self.expiry_time = expiry_time
        self.start_time = start_time

        self.reported_time = TH.current_epoch(second_precision=False) if reported_time is None else reported_time

        self.raid_level_info = RaidMaster.from_cache(self.level)

        if timer is not None:
            if self.raid_type == "egg":
                self.hatch_time = self.reported_time + timedelta(minutes=timer).seconds
                self.expiry_time = self.hatch_time + self.raid_level_info.egg_timer * 60
            elif self.raid_type == "raid":
                self.expiry_time = self.reported_time + timedelta(minutes=timer).seconds
        else:
            self.hatch_time = self.hatch_time or self.reported_time + timedelta(minutes=self.raid_level_info.egg_timer).seconds
            self.expiry_time = self.expiry_time or self.reported_time + timedelta(minutes=self.raid_level_info.egg_timer).seconds + timedelta(minutes=self.raid_level_info.raid_timer).seconds
        print(f"{self.reported_at} {self.hatches_at} {self.expires_at}")

        self.monitor_task_tuple = None
        self.expire_task_tuple = None
        self.hatch_task_tuple = None
        self.trainer_dict = trainer_dict
        self.snowflake = Snowflake()

    @property
    def monitor_task(self):
        if self.monitor_task_tuple:
            return self.monitor_task_tuple[0]

    @property
    def monitor_task_id(self) -> str:
        if self.monitor_task_tuple:
            return self.monitor_task_tuple[1]

    @monitor_task.setter
    def monitor_task(self, task_tuple: tuple):
        """ reset hatch and expiry tasks"""
        if self.monitor_task_tuple:
            Logger.info(f"[{self.cuid}][{self.monitor_task_id}] cancel existing monitor_task")
            self.monitor_task.cancel()
        self.monitor_task_tuple = task_tuple
        if task_tuple:
            Logger.info(f"[{self.cuid}] => Assigning task [{self.monitor_task_id}]")

    @property
    def expire_task(self):
        if self.expire_task_tuple:
            return self.expire_task_tuple[0]

    @property
    def expire_task_id(self):
        if self.expire_task_tuple:
            return self.expire_task_tuple[1]


    @expire_task.setter
    def expire_task(self, task_tuple: tuple):
        if self.expire_task_tuple:
            self.expire_task.cancel()
            Logger.info(f"[{self.cuid}][{self.expire_task_id}] cancel existing expire_task")
        self.expire_task_tuple = task_tuple
        if task_tuple:
            Logger.info(f"[{self.cuid}] => Assigning task [{self.expire_task_id}]")

    @property
    def hatch_task(self):
        if self.hatch_task_tuple:
            return self.hatch_task_tuple[0]

    @property
    def hatch_task_id(self):
        if self.hatch_task_tuple:
            return self.hatch_task_tuple[1]

    @hatch_task.setter
    def hatch_task(self, task_tuple: tuple):
        if self.hatch_task_tuple:
            self.hatch_task.cancel()
            Logger.info(f"[{self.cuid}][{self.hatch_task_id}] cancel existing hatch_task")
        self.hatch_task_tuple = task_tuple
        if task_tuple:
            Logger.info(f"[{self.cuid}] => Assigning task [{self.hatch_task_id}]")


    @property
    def guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self):
        return self.guild.get_channel(self.channel_id)


    @property
    def max_timer(self):
        if self.is_egg:
            return self.raid_level_info.egg_timer
        else:
            return self.raid_level_info.raid_timer


    def get_raid_dict(self):
        """Returns the raid_dict column value for the raid"""
        state_dict = {
            'raid_type': self.raid_type,
            'level': self.level,
            'pkmn' : self.pkmn,
            'author_id': self.author_id,
            'reported_time': self.reported_time,
            'hatch_time': self.hatch_time,
            'expiry_time': self.expiry_time,
            'start_time' : self.start_time,
            'timezone' : self.timezone,
            'raid_location': self.raid_location.to_dict(),
            'report_message': self.report_message,
            'response_message': self.response_message,
            'channel_message': self.channel_message,
        }
        if self.pkmn:
            state_dict['pkmn'] = self.pkmn.id

        if len(self.trainer_dict) > 0:
            state_dict['trainer_dict'] = self.trainer_dict

        return state_dict

    def get_state(self):
        """Returns the DB representation of the raid report"""
        state = self.get_raid_dict()
        db_state = {
            'raid_id': self.id,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'raid_dict': json.dumps(state)
        }
        return db_state



    def create_task_tuple(self, coro):
        task_id = CUIDGenerator.cuid(self.snowflake.next())
        return self.bot.loop.create_task(coro), task_id


    @classmethod
    def cache(cls, raid):
        cls.by_channel[raid.channel_id] = raid
        cls.by_id[raid.id] = raid

    @classmethod
    def evict(cls, raid):
        cls.by_channel.pop(raid.channel_id, None)
        cls.by_id.pop(raid.id, None)

    @classmethod
    async def from_cache(cls, ctx, raid_id=None):
        if raid_id:
            raid = cls.by_id.get(raid_id, None)
            if not raid:
                RaidRepository.set_dbi(ctx.bot.dbi)
                raid_from_db = await RaidRepository.find_raid_by_id(raid_id)
                raid = await Raid.from_db_dict(ctx.bot, raid_from_db)
                if not raid:
                    return None
                return raid
        else:
            raid = cls.by_channel.get(ctx.channel.id, None)
            if not raid:
                RaidRepository.set_dbi(ctx.bot.dbi)
                raid_from_db = await RaidRepository.find_raid_for_channel(ctx.guild.id, ctx.channel.id)
                raid = await Raid.from_db_dict(ctx.bot, raid_from_db)
                if not raid:
                    return None
                return raid


    @classmethod
    async def from_db_dict(cls, bot, db_dict):
        """
        :param bot:
        :param db_dict:
        :return: Raid object, also caches the object
        """
        guild_id, raid_channel_id, raid_id, raid_dict_text \
            = [db_dict.get(attr, None) for attr in ['guild_id', 'channel_id', 'raid_id', 'raid_dict']]

        raid_dict = json.loads(raid_dict_text)

        rl_dict, trainer_dict = [raid_dict.get(attr, {}) for attr in
               ['raid_location', 'trainer_dict']]

        p_rm, p_rr, p_cm = [raid_dict.get(attr, None) for attr in
                            ['report_message', 'response_message', 'channel_message']]

        raid_type, level, p_pkmn, p_author_id = [raid_dict.get(attr, None) for attr in
                                                 ['raid_type', 'level', 'pkmn', 'author_id']]

        reported_time, expiry_time, hatch_time, timezone \
            = [raid_dict.get(attr, None) for attr in ['reported_time', 'expiry_time', 'hatch_time', 'timezone']]

        pkmn = Pokemon.to_pokemon(p_pkmn) if p_pkmn else None

        raid_location = await POILocation.from_dict(bot, rl_dict)

        raid = Raid(raid_id=raid_id, bot=bot, guild_id=guild_id, channel_id=raid_channel_id, raid_type=raid_type,
                    level=level, pkmn=pkmn, raid_location=raid_location, author_id=p_author_id,
                    reported_time=reported_time, hatch_time=hatch_time, expiry_time=expiry_time, timezone=timezone,
                    report_message=p_rm, response_message=p_rr, channel_message=p_cm,
                    trainer_dict=trainer_dict)

        Raid.cache(raid)
        return raid

    @property
    def pokemon_label(self):
        if self.pkmn:
            return self.pkmn.label
        return None

    @property
    def cuid(self):
        return CUIDGenerator.cuid(self.id)

    @property
    def active(self):
        """checks whether the raid is still active or not."""
        return TH.is_in_future(self.expiry_time)

    @property
    def reported_at(self):
        """as Readable time"""
        # TODO: add guild timezone
        return TH.as_local_readable_time(self.reported_time, self.timezone)

    @property
    def expires_at(self):
        """as Readable time"""
        # TODO: add guild timezone
        return TH.as_local_readable_time(self.expiry_time, self.timezone)


    @property
    def hatches_at(self):
        """as Readable time"""
        if self.hatch_time:
            return TH.as_local_readable_time(self.hatch_time, self.timezone)
        return None

    @property
    def starts_at(self):
        """as Readable time"""
        if self.start_time:
            return TH.as_local_readable_time(self.start_time, self.timezone)
        return None


    @property
    def is_egg(self):
        return self.raid_type == "egg"

    def update_time(self, new_utc_timestamp):
        if self.raid_type == "egg":
            self.hatch_time = new_utc_timestamp
            self.expiry_time = self.hatch_time + self.raid_level_info.raid_timer * 60
        elif self.raid_type == "raid":
            self.expiry_time = new_utc_timestamp

        self.monitor_task = self.create_task_tuple(self.monitor_status())

    def verify_level(self):
        if self.level and not 0 < self.level < 6:
            raise InvalidRaidLevelError("Raid egg levels are only from 1-5.")

    @property
    def message(self):
        return self.report_message.message

    @property
    def raid_boss(self):
        return self.pkmn

    @raid_boss.setter
    def raid_boss(self, pkmn):
        self.pkmn = pkmn

    @property
    def image(self):
        """return the egg or pokemon image"""
        # print(f"Not implemented method: Raid.image()")
        return None

    @property
    def preview_url(self):
        """return the egg or pokemon image"""
        if self.pkmn:
            return self.pkmn.preview_url
        return None

    @property
    def possible_bosses_info(self):
        """return the egg or pokemon image"""
        return f"Not implemented method: Raid.possible_bosses_info()"

    @property
    def direction_description(self):
        return self.raid_location.gym.gym_display_name if self.raid_location.gym is not None else self.raid_location.location


    def __str__(self):
        hatch_info = f"| Hatches at: {self.hatches_at}" if self.hatch_time else ""
        end_info = f"| Ends at: {self.expires_at} " if self.expiry_time else ""
        value = f"#{self.channel_name}{hatch_info}{end_info}"

        return value

    def timer_info(self):
        hatch_info = f"Hatches at: {self.hatches_at}" if self.hatch_time else ""
        end_info = f"Ends at: {self.expires_at} " if self.expiry_time else ""
        value = f"{hatch_info}{' | ' if len(hatch_info) and len(end_info) else ''}{end_info}"
        return value

    @classmethod
    def from_raid_command(cls, text):

        return cls()

    @property
    def status(self):
        if TH.is_in_future(self.hatch_time):
            return "egg"
        elif not self.pkmn:
            return "hatched"
        elif TH.is_in_future(self.expiry_time):
            return "active"
        else:
            return "expired"

    # @property
    # def raid_boss(self):

    #
    # if self.hatch and time.time() < self.hatch:
    #     return f"level-{self.level}-egg-"
    # elif time.time() < self.end:
    #     return f"{self.pkmn}-"

    @property
    def channel_name(self):

        location = self.raid_location.name

        if self.is_egg:
            raid_boss = f"{self.level}-"
        else:
            if self.pkmn:
                raid_boss = f"{self.pokemon_label}-"
            else:
                raid_boss = f""

        status = self.status
        if status in ["hatched", "expired"]:
            channel_name = f"{self.status}-{raid_boss}{location}"
        else:
            channel_name = f"{raid_boss}{location}"

        return TextUtil.sanitize(channel_name.lower())

    @property
    def url(self):
        return self.raid_location.url

    def type_action_at(self):

        if self.is_egg:
            action = "hatches at"
            timestamp = self.hatches_at
        else:
            action = "ends at"
            timestamp = self.expires_at

        return self.raid_type, action, timestamp

    @property
    def timer_message(self):

        if self.raid_type == 'egg':
            action = "hatch"
            will_action_at = f"will {action} at **{self.hatches_at}**"
        else:
            action = "end"
            will_action_at = f"will {action} at **{self.expires_at}**"

        if not self.active:
            msg = f"The {self.raid_type}'s timer has already expired as of **{self.expires_at}**!"

        # TODO: Add date for EX-raid if self.level == 'EX' or self.raid_type == 'exraid':
        msg = f"This {self.raid_type} {will_action_at}."
        return msg

    async def insert(self):
        raid_table = self.bot.dbi.table('raid_report')
        raid_table_insert = raid_table.insert(**self.get_state())
        await raid_table_insert.commit()
        Raid.cache(raid=self)


    async def update(self):
        raid_table = self.bot.dbi.table('raid_report')
        raid_table_update = raid_table.update(raid_dict=json.dumps(self.get_raid_dict())).where(raid_id=self.id)
        await raid_table_update.commit()
        Raid.cache(raid=self)
        await self.update_messages()
        Logger.info(f"[{self.cuid}] => raid update() finished!")

    async def delete(self):
        """Deletes the raid record from DB and evicts from cache."""
        raid_table = self.bot.dbi.table('raid_report')
        raid_table_delete = raid_table.query().where(raid_id=self.id)
        self.bot.loop.create_task(raid_table_delete.delete())
        Raid.evict(raid=self)
        Logger.info(f"[{self.cuid}] => raid delete() finished!")

    # @classmethod
    # async def select(cls, raid_id):
    #     raid_table = cls.bot.dbi.table('raid_report')
    #     raid_table_delete = raid_table.query().where(raid_id=raid_id)
    #     cls.bot.loop.create_task(await raid_table_delete.delete())
    #     Raid.evict(raid=self)


    async def egg_embed(self):
        return (EggEmbed.from_raid(self)).embed

    async def raid_embed(self):
        return (RaidEmbed.from_raid(self)).embed


    async def expired_embed(self):
        author = await self.guild.fetch_member(self.author_id)

        raid_embed = Embeds.make_embed(content=f"This raid has expired!", msg_color=color())
        raid_embed.set_footer(text=f"Reported by {author.display_name} | Ended at {self.expires_at}")

        return raid_embed



    async def update_messages(self, content=''):
        Logger.info(f"[{self.cuid}] {self.channel_name}")

        try:
            chm_channel, chm_message = await ChannelMessage.from_text(self.bot, self.channel_message)
            if chm_channel and chm_channel.name != self.channel_name:
                try:
                    Logger.info("updating channel name")
                    await chm_channel.edit(name=self.channel_name)
                    Logger.info("updated channel name")
                except Exception as error:
                    Logger.error(error)
            Logger.info(f"Channel name is okay! {chm_channel.name}")

            if self.is_egg and TH.is_in_future(self.hatch_time):
                embed = await self.egg_embed()
            elif TH.is_in_future(self.expiry_time):
                embed = await self.raid_embed()
            else:
                embed = await self.expired_embed()


            if chm_message:
                # Logger.info(f"Updated channel message!")
                await chm_message.edit(embed=embed)

            res_channel, res_message = await ChannelMessage.from_text(self.bot, self.response_message)
            if res_channel and res_message:
                # Logger.info(f"Updated response message!")
                if self.active:
                    await res_message.edit(embed=embed)
                else:
                    await res_message.edit(content=content, embed=embed)

        except Exception as error:
            Logger.info(self.channel_message)
            Logger.error(error)


    def check_expiry(self):
        if self.expiry_time < TH.current_epoch():
            Logger.info(f"#{self.channel_name} is an expired raid.")
            self.expire_task = self.bot.loop.create_task(self.expire_raid())
            return True

        return False

    async def hatch_egg(self):
        Logger.info(f"===========> hatch_egg({self})")
        try:
            channel, message = await ChannelMessage.from_text(self.bot, self.channel_message)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

        self.raid_type = "raid"

        if self.pkmn is None:
            if len(self.raid_level_info.raid_boss_list) == 1:
                raid_boss_id=next(iter(self.raid_level_info.raid_boss_list))
                raid_boss = Pokemon.to_pokemon(raid_boss_id)
                return await self.report_hatch(raid_boss)
            else:
                await Embeds.message(channel, "This raid egg has hatched! Update raid-boss using `!boss`.")
        else:
            await Embeds.message(channel, f"The raid has hatched into a **{self.pkmn}** raid.")

        await self.update()
        self.monitor_task = self.create_task_tuple(self.monitor_status())
        return


    async def report_hatch(self, pkmn: Pokemon):
        cm_chnl, cm_msg = await ChannelMessage.from_text(self.bot, self.channel_message)
        if cm_chnl:
            # TODO: send notification to users about hatch
            self.pkmn = pkmn
            self.raid_type = "raid"
            await Embeds.message(cm_chnl, f"This egg has hatched into a **{pkmn}** raid.")
            await self.update()
            self.monitor_task = self.create_task_tuple(self.monitor_status())





    async def expire_raid(self):
        """ expires the raid, posts a message before clean up, updates embed, deletes channel and raid record"""
        lc = get_counter()
        Logger.info(f"===========> [{self.cuid}]><>[{lc}]<><=> expire_raid({self})")
        try:
            self.bot.loop.create_task(self.update_messages())
            Logger.info(f"[{self.cuid}]><>[{lc}]<><=> Messages update task triggered, will delete channel after 60 seconds.")
            await asyncio.sleep(60)

            if TH.is_in_future(self.expiry_time):
                Logger.info(f"[{self.cuid}]><>[{lc}]<><=> {self.channel_name} hasn't expired yet!")
                self.monitor_task = self.create_task_tuple(self.monitor_status())
                self.expire_task = None
                return


            # TODO: Archive if needed
            channel, message = await ChannelMessage.from_text(self.bot, self.channel_message)
            if channel:
                try:
                    await channel.delete()
                    Logger.info(f"[{self.cuid}]><>[{lc}]<><=> {self.channel_name} delete successful")
                except Exception as error:
                    Logger.info(f"Error while deleting channel : {error}" )
                    pass
            await self.update_messages()
            await self.delete()
        except asyncio.CancelledError:
            Logger.info(f"[{self.cuid}]><>[{lc}]<><=> Task cancelled.")
            self.hatch_task = None
            self.expire_task = None
            self.monitor_task = self.create_task_tuple(self.monitor_status())
            raise
        except Exception as error:
            Logger.error(error)


    async def safe_sleep(self, sleep_time):
        """
        sleeps for provided number of seconds and returns true if the monitor task hasn't changed during sleep
        """
        if sleep_time > 0:
            task_id = self.monitor_task_id
            Logger.info(f"[{self.cuid}] {task_id} => #{self.channel_name} will be checked after {int(sleep_time)} seconds.")
            await asyncio.sleep(sleep_time)
            if task_id == self.monitor_task_id:
                Logger.info(f"[{self.cuid}] [{task_id}] [{self.monitor_task_id}] Monitor task is same.")
                return True
        Logger.info(f"[{self.cuid}] [{task_id}] [{self.monitor_task_id}] Monitor task changed during sleep.")
        return False



    async def monitor_status(self):
        """
        checks the status of the raid and calls hatch_egg or expire_raid after waiting for certain time interval.
        """
        Logger.info(f"===========> [{self.cuid}] => {self.channel_name} => {self.status}")
        try:
            if not TH.is_in_future(self.expiry_time):
                Logger.info(f"[{self.cuid}] {self.channel_name} is expired!")
                self.expire_task = self.create_task_tuple(self.expire_raid())
                return

            if self.pkmn is None:
                if TH.is_in_future(self.hatch_time):
                    sleep_time = self.hatch_time - TH.current_epoch()
                    is_task_stale = not await self.safe_sleep(sleep_time)
                    if is_task_stale:
                        return
                if self.is_egg:
                    self.hatch_task = self.create_task_tuple(self.hatch_egg())
            else:
                if TH.is_in_future(self.expiry_time):
                    sleep_time = self.expiry_time - TH.current_epoch()
                    is_task_stale = not await self.safe_sleep(sleep_time)
                    if is_task_stale:
                        return
                self.expire_task = self.create_task_tuple(self.expire_raid())

        except asyncio.CancelledError:
            Logger.info("handling asyncio.CancelledError")
            # self.monitor_task = None


    async def handle_group_start(self):

        users_starting = {}

        for trainer_id in self.trainer_dict:
            print(trainer_id)

            if self.trainer_dict[trainer_id]['status'] in ["h", "hr", "ir"]:
                trainer = self.bot.get_user(int(trainer_id))
                users_starting[trainer_id] = trainer.mention

        for trainer_id in users_starting:
            del self.trainer_dict[trainer_id]

        if len(users_starting) > 0:
            embed_message = f"The group of trainers waiting are starting the raid. Trainers {', '.join(users_starting.values())}, please respond using `!h` or `!hr` if you waiting for another group."
            await Embeds.message(self.channel, description=embed_message)
        else:
            embed_message = f"How can you start when there is nobody waiting at the raid?"
            await Embeds.error(self.channel, description=embed_message)




def get_emoji(pokemon_type):
    if pokemon_type:
        key = pokemon_type.replace("POKEMON_TYPE_","").lower()
        return config_template.type_emoji[key]


class RaidEmbed:
    raid_icon = 'https://i.imgur.com/uRhgISs.png'

    class Position(Enum):
        BOSS = 0,
        GYM = 1,
        WEAK = 2,
        RESIST = 3,
        CP = 4,
        START = 5


    def __init__(self, embed):
        self.embed = embed

    def set_boss(self, boss_dict):
        name = boss_dict.get('name','name')
        self.embed.set_field_at(RaidEmbed.Position.BOSS, name="Boss", value=name)

    @classmethod
    def from_raid(cls, raid: Raid):
        boss = raid.pkmn
        bot = raid.bot

        if boss:
            field_title = "Boss"
            name = f"{boss.extended_label}"
            img_url = boss.preview_url
            weakness = f"{boss.weaknesses_icon}"
            cp_range = f"{boss.raid_cp_range}"
            # Logger.info(f"Weaknesses: {boss.weaknesses}")
        else:
            field_title = "Possible Bosses:"
            name = '\n'.join([Pokemon.to_pokemon(raid_boss).extended_label for raid_boss in RaidMaster.get_boss_list(raid.level)])
            img_url = get_egg_image_url(raid.level)
            weakness = None
            cp_range = None


        raid_location = raid.raid_location
        color = raid.guild.me.color

        author = raid.guild.get_member(raid.author_id)
        if author:
            footer_icon = Icons.avatar(author)

        start = None
        if raid.start_time:
            start = raid.starts_at

        footer = f"{raid.cuid} | Reported by {author.display_name} | {raid.timer_info()}"

        fields = {
            f"**{field_title}**" : name,
            "**Where**" : raid_location.gym_embed_label,
            "**Weaknesses**" : weakness,
            "**CP Range**" : cp_range,
            "**Suggested Start**" : start,
        }

        embed = Embeds.make_embed(header="Raid Report", header_icon=Icons.raid_report, thumbnail=img_url, fields=fields,
                                  footer=footer, footer_icon=footer_icon, msg_color=color)

        return cls(embed)




class EggEmbed:
    raid_icon = 'https://media.discordapp.net/attachments/423492585542385664/512682888236367872/imageedit_1_9330029197.png'

    class Position(Enum):
        CHANNEL = 0,
        LEVEL = 1,
        GYM = 2,


    def __init__(self, embed):
        self.embed = embed

    def set_boss(self, boss_dict):
        name = boss_dict.get('name','name')
        self.embed.set_field_at(RaidEmbed.Position.BOSS, name="Boss", value=name)

    @classmethod
    def from_raid(cls, raid: Raid):
        level = raid.level
        bot = raid.bot

        raid_location = raid.raid_location
        color = raid.guild.me.color
        img_url = get_egg_image_url(level)
        author = raid.guild.get_member(raid.author_id)
        if author:
            footer_icon = Icons.avatar(author)

        footer = f"{raid.cuid} | Reported by {author.display_name} | {raid.timer_info()}"

        raid_boss_list = '\n'.join([Pokemon.to_pokemon(raid_boss).extended_label for raid_boss in RaidMaster.get_boss_list(level)])

        fields = {
            "**Level**" : f"{level}",
            "**Where**" : f"{raid_location.gym_embed_label}",
            "**Possible Bosses**" : f"{raid_boss_list}"
        }

        embed = Embeds.make_embed(header="Raid Report", header_icon=Icons.raid_report, thumbnail=img_url, fields=fields,
                                  footer=footer, footer_icon=footer_icon, msg_color=color)

        return cls(embed)


class RosterLocationEmbed:

    def __init__(self, embed):
        self.embed = embed

    @classmethod
    def from_roster_location(cls, rl: RosterLocation):

        if rl.raid_boss == "egg":
            img_url = get_egg_image_url(5)
        else:
            pkmn = Pokemon.to_pokemon(rl.raid_boss)
            img_url = pkmn.preview_url

        fields = {
            "**Raid Boss**" : f"{rl.raid_boss}",
            "**Location**" : f"{rl.raid_at}"
        }
        embed = Embeds.make_embed(title="Roster Location Details Report", thumbnail=img_url, fields=fields,
                                  msg_color=color)
        return cls(embed)



class RaidPartyEmbed:


    def __init__(self, embed):
        self.embed = embed

    @classmethod
    def from_raid_party(cls, raid_party: RaidParty):
        raid_party_image_url = "https://media.discordapp.net/attachments/419935483477622793/450201828802560010/latest.png"
        description = cls.get_roster_message(raid_party)

        current = raid_party.current_location

        embed = Embeds.make_embed(header="Raid Party Roster", header_icon="https://i.imgur.com/iX5yWVW.png",
                                  title=f"Click here for directions to location {raid_party.current_location_index}",
                                  title_url=current.poi_location.url, content=description,
                                  thumbnail=raid_party_image_url, msg_color=color)
        return cls(embed)

    @classmethod
    def get_roster_message(self, raid_party: RaidParty):

        roster_message = ""
        index = raid_party.current_location_index
        for rloc in raid_party.roster:

            # emoji = "egg" if rloc.raid_boss == "egg" else rloc.raid_boss.emoji

            roster_message += f"{emojify_numbers(index)} {rloc.poi_location} - {rloc.raid_boss} - {rloc.eta}\n"
            index = index + 1

        return roster_message

def get_egg_image_url(egg_level):
    # url = icon_list.get(str(pokedex_number))
    url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/eggs/{0}.png?cache={1}".format(str(egg_level),30)
    if url:
        return url
    else:
        return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=egg_level)


numbers = {
    "0": ":zero:",
    "1": ":one:",
    "2": ":two:",
    "3": ":three:",
    "4": ":four:",
    "5": ":five:",
    "6": ":six:",
    "7": ":seven:",
    "8": ":eight:",
    "9": ":nine:"
}


def emojify_numbers(number):
    number_emoji = ""

    reverse = "".join(reversed(str(number)))

    for digit in reverse[::-1]:
        number_emoji = number_emoji + numbers.get(digit)

    return number_emoji

class RaidRepository:
    _dbi = None

    def __init__(self):
        pass

    @classmethod
    def set_dbi(cls, dbi):
        cls._dbi = dbi

    @classmethod
    async def find_raid_for_channel(cls, guild_id, channel_id):
        raid_table = cls._dbi.table('raid_report')
        raid_table_query = raid_table.query().select().where(guild_id=guild_id, channel_id=channel_id)
        list_of_raids = await raid_table_query.getjson()
        return list_of_raids[0]

    @classmethod
    async def find_raid_by_id(cls, raid_report_id):
        raid_table = cls._dbi.table('raid_report')
        raid_table_query = raid_table.query().select().where(raid_report_id=raid_report_id)
        list_of_raids = await raid_table_query.getjson()
        return list_of_raids[0]


    @classmethod
    async def find_raids(cls):
        raid_table = cls._dbi.table('raid_report')
        raid_table_query = raid_table.query().select()
        list_of_raids = await raid_table_query.getjson()
        return list_of_raids

    @classmethod
    async def find_raid_parties(cls):
        raid_table = cls._dbi.table('raid_party_report')
        raid_table_query = raid_table.query().select()
        list_of_raids = await raid_table_query.getjson()
        return list_of_raids


class DiscordOperations:

    def __init__(self, bot: discord.Client):
        self.bot = bot



    async def create_channel(self, ctx, raid: Raid):
        try:
            channel, message = await ChannelMessage.from_text(self.bot, raid.report_message)

            raid_channel = await ctx.guild.create_text_channel(raid.channel_name, overwrites=dict(channel.overwrites),
                                                category=ctx.guild.get_channel(channel.category_id))
            return raid_channel
        except discord.Forbidden:
                raise commands.BotMissingPermissions(['Manage Channels'])



    @staticmethod
    async def send_raid_response(raid: Raid, raid_embed, ref_channel: discord.TextChannel):
        channel, message = await ChannelMessage.from_text(raid.bot, raid.report_message)
        author = message.author

        raid_response_message = await channel.send(
            content=f"{MyEmojis.INFO} Coordinate the raid in {ref_channel.mention}", embed=raid_embed)

        return raid_response_message

    @staticmethod
    async def send_raid_channel_message(raid: Raid, raid_embed, raid_channel: discord.TextChannel):
        channel, message = await ChannelMessage.from_text(raid.bot, raid.report_message)
        city_channel = channel

        raid_channel_message = await raid_channel.send(
            content=f"{MyEmojis.INFO} Raid reported in {city_channel.mention}! Coordinate here!",
            embed=raid_embed)

        return raid_channel_message


class DiscordException(ValueError):
    pass


class InvalidDiscordIdException(ValueError):
    pass


class InvalidRaidLevelError(ValueError):
    pass

    # TODO: handle suggested start time
    # TODO: handle ex-raid
    # raid_time_value = fetch_channel_expire_time(message.channel.id).strftime("%I:%M %p (%H:%M)")
    # raid_time_label = "Raid Expires At"
    # if rc_d['type'] == 'egg':
    #     raid_time_label = "Egg Hatches At"
    #     if rc_d['egglevel'] == 'EX':
    #         raid_time_value = fetch_channel_expire_time(message.channel.id).strftime(
    #             "%B %d %I:%M %p (%H:%M)")
#
#     start_time = fetch_channel_start_time(message.channel.id)
#     start_time_label = "None"
#     if start_time:
#         raid_time_label = raid_time_label + " / Suggested Start Time"
#         raid_time_value = raid_time_value + " / " + start_time.strftime("%I:%M %p (%H:%M)")
#
#     additional_fields[raid_time_label] = raid_time_value

