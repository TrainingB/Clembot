from discord.ext import commands
from clembot.config import config_template
from clembot.core.logs import init_loggers
from clembot.core import checks
from clembot.exts.utils.utilities import Utilities, EmbedUtil
from clembot.exts.config.channelconfigmanager import ChannelConfigCache

import asyncio
import discord
import json


class Gym:
    attributes = ['city_state', 'gym_code', 'gym_display_name', 'gym_name', 'latitude', 'longitude',
                  'gym_city', 'gym_state', 'gym_url', 'gym_image', 'gym_tags']

    def __init__(self, data_dict):
        self.__dict__.update(data_dict)

    def __repr__(self):
        return f'Gym({self.gym_code}, {self.city_state}, {self.gym_name}, ({self.latitude},{self.longitude}))'

    def __getitem__(self, item):
        return self.to_dict()[item]

    @property
    def summary(self):
        return f"Gym#[{self.gym_id}] {self.gym_name} in {self.gym_city}, {self.gym_state}"

    @classmethod
    def from_dict(cls, gym_data: {}):
        return cls(gym_data)

    def to_dict(self):
        return self.__dict__

    def to_db_dict(self):
        return {
            'city_state': self.city_state,
            'gym_code': self.gym_code,
            'gym_display_name': self.gym_display_name,
            'gym_name': self.gym_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'gym_city': self.gym_city,
            'gym_state': self.gym_state,
            'gym_url': self.gym_url,
            'gym_alias': self.gym_alias,
            'gym_image': self.gym_image,
            'gym_tags': self.gym_tags,
            'gym_metadata': self.gym_metadata,
        }

    @property
    def gym_id(self):
        return self.__dict__.get('gym_id')

    @gym_id.setter
    def gym_id(self, gym_id):
        self.__dict__['id'] = gym_id

    @property
    def gym_code(self):
        return self.__dict__.get('gym_code')

    @gym_code.setter
    def gym_code(self, gym_code):
        self.__dict__['gym_code'] = gym_code

    @property
    def gym_name(self):
        return self.__dict__.get('gym_name')

    @gym_name.setter
    def gym_name(self, gym_name):
        self.__dict__['gym_name'] = gym_name

    @property
    def city_state(self):
        return self.__dict__.get('city_state')

    @city_state.setter
    def city_state(self, city_state):
        self.__dict__['city_state'] = city_state

    @property
    def latitude(self):
        return self.__dict__.get('latitude')

    @latitude.setter
    def latitude(self, latitude):
        self.__dict__['latitude'] = latitude

    @property
    def longitude(self):
        return self.__dict__.get('longitude')

    @longitude.setter
    def longitude(self, longitude):
        self.__dict__['longitude'] = longitude

    @property
    def gym_url(self):
        return self.__dict__.get('gym_url')

    @gym_url.setter
    def gym_url(self, gym_url):
        self.__dict__['gym_url'] = gym_url

    @property
    def gym_display_name(self):
        return self.__dict__.get('gym_display_name')

    @gym_display_name.setter
    def gym_display_name(self, gym_display_name):
        self.__dict__['gym_display_name'] = gym_display_name

    @property
    def gym_alias(self):
        return self.__dict__.get('gym_alias')

    @gym_alias.setter
    def gym_alias(self, gym_alias):
        self.__dict__['gym_alias'] = gym_alias

    @property
    def gym_image(self):
        return self.__dict__.get('gym_image')

    @gym_image.setter
    def gym_image(self, gym_image):
        self.__dict__['gym_image'] = gym_image

    @property
    def gym_metadata(self):
        return self.__dict__.get('gym_metadata')

    @gym_metadata.setter
    def gym_metadata(self, gym_metadata):
        self.__dict__['gym_metadata'] = gym_metadata

    @property
    def gym_tags(self):
        return self.__dict__.get('gym_tags')

    @gym_tags.setter
    def gym_tags(self, gym_tags):
        self.__dict__['gym_tags'] = gym_tags

    @property
    def gym_city(self):
        return self.__dict__.get('gym_city')

    @property
    def gym_state(self):
        return self.__dict__.get('gym_state')




    default_dict = [{
        "gym_name": "Name of the Gym",
        "latitude": 00.00000,
        "longitude": 00.00000,
        "gym_city": "CITY",
        "gym_state": "ST",
        "gym_display_name": "optional, uses gym_name",
        "gym_code": "optional, auto-generated"
    }]

    extended_dict = {
        "gym_display_name": "Gym Display Name",
        "gym_alias": ["alias1"],
        "gym_image": "image",
        "gym_code": "gym_code"
    }


