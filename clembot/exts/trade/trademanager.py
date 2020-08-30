import re
import traceback

import discord
from discord.ext import commands

from clembot.core import checks
from clembot.core.bot import group, command
from clembot.core.logs import Logger
from clembot.exts.profile.user_profile import UserProfile
from clembot.exts.trade.pokemonform import PokemonForm
from clembot.utilities.utils.converters import RemoveComma
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


def print_pokemon_list(list_of_pokemon):
    escaped_list = ['"%s"' % e if re.search('[^A-Za-z0-9-]', e) else e for e in list_of_pokemon]
    return ", ".join(escaped_list)


def print_pokemon(pokemon):
    return '"%s"' % pokemon if re.search('[^A-Za-z0-9-]', pokemon) else pokemon


def limited_embed_fields(list_of_items, header) -> dict:

    fields = {}
    list_len = 0
    my_list = []
    splits = 0
    new_header = f'{header} continued...'
    for item in list_of_items:
        if list_len + len(item) > 800 :
            fields[header] = [False, Utilities.trim_to(print_pokemon_list(my_list), 995)]
            list_len = 0
            my_list = []
            splits+=1
            header = f'{new_header} part-{splits}'

        list_len += len(item)
        my_list.append(item)

    if splits > 0:
        fields[f'{new_header} part-{splits}'] = [False, Utilities.trim_to(print_pokemon_list(my_list), 995)]
    else:
        fields[header] = [False, Utilities.trim_to(print_pokemon_list(my_list), 995)]

    return fields


def get_trade_preference_groups(trade_list):
    """
        returns 5 lists, first shiny, second legacy, third unown, fourth remaining and last one list with all of them in this order
    """
    shiny_offers, legacy_offers, unown_offers, remaining_offers, sorted_offers = [], [], [], [], []
    for trade_item in trade_list:

        if '-shiny' in trade_item:
            shiny_offers.append(trade_item.replace('-shiny',''))
        elif '-legacy' in trade_item:
            legacy_offers.append(trade_item.replace('-legacy', ''))
        elif 'unown-' in trade_item:
            unown_offers.append(trade_item.replace('unown-','').upper())
        else:
            remaining_offers.append(trade_item)


    if len(shiny_offers) > 0 and len(sorted_offers) < 20:
        sorted_offers.append('**Shiny:**')
        sorted_offers.extend([print_pokemon(item) for item in shiny_offers])

    if len(legacy_offers) > 0 and len(sorted_offers) < 20:
        sorted_offers.append('\n**Legacy:** ')
        sorted_offers.extend([print_pokemon(item) for item in legacy_offers])

    if len(unown_offers) > 0 and len(sorted_offers) < 20:
        sorted_offers.append('\n**Unown:** ')
        sorted_offers.extend([print_pokemon(item) for item in unown_offers])

    if len(remaining_offers) > 0 and len(sorted_offers) < 20:
        sorted_offers.append('\n**Others:** ')
        sorted_offers.extend([print_pokemon(item) for item in remaining_offers])

    return shiny_offers, legacy_offers, unown_offers, remaining_offers, sorted_offers


class TradeManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi

    @group(pass_context=True, hidden=True, aliases=["trade","t"])
    async def cmd_trade(self, ctx):
        """
        **Note:** All trades are grouped into **shiny, legacy, unown & others** in that order. If you want the whole unaltered list, use **!trade raw-list** instead.

        **!trade list** - lists all trades requests/offers
        **!trade list @user** - lists all trades requests/offers for @user
        **!trade list filter @user** - lists all trades requests/offers for @user and filters for matching *filter*
        """
        if not PokemonForm.available_pokemon_forms:
            await PokemonForm.load_forms(ctx.bot)

        if ctx.invoked_subcommand is None:
            await Embeds.message(ctx.channel, f"**!trade** can be used with various options. See **!beep trade** for more details.", ctx.message.author)


    @cmd_trade.command(aliases=["raw-list"])
    async def cmd_trade_raw_list(self, ctx, *parameters: RemoveComma):
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

        additional_fields = {}
        additional_fields.update(limited_embed_fields(filtered_trainer_trade_requests, 'Requests (Wants)') if len(filtered_trainer_trade_requests) > 0 else {'Requests (Wants)' : "No requests found!"})
        additional_fields.update(limited_embed_fields(filtered_trainer_trade_offers, 'Offers (Have)')if len(filtered_trainer_trade_offers) > 0 else {'Offers (Have)' : "No offers found!"})

        await ctx.send(embed=Embeds.make_embed(header=f"Trade Profile - {user.display_name}", header_icon=user.avatar_url, fields=additional_fields))


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

        shiny_offers, legacy_offers, unown_offers, remaining_offers, sorted_offers = get_trade_preference_groups(filtered_trainer_trade_offers)
        shiny_requests, legacy_requests, unown_requests, remaining_requests, sorted_requests = get_trade_preference_groups(filtered_trainer_trade_requests)

        additional_fields = {}
        additional_fields.update({f'Offers': [True, '-------------------------------------------------']})
        additional_fields.update(limited_embed_fields(shiny_offers, f'Shiny :sparkles: ({len(shiny_offers)}) - Offers') if len(shiny_offers) > 0 else {'':''})
        additional_fields.update(limited_embed_fields(legacy_offers, f'Legacy ({len(legacy_offers)}) - Offers') if len(legacy_offers) > 0 else {'': ''})
        additional_fields.update(limited_embed_fields(unown_offers, f'Unown ({len(unown_offers)}) - Offers') if len(unown_offers) > 0 else {'': ''})
        additional_fields.update(limited_embed_fields(remaining_offers, f'Other ({len(remaining_offers)}) - Offers') if len(remaining_offers) > 0 else {'': ''})
        additional_fields.update({f'Offers': [True, '-------------------------------------------------']})
        additional_fields.update(limited_embed_fields(shiny_requests, f'Shiny :sparkles: ({len(shiny_requests)}) - Requests') if len(shiny_requests) > 0 else {'': ''})
        additional_fields.update(limited_embed_fields(legacy_requests, f'Legacy ({len(legacy_requests)}) - Requests') if len(legacy_requests) > 0 else {'': ''})
        additional_fields.update(limited_embed_fields(unown_requests, f'Unown ({len(unown_requests)}) - Requests') if len(unown_requests) > 0 else {'': ''})
        additional_fields.update(limited_embed_fields(remaining_requests, f'Other ({len(remaining_requests)}) - Requests') if len(remaining_requests) > 0 else {'': ''})

        await ctx.send(embed=Embeds.make_embed(header=f"Trade Profile - {user.display_name}", header_icon=user.avatar_url, fields=additional_fields))


    @cmd_trade.command(aliases=["request","r"])
    async def cmd_trade_request(self, ctx, *pokemon_list: RemoveComma):
        try:
            valid_pokemon_list, invalid_pokemon_list = PokemonForm.split_pokemon_forms(pokemon_list)

            user_profile = await UserProfile.find(ctx.bot, ctx.message.author.id)


            if len(valid_pokemon_list) > 0:
                user_profile['trade_requests'] = list(set([pkmn for pkmn in valid_pokemon_list] + user_profile['trade_requests']))
                await user_profile.update()
                await ctx.send(embed=TradeProfileEmbed.trade_request_embed(ctx, user_profile, valid_pokemon_list, invalid_pokemon_list))
            else:
                await Embeds.error(ctx.channel, f"No changes have been made.", ctx.message.author)

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


    @cmd_trade.command(aliases=["offer","have","o","h"])
    async def cmd_trade_offer(self, ctx, *pokemon_list: RemoveComma):
        try:
            valid_pokemon_list, invalid_pokemon_list = PokemonForm.split_pokemon_forms(pokemon_list)

            user_profile = await UserProfile.find(ctx.bot, ctx.message.author.id)


            if len(valid_pokemon_list) > 0:
                user_profile['trade_offers'] = list(set([pkmn for pkmn in valid_pokemon_list] + user_profile['trade_offers']))
                await user_profile.update()
                await ctx.send(embed=TradeProfileEmbed.trade_offer_embed(ctx, user_profile, valid_pokemon_list, invalid_pokemon_list))
            else:
                await Embeds.error(ctx.channel, f"No changes have been made.", ctx.message.author)

        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")


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


            valid_pokemon_list, invalid_pokemon_list = PokemonForm.split_pokemon_forms(pokemon_list)
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

                await ctx.send(embed=TradeProfileEmbed.trade_clear_embed(ctx, user_profile, valid_pokemon_list, invalid_pokemon_list))
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

                        shiny_offers, legacy_offers, unown_offers, remaining_offers, sorted_offers = get_trade_preference_groups(trainer_trade_requests)

                        if len(sorted_offers) > 20:
                            additional_fields[f"{trainer.display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f"{' '.join(sorted_offers)}."
                        elif len(sorted_offers) > 0:
                            additional_fields[f"{trainer.display_name} ({has_or_wants} {trainer_trade_pokeform})"] = f"{' '.join(sorted_offers)}."
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






        # url = 'https://api.thesilphroad.com/v0/research/tasks'
        # headers = {'Authorization': f'Silph {silph_info.api_key}'}
        # while True:
        #     async with aiohttp.ClientSession() as sess:
        #         async with sess.get(url, headers=headers) as resp:
        #             try:
        #                 data = await resp.json()
        #             except:
        #                 return await ctx.send('Failed')
        #             table = ctx.bot.dbi.table('research_tasks')
        #             insert = table.insert
        #             query = table.query
        #             data = data['data']
        #             rows, verified = self.parse_tasks_from_silph(data)
        #             if verified:
        #                 await query.delete()
        #             insert.rows(rows)
        #             await insert.commit(do_update=True)
        #             if not verified:
        #                 await asyncio.sleep(300)
        #                 continue
        #             break
        # await ctx.success('New tasks verified')



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
    def trade_request_embed(ctx, user_profile, valid_pokemon_list, invalid_pokemon_list):

        valid_pokemon_text = Utilities.trim_to(print_pokemon_list(valid_pokemon_list), 900)
        invalid_pokemon_text = Utilities.trim_to(print_pokemon_list(invalid_pokemon_list), 900)

        additional_fields = {'Added to requests': [len(valid_pokemon_text) < 40, valid_pokemon_text],
                             'Not accepted': [len(invalid_pokemon_text) < 40, invalid_pokemon_text],
                             'Total requests': [True, str(len(user_profile['trade_requests']))]}


        embed = Embeds.make_embed(header="Trade Profile (Requests)", header_icon=ctx.message.author.avatar_url,
                                  fields=additional_fields)

        return embed

    @staticmethod
    def trade_offer_embed(ctx, user_profile, valid_pokemon_list, invalid_pokemon_list):

        valid_pokemon_text = Utilities.trim_to(print_pokemon_list(valid_pokemon_list), 900)
        invalid_pokemon_text = Utilities.trim_to(print_pokemon_list(invalid_pokemon_list), 900)

        additional_fields = {'Added to offers': [len(valid_pokemon_text) < 40, valid_pokemon_text],
                             'Not accepted': [len(invalid_pokemon_text) < 40, invalid_pokemon_text],
                             'Total offers': [True, str(len(user_profile['trade_offers']))]}

        embed = Embeds.make_embed(header="Trade Profile (Offers)", header_icon=ctx.message.author.avatar_url,
                                  fields=additional_fields)

        return embed


    @staticmethod
    def trade_clear_embed(ctx, user_profile, valid_pokemon_list, invalid_pokemon_list):

        valid_pokemon_text = Utilities.trim_to(print_pokemon_list(valid_pokemon_list), 900)
        invalid_pokemon_text = Utilities.trim_to(print_pokemon_list(invalid_pokemon_list), 900)

        additional_fields = {'Pokemon Removed': [len(valid_pokemon_text) < 40, valid_pokemon_text],
                             'Not accepted': [len(invalid_pokemon_text) < 40, invalid_pokemon_text],
                             'Total offers': [True, str(len(user_profile['trade_offers']))],
                             'Total requests': [True, str(len(user_profile['trade_requests']))]}

        embed = Embeds.make_embed(header="Trade Profile", header_icon=ctx.message.author.avatar_url,
                                  fields=additional_fields)

        return embed

