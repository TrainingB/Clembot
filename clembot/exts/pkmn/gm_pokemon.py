import asyncio
import json
import math
import os
import pydash as _

from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config import config_template
from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.core.logs import Logger
from clembot.exts.pkmn.cpcalculator import CPCalculator
from clembot.exts.pkmn.spelling import SpellHelper
from clembot.utilities.utils.utilities import Utilities

sample = {"templateId": "V0026_POKEMON_RAICHU_ALOLA",
          "pokemon": {"uniqueId": "RAICHU", "modelScale": 1.08, "type1": "POKEMON_TYPE_ELECTRIC",
                      "type2": "POKEMON_TYPE_PSYCHIC",
                      "stats": {"baseStamina": 155, "baseAttack": 201, "baseDefense": 154},
                      "quickMoves": ["VOLT_SWITCH_FAST", "SPARK_FAST", "THUNDER_SHOCK_FAST"],
                      "cinematicMoves": ["PSYCHIC", "THUNDER_PUNCH", "WILD_CHARGE", "GRASS_KNOT"], "evolutionPips": 1,
                      "pokedexHeightM": 0.7, "pokedexWeightKg": 21.0, "parentId": "PIKACHU", "heightStdDev": 0.0875,
                      "weightStdDev": 2.625, "familyId": "FAMILY_PIKACHU", "kmBuddyDistance": 1.0, "modelHeight": 0.83,
                      "modelScaleV2": 1.0, "form": "RAICHU_ALOLA", "buddyScale": 19.0,
                      "thirdMove": {"stardustToUnlock": 10000, "candyToUnlock": 25}, "isTransferable": True,
                      "isDeployable": True, "buddyGroupNumber": 2}}



class GMPokemonFormSpellHelper(SpellHelper):

    pass


