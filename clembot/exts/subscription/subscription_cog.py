import discord
from discord.ext import commands
from discord.ext.commands import RoleConverter, BadArgument

from clembot.core.bot import group
from clembot.core.errors import wrap_error
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.utilities.utils.embeds import Embeds


class SubscriptionCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @group(pass_context=True, category='Bot Info', aliases=["want"])
    @wrap_error
    async def cmd_want(self, ctx, *pokemon_list):
        """Add a Pokemon to your wanted list.

        Usage: !want pokemon"""

        if len(pokemon_list) == 0:
            allowed_want_list = []
            for role in ctx.guild.roles:
                if Pokemon.to_pokemon(role.name) is not None:
                    allowed_want_list.append(role.name)

            allowed_want_list = sorted(allowed_want_list)

            additional_fields = {
                'Usage' : f'**!want pokemon**',
                'Available Roles' : [False, f'**{", ".join(allowed_want_list)}**']
            }

            embed = Embeds.make_embed(header="Subscribe for pokemon notifications", fields=additional_fields)
            return await ctx.send(embed=embed)

        for pokemon in pokemon_list:
            pkmn = Pokemon.to_pokemon(pokemon)

            if pkmn is None:
                raise BadArgument(f"`{ctx.prefix}want` can be used for pokemon only.")

            role = discord.utils.get(ctx.guild.roles, name=pokemon)
            if role is None:
                return await Embeds.message(ctx.channel, f"That's great. Only a few pokemon can be selected for notifications.\nThe list is available using `{ctx.prefix}want`. Please contact an admin if you would like **{pokemon}** to be included.")

            await ctx.message.author.add_roles(role)
            await ctx.send(embed=Embeds.make_embed(content=f"Got it! {ctx.message.author.display_name} wants {pokemon.capitalize()}.", thumbnail=pkmn.preview_url))

        pass

    @group(pass_context=True, category='Bot Info', aliases=["unwant"])
    @wrap_error
    async def cmd_unwant(self, ctx, *pokemon_list):
        """Remove a Pokemon from your wanted list.

        Usage: !unwant pokemon"""


        if 'all' in pokemon_list:
            for role in ctx.message.author.roles:
                pkmn = Pokemon.to_pokemon(role.name)
                if pkmn is not None:
                    await ctx.message.author.remove_roles(role)

            return await ctx.message.add_reaction('✅')

        for pokemon in pokemon_list:
            pkmn = Pokemon.to_pokemon(pokemon)

            if pkmn is None:
                raise BadArgument(f"`{ctx.prefix}unwant` can be used for pokemon only.")

            role = discord.utils.get(ctx.guild.roles, name=pokemon)
            if role is None:
                return await Embeds.message(ctx.channel, f"That's great. Only a few pokemon can be selected for notifications.\nThe list is available using `{ctx.prefix}want`. Please contact an admin if you would like **{pokemon}** to be included.")

            await ctx.message.author.remove_roles(role)
            await ctx.message.add_reaction('✅')

