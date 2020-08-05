import json

import discord
import pydash as _

from clembot.config.constants import Icons

"""
create table guild_metadata (
    guild_id bigint not null unique,
    prefix text,
    city text,
    timezone text,
    welcome boolean,
    teams boolean,
    config text
);


create table guild_config (
    id,
    guild_id,
    config_name,
    config_value
);
"""

class GuildMetadata:


    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

    def __eq__(self, other):
        return self.guild.id == other.guild.id

    @property
    def _data(self):
        report_guild_query = self.bot.dbi.table('guild_metadata').query()
        _data = report_guild_query.where(guild_id=self.guild.id)
        return _data


    @classmethod
    async def data(cls, bot, guild_id, config_name):

        report_guild_query = bot.dbi.table('guild_metadata').query()
        _data = report_guild_query.where(guild_id=guild_id, config_name=config_name)
        db_record = await _data.get()

        if db_record:
            guild_metadata = GuildMetadata.deserialize(dict(db_record[0]))
            return guild_metadata

        return {}

    @classmethod
    async def city(cls, bot, guild_id):
        guild_dict = await GuildMetadata.data(bot, guild_id, 'city')
        return guild_dict.get('config_value')

    @classmethod
    async def bingo_card_repo(cls, bot, guild_id):
        guild_dict = await GuildMetadata.data(bot, guild_id, 'bingo-card-repo') or {}
        return guild_dict.get('config_value')

    @staticmethod
    def serialize(data_dict):
        return _.map_values(data_dict, lambda val: json.dumps(val) if isinstance(val, dict) else val)

    @staticmethod
    def deserialize(data_dict):
        return { k :json.loads(v) if k == 'config' and v is not None else v for (k, v) in data_dict.items()}


    @classmethod
    async def update(cls, bot, guild_dict):
        guild_metadata_table = bot.dbi.table('guild_metadata')
        update_dict=GuildMetadata.serialize(guild_dict)
        guild_metadata_table_update = guild_metadata_table.update(**update_dict).where(guild_id=guild_dict.get('guild_id'))
        await guild_metadata_table_update.commit()
        GuildMetadata.cache(guild_dict)

    @classmethod
    async def insert(cls, bot, guild_dict):
        guild_metadata_table = bot.dbi.table('guild_metadata')
        update_dict = GuildMetadata.serialize(guild_dict)
        guild_metadata_table_insert = guild_metadata_table.insert(**update_dict)
        await guild_metadata_table_insert.commit()
        GuildMetadata.cache(guild_dict)

    @staticmethod
    def embed(ctx, guild_dict):
        return (GuildMetadataEmbed.from_guild_metadata(ctx, guild_dict)).embed


class GuildMetadataEmbed:

    def __init__(self, embed):
        self.embed = embed



    @classmethod
    def from_guild_metadata(cls, metadata = dict, title=None, icon_url=None):

        if not title:
            title = "Here are the current configurations for this guild"

        embed = discord.Embed(title=title)

        if not icon_url:
            icon_url = Icons.configure
        embed.set_author(name="Guild Configuration", icon_url=icon_url)

        embed.add_field(name="**Prefix**", value=metadata.get('prefix'), inline=True)
        embed.add_field(name="**City**", value=metadata.get('city'), inline=True)
        embed.add_field(name="**Timezone**", value=metadata.get('timezone'), inline=True)

        return cls(embed)


