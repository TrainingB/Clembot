import discord
import pydash as _
import json

from clembot.config.constants import Icons


class ChannelMetadata:

    by_channel = dict()
    _in_progress_config_channels = []

    def __init__(self, bot, channel):
        self.bot = bot
        self.channel = channel

    def __eq__(self, other):
        return self.channel.id == other.channel.id

    @classmethod
    def begin_configuration(cls, channel_id):
        cls._in_progress_config_channels.append(channel_id)


    @classmethod
    def end_configuration(cls, channel_id):
        if cls.config_in_progress(channel_id):
            cls._in_progress_config_channels.remove(channel_id)

    @classmethod
    def config_in_progress(cls, channel_id):
        return channel_id in cls._in_progress_config_channels


    @property
    def _data(self):
        report_channel_query = self.bot.dbi.table('channel_metadata').query()
        _data = report_channel_query.where(channel_id=self.channel.id)
        return _data

    @classmethod
    def cache(cls, channel_dict):
        ChannelMetadata.by_channel[channel_dict.get('channel_id')] = channel_dict


    @classmethod
    async def data(cls, bot, channel_id):

        channel_metadata = ChannelMetadata.by_channel.get(channel_id)
        if channel_metadata:
            return channel_metadata

        report_channel_query = bot.dbi.table('channel_metadata').query()
        _data = report_channel_query.where(channel_id=channel_id)
        db_record = await _data.get()

        if db_record:
            channel_metadata = ChannelMetadata.deserialize(dict(db_record[0]))

        ChannelMetadata.cache(channel_metadata)
        return channel_metadata

    @classmethod
    async def city(cls, bot, channel_id):
        channel_dict = await ChannelMetadata.data(bot, channel_id)
        return channel_dict.get('city')

    @staticmethod
    def serialize(data_dict):
        return _.map_values(data_dict, lambda val: json.dumps(val) if isinstance(val, dict) else val)

    @staticmethod
    def deserialize(data_dict):
        return { k :json.loads(v) if k == 'config' and v is not None else v for (k, v) in data_dict.items()}


    @classmethod
    async def update(cls, bot, channel_dict):
        channel_metadata_table = bot.dbi.table('channel_metadata')
        update_dict=ChannelMetadata.serialize(channel_dict)
        channel_metadata_table_update = channel_metadata_table.update(**update_dict).where(channel_id=channel_dict.get('channel_id'))
        await channel_metadata_table_update.commit()
        ChannelMetadata.cache(channel_dict)

    @classmethod
    async def insert(cls, bot, channel_dict):
        channel_metadata_table = bot.dbi.table('channel_metadata')
        update_dict = ChannelMetadata.serialize(channel_dict)
        channel_metadata_table_insert = channel_metadata_table.insert(**update_dict)
        await channel_metadata_table_insert.commit()
        ChannelMetadata.cache(channel_dict)

    @staticmethod
    def embed(ctx, channel_dict):
        return (ChannelConfigEmbed.from_channel_metadata(ctx, channel_dict)).embed

    @staticmethod
    def success_embed(ctx, channel_dict):
        embed = (ChannelConfigEmbed.from_channel_metadata(ctx, channel_dict, "Configuration has been updated successfully.", Icons.configure_success)).embed
        return embed

    @staticmethod
    def failure_embed(ctx, channel_dict):
        embed = (ChannelConfigEmbed.from_channel_metadata(ctx, channel_dict, "No configuration changes done.", Icons.configure_failure)).embed
        return embed


class ChannelConfigEmbed:

    def __init__(self, embed):
        self.embed = embed

    FEATURES = ['raid', 'wild', 'nest', 'research', 'trade', 'rocket']

    @classmethod
    def from_channel_metadata(cls, ctx, metadata = dict, title=None, icon_url=None):

        labels = {
            'raid' : 'Raid Reports',
            'wild' : 'Wild Reports',
            'nest' : 'Nest Reports',
            'research': 'Research Reports',
            'rocket' : 'Grunt Reports',
            'trade' : 'Trade'
        }

        enabled_features = "\n".join([labels.get(feature) for feature in ChannelConfigEmbed.FEATURES if metadata.get(feature, False) and feature in labels.keys()])

        disabled_features = "\n".join([labels.get(feature) for feature in ChannelConfigEmbed.FEATURES if not metadata.get(feature) and feature in labels.keys()])

        categories = (metadata.get('config') or {}).get('categories')
        if categories:
            category_name = ', '.join([ctx.get.category(int(category_id)).name for category_id in categories.values()])
        else:
            category = metadata['category']
            if category:
                category_name = ctx.get.category(int(category)).name if category.isdigit() else None
            else:
                category_name = None

        if not title:
            title = "Here are the current configurations for this channel"

        embed = discord.Embed(title=title)

        if not icon_url:
            icon_url = Icons.configure
        embed.set_author(name="Channel Configuration", icon_url=icon_url)

        embed.add_field(name="**City**", value=f"{metadata['city']}", inline=False)
        if category_name:
            embed.add_field(name="**Category**", value=category_name, inline=False)

        embed.add_field(name="**:white_check_mark: Enabled Features**", value=enabled_features if len(enabled_features) > 0 else '-', inline=True)
        embed.add_field(name="**:negative_squared_cross_mark: Disabled Features**", value=disabled_features if len(disabled_features) > 0 else '-', inline=True)


        return cls(embed)


