import json

import discord
import pydash as _

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
    def evict(cls, channel_id):
        ChannelMetadata.by_channel.pop(channel_id, None)


    @classmethod
    async def find(cls, bot, channel_id, guild_id = None):

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

        if guild_id:
            await ChannelMetadata.insert(bot, {'channel_id': channel_id, 'guild_id': guild_id})
        return ChannelMetadata.by_channel.get(channel_id)


    @classmethod
    async def city(cls, bot, channel_id):
        channel_dict = await ChannelMetadata.find(bot, channel_id)
        if channel_dict:
            return channel_dict.get('city')
        raise Exception("City has not been set for this channel.")

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
        insert_dict = ChannelMetadata.serialize(channel_dict)
        channel_metadata_table_insert = channel_metadata_table.insert(**insert_dict)
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

    @staticmethod
    def profile_embed(ctx, channel_dict, title=None):
        return (ChannelConfigEmbed.from_channel_profile(ctx, channel_dict, title)).embed


class ChannelConfigEmbed:

    def __init__(self, embed):
        self.embed = embed

    FEATURES = ['raid', 'wild', 'nest', 'research', 'trade', 'rocket']

    @classmethod
    def from_channel_profile(cls, ctx, metadata = dict, title = None, icon_url = None):

        embed = discord.Embed(title=title, colour=discord.Color.blue())

        if not icon_url:
            icon_url = Icons.configure
        embed.set_author(name="Channel Configuration", icon_url=icon_url)

        embed.add_field(name=f"**City**", value=f"{metadata['city']}", inline=False)
        # for key in ChannelConfigEmbed.FEATURES:
        #     embed.add_field(name=f"**{key.capitalize()}**", value=f"{metadata[key]}", inline=True)

        # embed.add_field(name="**:white_check_mark: Enabled Features**", value=enabled_features if len(enabled_features) > 0 else '-', inline=True)
        # embed.add_field(name="**:negative_squared_cross_mark: Disabled Features**", value=disabled_features if len(disabled_features) > 0 else '-', inline=True)
        #
        # embed.set_footer(text=f"Use `!feature enable` or `!feature disable` to enable/disable features.")

        return cls(embed)


        pass


    @classmethod
    def from_channel_metadata(cls, ctx, metadata = dict, title=None, icon_url=None):

        labels = {
            'raid' : 'Raid Reports (raid)',
            'wild' : 'Wild Reports (wild)',
            'nest' : 'Nest Reports (nest)',
            'research': 'Research Reports(research)',
            'rocket' : 'Grunt Reports (rocket)',
            'trade' : 'Trade (trade)'
        }

        enabled_features = "\n".join([labels.get(feature) for feature in ChannelConfigEmbed.FEATURES if metadata.get(feature, False) and feature in labels.keys()])

        disabled_features = "\n".join([labels.get(feature) for feature in ChannelConfigEmbed.FEATURES if not metadata.get(feature) and feature in labels.keys()])

        categories = (metadata.get('config') or {}).get('categories')
        if categories:
            category_name = ', '.join([ctx.get.category(int(category_id)).name for category_id in categories.values()])
        else:
            category = metadata.get('category', None)
            if category:
                category_name = ctx.get.category(int(category)).name if category.isdigit() else None
            else:
                category_name = None

        if not title:
            title = "Here are the current configurations for this channel"

        embed = discord.Embed(title=title, colour=discord.Color.blue())

        if not icon_url:
            icon_url = Icons.configure
        embed.set_author(name="Channel Configuration", icon_url=icon_url)

        embed.add_field(name="**City**", value=f"{metadata['city']}", inline=False)
        if category_name:
            embed.add_field(name="**Category**", value=category_name, inline=False)

        embed.add_field(name="**:white_check_mark: Enabled Features**", value=enabled_features if len(enabled_features) > 0 else '-', inline=True)
        embed.add_field(name="**:negative_squared_cross_mark: Disabled Features**", value=disabled_features if len(disabled_features) > 0 else '-', inline=True)

        embed.set_footer(text=f"Use `!feature enable` or `!feature disable` to enable/disable features.")

        return cls(embed)


