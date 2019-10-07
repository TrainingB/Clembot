import discord
import json

from discord.ext import commands
from clembot.core import checks
from clembot.exts.utils.utilities import Utilities
from clembot.exts.pkmn.pokemon import Pokemon, PokemonConverter, PokemonCache, OptionalPokemonConverter
from discord.ext.commands import MemberConverter, UserConverter
import random
from PIL import Image


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
            return value

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







class DraftManagerCog(commands.Cog):


    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()
        self.dbi = bot.dbi
        self.draft_interface = DraftInterface(bot.dbi)
        self._cache = {}
        self._guild_channel_draft_cache = {}

    def add_draft(self, draft: Draft):
        self._guild_channel_draft_cache[f"{draft.guild_id}_{draft.channel_id}"] = draft.draft_code
        self._cache[draft.draft_code] = draft

    async def fetch_draft_for_channel(self, guild_id, channel_id):

        guild_channel_key = f"{guild_id}_{channel_id}"

        if not self._guild_channel_draft_cache.keys().__contains__(guild_channel_key):
            draft_from_db = await self.draft_interface.find_draft(guild_id, channel_id)
            if draft_from_db:
                self.add_draft(draft_from_db)
            else:
                raise Exception("No draft found.")
        draft_code = self._guild_channel_draft_cache[guild_channel_key]
        return self._cache[draft_code]

    @commands.group(pass_context=True, hidden=True, aliases=["draft", "d"])
    async def _draft(self, ctx):

        if ctx.invoked_subcommand is None:
            return await Utilities.message(ctx.message.channel, f"Draft feature is under development!", user=ctx.author)


    @_draft.command(aliases=["check"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_check(self, ctx, text):

        try:

            pokemon = await PokemonConverter.convert(text, ctx, text)

            if pokemon:
                await Utilities.message(ctx.channel, f"{pokemon} details {pokemon.to_dict}")

        except Exception as error:
            await Utilities.error(ctx.channel, error)



    @_draft.command(aliases=["create", "new"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_create(self, ctx, draft_channel: discord.TextChannel = None):

        if draft_channel is None:
            draft_channel = ctx.channel

        draft = await self.draft_interface.find_draft(guild_id=ctx.guild.id, channel_id=draft_channel.id)
        if draft:
            return await Utilities.message(ctx.message.channel, f"A draft already exists for {draft_channel.mention} with code **{draft.draft_code}**")


        draft = Draft(guild_id=ctx.guild.id, channel_id=draft_channel.id)
        await self.draft_interface.save_draft(draft)
        self.add_draft(draft)

        return await Utilities.message(ctx.message.channel, f"A new draft can be managed in {draft_channel.mention} with code **{draft.draft_code}**")


    @_draft.command(aliases=["info"], pass_context=True)
    async def _draft_info(self, ctx):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
            if draft:
                print(draft.draft_content)
                return await Utilities._send_embed(ctx.channel, "", f"**Draft [{draft.draft_code}] - {draft.status} **", draft.embed_fields, footer=f"Managed by : {draft.draft_code} | check mark - Auto draft enabled!")
            else:
                return await Utilities.error(ctx.message.channel, f"No draft found for **{ctx.channel.mention}**")
        except Exception as error:
            print(error)
            return await Utilities.error(ctx.message.channel, f"{error}")


    @_draft.command(aliases=["reset"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_reset(self, ctx, mode=None):
        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        if mode == 'team':
            draft.reset_teams()
        else:
            draft.reset(ctx.guild.id, ctx.channel.id)

        await self.draft_interface.save_draft(draft)

        await Utilities.message(ctx.channel, f"Draft **{draft}** has been reset.")


    @_draft.command(aliases=["shuffle"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_shuffle(self, ctx):
        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        draft.shuffle_player_list()

        await self.draft_interface.save_draft(draft)

        await Utilities.message(ctx.channel, f"Current draft order is : {draft.player_draft_order_mentions}")

    @_draft.command(aliases=["add-player", "ap"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_add_player(self, ctx, *player_list: discord.Member):

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
        if DraftStatus.value(draft.status) >= DraftStatus.value(DraftStatus.DRAFT):
            return await Utilities.error(ctx.channel, f"Draft {draft} is in {draft.status} status. New players can not be added to the draft anymore.")


        for player in player_list:
            if draft.is_player_exists(player):
                await Utilities.error(ctx.channel, f"{player.mention} is already on the player list.")
                continue
            if draft.add_player(player):
                await Utilities.message(ctx.channel, f"**[{draft.number_of_players}/{draft.max_number_of_players}]** {player.mention} has been added to the draft.")
                await self.draft_interface.save_draft(draft)

        print(draft)


    @_draft.command(aliases=["join"], pass_context=True)
    async def _draft_join(self, ctx):

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
        if DraftStatus.value(draft.status) >= DraftStatus.value(DraftStatus.DRAFT):
            return await Utilities.error(ctx.channel, f"Draft {draft} is in {draft.status} status. New players can not be added to the draft anymore.")

        player = ctx.message.author
        if draft.is_player_exists(player):
            await Utilities.error(ctx.channel, f"{player.mention} you are already on the player list.")

        if draft.add_player(player):
            await Utilities.message(ctx.channel, f"**[{draft.number_of_players}/{draft.max_number_of_players}]** {player.mention} has been added to the draft.")
            await self.draft_interface.save_draft(draft)

        print(draft)


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.CheckFailure):
            return await Utilities.error(ctx.channel, f"{ctx.author.mention}, it seems like you don't have access to run this command.")
        elif isinstance(error, discord.ext.commands.CommandInvokeError):
            return await Utilities.error(ctx.channel, f'{error.original}')
        return await Utilities.error(ctx.channel, f'{error}')






    @commands.command(aliases=["dump-form"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def _dump_pokeform(self, ctx):

        await Utilities.send_to_hastebin(ctx.channel, json.dumps(PokemonCache.cache()))


    @commands.command(aliases=["debug-form"], pass_context=True)
    async def _debug_pokemon_form(self, ctx):
        try:

            result_record = await self.dbi.table('tbl_pokemon_master').query().select().getjson()

            await Utilities.send_to_hastebin(ctx.channel, json.dumps(result_record))

        except Exception as error:
            await Utilities.error(ctx.channel, error)


    @commands.command(aliases=["refresh-cache"], pass_context=True)
    async def _refresh_cache(self, ctx):
        try:
            results = await PokemonCache.load_cache_from_dbi(self.dbi)

            await Utilities.send_to_hastebin(ctx.channel, json.dumps(results))

            await Utilities.message(ctx.channel, f"The current cache size for pokemon is **{PokemonCache.cache_size()}**!")
        except Exception as error:
            await Utilities.error(ctx.channel, error)

    @_draft.command(aliases=["save"], pass_context=True)
    async def _draft_save(self, ctx):

        for draft_code in self.get_cache().keys():
            print(f"Saving draft {draft_code}")
            await self.draft_interface.update_draft(draft_code, self._cache.keys(draft_code))



    async def send_dm_for_auto_draft(self, ctx, player, draft, message_content, new_selection):


        await Utilities.message(ctx.channel, f"{player.mention} check your DM for auto-draft updates!")

        if not player.bot:
            await Utilities.message(player, f"**Guild**: **{ctx.channel.guild.name}** \n**Draft**: {draft} in {ctx.channel.mention} "
            f"\n**You entered**: `{message_content}`"
            f"\n**Your current auto-draft selection**: {new_selection}")



    @_draft.group(aliases=["auto"], pass_context=True)
    async def _draft_auto(self, ctx):
        if ctx.invoked_subcommand is None:
            return await Utilities.message(ctx.message.channel, f"!draft auto allows following options `add, clear, remove`", user=ctx.author)


    @_draft_auto.command(aliases=["enable"], pass_context=True)
    async def _draft_auto_enable(self, ctx):
        await self._draft_auto_change(ctx, True)


    @_draft_auto.command(aliases=["disable"], pass_context=True)
    async def _draft_auto_disable(self, ctx):
        await self._draft_auto_change(ctx, False)


    async def _draft_auto_change(self, ctx, auto_draft_mode):
        player = ctx.message.author
        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        change_auto_draft = await Utilities.ask_confirmation(ctx, ctx.message,
                                                             f"Are you sure you want to change auto draft for {player.mention} to **{auto_draft_mode}**?",
                                                             "Alright, sit tight!",
                                                             "Okay, just wanted to make sure!", "Timed out! No change done.")
        if change_auto_draft:
            draft.set_auto_draft(player.id, auto_draft_mode)
            await self.draft_interface.save_draft(draft)

        await Utilities.message(ctx.channel, f"For Draft **{draft}**, auto draft has been set to **{auto_draft_mode}** for {player.mention}")


    async def get_member_and_pokemon(self, ctx, args):
        player = None
        list_of_pokemon = []
        pokemon_converter = OptionalPokemonConverter()
        for arg in args:

            pokemon = await pokemon_converter.convert(ctx, argument=arg)
            if pokemon:
                list_of_pokemon.append(pokemon)
                continue

            member = await get_member(ctx, [arg], False)
            if member:
                player = member
                continue

        return player, list_of_pokemon

    @_draft_auto.command(aliases=["add"], pass_context=True)
    async def _draft_auto_add(self, ctx, *args):

        player, list_of_pokemon = await self.get_member_and_pokemon(ctx, args)

        message_content = ctx.message.content

        if player and checks.guildowner_or_permissions(manage_channels=True):
            player = player
        else:
            player = ctx.message.author

        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        new_selection = draft.add_to_player_auto_draft_selection(player.id, list_of_pokemon)

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)


    @_draft_auto.command(aliases=["remove"], pass_context=True)
    async def _draft_auto_remove(self, ctx, *provided_list_of_pokemon: OptionalPokemonConverter):

        list_of_pokemon = OptionalPokemonConverter.remove_empty_members(provided_list_of_pokemon)
        message_content = ctx.message.content

        player = ctx.message.author
        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        new_selection = draft.remove_from_player_auto_draft_selection(player.id, list_of_pokemon)

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)


    @_draft_auto.command(aliases=["set"], pass_context=True)
    async def _draft_auto_set(self, ctx, *provided_list_of_pokemon: OptionalPokemonConverter):

        list_of_pokemon = OptionalPokemonConverter.remove_empty_members(provided_list_of_pokemon)
        message_content = ctx.message.content

        player = ctx.message.author
        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        draft.set_player_auto_draft_selection(player.id, [pokemon.pokemon_id for pokemon in list_of_pokemon])

        new_selection = draft.get_player_auto_draft_selection(player.id)

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)


    @_draft_auto.command(aliases=["clear"], pass_context=True)
    async def _draft_auto_clear(self, ctx):

        message_content = ctx.message.content

        player = ctx.message.author
        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        new_selection = draft.set_player_auto_draft_selection(player.id, [])

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)



    @_draft.command(aliases=["set"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_update_attributes(self, ctx, key=None, *argument_list):

        available_keys = ['status', 'admin', 'exclude', 'auto']
        new_value = None
        if key is None or key not in available_keys:
            raise Exception("Not enough details to set/change configuration. Usage `!draft set key value``")

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        if key == 'auto':

            player = await get_member(ctx, argument_list) if argument_list else ctx.message.author

            current_auto_draft_selection = draft.get_auto_draft(player.id)

            change_auto_draft = await Utilities.ask_confirmation(ctx, ctx.message, f"Auto draft for {player.mention} is set to **{current_auto_draft_selection}**. Are you sure you want to change to **{not current_auto_draft_selection}**?", "Alright, sit tight!",
                                                                 "Okay, just wanted to make sure!", "Timed out! No change done.")
            if change_auto_draft:
                current_auto_draft_selection = not current_auto_draft_selection
                draft.set_auto_draft(player.id, current_auto_draft_selection)

            new_value = f"{current_auto_draft_selection} for {player.mention}"

        elif key == 'status':
            value = argument_list[0]
            if value.upper() in DraftStatus.status_by_rank:
                status = value.upper()
                if status == DraftStatus.DRAFT:
                    shuffle_list = await Utilities.ask_confirmation(ctx, ctx.message, "Do you want to shuffle the player list for draft?", "Alright, shuffling player list.",
                                                                    "Alright, leaving order intact.", "Timed out!")
                    if shuffle_list:
                        draft.shuffle_player_list()
                        await Utilities.message(ctx.channel, f"Current draft order is : {draft.player_draft_order_mentions}")

                draft.status = status


                new_value = status
            else:
                raise Exception(f"Invalid value for status. Acceptable status are {', '.join(DraftStatus.status_by_rank)}")

        elif key == 'admin':

            try:
                if not argument_list:
                    draft.admin = []
                    new_value = draft.admin
                else:
                    member = await get_member(ctx, argument_list)
                    if member:
                        if member.id not in draft.admin:
                            draft.admin.append(member.id)
                            new_value = draft.admin_mention
                        else:
                            raise Exception(f"{member.mention} is already an admin for this draft.")
                    else:
                        raise Exception("Invalid user information. Only valid user can be set as draft admin.")

            except Exception as error:
                raise Exception(error)


        elif key == 'exclude':

            for pkmn in argument_list:
                pokemon = await PokemonConverter.convert(PokemonConverter, ctx, pkmn)
                if pokemon:
                    draft.add_as_excluded(pokemon)

            new_value = ", ".join(draft.excluded)

        await self.draft_interface.update_draft(draft)
        await Utilities.message(ctx.channel, f"For Draft **{draft}** the **{key}** is set to **{new_value}**")


    async def auto_draft_for_current_player(self, ctx, draft):

        while True:
            current_player_id = draft.current_player
            auto_draft_enabled = draft.get_auto_draft(current_player_id)

            if not auto_draft_enabled:
                return await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")

            await Utilities.message(ctx.channel, f"Trying to auto draft for <@{draft.current_player}>")

            pokemon_id_to_draft = None
            for pokemon_id in draft.get_player_auto_draft_selection(current_player_id):
                print(f"{pokemon_id} for {current_player_id}")
                if pokemon_id in draft.drafted:
                    continue
                else:
                    pokemon_id_to_draft = pokemon_id
                    break

            if not pokemon_id_to_draft:
                return await Utilities.message(ctx.channel, f"<@{draft.current_player}> has no valid pokemon remaining in auto-draft. Make the next pick!")

            player = await get_member(ctx, [current_player_id])
            pokemon = PokemonCache.to_pokemon(pokemon_id_to_draft)

            try:
                draft.draft_pokemon(player, pokemon)
                await Utilities.message(ctx.channel, f"**[{draft.current_drafted_slots}/{draft.total_drafted_slots}]** Player {player.mention} has drafted **{pokemon}** successfully. **[Auto Drafted]**")

            except Exception as error:
                return await Utilities.message(ctx.channel, f"<@{draft.current_player}> error happened while auto-drafting. Make the next pick!")


            if draft.complete:
                return await Utilities.message(ctx.channel, f"The draft is complete now. You can head over to the silph.gg and choose teams.")
            else:
                await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")


    @_draft.command(aliases=["pick"], pass_context=True)
    async def _draft_pick(self, ctx, pokemon: PokemonConverter, player: discord.Member = None):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

            if DraftStatus.value(draft.status) != DraftStatus.value(DraftStatus.DRAFT):
                return await Utilities.error(ctx.channel, f"Draft {draft} is in {draft.status} status. Drafting new pokemon is allowed during {DraftStatus.DRAFT} status only.")

            if player:
                if ctx.author.id not in draft.admin:
                    raise Exception("Only draft admin can pick pokemon for other players.")
            else:
                player = ctx.author

            if pokemon:
                draft.draft_pokemon(player, pokemon)
                await Utilities.message(ctx.channel, f"**[{draft.current_drafted_slots}/{draft.total_drafted_slots}]** Player {player.mention} has drafted **{pokemon}** successfully.")
                await self.draft_interface.save_draft(draft)

            if draft.complete:
                await Utilities.message(ctx.channel, f"The draft is complete now. You can head over to the silph.gg and choose teams.")
            else:
                await self.auto_draft_for_current_player(ctx, draft)
                # await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")

        except Exception as error:
            await Utilities.error(ctx.channel, error, ctx.author)

    @_draft.command(aliases=["next"], pass_context=True)
    async def _draft_next(self, ctx):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
            await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")
        except Exception as error:
            await Utilities.error(ctx.channel, error, ctx.author)

    @_draft.command(aliases=["dump"], pass_context=True)
    async def _draft_dump(self, ctx):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

            await Utilities.send_to_hastebin(ctx.channel, json.dumps(draft.draft_content))


        except Exception as error:
            await Utilities.error(ctx.channel, error, ctx.author)



    @_draft.command(aliases=["help"], pass_context=True)
    async def _draft_help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(
            embed=DraftManagerCog.get_beep_embed(title="Help - Draft Management", description=DraftManagerCog.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


    beep_notes = ("""**{member}** here are the commands for draft management. 

**Player commands**
**!draft join** - join the current draft for the channel.
**!draft pick pokemon** - drafts a pokemon for you if it is available for drafting purposes.
**!draft next** - send a mention to next person to make the selection
**!draft auto enable** - enable auto-drafting
**!draft auto disable** - disable auto-drafting

**!draft auto add pokemon-list** - add pokemon to your auto-draft list
**!draft auto remove pokemon-list** - remove pokemon from your auto-draft list
**!draft auto set pokemon-list** - set the pokemon list as your auto-draft list
**!draft auto clear** - clears your auto-draft list


**Admin commands (will need manage channel permissions)** 
**!draft create** - creates a draft in the current channel. One channel can hold only one draft.
**!draft set admin @user** - makes the user admin for the draft ( they need to have manage_channel permission )

**!draft set status *status_value*** - changes the status of the draft. 
**Drafts go from CREATED -> SIGN_UP -> DRAFT -> COMPLETE.**

**!draft add-player @user** - adds user to draft player team
**!draft info** - display draft information

""")

    @classmethod
    def get_beep_embed(cls, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(cls, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=DraftManagerCog.get_beep_embed(title="Help - Trade Management", description=DraftManagerCog.beep_notes.format(member=ctx.message.author.display_name), footer=footer))

    @commands.command(aliases=["add-emoji"], pass_context=True)
    async def _add_emoji(self, ctx, *pokemon_list: PokemonConverter):
        try:
            if pokemon_list:
                for pokemon in pokemon_list:
                    print(pokemon.emoji)
                    if not pokemon.emoji:
                        emoji = await PokemonCache.create_emoji(ctx, self.dbi, pokemon.pokemon_id)
                        await Utilities.message(ctx.channel, f"[{len(ctx.guild.emojis)}/50]{pokemon.pokemon_id}{emoji} can be accessed by \\{str(emoji)}!")

            else:
                list_of_pokemon = await self.dbi.table('tbl_pokemon_master').query().select().order_by('pokemon_id').getjson()
                for pokemon_record in list_of_pokemon:
                    print(pokemon_record['emoji_key'])
                    if not pokemon_record['emoji_key']:
                        emoji = await PokemonCache.create_emoji(ctx, self.dbi, pokemon_record['pokemon_id'])
                        await Utilities.message(ctx.channel, f"[{len(ctx.guild.emojis)}/50]{pokemon_record['pokemon_id']}{emoji} can be accessed by \\{str(emoji)}!")

        except Exception as error:
            await Utilities.error(ctx.channel, error)



async def get_member(ctx, argument_list, error_when_not_found=True):

    user_converter = UserConverter()

    # converter = MemberConverter()
    if argument_list is None:
        return None
    else:
        member = None
        try:
            member = await user_converter.convert(ctx=ctx, argument=str(argument_list[0]))
            return member
        except Exception as error:
            if error_when_not_found:
                print(error)
                raise Exception("Member not found!")
            else:
                return None

def setup(bot):
    bot.add_cog(DraftManagerCog(bot))


# def main():
#
#     my_list = [1,2,3,4,5,6,7,8]
#
#     for i in chunks(my_list, 3):
#         print(i)
#
#
# main()