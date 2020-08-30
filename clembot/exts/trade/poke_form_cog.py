from discord.ext import commands

from clembot.core.bot import group
from clembot.exts.trade.pokemonform import PokemonForm
from clembot.exts.trade.trademanager import print_pokemon, print_pokemon_list
from clembot.utilities.utils.converters import RemoveComma
from clembot.utilities.utils.embeds import Embeds


class PokemonFormCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi

    @staticmethod
    async def list_pokemon_forms(ctx, filter_text=None):
        additional_fields = {}

        filtered_results = ""

        if filter_text:
            filtered_results = f" ( for : {filter_text} )"
            filter_list = [form for form in PokemonForm.available_pokemon_forms if
                           filter_text and form.__contains__(filter_text)]
            if len(filter_list) < 1:
                filter_list.append("No pokemon forms found.")
        else:
            filter_list = PokemonForm.available_pokemon_forms

        filter_form_list = ', '.join(filter_list)

        if len(filter_form_list) < 1000:
            additional_fields[f"Available Pokemon Forms{filtered_results}"] = f"**{', '.join(filter_list)}**"
            await ctx.send(embed=Embeds.make_embed(fields=additional_fields))
        else:
            await Embeds.error(ctx.channel, f"list too long to display. You can provide a filter to reduce the list.",
                               ctx.message.author)


    @group(pass_context=True, hidden=True, aliases=["poke-form", "pokeform"])
    async def cmd_poke_form(self, ctx):
        if not PokemonForm.available_pokemon_forms:
            await PokemonForm.load_forms(self.bot)
        if ctx.invoked_subcommand is None:
            await Embeds.message(ctx.channel,
                                 f"Beep Beep! **{ctx.message.author.display_name}**, **!{ctx.invoked_with}** can be used with various options.")

    @cmd_poke_form.command(aliases=["list"])
    async def _poke_form_list(self, ctx, filter_text=None):
        await PokemonFormCog.list_pokemon_forms(ctx, filter_text)

    @cmd_poke_form.command(aliases=["load"])
    async def _poke_form_load(self, ctx):

        PokemonForm.available_pokemon_forms = await PokemonForm.load_forms(ctx.bot)

        await Embeds.message(ctx.channel,
                             f"loaded pokemon-forms successfully. See the complete list using **!poke-form list**.",
                             user=ctx.message.author)
        print(PokemonForm.available_pokemon_forms)

    @cmd_poke_form.command(aliases=["add"])
    async def cmd_poke_form_add(self, ctx, *pokemon_form_list: RemoveComma):
        added_poke_form_list = []

        for pokemon_form in pokemon_form_list:
            if pokemon_form not in PokemonForm.available_pokemon_forms:
                await PokemonForm.add(ctx.bot.dbi, pokemon_form)
                added_poke_form_list.append(pokemon_form)

        if len(added_poke_form_list) > 0:
            await Embeds.message(ctx.channel,
                                 f"**{print_pokemon_list(added_poke_form_list)}** has been added successfully. See the complete list using **!poke-form list**.",
                                 user=ctx.message.author)
        else:
            await Embeds.message(ctx.channel, f"No changes were made. See the complete list using **!poke-form list**.",
                                 user=ctx.message.author)

    @cmd_poke_form.command(aliases=["remove"])
    async def cmd_poke_form_remove(self, ctx, *pokemon_form_list: RemoveComma):

        removed_poke_form_list = []

        for pokemon_form in pokemon_form_list:
            if pokemon_form in PokemonForm.available_pokemon_forms:
                await PokemonForm.remove(ctx.bot.dbi, pokemon_form)
                removed_poke_form_list.append(pokemon_form)

        if len(removed_poke_form_list) > 0:
            await Embeds.message(ctx.channel,
                                 f"**{print_pokemon_list(removed_poke_form_list)}** has been removed successfully. See the complete list using **!poke-form list**.",
                                 user=ctx.message.author)
        else:
            await Embeds.message(ctx.channel, f"No changes were made. See the complete list using **!poke-form list**.",
                                 user=ctx.message.author)

    # @cmd_poke_form.command(aliases=["dump"])
    # async def _poke_form_dump(self, ctx):
    #
    #     list_of_forms = []
    #
    #     for guild_id in self.bot.guild_dict.keys():
    #         single_guild_dict = self.bot.guild_dict[guild_id]
    #         for trainerid in single_guild_dict.get('trainers', {}).keys():
    #             trainer_request = single_guild_dict.get('trainers').get(trainerid).get('trade_requests')
    #             if trainer_request:
    #                 list_of_forms.extend(trainer_request)
    #             trainer_offers = single_guild_dict.get('trainers').get(trainerid).get('trade_offers')
    #             if trainer_offers:
    #                 list_of_forms.extend(trainer_offers)
    #
    #     unique_poke_forms = set(list_of_forms)
    #
    #     for pokemon_form in unique_poke_forms:
    #         if pokemon_form not in PokemonForm.available_pokemon_forms:
    #             await self.save_poke_form(pokemon_form)
    #
    #     await Utilities._send_message(ctx.channel,
    #                                   f"Beep Beep! **{ctx.message.author.display_name}**, loaded {len(unique_poke_forms)} pokemon-forms successfully. See the complete list using **!poke-form list**.")
