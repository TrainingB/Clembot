import asyncio
import re

import discord

def colour(*args):
    """Returns a discord Colour object.

    Pass one as an argument to define colour:
        `int` match colour value.
        `str` match common colour names.
        `discord.Guild` bot's guild colour.
        `None` light grey.
    """
    arg = args[0] if args else None
    if isinstance(arg, int):
        return discord.Colour(arg)
    if isinstance(arg, str):
        colour = arg
        try:
            return getattr(discord.Colour, colour)()
        except AttributeError:
            return discord.Colour.lighter_grey()
    if isinstance(arg, discord.Guild):
        return arg.me.colour
    else:
        return discord.Colour.lighter_grey()

def make_embed(msg_type='', header=None, header_icon=None, title=None, title_url=None, content=None, thumbnail='',
               image='', fields=None, footer=None, footer_icon=None, inline=False, guild=None, msg_colour=None):
    """Returns a formatted discord embed object.

    Define either a type or a colour.
    Types are:
    error, warning, info, success, help.
    :param title:
    """

    embed_types = {
        'error':{
            'icon':'https://i.imgur.com/juhq2uJ.png',
            'colour':'red'
        },
        'warning':{
            'icon':'https://i.imgur.com/4JuaNt9.png',
            'colour':'gold'
        },
        'info':{
            'icon':'https://i.imgur.com/wzryVaS.png',
            'colour':'blue'
        },
        'success':{
            'icon':'https://i.imgur.com/ZTKc3mr.png',
            'colour':'green'
        },
        'help':{
            'icon':'https://i.imgur.com/kTTIZzR.png',
            'colour':'blue'
        }
    }
    if msg_type in embed_types.keys():
        msg_colour = embed_types[msg_type]['colour']
        header_icon = embed_types[msg_type]['icon']
    if guild and not msg_colour:
        msg_colour = colour(guild)
    else:
        if not isinstance(msg_colour, discord.Colour):
            msg_colour = colour(msg_colour)
    embed = discord.Embed(
        title = title or discord.Embed.Empty,
        title_url = title_url or discord.Embed.Empty,
        description=content, colour=msg_colour)

    if header:
        embed.set_author(name=header, icon_url=header_icon or discord.Embed.Empty, url=discord.Embed.Empty)

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if fields:
        for key, value in fields.items():
            ilf = inline
            if not isinstance(value, str):
                if value:
                    ilf = value[0]
                    value = value[1]
                else:
                    continue
            embed.add_field(name=f"**{key}**", value=value, inline=ilf)
    if footer:
        footer = {'text':footer}
        if footer_icon:
            footer['icon_url'] = footer_icon
        embed.set_footer(**footer)
    return embed

def bold(msg: str):
    """Format to bold markdown text"""
    return f'**{msg}**'

def italics(msg: str):
    """Format to italics markdown text"""
    return f'*{msg}*'

def bolditalics(msg: str):
    """Format to bold italics markdown text"""
    return f'***{msg}***'

def code(msg: str):
    """Format to markdown code block"""
    return f'```{msg}```'

def pycode(msg: str):
    """Format to code block with python code highlighting"""
    return f'```py\n{msg}```'

def ilcode(msg: str):
    """Format to inline markdown code"""
    return f'`{msg}`'

def convert_to_bool(argument):
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        return None

def sanitize_channel_name(name):
    """Converts a given string into a compatible discord channel name."""
    # Remove all characters other than alphanumerics,
    # dashes, underscores, and spaces
    ret = re.sub('[^a-zA-Z0-9 _\\-]', '', name)
    # Replace spaces with dashes
    ret = ret.replace(' ', '-')
    return ret



async def get_raid_help(prefix, avatar, user=None):
    helpembed = discord.Embed(colour=discord.Colour.lighter_grey())
    helpembed.set_author(name="Raid Coordination Help", icon_url=avatar)
    helpembed.add_field(
        name="Key",
        value="<> denote required arguments, [] denote optional arguments",
        inline=False)
    helpembed.add_field(
        name="Raid MGMT Commands",
        value=(
            f"`{prefix}raid <species>`\n"
            f"`{prefix}weather <weather>`\n"
            f"`{prefix}timerset <minutes>`\n"
            f"`{prefix}starttime <time>`\n"
            "`<google maps link>`\n"
            "**RSVP**\n"
            f"`{prefix}(i/c/h)...\n"
            "[total]...\n"
            "[team counts]`\n"
            "**Lists**\n"
            f"`{prefix}list [status]`\n"
            f"`{prefix}list [status] tags`\n"
            f"`{prefix}list teams`\n\n"
            f"`{prefix}starting [team]`"))
    helpembed.add_field(
        name="Description",
        value=(
            "`Hatches Egg channel`\n"
            "`Sets in-game weather`\n"
            "`Sets hatch/raid timer`\n"
            "`Sets start time`\n"
            "`Updates raid location`\n\n"
            "`interested/coming/here`\n"
            "`# of trainers`\n"
            "`# from each team (ex. 3m for 3 Mystic)`\n\n"
            "`Lists trainers by status`\n"
            "`@mentions trainers by status`\n"
            "`Lists trainers by team`\n\n"
            "`Moves trainers on 'here' list to a lobby.`"))
    if not user:
        return helpembed
    await user.send(embed=helpembed)