class GymRepository:
    _dbi = None
    logger = init_loggers()

    def __init__(self):
        pass

    @classmethod
    def set_dbi(cls, dbi):
        cls._dbi = dbi

    @classmethod
    def get_status(cls):
        is_dbi_set = cls._dbi is not None

        return is_dbi_set

    @classmethod
    async def search_by(cls, gym_code_or_name, city=None):
        try:
            gym_code_or_name = gym_code_or_name.upper()

            if gym_code_or_name:

                gym_table = cls._dbi.table('gym')
                gym_code_query = gym_table.query().select().where(gym_table['gym_code'].like(f'%{gym_code_or_name}%'), city_state=city).order_by('gym_code')

                list_of_gym = await gym_code_query.getjson()
                cls.logger.info(f"search_by({gym_code_or_name}, {city}) : {len(list_of_gym)} record(s) found!")

                if len(list_of_gym) == 0:
                    gym_name_query = cls._dbi.table('gym').query().select().where(gym_table['gym_name'].ilike(f'%{gym_code_or_name}%'),city_state=city).order_by('gym_code')
                    list_of_gym = await gym_name_query.getjson()

                return list_of_gym

        except Exception as error:
            cls.logger.error(error)

        return None


    @classmethod
    async def search_by_gym_code_city(cls, gym_code: str, city=None) -> list:
        gym_table = cls._dbi.table('gym')
        gym_table_query = gym_table.query().select().where(gym_code=gym_code.upper(), city_state=city.upper())
        list_of_gym = await gym_table_query.getjson()
        return list_of_gym

    @classmethod
    async def search_by_id(cls, gym_id: int):
        gym_table = cls._dbi.table('gym')
        gym_table_query = gym_table.query().select().where(gym_id=gym_id)
        list_of_gym = await gym_table_query.getjson()
        return list_of_gym

    @classmethod
    async def create(cls, **kwargs):
        gym_table = cls._dbi.table('gym')
        gym_table_insert = gym_table.insert(**kwargs)
        await gym_table_insert.commit()

    @classmethod
    async def update(cls, gym_id: int, attribute: str, value=None):
        gym_table = cls._dbi.table('gym')
        update_dict = {attribute: value}
        gym_table_update = gym_table.update(**update_dict).where(gym_id=gym_id)
        await gym_table_update.commit()

class CityConfigAdapter:

    _dbi = None
    logger = init_loggers()

    def __init__(self):
        pass

    @classmethod
    def set_dbi(cls, dbi):
        cls._dbi = dbi

    @staticmethod
    async def get_city_for_channel(guild_id, channel_id=None, parent_channel_id=None) -> str :
        try:
            city_for_channel = await CityConfigAdapter._get_config_by('city', guild_id=guild_id, channel_id=channel_id)

            if not city_for_channel:
                if parent_channel_id:
                    city_for_channel = await CityConfigAdapter._get_config_by('city', guild_id=guild_id, channel_id=parent_channel_id)

            # if not city_for_channel:
            #     city_for_channel = await CityConfigAdapter.MyGuildConfigCache.get_guild_config(guild_id=guild_id, config_name='city')
            return city_for_channel

        except Exception as error:
            print(error)
            CityConfigAdapter.logger.info(error)
            return None

    @staticmethod
    async def _get_config_by(config_name, **kwargs):
        try:

            guild_channel_config_tbl = CityConfigAdapter._dbi.table('guild_channel_config')
            kwargs.update(config_name=config_name)

            guild_channel_query = guild_channel_config_tbl.query().select().where(**kwargs)

            config_record = await guild_channel_query.get_first()
            if config_record:
                config_value = dict(config_record)['config_value']
                if config_value:
                    return config_value
        except Exception as error:
            CityConfigAdapter.logger.error(error)
        return None


