import os
import pickle
import re

import discord
from discord.ext import commands

from clembot.core.bot import group, command
from clembot.core.logs import Logger
from clembot.exts.profile.user_profile import UserProfile
from clembot.exts.trade.pokemonform import PokemonForm
from clembot.utilities.utils.converters import RemoveComma
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


def print_pokemon(list_of_pokemon):
    escaped_list = ['"%s"' % e if re.search('[^A-Za-z0-9-]', e) else e for e in list_of_pokemon]
    return ", ".join(escaped_list)


class TradeManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi

    # @_poke_form.command(aliases=["save"])
    # async def _poke_form_save(self, ctx):
    #     with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
    #         data = json.load(fd)
    #
    #     tmp = data['pokemon_forms']
    #     data['pokemon_forms'] = PokemonForm.available_pokemon_forms
    #
    #     with open(os.path.join('data', 'pokemon_forms.json'), 'w') as fd:
    #         json.dump(data, fd, indent=2, separators=(', ', ': '))
    #
    #     await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, saved pokemon-forms successfully. See the complete list using **!poke-form list**.")



    @group(pass_context=True, hidden=True, aliases=["trade","t"])
    async def cmd_trade(self, ctx):
        if not PokemonForm.available_pokemon_forms:
            await PokemonForm.load_forms(ctx.bot)

        if ctx.invoked_subcommand is None:
            await Embeds.message(ctx.channel, f"**!trade** can be used with various options. See **!beep trade** for more details.", ctx.message.author)


    @cmd_trade.command(aliases=["list"])
    async def cmd_trade_list(self, ctx, *parameters: RemoveComma):

        if len(ctx.message.mentions) > 0:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.author

        user_profile = await UserProfile.find(ctx.bot, user.id)

        trainer_trade_offers = user_profile['trade_offers']
        trainer_trade_requests = user_profile['trade_requests']

        filtered_trainer_trade_offers = []
        filtered_trainer_trade_requests = []

        if len(parameters) > len(ctx.message.mentions) :
            for parameter in parameters:
                filter_text = parameter
                if filter_text:
                    filtered_trainer_trade_offers.extend([ form for form in trainer_trade_offers if filter_text and form.__contains__(filter_text) and form not in filtered_trainer_trade_offers])
                    filtered_trainer_trade_requests.extend([ form for form in trainer_trade_requests if filter_text and form.__contains__(filter_text) and form not in filtered_trainer_trade_requests])

        else:
            filtered_trainer_trade_offers = trainer_trade_offers
            filtered_trainer_trade_requests = trainer_trade_requests

        trainer_trade_requests_text = Utilities.trim_to(print_pokemon(filtered_trainer_trade_requests), 990)
        trainer_trade_offers_text= Utilities.trim_to(print_pokemon(filtered_trainer_trade_offers), 990)

        additional_fields = {
            'Requests (Wants)': [False, trainer_trade_requests_text if len(trainer_trade_requests_text) > 0 else "No requests yet!"],
            'Offers (Have)': [False, trainer_trade_offers_text if len(trainer_trade_offers_text) > 0 else "No requests yet!"]}


        await ctx.send(embed=Embeds.make_embed(header=f"Trade Profile - {user.display_name}", header_icon=user.avatar_url, fields=additional_fields))



    @cmd_trade.command(aliases=["request","r"])
    async def cmd_trade_request(self, ctx, *pokemon_list: RemoveComma):
        try:
            valid_pokemon_list = PokemonForm.extract_valid_pokemon_forms(pokemon_list)

            user_profile = await UserProfile.find(ctx.bot, ctx.message.author.id)

            user_profile['trade_requests'] = [pkmn for pkmn in valid_pokemon_list if pkmn not in user_profile['trade_requests']]
            await user_profile.update()
            pokemon_request_message = print_pokemon(user_profile['trade_requests'])

            if len(pokemon_request_message) > 0:
                await ctx.send(embed=TradeProfileEmbed.trade_request_embed(ctx, user_profile, pokemon_list, valid_pokemon_list))
            else:
                await Embeds.error(ctx.channel, f"you have no pokemon requests registered with me yet!", ctx.message.author)
        except Exception as error:
            Logger.error(error)


    @cmd_trade.command(aliases=["offer","have","o","h"])
    async def cmd_trade_offer(self, ctx, *pokemon_list: RemoveComma):
        try:
            valid_pokemon_list = PokemonForm.extract_valid_pokemon_forms(pokemon_list)

            user_profile = await UserProfile.find(ctx.bot, ctx.message.author.id)

            user_profile['trade_offers'] = [pkmn for pkmn in valid_pokemon_list if pkmn not in user_profile['trade_offers']]
            await user_profile.update()
            pokemon_request_message = print_pokemon(user_profile['trade_offers'])

            if len(pokemon_request_message) > 0:
                await ctx.send(embed=TradeProfileEmbed.trade_offer_embed(ctx, user_profile, pokemon_list, valid_pokemon_list))
            else:
                await Embeds.error(ctx.channel, f"you have no pokemon for trade registered with me yet!", ctx.message.author)
        except Exception as error:
            Logger.error(error)


    @cmd_trade.command(aliases=["clear","c"])
    async def cmd_trade_clear(self, ctx, *pokemon_list: RemoveComma):
        try:
            user = ctx.message.author
            user_profile = await UserProfile.find(ctx.bot, ctx.message.author.id)

            if 'all' in pokemon_list:

                del user_profile['trade_offers']
                del user_profile['trade_requests']
                await user_profile.update()
                return await Embeds.message(ctx.channel, f"your request & offer list has been cleared!", user=user)


            valid_pokemon_list = PokemonForm.extract_valid_pokemon_forms(pokemon_list)
            removed_poke_form_list = []

            if len(valid_pokemon_list) > 0:

                trainer_trade_offers = list(user_profile['trade_offers'])
                trainer_trade_requests = list(user_profile['trade_requests'])

                del user_profile['trade_offers']
                del user_profile['trade_requests']

                for pokemon_offered in valid_pokemon_list:

                    if pokemon_offered in trainer_trade_offers:
                        trainer_trade_offers.remove(pokemon_offered)
                        removed_poke_form_list.append(pokemon_offered)

                    if pokemon_offered in trainer_trade_requests:
                        trainer_trade_requests.remove(pokemon_offered)
                        if pokemon_offered not in removed_poke_form_list:
                            removed_poke_form_list.append(pokemon_offered)

                user_profile['trade_offers'] = trainer_trade_offers
                user_profile['trade_requests'] = trainer_trade_requests
                await user_profile.update()

                await ctx.send(embed=TradeProfileEmbed.trade_clear_embed(ctx, user_profile, pokemon_list, valid_pokemon_list, removed_poke_form_list))
        except Exception as error:
            Logger.error(error)



    @command(pass_context=True, hidden=True, aliases=["x_x"])
    async def xx(self, ctx, *parameters):
        message = ctx.message
        arguments = message.content

        self.process_parameters(message)


        party_status = {}
        mentions_list = []

        args = arguments.split()
        # if mentions are provided
        if message.mentions:
            for mention in message.mentions:
                mention_text = mention.mention.replace('!','')
                mentions_list.append(mention_text)
                arguments = arguments.replace("<@!","<@")
                arguments = arguments.replace(mention_text,'#'+str(mention.id))

        only_arguments = [arg for arg in args if arg not in message.mentions]


        additional_fields = {}
        additional_fields['parameters'] = "|".join(parameters) if len(parameters) > 0 else "None"

        additional_fields['mentions'] = [xm.mention for xm in message.mentions]
        additional_fields['arguments'] = arguments if len(arguments) >0 else "None"

        additional_fields['mentions_list'] = mentions_list

        additional_fields['message.content'] = message.content

        additional_fields['only_arguments'] = only_arguments

        await Utilities._send_embed(ctx.channel, additional_fields=additional_fields)


    @cmd_trade.command(aliases=["migrate"])
    async def cmd_trade_migrate(self, ctx):
        try:
            with open(os.path.join(os.path.abspath('.'), 'data', 'guilddict_clembot'), "rb") as fd:
                server_dict_old = pickle.load(fd)

            for guild_id in server_dict_old.keys():
                print(f"Processing {guild_id}")
                guild_dict = server_dict_old.get(guild_id)

                trainers_dict = guild_dict.get('trainers')
                print(f"Found {len(trainers_dict.keys())} trainers.")
                for trainer_id in trainers_dict.keys():

                    trainer_dict = trainers_dict.get(trainer_id)
                    trainer_dict.pop('leaderboard-stats', None)
                    trainer_dict.pop('lifetime', None)
                    trainer_dict.pop('badges', None)

                    if not bool(trainer_dict):
                        continue

                    print(trainer_dict)
                    user_profile = await UserProfile.find(self.bot, trainer_id)
                    if user_profile['status'] == 'migrated':
                        continue

                    user_profile['trade_requests'] = trainer_dict.get('trade_requests')
                    user_profile['trade_offers'] = trainer_dict.get('trade_offers')
                    user_profile['trainer_code'] = trainer_dict.get('profile',{}).get('trainer-code')
                    user_profile['ign'] = trainer_dict.get('profile', {}).get('ign')
                    user_profile['silph_id'] = trainer_dict.get('profile', {}).get('silph-id')
                    user_profile['pokebattler_id'] = trainer_dict.get('profile', {}).get('pokebattler_id')
                    user_profile['status'] = 'migrated'
                    await user_profile.update()
                    # print(user_profile.db_dict)
        except Exception as error:
            print(error)


    @cmd_trade.command(aliases=["search"])
    async def cmd_trade_search(self, ctx, *search_for: RemoveComma):
        """Allows search for trades"""
        searchable_list_key = 'trade_offers'
        search_result_list_key = 'trade_requests'
        offers_or_request = 'offers'
        offering_or_requesting = 'offering'
        offered_or_requested = 'requested'
        has_or_wants = 'has'
        if '-request' in search_for :
            searchable_list_key = 'trade_requests'
            search_result_list_key = 'trade_offers'
            offers_or_request = 'requests'
            offering_or_requesting = 'requesting'
            offered_or_requested = 'to offer'
            has_or_wants = 'wants'
            search_for = tuple([x for x in search_for if x != '-request'])

        try:
            if len(search_for) == 0:
                return await Embeds.error(ctx.channel, f"Usage `!trade search pokemon`")
            valid_pokemon_list = PokemonForm.extract_valid_pokemon_forms(search_for)
            if len(valid_pokemon_list) == 0:
                valid_pokemon_list = search_for

            for pokemon_searched_for in valid_pokemon_list:

                trainers_with_pokemon = []
                trainer_list = []
                additional_fields = {}
                additional_trainer_id_list = []
                additional_trainer_list = []

                trainer_trade_pokeform = pokemon_searched_for if PokemonForm.is_valid(pokemon_searched_for) else f'something like {pokemon_searched_for}'
                user_profile_list = await UserProfile.find_all_by_trade_preferences(self.bot, pokemon_searched_for, searchable_list_key)

                for user_profile in user_profile_list:

                    trainer = ctx.guild.get_member(user_profile.user_id)
                    if trainer is None:
                        Logger.info(f"{user_profile.user_id} is not present on this guild.")
                        continue

                    if len(trainers_with_pokemon) > 10:
                        additional_trainer_id_list.append(trainer.id)
                        additional_trainer_list.append(f'{trainer.display_name}')

                    else:
                        trainers_with_pokemon.append(trainer.id)
                        trainer_trade_requests = user_profile[search_result_list_key]

                        if len(trainer_trade_requests) > 10:
                            additional_fields[f"{trainer.display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f"{print_pokemon(trainer_trade_requests[:10])} and more."
                        elif len(trainer_trade_requests) > 0:
                            additional_fields[f"{trainer.display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f'{print_pokemon(trainer_trade_requests)}'
                        else:
                            additional_fields[f"{trainer.display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f'No {offers_or_request} yet!'

                if additional_trainer_list:
                    additional_fields[f"Other Trainers {offering_or_requesting} {trainer_trade_pokeform}"] = ", ".join(additional_trainer_list)

                if len(additional_fields) > 0:
                    await ctx.send(embed=Embeds.make_embed(header=f"Trade Search Results for {pokemon_searched_for}", header_icon=ctx.message.author.avatar_url,
                        content=f"Trainer(s) {offering_or_requesting} **{trainer_trade_pokeform}** for trade and here is what they have {offered_or_requested}:",
                                                           fields=additional_fields))
                else:
                    await Embeds.error(ctx.channel, f"No trainer is {offering_or_requesting} **{pokemon_searched_for}** for trading yet!", ctx.message.author)
        except Exception as error:
            await Embeds.error(ctx.channel, f"Error occured while searching : {error}")





    beep_notes = ("""**{member}** here are the commands for trade management. 

**!trade offer <pokemon>** - to add pokemon to your offers list.
**!trade request <pokemon>** - to add pokemon to your requests list.

**!trade clear <pokemon>** - to remove pokemon from your trade offer or request list.
**!trade clear all** - to clear your trade offer and request list.

**!trade list** - brings up pokemon in your trade offer/request list.
**!trade list @user** - brings up pokemon in user's trade offer/request list.
**!trade list pokemon** - filters your trade offer/request list by specified pokemon.

**!trade search <pokemon>** - brings up a list of all the users and details for first 10 users who are offering the pokemon.
**!trade search -request <pokemon>** - brings up a list of all the users and details for first 10 users who are looking for the pokemon.

**<pokemon> - can be one or more pokemon or pokedex# separated by space.**

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
        await ctx.message.channel.send(embed=TradeManager.get_beep_embed(title="Help - Trade Management", description=TradeManager.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


class TradeProfileEmbed:

    @staticmethod
    def trade_request_embed(ctx, user_profile, pokemon_list, valid_pokemon_list):

        pokemon_request_message = print_pokemon(user_profile['trade_requests'])

        footer = None
        if len(valid_pokemon_list) < len(pokemon_list):
            footer = "Tip: You can use Pokedex # instead of pokemon name. To see available options use !poke-form list <filter>"

        additional_fields = {'Accepted Input': [False, Utilities.trim_to(print_pokemon(valid_pokemon_list), 900)],
                             'Request (Wants)': [False, Utilities.trim_to(pokemon_request_message, 980)]}


        embed = Embeds.make_embed(header="Trade Profile (Requests)", header_icon=ctx.message.author.avatar_url, footer=footer,
                                  fields=additional_fields)

        return embed

    @staticmethod
    def trade_offer_embed(ctx, user_profile, pokemon_list, valid_pokemon_list):

        pokemon_request_message = print_pokemon(user_profile['trade_offers'])

        footer = None
        if len(valid_pokemon_list) < len(pokemon_list):
            footer = "Tip: You can use Pokedex # instead of pokemon name. To see available options use !poke-form list <filter>"

        additional_fields = {'Accepted Input': [False, Utilities.trim_to(print_pokemon(valid_pokemon_list), 900)],
                             'Offer (Have)': [False, Utilities.trim_to(pokemon_request_message, 980)]}

        embed = Embeds.make_embed(header="Trade Profile (Offers)", header_icon=ctx.message.author.avatar_url, footer=footer,
                                  fields=additional_fields)

        return embed


    @staticmethod
    def trade_clear_embed(ctx, user_profile, pokemon_list, valid_pokemon_list, removed_poke_form_list):

        pokemon_offers_message = Utilities.trim_to(print_pokemon(user_profile['trade_offers']), 900)
        pokemon_request_message = Utilities.trim_to(print_pokemon(user_profile['trade_requests']), 900)

        footer = None
        if len(valid_pokemon_list) < len(pokemon_list):
            footer = "Tip: You can use Pokedex # instead of pokemon name. To see available options use !poke-form list <filter>"

        additional_fields = {'Accepted Input': [False, Utilities.trim_to(print_pokemon(valid_pokemon_list), 900)],
                             'Pokemon Removed': [False, Utilities.trim_to(print_pokemon(removed_poke_form_list), 900)],
                             'Offer (Have)': [False, pokemon_offers_message],
                             'Request (Wants)': [False, pokemon_request_message]}

        embed = Embeds.make_embed(header="Trade Profile", header_icon=ctx.message.author.avatar_url, footer=footer,
                                  fields=additional_fields)

        return embed