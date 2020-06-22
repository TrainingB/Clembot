from random import randint

import discord
from discord.ext.commands import command

from clembot.core.logs import Logger
from clembot.core.utils import sanitize_channel_name

guild_dict = {}

@command(pass_context=True)
# @commands.has_permissions(manage_guild=True)
async def contest(ctx):
    await _contest(ctx.message)
    return

async def _contest(message):
    try:
        raid_split = message.clean_content.lower().split()
        del raid_split[0]

        option = "ALL"
        if len(raid_split) > 1:
            option = raid_split[1].upper()
            if option not in ["ALL", "TEST", "GEN1", "GEN2", "GEN3", "GEN12"]:
                await message.channel.send( "Beep Beep! valid options are : ALL,TEST,GEN1,GEN2,GEN3,GEN12")
                return

        everyone_perms = discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=True)
        my_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_roles=True, manage_messages=True, embed_links=True, attach_files=True, add_reactions=True, mention_everyone=True)

        channel_name = sanitize_channel_name(raid_split[0])

        if channel_name == "here":
            contest_channel = message.channel
        else:
            raid_channel_category = get_category(message.channel, None)
            raid_channel = await message.guild.create_text_channel(channel_name, overwrites=dict(message.channel.overwrites), category=raid_channel_category)

        await contest_channel.edit(target=message.guild.default_role, overwrite=everyone_perms)
        await contest_channel.edit(target=message.guild.me, overwrite=my_perms)

        pokemon = generate_pokemon(option)

        await message.channel.send( content=_("Beep Beep! A contest is about to take place in {channel}!".format(channel=contest_channel.mention)))

        raid_embed = discord.Embed(title=_("Beep Beep! A contest is about to take place in this channel!"), colour=discord.Colour.gold(), description="The first member to correctly guess (and spell) the randomly selected pokemon name will win!")
        raid_embed.add_field(name="**Option:**", value=_("{option}").format(option=option))
        raid_embed.add_field(name="**Rules:**", value=_("{rules}").format(rules="One pokemon per attempt per line!"))
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=message.author.avatar_url)
        raid_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/396098777729204226/396103528554168320/imageedit_15_4199265561.png")
        await contest_channel.send(embed=raid_embed)

        embed = discord.Embed(colour=discord.Colour.gold(), description="Beep Beep! A contest channel has been created!").set_author(name=_("Clembot Contest Notification - {0}").format(message.guild), icon_url=Clembot.user.avatar_url)
        embed.add_field(name="**Channel:**", value=_(" {member}").format(member=contest_channel.name), inline=True)
        embed.add_field(name="**Option**", value=_(" {member}").format(member=option), inline=True)
        embed.add_field(name="**Pokemon**", value=_(" {member}").format(member=pokemon), inline=True)
        embed.add_field(name="**Server:**", value=_("{member}").format(member=message.guild.name), inline=True)
        embed.add_field(name="**Reported By:**", value=_("{member}").format(member=message.author.display_name), inline=True)
        await Clembot.owner.send(embed=embed)
        if message.author.id != bot.owner.id:
            await message.author.send(embed=embed)

        await contest_channel.send( "Beep Beep! {reporter} can start the contest anytime using `!ready` command".format(reporter=message.author.mention))

        add_contest_to_guild_dict(message.guild.id)
        contest_channel_dict = {contest_channel.id: {'pokemon': pokemon, 'started': False, 'reported_by': message.author.id, 'option': option}}

        guild_dict[message.guild.id]['contest_channel'].update(contest_channel_dict)

    except Exception as error:
        Logger.info(error)

    return

def add_contest_to_guild_dict(guildid):
    if 'contest_channel' in guild_dict[guildid]:
        return

    guild_contest = {'contest_channel': {}}
    guild_dict[guildid].update(guild_contest)
    return


def generate_pokemon(option=None):
    if option is None:
        pokedex = randint(1, 383)
    else:
        option = option.upper()
        if option == 'TEST':
            pokedex = randint(1, 100)
        elif option == 'GEN1':
            pokedex = randint(1, 151)
        elif option == 'GEN2':
            pokedex = randint(152, 251)
        elif option == 'GEN3':
            pokedex = randint(252, 383)
        elif option == 'GEN12':
            pokedex = randint(1, 251)
        else:
            pokedex = randint(1, 383)

    pokemon = get_name(pokedex)
    return pokemon