class GymAdapter:




    @staticmethod
    async def to_gym_by_code(gym_code, message) -> Gym:
        city = await CityConfigAdapter.get_city_for_channel(message.guild.id, message.channel.id)
        list_of_gym = await GymRepository.search_by_gym_code_city(gym_code, city)
        gym = Gym.from_dict(list_of_gym[0]) if len(list_of_gym) > 0 else None

        if not gym:
            print(f"===> Gym for ({gym_code}, {city}) not found. GymRepository DBI Status: {GymRepository.get_status()}")

        return gym


    @staticmethod
    async def to_gym_by_code_city(gym_code, city) -> Gym:
        list_of_gym = await GymRepository.search_by_gym_code_city(gym_code, city)
        gym = Gym.from_dict(list_of_gym[0]) if len(list_of_gym) > 0 else None
        return gym

    @staticmethod
    async def to_gym_list(gym_code, city):
        list_of_gym = await GymRepository.search_by(gym_code, city)
        gym_list = [Gym.from_dict(gym) for gym in list_of_gym]
        return gym_list

    @staticmethod
    async def to_gym_by_id(gym_id) -> Gym:
        list_of_gym = await GymRepository.search_by_id(gym_id)
        gym = Gym.from_dict(list_of_gym[0]) if len(list_of_gym) > 0 else None
        return gym

    @staticmethod
    def construct_gym(**gym_dict) -> Gym:
        gym = Gym.from_dict(gym_dict)
        gym.gym_display_name = gym.gym_name if gym.gym_display_name is None else gym.gym_display_name

        gym.gym_code = "".join(
            [word[0:2] for word in gym.gym_name.upper().split(" ")[:3]]) if gym.gym_code is None else gym.gym_code

        gym.city_state = gym.gym_city.upper() + gym.gym_state.upper()
        gym.gym_url = f'https://www.google.com/maps/place/{gym.latitude},{gym.longitude}'
        return gym