class Pokemon:

    _cache = dict()

    def __init__(self, db_dict, pokedex_num, aliases=[]):
        self.db_dict = db_dict
        self.pokedex_num = pokedex_num
        self.aliases = aliases

    def __getitem__(self, item):
        """use [] operator to access members, simpler to create entity objects"""
        return self.db_dict.get(item)


    def __setitem__(self, key, value):
        """use [] operator to access members, simpler to create entity objects. Handles array kind of values."""
        self.db_dict[key] = value


    def __repr__(self):
        return self.label

    @property
    def id(self):
        return self.aliases[0] if self.aliases else None

    @property
    def label(self):
        return self.id.capitalize()

    # @property
    # def label(self):
    #     if self.pokeform_display_text:
    #         return self.pokeform_display_text.capitalize()
    #     return None


    @property
    def form(self):
        form = _.get(self.db_dict, 'pokemon.form') or _.get(self.db_dict, 'pokemon.uniqueId')
        if '_ALOLA' in form:
            form = form.replace('_ALOLA','_ALOLA_FORM')
        return form

    @property
    def base_attack(self):
        return _.get(self.db_dict, 'pokemon.stats.baseAttack')

    @property
    def base_defense(self):
        return _.get(self.db_dict, 'pokemon.stats.baseDefense')

    @property
    def base_stamina(self):
        return _.get(self.db_dict, 'pokemon.stats.baseStamina')

    @property
    def fast_moves(self):
        return list(map(lambda move: move.replace("_FAST", ""), _.get(self.db_dict, 'pokemon.quickMoves')))

    @property
    def fast_moves_labels(self):
        return list(map(lambda move: move.replace("_"," ").title() , self.fast_moves))

    @property
    def charge_moves(self):
        return list(map(lambda move: move, _.get(self.db_dict, 'pokemon.cinematicMoves')))

    @property
    def charge_moves_labels(self):
        return list(map(lambda move: move.replace("_"," ").title() , self.charge_moves))


    @property
    def type1(self):
        type1 = _.get(self.db_dict, 'pokemon.type1')
        if type1:
            return type1.replace("POKEMON_TYPE_","").upper()
        return None

    @property
    def type2(self):
        type2 = _.get(self.db_dict, 'pokemon.type2')
        if type2:
            return type2.replace("POKEMON_TYPE_", "").upper()
        return None

    @property
    def types(self):
        if self.type2:
            return [self.type1, self.type2]
        return [self.type1]

    @property
    def type1_icon(self):
        if self.type1:
            key = self.type1.lower()
            return config_template.type_emoji[key]
        return None

    @property
    def type2_icon(self):
        if self.type2:
            key = self.type2.lower()
            return config_template.type_emoji[key]
        return None

    @property
    def shiny(self):
        return False

    def _gender_type(self):
        return 'X'

    @property
    def gender(self):
        return 'MALE'


    @property
    def extended_label(self):
        """returns pokemon(pokedex) type1 type2"""
        extended_label=f"{self.label} ({self.pokedex_num}) {self.type1_icon}"
        if self.type2_icon:
            extended_label=f"{extended_label}{self.type2_icon}"
        return extended_label

    @property
    def preview_url(self):
        url = "https://raw.githubusercontent.com/TrainingB/Clembot/v2-rewrite/images/pkmn/"
        if self.form:
            url += str(self.form)
        if self.shiny:
            url += '_SHINY'
        if self._gender_type() == 'DIMORPH' and self.gender:
            url += f'_{self.gender.upper()}'
        url += '.png'
        # url += '?cache=5'
        return url

    # async def color(self):
    #     url = await self.sprite_url()
    #     color = await formatters.url_color(url)
    #     return color

    @property
    def raid_cp_range(self):
        low_cp = self.calculate_cp(20, 10, 10, 10)
        high_cp = self.calculate_cp(20, 15, 15, 15)
        return [low_cp, high_cp]


    def calculate_cp(self, level, attiv, defiv, staiv):
        if None in [level, attiv, defiv, staiv]:
            return None
        else:
            cpm = CPCalculator().cpM[level]
            att = (self.base_attack + attiv)*cpm
            defense = (self.base_defense + defiv)*cpm
            sta = (self.base_stamina + staiv)*cpm
            cp = math.floor((att*defense**0.5*sta**0.5)/10)
            if cp < 10:
                cp = 10
            return cp





    @classmethod
    def cache(cls, form):
        Pokemon._cache[form.aliases[0]] = form

    @classmethod
    def to_pokemon(cls, search_for):
        if len(cls._cache) < 1:
            raise Exception("Error : Pokemon forms are not loaded.")

        if search_for:
            form = cls._cache.get(search_for.upper(), None)

        return form

    @classmethod
    async def load(cls, bot):

        if len(Pokemon._cache) == 0:
            table = bot.dbi.table('GM_POKEMON_FORMS')
            forms = await table.query().select().getjson()

            for form in forms:
                pForm = Pokemon(json.loads(form.get('data')), form.get('pokedex_id'), form.get('aliases'))
                Pokemon.cache(pForm)
        GMPokemonFormSpellHelper.set_dictionary(cls._cache.keys())

    @classmethod
    async def convert(cls, ctx, argument) :

        await cls.load(ctx.bot)

        pokemon_form = cls.to_pokemon(argument.upper())
        if pokemon_form:
            return pokemon_form
        else:
            possible_pokemon_form = await Pokemon.auto_correct(ctx, argument.upper())
            if possible_pokemon_form:
                pokemon_form = cls.to_pokemon(possible_pokemon_form)
                return pokemon_form

        raise BadArgument(f"{argument} could not be resolved to a pokemon.")

    @staticmethod
    async def auto_correct(ctx, pokemon_as_text):

        not_acceptable_message = f"**{pokemon_as_text}** isn't a Pokemon!"

        suggestion = GMPokemonFormSpellHelper.correction(pokemon_as_text)

        if suggestion and suggestion != pokemon_as_text:

            not_acceptable_message += f" Did you mean **{suggestion}**?"
            replace_pokemon = await Utilities.ask_confirmation(ctx, ctx.message, not_acceptable_message, "Alright!", "That's okay!", "Timed Out!")
            if replace_pokemon:
                return suggestion

        return None





    @property
    def weaknesses(self):
        """
        Given a Pokemon name, return a list of its weaknesses as defined in the type chart
        Calculate sum of its weaknesses and resistances.
        -2 == immune , -1 == NVE, 0 == neutral, 1 == SE, 2 == double SE
        """
        type_eff = {}
        for p_type in self.types:
            for atk_type in _TYPE_CHART[p_type]:
                if atk_type not in type_eff:
                    type_eff[atk_type] = 0
                type_eff[atk_type] += _TYPE_CHART[p_type][atk_type]

        # Summarize into a list of weaknesses,
        # sorting double weaknesses to the front and marking them with 'x2'.
        ret = []
        for p_type, effectiveness in sorted(type_eff.items(), key=lambda x: x[1], reverse=True):
            if effectiveness == 1:
                ret.append(p_type.lower())
            elif effectiveness == 2:
                ret.append(p_type.lower() + "x2")

        return ret


    @property
    def weaknesses_icon(self):
        """
        Given a list of weaknesses, return a space-separated string of their type IDs as defined in the type_id_dict
        """
        ret = ""
        for weakness in self.weaknesses:
            # Handle an "x2" postfix defining a double weakness
            x2 = ""
            if weakness[-2:] == "x2":
                weakness = weakness[:-2]
                x2 = "x2"

            # Append to string
            ret += config_template.type_emoji[weakness] + x2 + " "

        return ret


