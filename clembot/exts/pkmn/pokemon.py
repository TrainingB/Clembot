from discord.ext import commands
import json
import os
import asyncio
import hastebin
from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.exts.pkmn.spelling import SpellHelper
from clembot.exts.utils.utilities import Utilities

class Pokemon:

    def __init__(self, pokemon_id, label=None, pokedex_id=None, pokedex_num=None, base_attack=None, base_defense=None, base_stamina=None, alias=None, tags=None, type1=None, type2=None, emoji_key=None):
        self.pokemon_id = pokemon_id
        self.label = label
        self.pokedex_id = pokedex_id
        self.pokedex_num = pokedex_num
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_stamina = base_stamina
        self.alias = alias
        self.tags = tags
        self.type1 = type1
        self.type2 = type2
        self.emoji_key = emoji_key


    def __str__(self):
        return self.label


    @property
    def to_dict(self):
        d = {
            'pokemon_id': self.pokemon_id,
            'pokeform_display_text': self.label,
            'pokedex_id': self.pokedex_id,
            'pokedex_num': self.pokedex_num,
            'base_attack': self.base_attack,
            'base_defense': self.base_defense,
            'base_stamina': self.base_stamina,
            'pokeform_alias': self.alias,
            'pokeform_tags': self.tags,
            'type_1': self.type1,
            'type_2': self.type2,
            'emoji_key' : self.emoji_key
        }
        return d

    @classmethod
    def from_dict(cls, data):

        pokemon_id = data['pokemon_id']
        label = data['pokeform_display_text']
        pokedex_id = data['pokedex_id']
        pokedex_num = data['pokedex_num']
        type1 = data['type_1']
        type2 = data['type_2']
        base_attack = data['base_attack']
        base_defense = data['base_defense']
        base_stamina = data['base_stamina']
        alias = data['pokeform_alias']
        tags = data['pokeform_tags']
        emoji_key = data['emoji_key']

        return cls(pokemon_id, label, pokedex_id, pokedex_num, base_attack, base_defense, base_stamina, alias, tags, type1, type2, emoji_key)


    @property
    def emoji(self):
        if self.emoji_key:
            return self.emoji_key
        return None

    @emoji.setter
    def emoji(self, emoji_key):
        self.emoji_key = emoji_key


class OptionalPokemonConverter(commands.Converter):

    async def convert(self, ctx, argument) -> Pokemon:

        pokemon_form = PokemonCache.to_pokemon(argument.upper())
        if pokemon_form:
            return pokemon_form
        else:
            possible_pokemon_form = await PokemonConverter.auto_correct(ctx, argument.upper())
            if possible_pokemon_form:
                pokemon_form = PokemonCache.to_pokemon(possible_pokemon_form)
                return pokemon_form

        return None

    @staticmethod
    def remove_empty_members(list_of_elements):

        new_list = [element for element in list_of_elements if element is not None]
        return new_list


class PokemonConverter(commands.Converter):

    async def convert(self, ctx, argument) -> Pokemon:

        pokemon_form = PokemonCache.to_pokemon(argument.upper())
        if pokemon_form:
            return pokemon_form
        else:
            possible_pokemon_form = await PokemonConverter.auto_correct(ctx, argument.upper())
            if possible_pokemon_form:
                pokemon_form = PokemonCache.to_pokemon(possible_pokemon_form)
                return pokemon_form

        raise Exception(f"{argument} could not be resolved to a pokemon.")

    @staticmethod
    async def auto_correct(ctx, pokemon_as_text):

        not_acceptable_message = f"**{pokemon_as_text}** isn't a Pokemon!"

        spellcheck_suggestion = SpellHelper.correction(pokemon_as_text)

        if spellcheck_suggestion and spellcheck_suggestion != pokemon_as_text:

            not_acceptable_message += f" Did you mean **{spellcheck_suggestion}**?"
            replace_pokemon = await Utilities.ask_confirmation(ctx, ctx.message, not_acceptable_message, "Alright!", "That's okay!", "Timed Out!")
            if replace_pokemon:
                return spellcheck_suggestion

        return None


