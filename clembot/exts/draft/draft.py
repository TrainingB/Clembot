import json
import random

import discord
from discord.ext import commands

from clembot.exts.pkmn.pokemon import PokemonCache, Pokemon


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_emoji(pokemon_id):

    pokemon = PokemonCache.pokemon(pokemon_id)

    if pokemon.emoji:
        return pokemon.emoji
    return pokemon_id

class Base36:
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'


    @classmethod
    def dumps(self, number):
        """Dumps an integer into a base36 string.
        :param number: the 10-based integer.
        :returns: the base36 string.
        """
        if not isinstance(number, int):
            raise TypeError('number must be an integer')

        if number < 0:
            return '-' + Base36.dumps(-number)

        value = ''

        while number != 0:
            number, index = divmod(number, len(Base36.alphabet))
            value = Base36.alphabet[index] + value

        return value or '0'


    @classmethod
    def loads(self, value):
        """Loads a base36 string and parse it into 10-based integer.
        :param value: the base36 string.
        :returns: the parsed integer.
        """
        return int(value, 36)


class CUIDGenerator:


    @classmethod
    def cuid(cls, id):
        try:
            value = Base36.dumps(divmod(id, 10 ** 6)[1])
            return value.upper()

        except Exception as error:
            print(error)
            return id


class DraftStatus:

    status_by_rank = ['CREATED', 'SIGN_UP', 'DRAFT', 'COMPLETE']

    CREATED, SIGN_UP, DRAFT, COMPLETE = status_by_rank

    @classmethod
    def value(cls, status):
        return cls.status_by_rank.index(status)


class DraftStatusConverter(commands.Converter):

    async def convert(self, ctx, argument) -> DraftStatus:

        pokemon_form = PokemonCache.to_pokemon(argument.upper())
        if pokemon_form:
            return pokemon_form
        else:
            raise Exception(f"{argument} could not resolved to a pokemon.")