def get_number(bot, pkm_name):
    try:
        number = bot.pkmn_info['pokemon_list'].index(pkm_name) + 1
    except ValueError:
        number = None
    return number

def get_name(bot, pkmn_number):
    pkmn_number = int(pkmn_number) - 1
    try:
        name = bot.pkmn_info['pokemon_list'][pkmn_number]
    except IndexError:
        name = None
    return name

def get_raidlist(bot):
    raidlist = []
    for level in bot.raid_info['raid_eggs']:
        for pokemon in bot.raid_info['raid_eggs'][level]['pokemon']:
            raidlist.append(pokemon)
            raidlist.append(get_name(pokemon).lower())
    return raidlist

def get_level(bot, pkmn):
    if str(pkmn).isdigit():
        pkmn_number = pkmn
    else:
        pkmn_number = get_number(bot, pkmn)
    for level in bot.raid_info['raid_eggs']:
        for level, pkmn_list in bot.raid_info['raid_eggs'].items():
            if pkmn_number in pkmn_list["pokemon"]:
                return level

async def ask(bot, message, user_list=None, timeout=60, *, react_list=['✅', '❎']):
    if user_list and type(user_list) != __builtins__.list:
        user_list = [user_list]
    def check(reaction, user):
        if user_list and type(user_list) is __builtins__.list:
            return (user.id in user_list) and (reaction.message.id == message.id) and (reaction.emoji in react_list)
        elif not user_list:
            return (user.id != message.author.id) and (reaction.message.id == message.id) and (reaction.emoji in react_list)
    for r in react_list:
        await asyncio.sleep(0.25)
        await message.add_reaction(r)
    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=timeout)
        return reaction, user
    except asyncio.TimeoutError:
        await message.clear_reactions()
        return



numbers_text = ["zero","one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

one_to_ten = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']




def emojify(numbers_text, one_to_ten, guild, normalized_emoji):

    emoji_array = [':%s:%s' %(guild_emoji.name,guild_emoji.id) for guild_emoji in guild.emojis if guild_emoji.name == normalized_emoji or str(guild_emoji) == normalized_emoji]

    if len(emoji_array) > 0:
        return emoji_array[0]

    if normalized_emoji in numbers_text:
        normalized_emoji = numbers_text.index(normalized_emoji)
        normalized_emoji = f'{normalized_emoji}\u20e3'

    if normalized_emoji.isdigit():
        normalized_emoji = f'{normalized_emoji}\u20e3'

    if normalized_emoji in one_to_ten:
        return normalized_emoji

    return None

def _new_serialize(emoji):
    if isinstance(emoji, discord.Reaction):
         emoji = emoji.emoji
    if isinstance(emoji, discord.Emoji):
        emoji = '%s:%s' % (emoji.name, emoji.id)
    elif isinstance(emoji, discord.PartialEmoji):
        emoji = emoji._as_reaction()
    elif isinstance(emoji, str):
        pass

    if emoji.__contains__(">") and emoji.__contains__("<"):
        emoji = emoji.replace('<','').replace('>','')
    return emoji


def serialize(guild, emoji):
    emoji_array = [guild_emoji.name for guild_emoji in guild.emojis if guild_emoji.name == emoji or str(guild_emoji) == emoji]

    if len(emoji_array) > 0:
        return emoji_array[0]

    if emoji in numbers_text:
        emoji = numbers_text.index(emoji)
        emoji = f'{emoji}\u20e3'

    if emoji.isdigit():
        emoji = f'{emoji}\u20e3'

    if emoji in one_to_ten:
        return emoji

    return None

def demojify(guild, emoji_string):

    if emoji_string in one_to_ten:
        return emoji_string

    emoji = emoji_string.replace('<','').replace('>','').split(":")[1]

    return emoji

# convert input to standard emoji format

def printable(guild, emoji_text):
    if emoji_text in one_to_ten:
        return emoji_text

    emoji_array = ['<:%s:%s>' % (guild_emoji.name, guild_emoji.id) for guild_emoji in guild.emojis if guild_emoji.name == emoji_text or str(guild_emoji) == emoji_text]

    if len(emoji_array) > 0:
        return emoji_array[0]