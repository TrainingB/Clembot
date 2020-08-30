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

    #
    # async def assign_role_to_user(self, role_name, user_id):
    #
    #
    #
    #
    #
    #     await ctx.message.author.add_roles(role)
    #
    #
    #     pass
    #


    @group(pass_context=True, hidden=True, aliases=["want"])
    # @channel_checks.raid_report_enabled()
    @wrap_error
    async def cmd_want(self, ctx, *pokemon_list):


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
#
#     @group(pass_context=True, hidden=True, aliases=["subscribe"])
#     # @channel_checks.raid_report_enabled()
#     async def cmd_subscribe(self):
#         """Allows user to sign-up for a role, if the guild allows subscription for it.
#         """
#
#
#
#
#
#         pass
#
#
#
#
#
#
# @Clembot.command(pass_context=True, hidden=True)
# @checks.wantset()
# @checks.nonraidchannel()
# @checks.wantchannel()
# async def want(ctx):
#     """Add a Pokemon to your wanted list.
#
#     Usage: !want <species>
#     Clembot will mention you if anyone reports seeing
#     this species in their !wild or !raid command."""
#
#     """Behind the scenes, Clembot tracks user !wants by
#     creating a guild role for the Pokemon species, and
#     assigning it to the user."""
#     message = ctx.message
#     guild = message.guild
#     channel = message.channel
#     want_split = message.clean_content.lower().split()
#     del want_split[0]
#
#     if len(want_split) < 1:
#         help_embed = get_help_embed("Subscribe for Pokemon notifications.", "!want pokemon", "Available Roles: ", _want_roles(ctx.message.guild), "message")
#         await ctx.channel.send(embed=help_embed)
#         return
#
#
#     entered_want = " ".join(want_split)
#     old_entered_want = entered_want
#     if entered_want not in pkmn_info['pokemon_list']:
#         entered_want = await autocorrect(entered_want, message.channel, message.author)
#
#     if entered_want == None:
#         return
#
#
#     role = discord.utils.get(guild.roles, name=entered_want)
#     # Create role if it doesn't exist yet
#     if role is None:
#         if entered_want not in get_raidlist():
#             if entered_want not in pkmn_info['pokemon_list']:
#                 await _send_error_message(channel, _("Beep Beep! **{member}** {entered_want} is not a pokemon. Please use a valid pokemon name.").format(member=ctx.message.author.mention, entered_want=edisplay_name))
#             else:
#                 await _send_error_message(channel, _("Beep Beep! **{member}** only specific pokemon are allowed to be notified!\nYou can type **!want** to see available pokemon for subscription. Please contact an admin if you want **{entered_want}** to be included.").format(member=ctx.message.author.display_name, entered_want=entered_want))
#             return
#         role = await guild.create_role(name=entered_want, hoist=False, mentionable=True)
#         await asyncio.sleep(0.5)
#
#     # If user is already wanting the Pokemon,
#     # print a less noisy message
#     if role in ctx.message.author.roles:
#         await channel.send("Beep Beep! **{member}**, I already know you want **{pokemon}**!".format(member=ctx.message.author.display_name, pokemon=entered_want.capitalize()))
#     else:
#         await ctx.message.author.add_roles(role)
#         want_number = pkmn_info['pokemon_list'].index(entered_want) + 1
#         want_img_url = "https://raw.githubusercontent.com/TrainingB/Clembot/master/images/pkmn/{0}_.png".format(str(want_number).zfill(3))  # This part embeds the sprite
#         want_img_url = get_pokemon_image_url(want_number)  # This part embeds the sprite
#         want_embed = discord.Embed(colour=guild.me.colour)
#         want_embed.set_thumbnail(url=want_img_url)
#         await channel.send(_("Beep Beep! Got it! {member} wants {pokemon}").format(member=ctx.message.author.mention, pokemon=entered_want.capitalize()), embed=want_embed)
#
#
#
#
# @Clembot.group(pass_context=True, hidden=True)
# @checks.wantset()
# @checks.nonraidchannel()
# @checks.wantchannel()
# async def unwant(ctx):
#     """Remove a Pokemon from your wanted list.
#
#     Usage: !unwant <species>
#     You will no longer be notified of reports about this Pokemon."""
#
#     """Behind the scenes, Clembot removes the user from
#     the guild role for the Pokemon species."""
#     message = ctx.message
#     guild = message.guild
#     channel = message.channel
#     if ctx.invoked_subcommand is None:
#         unwant_split = message.clean_content.lower().split()
#         del unwant_split[0]
#         entered_unwant = " ".join(unwant_split)
#         role = discord.utils.get(guild.roles, name=entered_unwant)
#         if role is None:
#             await channel.send(_("Beep Beep! {member} unwant works on only specific pokemon! Please contact an admin if you want {entered_want} to be included.").format(member=ctx.message.author.mention, entered_want=entered_unwant))
#             return
#
#         if entered_unwant not in pkmn_info['pokemon_list']:
#             await channel.send(spellcheck(entered_unwant))
#             return
#         else:
#             # If user is not already wanting the Pokemon,
#             # print a less noisy message
#             if role not in ctx.message.author.roles:
#                 await message.add_reaction('✅')
#             else:
#                 await message.author.remove_roles(role)
#                 unwant_number = pkmn_info['pokemon_list'].index(entered_unwant) + 1
#                 await message.add_reaction('✅')
#
#
#
# @unwant.command(pass_context=True, hidden=True)
# @checks.wantset()
# @checks.nonraidchannel()
# @checks.wantchannel()
# async def all(ctx):
#     """Remove all Pokemon from your wanted list.
#
#     Usage: !unwant all
#     All Pokemon roles are removed."""
#
#     """Behind the scenes, Clembot removes the user from
#     the guild role for the Pokemon species."""
#     message = ctx.message
#     guild = message.guild
#     channel = message.channel
#     author = message.author
#     await channel.trigger_typing()
#     count = 0
#     roles = author.roles
#     remove_roles = []
#     for role in roles:
#         if role.name in pkmn_info['pokemon_list']:
#             remove_roles.append(role)
#             await message.author.remove_roles(role)
#             count += 1
#         continue
#
#     await author.remove_roles(*remove_roles)
#
#     if count == 0:
#         await channel.send( content=_("{0}, you have no pokemon in your want list.").format(author.mention, count))
#         return
#     await channel.send( content=_("{0}, I've removed {1} pokemon from your want list.").format(author.mention, count))
#     return