#     @property
#     def emoji(self):
#         if self.emoji_key:
#             return self.emoji_key
#         return None
#
#     @emoji.setter
#     def emoji(self, emoji_key):
#         self.emoji_key = emoji_key
#


class OptionalPokemonConverter(commands.Converter):

    async def convert(self, ctx, argument) -> Pokemon:

        pokemon_form = Pokemon.to_pokemon(argument.upper())
        if pokemon_form:
            return pokemon_form
        else:
            possible_pokemon_form = await Pokemon.auto_correct(ctx, argument.upper())
            if possible_pokemon_form:
                pokemon_form = Pokemon.to_pokemon(possible_pokemon_form)
                return pokemon_form

        return None

    @staticmethod
    def remove_empty_members(list_of_elements):

        new_list = [element for element in list_of_elements if element is not None]
        return new_list



#
#
# class PokemonCache:
#
#     _cache = {}
#     _pkmn_map = {}
#     __shared_state = {}
#
#     def __init__(self):
#         self.__dict__ = self.__shared_state
#
#     @classmethod
#     def cache_size(cls):
#         return cls._cache.__len__()
#
#     @classmethod
#     def cache(cls):
#         return cls._cache
#
#
#     @classmethod
#     def pokemon(cls, pokemon_id):
#         return Pokemon.from_dict(cls._pkmn_map.get(pokemon_id, None))
#
#
#     @classmethod
#     def update_cache(cls, pokemon):
#
#         pkmn_dict = pokemon.to_dict
#         for alias in pokemon.alias:
#             cls._cache[alias] = pkmn_dict
#
#         cls._pkmn_map[pokemon.pokemon_id] = pkmn_dict
#
#
#
#     @classmethod
#     def load_cache(cls, list_of_pokemon_records):
#         pokemon_form_master = {}
#         pokemon_id_map = {}
#
#         for record in list_of_pokemon_records:
#             pokemon_id_map[record['pokemon_id']] = record
#             for alias in record['pokeform_alias']:
#                 pokemon_form_master[alias] = record
#
#         cls._cache = pokemon_form_master
#         cls._pkmn_map = pokemon_id_map
#         SpellHelper.set_dictionary(list(pokemon_form_master.keys()))
#
#     @classmethod
#     def to_pokemon(cls, text) -> Pokemon:
#         if cls._cache.__len__() < 1:
#             raise Exception("Error : Pokemon forms are not loaded.")
#
#         if cls._cache.keys().__contains__(text.upper()):
#             my_object = cls._cache.get(text.upper())
#             return Pokemon.from_dict(my_object)
#
#         return None
#
#     @classmethod
#     async def load_cache_from_dbi(cls, dbi, force_reload = False):
#
#         try:
#
#             if cls._cache.__len__() > 0 and not force_reload:
#                 return
#
#             result_record = await dbi.table('tbl_pokemon_master').query().select().getjson()
#
#             PokemonCache.load_cache(result_record)
#
#             Logger.info(f'{len(result_record)} Pokemon Form(s) Loaded from tbl_pokemon_master.')
#             return result_record
#         except Exception as error:
#             Logger.error(f"{traceback.format_exc()}")
#             raise Exception("Couldn't load pokemon forms from DB due to error " + str(error))
#
#     @classmethod
#     async def update_pokemon(cls, local_dbi, pokemon_id, data):
#
#         if local_dbi:
#             tbl_pokemon_master = local_dbi.table('tbl_pokemon_master')
#             existing_pokemon_record = await tbl_pokemon_master.query().select().where(pokemon_id=pokemon_id).get_first()
#
#             if existing_pokemon_record:
#                 print(f"updating {pokemon_id} with {data}")
#                 update_query = tbl_pokemon_master.update(**data).where(pokemon_id=pokemon_id)
#                 await update_query.commit()
#             else:
#                 insert_query = tbl_pokemon_master.insert(**data)
#                 await insert_query.commit()
#
#     @classmethod
#     async def create_emoji(cls, ctx, local_dbi, pokemon_id):
#
#         pokemon = PokemonCache.pokemon(pokemon_id)
#
#         script_path = os.path.dirname(os.path.realpath(__file__))
#         dir_path = os.path.join(script_path)
#         folder_path = os.path.join(script_path, "../../../images/pkmn")
#
#         print(folder_path)
#
#         file_path = f"{folder_path}/{pokemon_id.upper()}.png"
#
#
#         if pokemon and pokemon.emoji:
#             return pokemon.emoji
#
#
#         print(file_path)
#         emoji = '<:unknown_encounter:629202330419724288>'
#
#
#         try:
#             with open(file_path, "rb") as image:
#                 f = image.read()
#                 image = bytearray(f)
#
#             emoji = await ctx.channel.guild.create_custom_emoji(name=pokemon_id, image=image)
#
#             pokemon.emoji = str(emoji)
#             await PokemonCache.update_pokemon(local_dbi, pokemon_id, pokemon.to_dict)
#             PokemonCache.update_cache(pokemon)
#
#         except Exception as error:
#             Logger.error(f"{traceback.format_exc()}")
#             raise Exception(error)
#
#
#
#         return emoji
#
#

