import asyncio
import json

from clembot.config import config_template
from clembot.config.constants import Icons
from clembot.core.logs import Logger
from clembot.exts.draft.draft import CUIDGenerator
from clembot.exts.gymmanager.gym import POILocation
from clembot.exts.pkmn.pokemon import Pokemon
from clembot.exts.raid.raid import ChannelMessage
from clembot.utilities.timezone import timehandler as TH
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.snowflake import Snowflake


class Wild:
    by_id = dict()
    by_message = dict()

    def __init__(self, bot, wild_id, guild_id, reporter_id, pkmn: Pokemon, location: POILocation = None, timezone=None,
                 caught_by=None,
                 message_id=None, channel_id=None, reported_time=None, despawn_time=None):
        self.bot = bot
        self.wild_id = wild_id
        self.guild_id = guild_id
        self.reporter_id = reporter_id
        self.location = location
        self.pkmn = pkmn
        self.reported_time = TH.current_epoch(second_precision=True) if reported_time is None else reported_time
        self.despawn_time = self.reported_time + (config_template.development_timer or 30) * 60 if despawn_time is None else despawn_time
        self.message_id = message_id
        self.channel_id = channel_id
        self.caught_by = caught_by or []
        self.timezone = timezone
        self.monitor_task_tuple = None
        self.snowflake = Snowflake()

    def to_db_dict(self):
        state = {
            'wild_id': self.wild_id,
            'guild_id': self.guild_id,
            'reporter_id': self.reporter_id,
            'pokemon_id': self.pkmn.id,
            'location': json.dumps(self.location.to_dict()),
            'reported_time': self.reported_time,
            'despawn_time': self.despawn_time,
            'message_id': self.message_id,
            'channel_id': self.channel_id,
            'timezone': self.timezone
        }
        return state


    @classmethod
    async def from_db_dict(cls, bot, db_dict):

        wild_id, guild_id, reporter_id, pokemon_id, location, reported_time, despawn_time, message_id, channel_id, timezone = [
            db_dict.get(attr, None) for attr in
            ['wild_id', 'guild_id', 'reporter_id', 'pokemon_id', 'location', 'reported_time', 'despawn_time',
             'message_id',
             'channel_id', 'timezone']]

        pkmn = Pokemon.to_pokemon(pokemon_id) if pokemon_id else None
        wild_location = await POILocation.from_dict(bot, json.loads(location))

        wild = cls(bot, wild_id=wild_id, guild_id=guild_id, reporter_id=reporter_id,
                   pkmn=pkmn, location=wild_location, timezone=timezone,
                   message_id=message_id, channel_id=channel_id,
                   reported_time=reported_time, despawn_time=despawn_time)

        Wild.cache(wild)
        return wild


    def create_task_tuple(self, coro):
        task_id = CUIDGenerator.cuid(self.snowflake.next())
        return self.bot.loop.create_task(coro), task_id


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
            self.monitor_task.cancel()
        self.monitor_task_tuple = task_tuple


    @property
    def reported_at(self):
        """as Readable time"""
        # TODO: add guild timezone
        return TH.as_local_readable_time(self.reported_time, self.timezone)


    def timer_info(self):
        timer_info = f"Reported at: {self.reported_at}" if self.reported_time else ""
        return timer_info


    @classmethod
    def cache(cls, wild):
        cls.by_message[wild.message_id] = wild
        cls.by_id[wild.wild_id] = wild


    @classmethod
    def evict(cls, wild):
        cls.by_message.pop(wild.message_id, None)
        cls.by_id.pop(wild.wild_id, None)


    def set_message(self, message):
        self.message_id = message.id
        self.channel_id = message.channel.id


    @staticmethod
    async def find_all(bot):
        wild_table = bot.dbi.table('wild_report')
        wild_table_query = wild_table.query().select()
        record_list = await wild_table_query.getjson()
        return record_list


    async def insert(self):
        wild_table = self.bot.dbi.table('wild_report')
        wild_table_insert = wild_table.insert(**self.to_db_dict())
        await wild_table_insert.commit()
        Wild.cache(self)


    async def delete(self):
        wild_table = self.bot.dbi.table('wild_report')
        wild_table_delete = wild_table.query().where(wild_id=self.wild_id)
        await wild_table_delete.delete()
        Wild.evict(self)


    def wild_embed(self, ctx):
        return (WildEmbed.from_wild_report(ctx, self)).embed


    def expire_embed(self):
        return (WildEmbed.expire_embed(self)).embed


    async def despawn(self):
        try:
            channel, message = await ChannelMessage.from_id(self.bot, self.channel_id, self.message_id)
            embed = self.expire_embed()
            await message.edit(content="", embed=embed)
            await message.clear_reactions()
        except Exception as error:
            Logger.info(error)

        await self.delete()
        self.monitor_task = None


    async def monitor_status(self):
        Logger.info(f"{self.pkmn.label} at {self.location}")
        sleep_time = self.despawn_time - TH.current_epoch()
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

        await self.despawn()


class WildEmbed:

    def __init__(self, embed):
        self.embed = embed

    @classmethod
    def from_wild_report(cls, ctx, wild: Wild):
        location = wild.location
        color = ctx.guild.me.color
        img_url = wild.pkmn.preview_url
        author = ctx.guild.get_member(wild.reporter_id)
        if author:
            footer_icon = Icons.avatar(author)

        footer = f"Reported by {author.display_name} | {wild.timer_info()}"

        fields = {
            "**Pokemon**": [True, f"{wild.pkmn.extended_label}"],
            "**Where**": [True, f"{location.embed_label}"],
            "**Reaction(s)**": [False, f":dash: - Despawned!"]
        }

        embed = Embeds.make_embed(header="Wild Report", header_icon=Icons.wild_report, thumbnail=img_url, fields=fields,
                                  footer=footer, footer_icon=footer_icon, msg_color=color)

        return cls(embed)

    @classmethod
    def expire_embed(cls, wild: Wild):
        footer = f"{wild.timer_info()}"

        embed = Embeds.make_embed(header="Wild Report", header_icon=Icons.wild_report,
                                  content=f"The {wild.pkmn.label} has despawned!", footer=footer
                                  )

        return cls(embed)
