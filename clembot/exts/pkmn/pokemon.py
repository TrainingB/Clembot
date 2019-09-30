from discord.ext import commands
import json
import os
import asyncio
from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.exts.pkmn.spelling import SpellHelper
from clembot.exts.utils.utilities import Utilities

class Pokemon:

    def __init__(self, pokemon_id, label=None, pokedex_id=None, pokedex_num=None, base_attack=None, base_defense=None, base_stamina=None, alias=None, tags=None, type1=None, type2=None):
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

    def __str__(self):
        return self.label


    @property
    def to_dict(self):
        d = {
            'pokemon_id': self.pokemon_id,
            'label': self.label,
            'pokedex_id': self.pokedex_id,
            'pokedex_num': self.pokedex_num,
            'base_attack': self.base_attack,
            'base_defense': self.base_defense,
            'base_stamina': self.base_stamina,
            'alias': self.alias,
            'tags': self.tags,
            'type1': self.type1,
            'type2': self.type2
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


        return cls(pokemon_id, label, pokedex_id, pokedex_num, base_attack, base_defense, base_stamina, alias, tags, type1, type2)


class PokemonConverter(commands.Converter):

    async def convert(self, ctx, argument) -> Pokemon:

        pokemon_form = PokemonCache.to_pokemon(argument.upper())
        if pokemon_form:
            return pokemon_form
        else:
            possible_pokemon_form = await self.auto_correct(ctx, argument.upper())
            if possible_pokemon_form:
                pokemon_form = PokemonCache.to_pokemon(possible_pokemon_form)
                return pokemon_form

        raise Exception(f"{argument} could not be resolved to a pokemon.")

    async def auto_correct(self, ctx, pokemon_as_text):

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
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    @classmethod
    def cache_size(cls):
        return cls._cache.__len__()

    @classmethod
    def load_cache(cls, list_of_pokemon_records):

        pokemon_form_master = {}

        for record in list_of_pokemon_records:
            for alias in record['pokeform_alias']:
                pokemon_form_master[alias] = record

        cls._cache = pokemon_form_master
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

        except Exception as error:
            raise Exception("Couldn't load pokemon forms from DB due to error" + error)



class GameMasterParser:

    _cache = {}
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state


    @classmethod
    async def load_pokedex(cls, dbi):
        # if not cls._cache.__len__() == 0:
        # with open("https://raw.githubusercontent.com/PokeMiners/game_masters/master/previous_game_masters/gm_apk1532_Wed_Sep_18_10_26_26_2019/game_master.json", "r") as fd:

        with open(os.path.join('data', "game_master_000.json"), "r") as fd:
            print('opened file')
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
                    await GameMasterInterface.update_game_master(dbi, pokemonId, data)

            except Exception as error:
                print(error)
                print(json.dumps(pmr))

        print("load_pokedex() finished.")


class GameMasterInterface:

    def __int__(self):
       self.a=10

    @classmethod
    async def update_game_master(cls, dbi, pokemonId, data, forcedUpdate=False):

        if dbi:
            tbl_game_master = dbi.table('game_master')
            existing_pokemon_record = await tbl_game_master.query().clear().select().where(pokemon_id=pokemonId).get_first()

            if existing_pokemon_record:
                if forcedUpdate:
                    update_query = tbl_game_master.update(**data).where(pokemon_id=pokemonId)
                    await update_query.commit()
            else:
                insert_query = tbl_game_master.insert(**data)
                await insert_query.commit()

    @classmethod
    async def get_pokemon_master_list(cls, dbi):

        tbl_game_master = dbi.table('game_master')
        existing_pokemon_record = await tbl_game_master.query().clear().select('pokemon_id').where().get()

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
        await GameMasterParser.load_pokedex(dbi)



    except Exception as error:
        print(error)



def main():
    try:


        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize())
        loop.run_until_complete(test_condition())
        loop.run_until_complete(cleanup())

    except Exception as error:
        print(error)


# main()