class PokemonCache:

    _cache = {}
    _pkmn_map = {}
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    @classmethod
    def cache_size(cls):
        return cls._cache.__len__()

    @classmethod
    def cache(cls):
        return cls._cache


    @classmethod
    def pokemon(cls, pokemon_id):
        return Pokemon.from_dict(cls._pkmn_map.get(pokemon_id, None))


    @classmethod
    def update_cache(cls, pokemon):

        pkmn_dict = pokemon.to_dict
        for alias in pokemon.tags:
            cls._cache[alias] = pkmn_dict

        cls._pkmn_map[pokemon.pokemon_id] = pkmn_dict



    @classmethod
    def load_cache(cls, list_of_pokemon_records):
        pokemon_form_master = {}
        pokemon_id_map = {}

        for record in list_of_pokemon_records:
            pokemon_id_map[record['pokemon_id']] = record
            for alias in record['pokeform_alias']:
                pokemon_form_master[alias] = record

        cls._cache = pokemon_form_master
        cls._pkmn_map = pokemon_id_map
        SpellHelper.set_dictionary(list(pokemon_form_master.keys()))

    @classmethod
    def to_pokemon(cls, text) -> Pokemon:
        if cls._cache.__len__() < 1:
            raise Exception("Error : Pokemon forms are not loaded.")

        if cls._cache.keys().__contains__(text.upper()):
            my_object = cls._cache.get(text.upper())
            return Pokemon.from_dict(my_object)

        return None

    @classmethod
    async def load_cache_from_dbi(cls, dbi):

        try:
            result_record = await dbi.table('tbl_pokemon_master').query().select().getjson()

            PokemonCache.load_cache(result_record)

            print(f'{len(result_record)} Pokemon Form(s) Loaded from tbl_pokemon_master.')
            return result_record
        except Exception as error:
            print(error)
            raise Exception("Couldn't load pokemon forms from DB due to error " + str(error))

    @classmethod
    async def update_pokemon(cls, local_dbi, pokemon_id, data):

        if local_dbi:
            tbl_pokemon_master = local_dbi.table('tbl_pokemon_master')
            existing_pokemon_record = await tbl_pokemon_master.query().select().where(pokemon_id=pokemon_id).get_first()

            if existing_pokemon_record:
                print(f"updating {pokemon_id} with {data}")
                update_query = tbl_pokemon_master.update(**data).where(pokemon_id=pokemon_id)
                await update_query.commit()
            else:
                insert_query = tbl_pokemon_master.insert(**data)
                await insert_query.commit()

    @classmethod
    async def create_emoji(cls, ctx, local_dbi, pokemon_id):

        pokemon = PokemonCache.pokemon(pokemon_id)

        script_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.join(script_path)
        folder_path = os.path.join(script_path, "../../../images/pkmn")

        print(folder_path)

        file_path = f"{folder_path}/{pokemon_id.upper()}.png"


        if pokemon and pokemon.emoji:
            return pokemon.emoji


        print(file_path)
        emoji = '<:unknown_encounter:629202330419724288>'


        try:
            with open(file_path, "rb") as image:
                f = image.read()
                image = bytearray(f)

            emoji = await ctx.channel.guild.create_custom_emoji(name=pokemon_id, image=image)

            pokemon.emoji = str(emoji)
            await PokemonCache.update_pokemon(local_dbi, pokemon_id, pokemon.to_dict)
            PokemonCache.update_cache(pokemon)

        except Exception as error:
            print(error)
            raise Exception(error)



        return emoji


class GameMasterParser:

    _cache = {}
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state


    @classmethod
    async def load_pokedex(cls, local_dbi):
        # if not cls._cache.__len__() == 0:
        # with open("https://raw.githubusercontent.com/PokeMiners/game_masters/master/previous_game_masters/gm_apk1532_Wed_Sep_18_10_26_26_2019/game_master.json", "r") as fd:

        file_name = "game_master_000.json"

        with open(os.path.join('data', file_name), "r") as fd:
            print(f'opened file {file_name}')
            pokemon_master = json.load(fd)

        pokemon_master_list = await GameMasterInterface.get_pokemon_master_list(dbi)

        for pmr in pokemon_master:
            try:
                templateId = pmr['templateId']

                if templateId.startswith('V') and templateId.__contains__('_POKEMON_'):

                    ps = pmr.get('pokemonSettings',{})
                    pokemonId = ps.get('form', ps.get('pokemonId')).replace('_SHADOW','').replace('_PURIFIED', '').replace('_NORMAL', '')


                    if pokemon_master_list.__contains__(pokemonId):
                        print(f"{templateId} skipped!")
                        continue
                    print(f"{templateId} => {pokemonId}")

                    pokemon_master_list.append(pokemonId)

                    data = {
                        "pokemon_id": pokemonId,
                        "pokemon_display_text" : pokemonId.replace('_','-').replace('FORM',''),
                        "pokedex_id": ps.get('pokemonId'),
                        "type_1": ps.get('type'),
                        "type_2": ps.get('type2'),
                        "base_attack" : ps.get('stats').get('baseAttack'),
                        "base_defense" : ps.get('stats').get('baseDefense'),
                        "base_stamina" : ps.get('stats').get('baseStamina'),
                        "parent_pokemon_id" : ps.get('parentPokemonId'),
                        "pokemon_family_id": ps.get('familyId'),
                        "cinematic_moves" : ps.get('cinematicMoves'),
                        "quick_moves": ps.get('quickMoves')
                    }
                    # print(json.dumps(data))
                    await GameMasterInterface.update_game_master(local_dbi, pokemonId, data)

            except Exception as error:
                print(error)
                print(json.dumps(pmr))

        print("load_pokedex() finished.")


class GameMasterInterface:

    def __int__(self):
       self.a=10

    @classmethod
    async def update_game_master(cls, local_dbi, pokemonId, data, forcedUpdate=False):

        if local_dbi:
            tbl_game_master = local_dbi.table('game_master')
            existing_pokemon_record = await tbl_game_master.query().select().where(pokemon_id=pokemonId).get_first()

            if existing_pokemon_record:
                if forcedUpdate:
                    update_query = tbl_game_master.update(**data).where(pokemon_id=pokemonId)
                    await update_query.commit()
            else:
                insert_query = tbl_game_master.insert(**data)
                await insert_query.commit()

    @classmethod
    async def get_pokemon_master_list(cls, local_dbi):

        tbl_game_master = local_dbi.table('game_master')
        existing_pokemon_record = await tbl_game_master.query().select('pokemon_id').where().get()

        list_of_pokemon_id = []
        for record in existing_pokemon_record:
            list_of_pokemon_id.append(record.get('pokemon_id'))

        return list_of_pokemon_id

dbi = None

async def initialize():
    global dbi
    dbi = DatabaseInterface()
    await dbi.start()

async def cleanup():
    global dbi
    await dbi.stop()


async def test_condition():
    try:

        # something = await GameMasterInterface.get_game_master(dbi)
        # print(something)
        # await GameMasterParser.load_pokedex(dbi)
        await PokemonCache.load_cache_from_dbi(dbi)


    except Exception as error:
        print(error)



def main():
    try:


        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize())
        loop.run_until_complete(test_condition())
        loop.run_until_complete(cleanup())

        print(f"[pokemon.py] main() finished.")

    except Exception as error:
        print(error)


#main()