@Clembot.command(pass_context=True)
async def renew(ctx):
    message = ctx.message
    if 'contest_channel' in guild_dict[message.guild.id]:
        if guild_dict[message.guild.id]['contest_channel'][message.channel.id].get('started', True) == False:
            if ctx.message.author.id == guild_dict[message.guild.id]['contest_channel'][message.channel.id].get('reported_by', 0):

                option = guild_dict[message.guild.id]['contest_channel'][message.channel.id].get('option', "ALL")

                pokemon = generate_pokemon(option)
                contest_channel_dict = {message.channel.id: {'pokemon': pokemon, 'started': False, 'reported_by': message.author.id, 'option': option}}
                guild_dict[message.guild.id]['contest_channel'].update(contest_channel_dict)

                embed = discord.Embed(colour=discord.Colour.gold(), description="Beep Beep! A contest channel has been created!").set_author(name=_("Clembot Contest Notification - {0}").format(message.guild), icon_url=Clembot.user.avatar_url)
                embed.add_field(name="**Channel:**", value=_(" {member}").format(member=message.channel.name), inline=True)
                embed.add_field(name="**Option**", value=_(" {member}").format(member=option), inline=True)
                embed.add_field(name="**Pokemon**", value=_(" {member}").format(member=pokemon), inline=True)
                embed.add_field(name="**Server:**", value=_("{member}").format(member=message.guild.name), inline=True)
                embed.add_field(name="**Reported By:**", value=_("{member}").format(member=message.author.display_name), inline=True)

                await ctx.message.delete()
                await bot.owner.send( embed=embed)
                if message.author.id != bot.owner.id:
                    await message.author.send( embed=embed)


@Clembot.command(pass_context=True)
async def ready(ctx):
    message = ctx.message
    if 'contest_channel' in guild_dict[message.guild.id]:
        if guild_dict[message.guild.id]['contest_channel'][message.channel.id].get('started', True) == False:
            if ctx.message.author.id == guild_dict[message.guild.id]['contest_channel'][message.channel.id].get('reported_by', 0):

                role = message.guild.default_role
                args = ctx.message.clean_content.lower().split()
                del args[0]
                if len(args) > 0:
                    role_name = args[0]
                    role = discord.utils.get(ctx.message.guild.roles, name=role_name)
                    if role is None:
                        role = message.guild.default_role

                everyone_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
                await message.channel.edit(target=role, overwrite=everyone_perms)

                contest_channel_started_dict = {'started': True}
                guild_dict[message.guild.id]['contest_channel'][message.channel.id].update(contest_channel_started_dict)

                raid_embed = discord.Embed(title=_("Beep Beep! The channel is open for submissions now!"), colour=discord.Colour.gold())
                raid_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/396098777729204226/396101362460524545/imageedit_14_9502845615.png")
                await message.channel.send( embed=raid_embed)
            else:
                await message.channel.send( content="Beep Beep! Only contest organizer can do this!")
            return


async def contestEntry(message, pokemon=None):
    if pokemon == None:
        pokemon = guild_dict[message.guild.id]['contest_channel'][message.channel.id]['pokemon']

    if pokemon.lower() == message.content.lower():
        del guild_dict[message.guild.id]['contest_channel'][message.channel.id]
        await message.add_reaction( '✅')
        await message.add_reaction( '🎉')

        raid_embed = discord.Embed(title=_("**We have a winner!🎉🎉🎉**"), description="", colour=discord.Colour.dark_gold())

        raid_embed.add_field(name="**Winner:**", value=_("{member}").format(member=message.author.mention), inline=True)
        raid_embed.add_field(name="**Winning Entry:**", value=_("{pokemon}").format(pokemon=pokemon), inline=True)
        raid_embed.set_thumbnail(url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=message.author, format="jpg")))
        # raid_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/396098777729204226/396106669622296597/imageedit_17_5142594467.png")

        await message.channel.send( embed=raid_embed)

        await message.channel.send( content=_("Beep Beep! Congratulations {winner}!").format(winner=message.author.mention))

    elif message.content.lower() in pkmn_info['pokemon_list']:
        await message.add_reaction('🔴')
    return
