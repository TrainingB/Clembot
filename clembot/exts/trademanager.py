import re
import discord
import os
import time_util
from discord.ext import commands
from exts.utilities import Utilities
from exts.utilities import RemoveComma
from random import *
from exts.pokemonform import PokemonForm
# from exts.pokemon import Pokemon

import json


class TradeManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()
        self.pokemon_forms = []
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        self.pokemon_forms = data['pokemon_forms']

    @commands.group(pass_context=True, hidden=True, aliases=["poke-form","pokeform"])
    async def _poke_form(self, ctx):

        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    def print_pokemon(self, list_of_pokemon):
        escaped_list = ['"%s"' % e if re.search('[^A-Za-z0-9-]', e) else e for e in list_of_pokemon]
        return ", ".join(escaped_list)

    async def poke_form_listed(self, ctx, filter_text=None):
        additional_fields = {}

        filtered_results=""

        if filter_text:
            filtered_results = f" ( for : {filter_text} )"
            filter_list = [ form for form in self.pokemon_forms if filter_text and form.__contains__(filter_text)]
            if len(filter_list) < 1:
                filter_list.append("No pokemon forms found.")
        else:
            filter_list = self.pokemon_forms

        filter_form_list = ', '.join(filter_list)

        if len(filter_form_list) < 1000:
            additional_fields[f"Available Pokemon Forms{filtered_results}"] = f"**{', '.join(filter_list)}**"
            await self.utilities._send_embed(channel=ctx.channel, additional_fields=additional_fields)
        else:
            await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, list too long to display. You can provide a filter to reduce the list.")


    @_poke_form.command(aliases=["list"])
    async def _poke_form_list(self, ctx, filter_text=None):
        await self.poke_form_listed(ctx, filter_text)


    @_poke_form.command(aliases=["save"])
    async def _poke_form_save(self, ctx):
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        tmp = data['pokemon_forms']
        data['pokemon_forms'] = self.pokemon_forms

        with open(os.path.join('data', 'pokemon_forms.json'), 'w') as fd:
            json.dump(data, fd, indent=2, separators=(', ', ': '))

        await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, saved pokemon-forms successfully. See the complete list using **!poke-form list**.")

    @_poke_form.command(aliases=["load"])
    async def _poke_form_load(self, ctx):
        with open(os.path.join('data', 'pokemon_forms.json'), 'r') as fd:
            data = json.load(fd)

        self.pokemon_forms = data['pokemon_forms']
        await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, loaded pokemon-forms successfully. See the complete list using **!poke-form list**.")

    @_poke_form.command(aliases=["add"])
    async def _poke_form_add(self, ctx, *pokemon_form_list: RemoveComma):

        added_poke_form_list = []

        for pokemon_form in pokemon_form_list:
            if pokemon_form not in self.pokemon_forms:
                self.pokemon_forms.append(pokemon_form)
                added_poke_form_list.append(pokemon_form)

        if len(added_poke_form_list) > 0:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **{self.print_pokemon(added_poke_form_list)}** has been added successfully. See the complete list using **!poke-form list**.")
        else:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, No changes were made. See the complete list using **!poke-form list**.")

    @_poke_form.command(aliases=["remove"])
    async def _poke_form_remove(self, ctx, *pokemon_form_list: RemoveComma):

        removed_poke_form_list = []

        for pokemon_form in pokemon_form_list:
            if pokemon_form in self.pokemon_forms:
                self.pokemon_forms.remove(pokemon_form)
                removed_poke_form_list.append(pokemon_form)

        if len(removed_poke_form_list) > 0:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **{self.print_pokemon(removed_poke_form_list)}** has been removed successfully. See the complete list using **!poke-form list**.")
        else:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, No changes were made. See the complete list using **!poke-form list**.")

    @commands.group(pass_context=True, hidden=True, aliases=["trade","t"])
    async def _trade(self, ctx):

        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!trade** can be used with various options. See **!beep trade** for more details.")


    def extract_poke_form(self, ctx, list_of_pokemon):
        pokemon_list = [e.lower() for e in list_of_pokemon if e.lower() in ctx.bot.pkmn_info['pokemon_list'] or e.lower() in self.pokemon_forms]
        pokemon_list.extend([ctx.bot.pkmn_info['pokemon_list'][int(e)-1] for e in list_of_pokemon if e.isdigit()])
        return pokemon_list

    async def _trade_add_to_list(self, ctx, pokemon_list, list_name):
        user = ctx.message.author

        trainer_trade_pokemon = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {}).get(list_name,[])

        if len(pokemon_list) > 0:

            for pokemon_offered in pokemon_list:

                if pokemon_offered not in trainer_trade_pokemon:
                        trainer_trade_pokemon.append(pokemon_offered)

                ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {})[list_name] = trainer_trade_pokemon

        pokemon_request_message = self.print_pokemon(ctx.bot.guild_dict[ctx.guild.id]['trainers'][user.id].get(list_name,[]))

        return pokemon_request_message


    @_trade.command(aliases=["request","r"])
    async def _trade_request(self, ctx, *pokemon: RemoveComma):

        pokemon_list = self.extract_poke_form(ctx, pokemon)

        footer=None
        if len(pokemon_list) < len(pokemon):
            footer = "Tip: You can use Pokedex # instead of pokemon name. To see available options use !poke-form list <filter>"

        pokemon_request_message = await self._trade_add_to_list(ctx, pokemon_list, list_name='trade_requests')

        additional_fields= {}
        additional_fields['Accepted Input'] = self.utilities.trim_to(self.print_pokemon(pokemon_list), 900)
        additional_fields['Request (Wants)'] = self.utilities.trim_to(pokemon_request_message, 980)

        if len(pokemon_request_message) > 0:
            # await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** is looking for : **{pokemon_request_message}**")
            await self.utilities._send_embed(ctx.channel, title=f"**{ctx.message.author.display_name}** Here are your trade options:", additional_fields=additional_fields, footer=footer)
        else:
            await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** has no pokemon requests registered with me yet!")


    @_trade.command(aliases=["offer","have","o","h"])
    async def _trade_offer(self, ctx, *pokemon: RemoveComma):

        pokemon_list = self.extract_poke_form(ctx, pokemon)

        footer=None
        if len(pokemon_list) < len(pokemon):
            footer = "Tip: You can use Pokedex # instead of pokemon name. To see available options use !poke-form list <filter>"

        pokemon_request_message = await self._trade_add_to_list(ctx, pokemon_list, list_name='trade_offers')

        additional_fields= {}
        additional_fields['Accepted Input'] = self.utilities.trim_to(self.print_pokemon(pokemon_list), 900)
        additional_fields['Offer (Have)'] = self.utilities.trim_to(pokemon_request_message, 980)

        if len(pokemon_request_message) > 0:
            #await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** has following Pokemon for trade : **{pokemon_request_message}**")
            await self.utilities._send_embed(ctx.channel, title=f"**{ctx.message.author.display_name}** Here are your trade options:", additional_fields=additional_fields, footer=footer)
        else:
            await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** has no pokemon for trade registered with me yet!")

    @_trade.command(aliases=["clear","c"])
    async def _trade_clear(self, ctx, *pokemon: RemoveComma):

        user = ctx.message.author

        if 'all' in pokemon:
            ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {})['trade_offers']=[]
            ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {})['trade_requests'] = []
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, your request & offer list has been cleared!")
            return

        pokemon_list = self.extract_poke_form(ctx, pokemon)

        footer = None
        if len(pokemon_list) < len(pokemon):
            footer = "Tip: You can use Pokedex # instead of pokemon name. To see available options use !poke-form list <filter>"

        removed_poke_form_list = []
        if len(pokemon_list) > 0:

            trainer_trade_offers = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {}).get('trade_offers', [])
            trainer_trade_requests = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {}).get('trade_requests', [])

            for pokemon_offered in pokemon_list:

                if pokemon_offered in trainer_trade_offers:
                    trainer_trade_offers.remove(pokemon_offered)
                    removed_poke_form_list.append(pokemon_offered)

                if pokemon_offered in trainer_trade_requests:
                    trainer_trade_requests.remove(pokemon_offered)
                    if pokemon_offered not in removed_poke_form_list:
                        removed_poke_form_list.append(pokemon_offered)

        additional_fields= {}
        additional_fields['Accepted Input'] = self.utilities.trim_to(self.print_pokemon(pokemon_list), 900)
        additional_fields['Pokemon Removed'] = self.utilities.trim_to(self.print_pokemon(removed_poke_form_list), 900)

        await self.utilities._send_embed(ctx.channel, title=f"**{ctx.message.author.display_name}** Here are your trade options:", additional_fields=additional_fields, footer=footer)

    @_trade.command(aliases=["list"])
    async def _trade_list(self, ctx, *parameters: RemoveComma):

        if len(ctx.message.mentions) > 0:
            user = ctx.message.mentions[0]
            msg = f"for **{user.display_name}** "
        else:
            user = ctx.message.author
            msg = ""

        trainer_trade_offers = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {}).get('trade_offers', [])
        trainer_trade_requests = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {}).get('trade_requests', [])

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

        trainer_trade_requests_text = self.utilities.trim_to(self.print_pokemon(filtered_trainer_trade_requests), 990)
        trainer_trade_offers_text= self.utilities.trim_to(self.print_pokemon(filtered_trainer_trade_offers), 990)

        additional_fields = {}
        additional_fields['Requests (Wants)'] = trainer_trade_requests_text if len(trainer_trade_requests_text) > 0 else "No requests yet!"
        additional_fields['Offers (Have)'] = trainer_trade_offers_text if len(trainer_trade_offers_text) > 0 else "No requests yet!"

        await self.utilities._send_embed(ctx.channel, f"**{ctx.message.author.display_name}** The current trade options {msg}are:", additional_fields=additional_fields)



    @commands.command(pass_context=True, hidden=True, aliases=["x_x"])
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




        await self.utilities._send_embed(ctx.channel, additional_fields=additional_fields)




    @_trade.command(aliases=["search"])
    async def _trade_search(self, ctx, *pokemon: RemoveComma):

        searchable_list_key = 'trade_offers'
        search_result_list_key = 'trade_requests'
        offers_or_request = 'offers'
        offering_or_requesting = 'offering'
        offered_or_requested = 'requested'
        has_or_wants = 'has'
        if '-request' in pokemon :
            searchable_list_key = 'trade_requests'
            search_result_list_key = 'trade_offers'
            offers_or_request = 'requests'
            offering_or_requesting = 'requesting'
            offered_or_requested = 'to offer'
            has_or_wants = 'wants'

        try:
            pokemon_list = self.extract_poke_form(ctx, pokemon)
            if len(pokemon_list) == 0:
                pokemon_list = pokemon

            # self.extract_poke_form(ctx, pokemon)

            user = ctx.message.author

            trainers_with_pokemon = []

            # if len(pokemon_list) == 0:
            #     return await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** No valid pokemon found to search!")

            guild_trainer_dict = ctx.bot.guild_dict[ctx.guild.id]['trainers']


            trainer_list = []
            additional_fields = {}
            additional_trainer_id_list = []
            additional_trainer_list = []




            for trainer_id, trainer_dict in guild_trainer_dict.items():

                trainer_trade_offers = trainer_dict.get(searchable_list_key, [])

                for trainer_trade_pokeform in trainer_trade_offers:
                    trainer_trade_pokemonform = PokemonForm(trainer_trade_pokeform)

                    for pokemon_searched_for in pokemon_list:
                        pokeform_searched_for = PokemonForm(pokemon_searched_for)

                        if trainer_trade_pokeform.__contains__(pokemon_searched_for) or pokeform_searched_for == trainer_trade_pokemonform:

                            if not trainers_with_pokemon.__contains__(trainer_id) and not additional_trainer_id_list.__contains__(trainer_id):
                                try:
                                    if len(trainers_with_pokemon) > 10 :
                                        additional_trainer_id_list.append(trainer_id)
                                        additional_trainer_list.append(f"{ctx.guild.get_member(trainer_id).display_name}")

                                    else :

                                        trainers_with_pokemon.append(trainer_id)

                                        trainer_trade_requests = guild_trainer_dict.setdefault(trainer_id, {}).get(search_result_list_key, [])
                                        try:
                                            trainer_name = ctx.guild.get_member(trainer_id).display_name
                                        except:
                                            continue
                                        if len(trainer_trade_requests) > 10:
                                            additional_fields[f"{ctx.guild.get_member(trainer_id).display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f"{self.print_pokemon(trainer_trade_requests[:10])} and more."
                                        elif len(trainer_trade_requests) > 0:
                                            additional_fields[f"{ctx.guild.get_member(trainer_id).display_name} ({has_or_wants} {trainer_trade_pokeform})"] = self.print_pokemon(trainer_trade_requests)
                                        else:
                                            additional_fields[f"{ctx.guild.get_member(trainer_id).display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f'No {offers_or_request} yet!'
                                except Exception as error:
                                    continue


            trainer_search_result = "\n ".join(trainer_list)

            if additional_trainer_list:
                additional_fields[f"Other Trainers {offering_or_requesting} {pokemon_searched_for}"] = ", ".join(additional_trainer_list)

            if len(additional_fields) > 0:
                await self.utilities._send_embed(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** Following trainers are {offering_or_requesting} **{', '.join(pokemon_list)}** for trade and here is what they have {offered_or_requested}:", additional_fields=additional_fields)
            else:
                await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** No trainer is {offering_or_requesting} **{', '.join(pokemon_list)}** for trading yet!")
        except Exception as error:
            await self.utilities._send_error_message(ctx.channel, f"Beep Beep! Error occured while searching : {error}.")

    @_trade.command(aliases=["search request"])
    async def _trade_search_request(self, ctx, *pokemon: RemoveComma):

        try:
            pokemon_list = self.extract_poke_form(ctx, pokemon)
            if len(pokemon_list) == 0:
                pokemon_list = pokemon

            # self.extract_poke_form(ctx, pokemon)

            user = ctx.message.author

            trainers_with_pokemon = []

            # if len(pokemon_list) == 0:
            #     return await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** No valid pokemon found to search!")

            guild_trainer_dict = ctx.bot.guild_dict[ctx.guild.id]['trainers']


            trainer_list = []
            additional_fields = {}
            additional_trainer_id_list = []
            additional_trainer_list = []




            for trainer_id, trainer_dict in guild_trainer_dict.items():

                trainer_trade_requests = trainer_dict.get('trade_requests', [])

                for trainer_trade_pokeform in trainer_trade_requests:
                    trainer_trade_pokemonform = PokemonForm(trainer_trade_pokeform)

                    for pokemon_searched_for in pokemon_list:
                        pokeform_searched_for = PokemonForm(pokemon_searched_for)

                        if trainer_trade_pokeform.__contains__(pokemon_searched_for) or pokeform_searched_for == trainer_trade_pokemonform:

                            if not trainers_with_pokemon.__contains__(trainer_id) and not additional_trainer_id_list.__contains__(trainer_id):

                                if len(trainers_with_pokemon) > 10 :
                                    additional_trainer_id_list.append(trainer_id)
                                    additional_trainer_list.append(f"{ctx.guild.get_member(trainer_id).display_name}")

                                else :

                                    trainers_with_pokemon.append(trainer_id)

                                    trainer_trade_requests = guild_trainer_dict.setdefault(trainer_id, {}).get('trade_offers', [])
                                    try:
                                        trainer_name = ctx.guild.get_member(trainer_id).display_name
                                    except:
                                        continue
                                    if len(trainer_trade_requests) > 10:
                                        additional_fields[f"{ctx.guild.get_member(trainer_id).display_name} (has {trainer_trade_pokeform})"] = f"{self.print_pokemon(trainer_trade_requests[:10])} and more."
                                    elif len(trainer_trade_requests) > 0:
                                        additional_fields[f"{ctx.guild.get_member(trainer_id).display_name} (has {trainer_trade_pokeform})"] = self.print_pokemon(trainer_trade_requests)
                                    else:
                                        additional_fields[f"{ctx.guild.get_member(trainer_id).display_name} (has {trainer_trade_pokeform})"] = 'No Requests yet!'



            trainer_search_result = "\n ".join(trainer_list)

            if additional_trainer_list:
                additional_fields[f"Other Trainers with {pokemon_searched_for}"] = ", ".join(additional_trainer_list)

            if len(additional_fields) > 0:
                await self.utilities._send_embed(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** Following trainers are offering **{', '.join(pokemon_list)}** for trade and here is what they are looking for:", additional_fields=additional_fields)
            else:
                await self.utilities._send_error_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}** No trainer is offering **{', '.join(pokemon_list)}** for trading yet!")
        except Exception as error:
            await self.utilities._send_error_message(ctx.channel, f"Beep Beep! Error occured while searching : {error}.")



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

    def get_beep_embed(self, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - Trade Management", description=self.beep_notes.format(member=ctx.message.author.display_name), footer=footer))

    # @commands.command(aliases=["debug"])
    # async def _debug(self, ctx, *pokemon_list):
    #     for pokemon in pokemon_list:
    #         try:
    #             # pokemon_test = await Pokemon.convert_pokemon(ctx, 'unown-y')
    #             # await self.utilities._send_message(ctx.channel, pokemon_test.pokemon_info())
    #             # pokemon_test = await Pokemon.convert_pokemon(ctx, 'unown y')
    #             # await self.utilities._send_message(ctx.channel, pokemon_test.pokemon_info())
    #             pokemon_info = await Pokemon.convert_pokemon(ctx, pokemon)
    #
    #             response_text = json.dumps(pokemon_info, indent=4)
    #             await self.utilities._send_message(ctx.channel, f"`{response_text}`")
    #
    #             if pokemon_info['match']:
    #                 await self.utilities.get_image_embed(ctx.channel, pokemon_info['img_url'])
    #
    #
    #
    #         except Exception as error:
    #             pass
    #             print(error)


def setup(bot):
    bot.add_cog(TradeManager(bot))


