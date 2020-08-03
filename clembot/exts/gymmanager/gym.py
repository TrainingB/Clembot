from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.core.logs import Logger
from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.exts.config.channelconfigmanager import ChannelCity, MapsUtil
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import TextUtil


# class CityConfigAdapter:
#
#     _dbi = None
#
#     def __init__(self):
#         pass
#
#     @classmethod
#     def set_dbi(cls, dbi):
#         cls._dbi = dbi
#
#     @staticmethod
#     async def get_city_for_channel(guild_id, channel_id=None, parent_channel_id=None) -> str :
#         try:
#             city_for_channel = await CityConfigAdapter._get_config_by('city', guild_id=guild_id, channel_id=channel_id)
#
#             if not city_for_channel:
#                 if parent_channel_id:
#                     city_for_channel = await CityConfigAdapter._get_config_by('city', guild_id=guild_id, channel_id=parent_channel_id)
#
#             # if not city_for_channel:
#             #     city_for_channel = await CityConfigAdapter.MyGuildConfigCache.get_guild_config(guild_id=guild_id, config_name='city')
#             return city_for_channel
#
#         except Exception as error:
#             Logger.error(f"{traceback.format_exc()}")
#             CityConfigAdapter.logger.info(error)
#             return None
#
#     @staticmethod
#     async def _get_config_by(config_name, **kwargs):
#         try:
#
#             guild_channel_config_tbl = CityConfigAdapter._dbi.table('guild_channel_config')
#             kwargs.update(config_name=config_name)
#
#             guild_channel_query = guild_channel_config_tbl.query().select().where(**kwargs)
#
#             config_record = await guild_channel_query.get_first()
#             if config_record:
#                 config_value = dict(config_record)['config_value']
#                 if config_value:
#                     return config_value
#         except Exception as error:
#             Logger.error(error)
#         return None



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

    @classmethod
    async def convert(cls, bot, gym_id: int):
        gym_table = bot.dbi.table('gym')
        gym_table_query = gym_table.query().select().where(gym_id=gym_id)
        list_of_gym = await gym_table_query.getjson()
        if len(list_of_gym) > 0:
            gym_record = list_of_gym[0]
        return cls.from_dict(gym_record)

    @property
    def _data(self):
        data = self.bot.dbi.table('gym').query()
        data = data.where(id=self.id)
        return data


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

    @property
    def google_preview_url(self):
        return Embeds.google_location_preview_url(f"{self.latitude},{self.longitude}")


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


    @classmethod
    async def find_first_by(cls, bot, gym_code, city):

        gym_table = bot.dbi.table('gym')
        gym_table_query = gym_table.query().select().where(gym_code=gym_code.upper(), city_state=city.upper())
        list_of_gym = await gym_table_query.getjson()
        gym = Gym.from_dict(list_of_gym[0]) if len(list_of_gym) > 0 else None
        return gym




class GymRepository:

    def __init__(self, dbi):
        self._dbi = dbi

    def set_dbi(self, dbi):
        if self._dbi is not None:
            self._dbi = dbi

        raise ValueError(f"set_dbi(): Ignored as dbi : {dbi.dsn} is already available!")


    async def search_by(self, gym_code_or_name, city=None):
        try:
            gym_code_or_name = gym_code_or_name.upper()

            if gym_code_or_name:

                gym_table = self._dbi.table('gym')
                gym_code_query = gym_table.query().select().where(gym_table['gym_code'].like(f'%{gym_code_or_name}%'), city_state=city).order_by('gym_code')

                list_of_gym = await gym_code_query.getjson()
                Logger.info(f"search_by({gym_code_or_name}, {city}) : {len(list_of_gym)} record(s) found!")

                if len(list_of_gym) == 0:
                    gym_table = self._dbi.table('gym')
                    gym_name_query = gym_table.query().select().where(gym_table['gym_name'].ilike(f'%{gym_code_or_name}%'),city_state=city).order_by('gym_code')
                    list_of_gym = await gym_name_query.getjson()

                return list_of_gym

        except Exception as error:
            Logger.error(error)

        return None


    async def search_by_gym_code_city(self, gym_code: str, city=None) -> list:
        gym_table = self._dbi.table('gym')
        gym_table_query = gym_table.query().select().where(gym_code=gym_code.upper(), city_state=city.upper())
        list_of_gym = await gym_table_query.getjson()
        return list_of_gym


    async def search_by_id(self, gym_id: int):
        gym_table = self._dbi.table('gym')
        gym_table_query = gym_table.query().select().where(gym_id=gym_id)
        list_of_gym = await gym_table_query.getjson()
        return list_of_gym


    async def insert(self, **kwargs):
        gym_table = self._dbi.table('gym')
        gym_table_insert = gym_table.insert(**kwargs)
        await gym_table_insert.commit()


    async def update(self, gym_id: int, attribute: str, value=None):
        gym_table = self._dbi.table('gym')
        update_dict = {attribute: value}
        gym_table_update = gym_table.update(**update_dict).where(gym_id=gym_id)
        await gym_table_update.commit()


    async def to_gym_by_code(self, gym_code, message) -> Gym:
        city = await ChannelMetadata.city({'dbi': self.dbi}, message.channel.id)
        list_of_gym = await self.search_by_gym_code_city(gym_code, city)
        gym = Gym.from_dict(list_of_gym[0]) if len(list_of_gym) > 0 else None
        return gym


    async def to_gym_by_code_city(self, gym_code, city) -> Gym:
        list_of_gym = await self.search_by_gym_code_city(gym_code, city)
        gym = Gym.from_dict(list_of_gym[0]) if list_of_gym and len(list_of_gym) > 0 else None
        return gym


    async def to_gym_list(self, gym_code, city):
        list_of_gym = await self.search_by(gym_code, city)
        gym_list = [Gym.from_dict(gym) for gym in list_of_gym]
        return gym_list


    async def to_gym_by_id(self, gym_id) -> Gym:
        list_of_gym = await self.search_by_id(gym_id)
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