class Draft:

    sample_draft_master = {

        "properties": {
            "code": "",
            "channel_id": -1,
            "guild_id": -1
        },
        "configuration": {
            "admin": [],
            "status": DraftStatus.CREATED,
            "number_of_players": 0,
            "max_number_of_players": 16,
            "draft_team_size": 6,
            "total_drafted_slots": 0,
            "current_drafted_slots": 0,
            "current_player_index": 0,
        },

        "player_list": [
        ],

        "player_draft_order": [
        ],

        "choices": {
            "available": [],
            "drafted": [],
            "excluded": []
        },

        "player_selection": {

        },

        "player_selections": {
            # "drafted": {},
            # "auto_draft_options": {},
            # "enable_auto_draft": False
        },
    }

    def __init__(self, data_dict=None, guild_id=None, channel_id=None):
        if data_dict:
            self.draft_content = json.loads(data_dict['draft_content'])

            new_player_selection = {}
            new_player_selections = {}
            for key, value in self.player_selection.items():
                new_player_selection[int(key)] = value

            for key, value in self.player_selections.items():
                new_player_selections[int(key)] = value

            self.player_selection = new_player_selection
            self.player_selections = new_player_selections

        else:
            self.reset(guild_id, channel_id)

    def __str__(self):
        return self.draft_code
        # return json.dumps(self.draft_content)


    def set_auto_draft(self, player_id, draft: bool):
        self.player_selections.setdefault(player_id, {})['enable_auto_draft'] = draft

    def get_auto_draft(self, player_id):
        return self.player_selections.setdefault(player_id, {}).get('enable_auto_draft', False)


    def get_player_auto_draft_selection(self, player_id):
        return self.player_selections.get(player_id, {}).get('auto_draft_options', [])

    def set_player_auto_draft_selection(self, player_id, list_of_pokemon):
        self.player_selections.setdefault(player_id, {})['auto_draft_options'] = [pokemon for pokemon in list_of_pokemon if pokemon is not None]


    def add_to_player_auto_draft_selection(self, player_id, list_of_pokemon):
        new_list = list(self.get_player_auto_draft_selection(player_id))

        for pokemon in list_of_pokemon:
            if pokemon and pokemon.pokemon_id not in new_list:
                new_list.append(pokemon.pokemon_id)

        self.set_player_auto_draft_selection(player_id, new_list)

        return self.get_player_auto_draft_selection(player_id)

    def remove_from_player_auto_draft_selection(self, player_id, list_of_pokemon):
        new_list = list(self.get_player_auto_draft_selection(player_id))

        for pokemon in list_of_pokemon:
            if pokemon.pokemon_id in self.get_player_auto_draft_selection(player_id):
                new_list.remove(pokemon.pokemon_id)

        self.set_player_auto_draft_selection(player_id, new_list)

        return self.get_player_auto_draft_selection(player_id)

    @property
    def draft_code(self):
        return self.draft_content['properties']['code']

    @property
    def channel_id(self):
        return self.draft_content['properties']['channel_id']

    @property
    def guild_id(self):
        return self.draft_content['properties']['guild_id']

    @property
    def status(self):
        return self.draft_content['configuration']['status']

    @status.setter
    def status(self, draft_status):
        if draft_status == DraftStatus.DRAFT and not self.player_draft_order:
            self.player_draft_order = list(self.player_list)

        self.draft_content['configuration']['status'] = draft_status

    @property
    def number_of_players(self):
        return self.draft_content['configuration']['number_of_players']

    @property
    def max_number_of_players(self):
        return self.draft_content['configuration']['max_number_of_players']


    @property
    def embed_fields(self):

        embed_fields = {
            f"Status": self.status,
        }


        if DraftStatus.value(self.status) == DraftStatus.value(DraftStatus.SIGN_UP):
            players_mention = ""
            for player_id in self.player_list:
                players_mention = f"{players_mention} <@{player_id}>"
            embed_fields[f"Signed up Players ({self.number_of_players}/{self.max_number_of_players})"]=f"{players_mention}"

        elif DraftStatus.value(self.status) >= DraftStatus.value(DraftStatus.DRAFT):
            players_mention = ""
            for player_id in self.player_draft_order:
                players_mention = f"{players_mention} <@{player_id}> {':ballot_box_with_check:' if self.get_auto_draft(player_id) else ''}"

            embed_fields[f"Players (in draft order) [{self.number_of_players}/{self.max_number_of_players}]"] = f"{players_mention}"

        if DraftStatus.value(self.status) >= DraftStatus.value(DraftStatus.DRAFT):
            embed_fields_title = "Teams"

            for part_player_id_list in chunks(list(self.draft_content['player_selection'].keys()), 2):
                player_line = ""

                for player_id in part_player_id_list:

                    player_mention = f"<@{player_id}>"
                    current_player_selection = self.player_selection[player_id]
                    print([get_emoji(pokemon_id) for pokemon_id in current_player_selection])

                    player_selection = f"{(', '.join([get_emoji(pokemon_id) for pokemon_id in current_player_selection]))}"

                    player_line = f"{player_line}\n{player_mention} - {player_selection}"

                embed_fields[f"{embed_fields_title}"] = f"{player_line}"
                embed_fields_title = f"--" if embed_fields_title == "Teams" else f"{embed_fields_title}-"

            pokemon_mention = ""
            for pokemon in self.draft_content['choices']['drafted']:
                pokemon_mention = f"{pokemon_mention}{PokemonCache.pokemon(pokemon)}, "

        if DraftStatus.value(self.status) == DraftStatus.value(DraftStatus.DRAFT):
            embed_fields[f"Next to pick:"] = f"<@{self.current_player}>"



        return embed_fields

    @property
    def player_draft_order_mentions(self):

        players_mention = ""
        for player_id in self.player_draft_order:
            players_mention = f"{players_mention} <@{player_id}>"
        return f"{players_mention}"

    @property
    def player_list(self):
        return self.draft_content.get('player_list')

    @player_list.setter
    def player_list(self, player_list):
        self.draft_content['player_list'] = player_list

    @property
    def player_draft_order(self):
        return self.draft_content.get('player_draft_order')

    @player_draft_order.setter
    def player_draft_order(self, player_draft_order):
        self.draft_content['player_draft_order'] = player_draft_order


    @property
    def configuration(self):
        return self.draft_content['configuration']

    @property
    def total_drafted_slots(self):
        return self.configuration['total_drafted_slots']

    @total_drafted_slots.setter
    def total_drafted_slots(self, total_drafted_slots):
        self.configuration['total_drafted_slots'] = total_drafted_slots

    @property
    def current_drafted_slots(self):
        return self.configuration['current_drafted_slots']

    @current_drafted_slots.setter
    def current_drafted_slots(self, current_drafted_slots):
        self.configuration['current_drafted_slots'] = current_drafted_slots



    @property
    def admin(self):
        return self.configuration['admin']

    @admin.setter
    def admin(self, admin_list):
        self.configuration['admin'] = admin_list


    @property
    def draft_team_size(self):
        return self.configuration['draft_team_size']

    @property
    def current_player_index(self):
        return self.configuration['current_player_index']

    @current_player_index.setter
    def current_player_index(self, current_player_index):
        self.configuration['current_player_index'] = current_player_index

    @property
    def next_player_index(self):

        size_of_team = self.number_of_players
        players_already_drafted = self.current_drafted_slots
        current_player_index = self.current_player_index

        direction = 0
        next_index = players_already_drafted % size_of_team
        if (players_already_drafted % (size_of_team * 2)) > size_of_team - 1:
            direction = 1
            next_index = size_of_team - next_index - 1

        return next_index

    @property
    def current_player(self):
        return self.player_draft_order[self.current_player_index]


    @property
    def admin_mention(self):
        players_mention = ""
        for player_id in self.admin:
            players_mention = f"{players_mention} <@{player_id}>"
        return players_mention

    def draft_content(self):
        return self.draft_content

    def add_player(self, player: discord.Member):

        if self.status != DraftStatus.SIGN_UP:
            raise Exception("Draft should be in SIGN_UP stage for adding players to draft.")

        if self.is_player_exists(player):
            return False

        self.player_list.append(player.id)
        self.draft_content['configuration']['number_of_players'] = self.number_of_players + 1
        self.total_drafted_slots = 6 * self.number_of_players
        if self.current_player_index == -1:
            self.current_player_index = 0

        return True

    def is_player_exists(self, player: discord.Member):
        return self.draft_content.get('player_list').__contains__(player.id)

    def remove_player(self, player: discord.Member):
        self.draft_content.get('player_list').remove(player.id)

    def reset(self, guild_id, channel_id):
        self.draft_content = self.sample_draft_master
        draft_code = CUIDGenerator.cuid(channel_id)
        self.draft_content["properties"] = {
            "code": draft_code,
            "guild_id": guild_id,
            "channel_id": channel_id,
        }

    def shuffle_player_list(self):
        if self.status != DraftStatus.SIGN_UP:
            raise Exception("Draft should be in SIGN_UP stage for shuffling players.")

        player_draft_order = list(self.player_list)

        print(player_draft_order)
        random.shuffle(player_draft_order)
        print(player_draft_order)

        self.player_draft_order = player_draft_order


    def draft_pokemon(self, player: discord.Member, pokemon: Pokemon):

        if 0 < self.current_drafted_slots >= self.total_drafted_slots:
            raise Exception(f"A team of {self.draft_team_size} has been drafted for everyone.")

        if self.status != DraftStatus.DRAFT:
            raise Exception("Draft should be in DRAFT stage before you can draft pokemon.")

        if player.id not in self.player_list:
            raise Exception(f"{player.mention} is not added to the draft yet!")

        if self.current_player != player.id:
            raise Exception(f"It's not {player.mention}'s turn yet to draft.")

        pokemon_id = pokemon.pokemon_id
        if pokemon_id in self.drafted or pokemon_id in self.excluded:
            raise Exception(f"Pokemon {pokemon} is already drafted (or excluded)!")

        self.player_selection.setdefault(player.id, []).append(pokemon.pokemon_id)
        self.add_as_drafted(pokemon)
        self.current_drafted_slots = self.current_drafted_slots + 1
        if self.complete:
            self.status = DraftStatus.COMPLETE

        self.current_player_index = self.next_player_index


    @property
    def complete(self):
        if self.current_drafted_slots >= self.total_drafted_slots:
            return True
        return False


    @property
    def player_selections(self):
        self.draft_content.setdefault('player_selections',{})
        return self.draft_content['player_selections']

    @player_selections.setter
    def player_selections(self, player_selections_dict):
        self.draft_content['player_selections'] = player_selections_dict

    @property
    def player_selection(self):
        return self.draft_content['player_selection']

    @player_selection.setter
    def player_selection(self, player_selection_dict):
        self.draft_content['player_selection'] = player_selection_dict


    @property
    def choices(self):
        return self.draft_content['choices']

    @property
    def available(self):
        return self.choices['available']

    @property
    def drafted(self):
        return self.choices['drafted']

    @drafted.setter
    def drafted(self, drafted_list):
        self.choices['drafted'] = drafted_list

    @property
    def excluded(self):
        return self.choices['excluded']

    @excluded.setter
    def excluded(self, excluded_list):
        self.choices['excluded'] = excluded_list

    def add_as_excluded(self, excluded_pokemon: Pokemon):
        self.choices.setdefault('excluded', []).append(excluded_pokemon.pokemon_id)

    def add_as_drafted(self, drafted_pokemon: Pokemon):
        self.choices.setdefault('drafted', []).append(drafted_pokemon.pokemon_id)


    def reset_teams(self):
        self.player_selection = {}
        self.current_drafted_slots = 0
        self.current_player_index = self.next_player_index
        self.drafted = []


