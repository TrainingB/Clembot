import discord
import pydash as _
import json

from clembot.config.constants import Icons


class GuildMetadata:

    # guild_id bigint not null unique,
    # prefix text,
    # timezone text,
    # city text,
    # config text

    by_guild = dict()

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
    def cache(cls, guild_dict):
        GuildMetadata.by_guild[guild_dict.get('guild_id')] = guild_dict


    @classmethod
    async def data(cls, bot, guild_id):

        guild_metadata = GuildMetadata.by_channel.get(guild_id)
        if guild_metadata:
            return guild_metadata

        report_guild_query = bot.dbi.table('guild_metadata').query()
        _data = report_guild_query.where(guild_id=guild_id)
        db_record = await _data.get()

        if db_record:
            guild_metadata = GuildMetadata.deserialize(dict(db_record[0]))

        GuildMetadata.cache(guild_metadata)
        return guild_metadata

    @classmethod
    async def city(cls, bot, guild_id):
        guild_dict = await GuildMetadata.data(bot, guild_id)
        return guild_dict.get('city')

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

    FIELDS = ['prefix', 'city', 'timezone']

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