_TYPE_CHART = {
  "GHOST": {
    "GHOST": 1,
    "NORMAL": -2,
    "POISON": -1,
    "DARK": 1,
    "FIGHTING": -2,
    "BUG": -1
  },
  "STEEL": {
    "STEEL": -1,
    "ICE": -1,
    "NORMAL": -1,
    "FIRE": 1,
    "PSYCHIC": -1,
    "FLYING": -1,
    "POISON": -2,
    "DRAGON": -1,
    "FIGHTING": 1,
    "ROCK": -1,
    "FAIRY": -1,
    "GRASS": -1,
    "BUG": -1,
    "GROUND": 1
  },
  "DARK": {
    "GHOST": -1,
    "PSYCHIC": -2,
    "FIGHTING": 1,
    "DARK": -1,
    "FAIRY": 1,
    "BUG": 1
  },
  "ELECTRIC": {
    "STEEL": -1,
    "FLYING": -1,
    "ELECTRIC": -1,
    "GROUND": 1
  },
  "ICE": {
    "STEEL": 1,
    "FIRE": 1,
    "ICE": -1,
    "FIGHTING": 1,
    "ROCK": 1
  },
  "NORMAL": {
    "GHOST": -2,
    "FIGHTING": 1
  },
  "FIRE": {
    "STEEL": -1,
    "FIRE": -1,
    "ICE": -1,
    "WATER": 1,
    "ROCK": 1,
    "FAIRY": -1,
    "GRASS": -1,
    "BUG": -1,
    "GROUND": 1
  },
  "PSYCHIC": {
    "GHOST": 1,
    "DARK": 1,
    "PSYCHIC": -1,
    "BUG": 1,
    "FIGHTING": -1
  },
  "FLYING": {
    "ELECTRIC": 1,
    "FIGHTING": -1,
    "ICE": 1,
    "ROCK": 1,
    "GRASS": -1,
    "BUG": -1,
    "GROUND": -2
  },
  "POISON": {
    "PSYCHIC": 1,
    "POISON": -1,
    "FIGHTING": -1,
    "FAIRY": -1,
    "GRASS": -1,
    "BUG": -1,
    "GROUND": 1
  },
  "DRAGON": {
    "ELECTRIC": -1,
    "FIRE": -1,
    "ICE": 1,
    "DRAGON": 1,
    "WATER": -1,
    "FAIRY": 1,
    "GRASS": -1
  },
  "WATER": {
    "STEEL": -1,
    "ELECTRIC": 1,
    "FIRE": -1,
    "ICE": -1,
    "WATER": -1,
    "GRASS": 1
  },
  "FIGHTING": {
    "PSYCHIC": 1,
    "FLYING": 1,
    "DARK": -1,
    "ROCK": -1,
    "FAIRY": 1,
    "BUG": -1
  },
  "ROCK": {
    "STEEL": 1,
    "NORMAL": -1,
    "FIRE": -1,
    "FLYING": -1,
    "POISON": -1,
    "WATER": 1,
    "FIGHTING": 1,
    "GRASS": 1,
    "GROUND": 1
  },
  "FAIRY": {
    "STEEL": 1,
    "POISON": 1,
    "DRAGON": -2,
    "DARK": -1,
    "FIGHTING": -1,
    "BUG": -1
  },
  "GRASS": {
    "ELECTRIC": -1,
    "FIRE": 1,
    "FLYING": 1,
    "POISON": 1,
    "WATER": -1,
    "ICE": 1,
    "GRASS": -1,
    "BUG": 1,
    "GROUND": -1
  },
  "BUG": {
    "FIRE": 1,
    "FLYING": 1,
    "FIGHTING": -1,
    "ROCK": 1,
    "GRASS": -1,
    "GROUND": -1
  },
  "GROUND": {
    "ELECTRIC": -2,
    "ICE": 1,
    "WATER": 1,
    "POISON": -1,
    "ROCK": -1,
    "GRASS": 1
  }
}