class DraftInterface:

    def __init__(self, dbi):
        self.dbi = dbi

    async def load_draft_from_db(self):

        draft_master_query = self.dbi.table("draft_master").query().select('draft_content')

        record_list = await draft_master_query.getjson()

        return record_list




    async def find_draft(self, guild_id, channel_id):

        try:

            draft_master_query = self.dbi.table("draft_master").query().select('draft_content').where(guild_id=guild_id, channel_id=channel_id)

            existing_draft_master = await draft_master_query.getjson()

            if existing_draft_master:
                return Draft(existing_draft_master[0])

        except Exception as error:
            raise Exception("No draft found.")


    async def find_draft_code(self, draft_code=None):

        try:
            draft_master_query = self.dbi.table("draft_master").query().select('draft_content').where(draft_code=draft_code)

            existing_draft_master = await draft_master_query.getjson()

            return existing_draft_master


        except Exception as error:
            print(error)


    async def update_draft(self, draft: Draft):

        try:

            tbl_draft_master = self.dbi.table('draft_master')

            existing_draft_master_record = await tbl_draft_master.query().select().where(
                draft_code=draft.draft_code).get_first()

            if existing_draft_master_record:
                update_query = tbl_draft_master.update(draft_content=json.dumps(draft.draft_content)).where(
                    draft_id=existing_draft_master_record["draft_id"])
                await update_query.commit()

        except Exception as error:
            print(error)


    async def save_draft(self, draft: Draft):

        try:
            draft_master_record = dict(
                guild_id=draft.guild_id,
                channel_id=draft.channel_id,
                draft_code=draft.draft_code,
                draft_content=json.dumps(draft.draft_content)
            )
            tbl_draft_master = self.dbi.table('draft_master')

            existing_draft_master_record = await tbl_draft_master.query().select().where(guild_id=draft.guild_id,
                                                                                         channel_id=draft.channel_id).get_first()

            if existing_draft_master_record:
                update_query = tbl_draft_master.update(draft_content=json.dumps(draft.draft_content)).where(
                    draft_id=existing_draft_master_record["draft_id"])
                await update_query.commit()
            else:
                insert_query = tbl_draft_master.insert(**draft_master_record)
                await insert_query.commit()

            print(f"{draft} is saved successfully!")
        except Exception as error:
            print(error)