class POILocation:
    """
    saved in Raids by gym_id
    selected input will have location text & city

    Represent raid location a gym or a text phrase
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(raid_details)
        direction_description = f"{raid_details} [Click here for directions]({raid_gmaps_link})"
    """

    def __init__(self, location: str = None, city=None, gym: Gym = None, url = None):
        if gym:
            self.gym = gym
            self.city = self.gym.gym_city
        else:
            self.gym = None

        if url:
            self._url = url
        else:
            self._url = None

        self.location = location
        self.city = city

    @classmethod
    def convert(cls, ctx, location):
        city = ChannelCity.get_city_for_channel_only(ctx)
        return cls(location=location, city=city)


    def to_dict(self):
        if self.gym:
            return { 'gym_id' : self.gym.gym_id }
        else:
            state_dict = {
                'city': self.city,
                'location': self.location,
            }
            return state_dict

    @classmethod
    async def from_dict(cls, bot, state):
        city, location, gym_id = ([state.get(attr, None) for attr in ['city', 'location', 'gym_id']])
        if gym_id:
            found_gym = await Gym.convert(bot, gym_id)
            if found_gym:
                return cls(gym=found_gym)
        return cls(location=location, city=city)

    @classmethod
    def from_gym(cls, gym: Gym):
        """When gym is available from parsed arguments"""
        return cls(gym=gym)


    @classmethod
    def from_location_city(cls, location: str, city: str):
        """"""
        return cls(location=location, city=city)

    @classmethod
    def from_url(cls, location, url):
        return cls(location=location, url=url)


    @property
    def name(self):
        if self.gym:
            return self.gym.gym_display_name
        return self.location

    @property
    def url(self):
        if self.gym:
            return self.gym.gym_url
        if self._url:
            return self._url
        return MapsUtil.google_url(self.location, self.city)

    @property
    def is_gym(self):
        return self.gym is not None

    @property
    def gym_embed_label(self):
        if self.is_gym:
            directions = f"[{self.gym.gym_display_name}]({self.url})"
        else:
            directions = f"[{self.name} (Unknown Gym)]({self.url})"
        return directions

    @property
    def embed_label(self):
        if self.is_gym:
            directions = f"[{self.gym.gym_display_name}]({self.url})"
        else:
            directions = f"[{self.name}]({self.url})"
        return directions

    @property
    def google_preview_url(self):
        if self.is_gym:
            return self.gym.google_preview_url
        return None

    def __str__(self):
        directions = f"[{self.name}]({self.url})"

        return directions

    def __repr__(self):
        directions = f"[{self.name}]({self.url})"

        return directions


class POILocationConverter(commands.Converter):
    """
    !nest chimchar MESC
    !nest pikachu somewhere closer
    !nest aron some park http://google-url.com
    """

    @staticmethod
    async def convert_from_text(ctx, *argument) -> POILocation:

        try:
            if len(argument) == 1:
                city = await ctx.city()
                gym = await GymRepository(ctx.bot.dbi).to_gym_by_code_city(argument[0], city)
                if gym:
                    return POILocation.from_gym(gym)

            text = " ".join(argument)
            maps_link = TextUtil.extract_link_from_text(text)
            if maps_link:
                new_text = text.replace(maps_link, '')
                return POILocation.from_url( new_text if new_text.__len__() > 0 else "Click for directions", maps_link)

            return POILocation.from_location_city(text, "")

        except Exception as error:
            raise BadArgument(error)


    @staticmethod
    async def convert(ctx, argument) -> POILocation:
        try:
            city = await ctx.city()
            if city is None:
                city = await ctx.guild_profile(key='city')
            gym = await GymRepository(ctx.bot.dbi).to_gym_by_code_city(argument, city)

            if gym:
                return POILocation.from_gym(gym)
            else:
                return POILocation.from_location_city(argument, city)
        except Exception as error:
            raise BadArgument(error)

    @staticmethod
    def combine(location_list):

        location_text = []
        for rl in location_list:
            if rl.is_gym:
                return rl
            location_text.append(rl.location)

        return POILocation.from_location_city(" ".join(location_text), location_list[0].city)



    # @staticmethod
    # async def auto_correct(ctx, pokemon_as_text):
    #
    #     not_acceptable_message = f"**{pokemon_as_text}** isn't a Pokemon!"
    #
    #     spellcheck_suggestion = SpellHelper.correction(pokemon_as_text)
    #
    #     if spellcheck_suggestion and spellcheck_suggestion != pokemon_as_text:
    #
    #         not_acceptable_message += f" Did you mean **{spellcheck_suggestion}**?"
    #         replace_pokemon = await Utilities.ask_confirmation(ctx, ctx.message, not_acceptable_message, "Alright!", "That's okay!", "Timed Out!")
    #         if replace_pokemon:
    #             return spellcheck_suggestion
    #
    #     return None