class GymManagerCog(commands.Cog):
    """
    Loads Gym Manager Code
    """

    def __init__(self, bot):
        self._bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()
        self.logger = init_loggers()
        self.CityManager = ChannelConfigCache(bot)
        GymRepository.set_dbi(self._dbi)
        CityConfigAdapter.set_dbi(self._dbi)

    @commands.group(pass_context=True, hidden=True, aliases=["gym"])
    async def _command_gym(self, ctx):
        try:
            if ctx.invoked_subcommand is None:
                if ctx.subcommand_passed is None:
                    return await EmbedUtil.error(ctx.channel,
                                                 f"**{ctx.invoked_with}** can be used with various options.",
                                                 user=ctx.message.author)

                city_state = ctx.message.content.split()[2] if len(ctx.message.content.split()) > 2 else None

                return await self.send_gym_embed(ctx, ctx.subcommand_passed, city_state)
        except Exception as error:
            self.logger.error(error)


    @_command_gym.command(pass_context=True, hidden=True, aliases=["find"])
    async def _command_gym_find(self, ctx, gym_code, city=None):
        return await self.send_gym_embed(ctx, gym_code, city)


    @_command_gym.group(pass_context=True, hidden=True, aliases=["update"])
    @checks.guildowner_or_permissions(manage_guild=True)
    async def _command_gym_update(self, ctx, gym_id: int, attribute, value):

        gym = await GymAdapter.to_gym_by_id(gym_id)

        if gym is None:
            return await EmbedUtil.error(ctx.channel, f"No gym found by id: **{gym_id}.", user=ctx.message.author)

        if attribute not in Gym.attributes:
            return await EmbedUtil.error(ctx.channel, f"Only following attributes can be updated : `{Gym.attributes}`.",
                                         user=ctx.message.author)

        await GymRepository.update(gym_id, attribute, value)

        updated_gym = await GymAdapter.to_gym_by_id(gym_id)

        message_text = f"Gym **{updated_gym.gym_name} [{updated_gym.gym_code}]** has been updated successfully."
        await EmbedUtil.message(ctx.message.channel, message_text, user=ctx.message.author, footer=updated_gym.summary)


    @_command_gym.command(pass_context=True, hidden=True, aliases=["add"])
    @checks.guildowner_or_permissions(manage_guild=True)
    async def _command_gym_add(self, ctx, *, raw_gym_list=None):
        self.logger.info("_gym_add()")
        try:
            if raw_gym_list is None:
                return await EmbedUtil.message(ctx.message.channel,
                                               f"Beep Beep! **{ctx.message.author.display_name}**, please provide gym information is following format. \n```!gym add \n{json.dumps(Gym.default_dict, indent=1)}```\n You can use https://www.csvjson.com/csv2json to convert CSV to JSON.")
            gym_list = json.loads(raw_gym_list)

            for gym_dict in gym_list:

                gym = GymAdapter.construct_gym(**gym_dict)

                existing_gym = await GymAdapter.to_gym_by_code_city(gym.gym_code, gym.city_state)

                if existing_gym:
                    message_text = f"Gym **{existing_gym.gym_name}** already exists for **{existing_gym.city_state}**."
                    await EmbedUtil.error(ctx.message.channel, message_text, user=ctx.message.author)
                else:
                    await GymRepository.create(**gym.to_db_dict())
                    new_gym = await GymAdapter.to_gym_by_code_city(gym.gym_code, gym.city_state)

                    message_text = f"Gym **{new_gym.gym_name} [{new_gym.gym_code}]** has been added successfully for **{new_gym.city_state}**."
                    await EmbedUtil.message(ctx.message.channel, message_text, user=ctx.message.author,
                                            footer=new_gym.summary)

        except Exception as error:
            self.logger.error(error)
            await EmbedUtil.error(ctx.message.channel, error)
        else:
            await asyncio.sleep(15)
            await ctx.message.delete()

        return

    async def send_gym_embed(self, ctx, gym_code, city=None):

        city = await self.CityManager.get_city_for_channel(ctx.guild.id, ctx.channel.id) if city is None else city

        gym = await GymAdapter.to_gym_by_code_city(gym_code, city)

        if gym:
            return await GymManagerCog._generate_gym_embed(ctx.message, gym)
        else:
            await EmbedUtil.error(ctx.message.channel,
                                  f"I could not find any gyms with gym-code **{gym_code}** in **{city}**.\nPlease use **!gym list word** to see the list of gyms.",
                                  user=ctx.message.author)

    @staticmethod
    async def _generate_gym_embed(message, gym: Gym):

        embed_title = f"Click here for direction to {gym.gym_name}!"
        embed_description = f"**Gym Code :** {gym.gym_code}\n**Gym Name :** {gym.gym_display_name}\n**City :** {gym.gym_city}"

        gym_embed = discord.Embed(title=f"Beep Beep! {embed_title}", url=gym['gym_url'],
                                  description=embed_description, color=message.guild.me.color)

        gym_embed.set_footer(text=gym.summary)
        gym_embed.set_image(url=GymManagerCog.convert_to_google_url(f"{gym.latitude},{gym.longitude}"))

        if gym['gym_image']:
            gym_embed.set_thumbnail(url=gym['gym_image'])
        roster_message = "here are the gym details! "

        await message.channel.send(content=f"Beep Beep! {message.author.mention} {roster_message}", embed=gym_embed)

    @staticmethod
    def convert_to_google_url(lat_long):
        key = config_template.api_keys["google-api-key"]
        gmap_base_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat_long}&markers=color:red%7C{lat_long}&maptype=roadmap&size=250x125&zoom=15&key={key}"

        return gmap_base_url


    @commands.group(pass_context=True, hidden=True, aliases=["gyms"])
    async def _command_gyms(self, ctx, gym_code_or_name=None, city=None):
        await self._gyms(ctx.message, gym_code_or_name, city)


    async def _gyms(self, message, gym_code_or_name = None, city=None):

        gym_code_or_name = gym_code_or_name.upper() if gym_code_or_name is not None else gym_code_or_name

        if len(gym_code_or_name) < 1:
            await EmbedUtil.error(message.channel, "I need at-least one character for lookup!", user=message.author)
            return

        try:

            city_state = await self.CityManager.get_city_for_channel(message.guild.id, message.channel.id) if city is None else city

            if not city_state:
                return await EmbedUtil.error(message.channel, "this channel doesn't have a city assigned. Please contact an admin to assign a city.", user=message.author)

            list_of_gyms = await GymAdapter.to_gym_list(gym_code_or_name, city_state)

            if len(list_of_gyms) < 1:
                return await EmbedUtil.error (message.channel, f"I could not find any gym starting with **{gym_code_or_name}** for **{city_state}**!", user=message.author)

            gym_message_output = f"Here is a list of gyms for **{city_state}** :\n\n"

            for gym in list_of_gyms:
                new_gym_info = f"**{gym.gym_code.ljust(6)}** - {gym.gym_name}\n"

                if len(gym_message_output) + len(new_gym_info) > 1990:
                    await EmbedUtil.message(message.channel, gym_message_output, user=message.author)
                    gym_message_output = ""

                gym_message_output += new_gym_info

            if gym_message_output:
                await EmbedUtil.message(message.channel, gym_message_output, user=message.author)
            else:
                await EmbedUtil.error(message.channel, f"No matches found for **{gym_code_or_name}** in **{city_state}**! **Tip:** Use first two letters of the gym-name to search.", user=message.author)
        except Exception as error:
            self.logger.error(error)
            await EmbedUtil.error(message.channel, f"No matches found for **{gym_code_or_name}** in **{city_state}**! **Tip:** Use first two letters of the gym-name to search.", user=message.author)


def setup(bot):
    bot.add_cog(GymManagerCog(bot))
    CityConfigAdapter.set_dbi(bot.dbi)
    GymRepository.set_dbi(bot.dbi)
