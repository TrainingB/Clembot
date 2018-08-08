import os
import sys
import tempfile
import asyncio
import gettext
import re
import pickle
import json
import time
import datetime
from os import name

from dateutil.relativedelta import relativedelta
from dateutil import tz
import copy
import functools
import textwrap
from time import strftime

from discord.colour import Colour

from logs import init_loggers
import discord
from discord.ext import commands
import spelling
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
import requests
import aiohttp
from io import BytesIO
import checks
import hastebin
from operator import itemgetter
from errors import custom_error_handling
import dateparser
import textwrap
import io
import traceback
from contextlib import redirect_stdout
# --B--
# ---- dependencies
import gymsql
import operator

import time
from datetime import timedelta
import calendar
import copy
from random import *
import pytz
from pytz import timezone
import jsonpickle
import bingo_generator
from WowBingo import WowBingo
from exts.argparser import ArgParser
from exts.propertieshandler import PropertiesHandler
from exts.profilemanager import ProfileManager
from exts.trademanager import TradeManager
from exts.utilities import Utilities
from exts.reactrolemanager import ReactRoleManager
from exts.autoresponder import AutoResponder
from exts.rostermanager import RosterManager
from exts.configmanager import ConfigManager


tessdata_dir_config = "--tessdata-dir 'C:\\Program Files (x86)\\Tesseract-OCR\\tessdata' "
xtraconfig = '-l eng -c tessedit_char_blacklist=&|=+%#^*[]{};<> -psm 6'
if os.name == 'nt':
    tesseract_config = tessdata_dir_config + xtraconfig
else:
    tesseract_config = xtraconfig

logger = init_loggers()


def _get_prefix(bot, message):
    guild = message.guild
    try:
        set_prefix = bot.guild_dict[guild.id]["prefix"]
    except (KeyError, AttributeError):
        set_prefix = None
    default_prefix = bot.config["default_prefix"]
    return set_prefix or default_prefix


Clembot = commands.Bot(command_prefix=_get_prefix, case_insensitive=True, activity=discord.Game(name="Pokemon Go"))
Clembot.remove_command("help")
custom_error_handling(Clembot, logger)

try:
    with open(os.path.join('data', 'guilddict'), "rb") as fd:
        Clembot.guild_dict = pickle.load(fd)
    logger.info("Serverdict Loaded Successfully")
except OSError:
    logger.info("Serverdict Not Found - Looking for Backup")
    try:
        with open(os.path.join('data', 'guilddict_backup'), "rb") as fd:
            Clembot.guild_dict = pickle.load(fd)
        logger.info("Serverdict Backup Loaded Successfully")
    except OSError:
        logger.info("Serverdict Backup Not Found - Creating New Serverdict")
        Clembot.guild_dict = {}
        with open(os.path.join('data', 'guilddict'), "wb") as fd:
            pickle.dump(Clembot.guild_dict, fd, -1)
        logger.info("Serverdict Created")

guild_dict = Clembot.guild_dict


Clembot.raidlist = {}
bingo_template = {}
config = {}
pkmn_info = {}
type_chart = {}
type_list = []
raid_info = {}
active_raids = []
gym_info_list = {}
egg_timer = 0
raid_timer = 0
icon_list = {}
GOOGLE_API_KEY = ""
GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/staticmap?center={latlong}&markers=color:red%7C{latlong}&maptype=roadmap&size=250x125&zoom=15&key=" + GOOGLE_API_KEY
INVITE_CODE = "AUzEXRU"
SQLITE_DB = ""
CACHE_VERSION = 7

# Append path of this script to the path of
# config files which we're loading.
# Assumes that config files will always live in the same directory.
script_path = os.path.dirname(os.path.realpath(__file__))


def load_config():
    global config
    global pkmn_info
    global type_chart
    global type_list
    global raid_info
    global egg_timer
    global raid_timer
    global icon_list
    global GOOGLE_API_KEY
    global GOOGLE_MAPS_URL
    global SQLITE_DB
    global raidlist
    # Load configuration
    with open("config.json", "r") as fd:
        config = json.load(fd)

    # Set up message catalog access
    language = gettext.translation('clembot', localedir='locale', languages=[config['bot-language']])
    language.install()
    pokemon_language = [config['pokemon-language']]
    pokemon_path_source = os.path.join('locale', '{0}', 'pkmn.json').format(config['pokemon-language'])

    # Load Pokemon list and raid info
    with open(pokemon_path_source, "r") as fd:
        pkmn_info = json.load(fd)
    with open(os.path.join('data', 'raid_info.json'), "r") as fd:
        raid_info = json.load(fd)

    # Load type information
    with open(os.path.join('data', 'type_chart.json'), "r") as fd:
        type_chart = json.load(fd)
    with open(os.path.join('data', 'type_list.json'), "r") as fd:
        type_list = json.load(fd)

    with open(os.path.join('data', "icon.json"), "r") as fd:
        icon_list = json.load(fd)

    # Set spelling dictionary to our list of Pokemon
    spelling.set_dictionary(pkmn_info['pokemon_list'])

    # --B--
    egg_timer = config['egg-timer']
    raid_timer = config['raid-timer']
    GOOGLE_API_KEY = config['google-api-key']
    GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/staticmap?center={latlong}&markers=color:red%7C{latlong}&maptype=roadmap&size=250x125&zoom=15&key=" + GOOGLE_API_KEY
    SQLITE_DB = config['sqlite_db']

    gymsql.set_db_name(SQLITE_DB)
    # gymutil.load_gyms()
    bingo_template[347397406033182721] = "bingo_template_bur.png"
    bingo_template[329013844427014145] = "bingo_template_qcy.png"
    bingo_template[341367173266276353] = "bingo_template_spg.png"

load_config()

Clembot.config = config
Clembot.pkmn_info = pkmn_info


poke_alarm_image_url = "/icons/{0}.png?width=80&height=80"
floatzel_image_url = "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png"




default_exts = ['exts.silph','exts.propertieshandler', 'exts.utilities', 'exts.trademanager',
                'exts.profilemanager','exts.reactrolemanager','exts.gymmanager','exts.autoresponder',
                'exts.rostermanager', 'exts.configmanager', 'exts.cpcalculator']
#default_exts = ['exts.silph','exts.propertieshandler', 'exts.utilities']
for ext in default_exts:
    try:
        Clembot.load_extension(ext)
    except Exception as e:
        print(f'**Error when loading extension {ext}:**\n{type(e).__name__}: {e}')
    else:
        print(f'Loaded {ext} extension.')

@Clembot.command(name='load')
@checks.is_owner()
async def _load(ctx, *extensions):
    for ext in extensions:
        try:
            ctx.bot.unload_extension(f"exts.{ext}")
            ctx.bot.load_extension(f"exts.{ext}")
        except Exception as e:
            error_title = _('**Error when loading extension')
            await ctx.send(f'{error_title} {ext}:**\n'
                           f'{type(e).__name__}: {e}')
        else:
            await ctx.send(_('**Extension {ext} Loaded.**\n').format(ext=ext))

@Clembot.command(name='unload')
@checks.is_owner()
async def _unload(ctx, *extensions):
    exts = [e for e in extensions if f"exts.{e}" in Clembot.extensions]
    for ext in exts:
        ctx.bot.unload_extension(f"exts.{ext}")
    s = 's' if len(exts) > 1 else ''
    await ctx.send(_("**Extension{plural} {est} unloaded.**\n").format(plural=s, est=', '.join(exts)))


Parser = ArgParser()
MyTradeManager = TradeManager(Clembot)
MyAutoResponder = AutoResponder(Clembot)
MyRosterManager = RosterManager(Clembot)
MyConfigManager = ConfigManager(Clembot)
"""

======================

Helper functions

======================

"""


# --B--
@Clembot.command(pass_context=True, hidden=True, aliases= ["remove-channel"])
@checks.is_owner()
async def remove_channel(ctx, channel_id):

    try :
        if channel_id:
            stuck_channel = Clembot.get_channel(channel_id)
            stuck_channel.delete()
            await _send_message(ctx.channel, "Channel deleted successfully.")
        else:
            await _send_error_message(ctx.channel, "Channel doesn't exists.")
    except Exception as error:
        await _send_error_message(ctx.channel, "Channel doesn't exists.")


def clembot_time_in_guild_timezone(message):
    guild_offset = guild_dict[message.channel.guild.id]['offset']
    clembot_offset = -8

    return time.time() + 3600 * (guild_offset - clembot_offset)


def get_pokemon_image_url(pokedex_number):
    # url = icon_list.get(str(pokedex_number))
    url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/pkmn/{0}_.png?cache={1}".format(str(pokedex_number).zfill(3),CACHE_VERSION)
    if url:
        return url
    else:
        return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=pokedex_number)


def get_egg_image_url(egg_level):
    # url = icon_list.get(str(pokedex_number))
    url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/eggs/{0}.png?cache={1}".format(str(egg_level),CACHE_VERSION)
    if url:
        return url
    else:
        return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=egg_level)


def _set_prefix(bot, guild, prefix):
    bot.guild_dict[guild.id]["prefix"] = prefix


def get_city_list(message):
    city_list = []
    try:
        city_channel = guild_dict[message.guild.id]['city_channels'].get(message.channel.name)
        if city_channel:
            city_list.append(city_channel.replace(" ", "").upper())
            return city_list

        city_channel = gymsql.read_channel_city(message.guild.id, message.channel.id)
        if city_channel:
            city_list.append(city_channel)
        else:
            guild_channel = gymsql.read_guild_city(message.guild.id)
            if guild_channel:
                city_list.append(guild_channel)
        return city_list

        # for key in guild_dict[message.guild.id]['city_channels'].keys():
        #     city_name = guild_dict[message.guild.id]['city_channels'].get(key)
        #     city_key = city_name.replace(" ", "").upper()
        #     if city_list.__contains__(city_key):
        #         pass
        #     else:
        #         city_list.append(city_key)

    except Exception as error:
        print(error)

    return city_list


# @Clembot.command(pass_context=True, hidden=True)
# async def test(ctx):
#     await ctx.message.channel.send(content=get_city_list(ctx))



# Given a Pokemon name, return a list of its
# weaknesses as defined in the type chart
def get_type(guild, pkmn_number):
    pkmn_number = int(pkmn_number) - 1
    types = type_list[pkmn_number]
    ret = []
    for type in types:
        ret.append(parse_emoji(guild, config['type_id_dict'][type.lower()]))
    return ret


def get_weather(guild, weather):
    weather_emoji = parse_emoji(guild, config['weather_id_dict'].get(weather.lower(), ""))
    return weather_emoji

def get_name(pkmn_number):
    pkmn_number = int(pkmn_number) - 1
    name = pkmn_info['pokemon_list'][pkmn_number].capitalize()
    return name


def get_number(pkm_name):
    number = pkmn_info['pokemon_list'].index(pkm_name) + 1
    return number


def get_level(pkmn):
    if str(pkmn).isdigit():
        pkmn_number = pkmn
    elif not str(pkmn).isdigit():
        pkmn_number = get_number(pkmn)
    for level in raid_info["raid_eggs"]:
        for pokemon in raid_info["raid_eggs"][level]["pokemon"]:
            if pokemon == pkmn_number:
                return level




def get_raidlist():
    raidlist = []
    for level in raid_info["raid_eggs"]:
        for pokemon in raid_info["raid_eggs"][level]["pokemon"]:
            raidlist.append(pokemon)
            raidlist.append(get_name(pokemon).lower())
    return raidlist

Clembot.raidlist = get_raidlist()


# Given a Pokemon name, return a list of its
# weaknesses as defined in the type chart
def get_weaknesses(species):
    # Get the Pokemon's number
    number = pkmn_info['pokemon_list'].index(species)
    # Look up its type
    pk_type = type_list[number]

    # Calculate sum of its weaknesses
    # and resistances.
    # -2 == immune
    # -1 == NVE
    #  0 == neutral
    #  1 == SE
    #  2 == double SE
    type_eff = {}
    for type in pk_type:
        for atk_type in type_chart[type]:
            if atk_type not in type_eff:
                type_eff[atk_type] = 0
            type_eff[atk_type] += type_chart[type][atk_type]

    # Summarize into a list of weaknesses,
    # sorting double weaknesses to the front and marking them with 'x2'.
    ret = []
    for type, effectiveness in sorted(type_eff.items(), key=lambda x: x[1], reverse=True):
        if effectiveness == 1:
            ret.append(type.lower())
        elif effectiveness == 2:
            ret.append(type.lower() + "x2")

    return ret


# Given a list of weaknesses, return a
# space-separated string of their type IDs,
# as defined in the type_id_dict
def weakness_to_str(guild, weak_list):
    ret = ""
    for weakness in weak_list:
        # Handle an "x2" postfix defining a double weakness
        x2 = ""
        if weakness[-2:] == "x2":
            weakness = weakness[:-2]
            x2 = "x2"

        # Append to string
        ret += parse_emoji(guild, config['type_id_dict'][weakness]) + x2 + " "

    return ret


# Convert an arbitrary string into something which
# is acceptable as a Discord channel name.
def sanitize_channel_name(name):
    # Remove all characters other than alphanumerics,
    # dashes, underscores, and spaces
    ret = re.sub(r"[^a-zA-Z0-9 _\-]", "", name)
    # Replace spaces with dashes
    ret = ret.replace(" ", "-")
    return ret


# Given a string, if it fits the pattern :emoji name:,
# and <emoji_name> is in the guild's emoji list, then
# return the string <:emoji name:emoji id>. Otherwise,
# just return the string unmodified.
def parse_emoji(guild, emoji_string):
    if len(emoji_string) == 0:
        return ""
    if emoji_string[0] == ':' and emoji_string[-1] == ':':
        emoji = discord.utils.get(guild.emojis, name=emoji_string.strip(':'))
        if emoji:
            emoji_string = "<:{0}:{1}>".format(emoji.name, emoji.id)
        else:
            emoji_string = "{0}".format(emoji_string.strip(':').capitalize())

    return emoji_string


def print_emoji_name(guild, emoji_string):
    # By default, just print the emoji_string
    ret = "`" + emoji_string + "`"

    emoji = parse_emoji(guild, emoji_string)
    # If the string was transformed by the parse_emoji
    # call, then it really was an emoji and we should
    # add the raw string so people know what to write.
    if emoji != emoji_string:
        ret = emoji + " (`" + emoji_string + "`)"

    return ret


# --B--

def extract_lat_long_from(gmap_link):
    lat_long = gmap_link.replace("http://maps.google.com/maps?q=", "")
    lat_long = lat_long.replace("https://maps.google.com/maps?q=", "")
    lat_long = lat_long.replace("https://www.google.com/maps/place/", "")

    pattern = re.compile("^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$")

    if pattern.match(lat_long):
        return lat_long

    return None


def fetch_gmap_image_link(lat_long):
    key = GOOGLE_API_KEY
    gmap_base_url = "https://maps.googleapis.com/maps/api/staticmap?center={0}&markers=color:red%7C{1}&maptype=roadmap&size=250x125&zoom=15&key={2}".format(lat_long, lat_long, key)

    return gmap_base_url


# fix for links for general location add
def fetch_gmap_link(gym_code, channel):
    try:
        details_list = gym_code.split()
        report_channel = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['reportcity']
        city_channel = guild_dict[channel.guild.id]['city_channels'][report_channel]
        loc_list = city_channel.split()
        return "https://www.google.com/maps/search/?api=1&query={0}+{1}".format('+'.join(details_list), '+'.join(loc_list))
    except Exception as error:
        return "https://www.google.com/maps/search/?api=1&query={0}+{1}"


# Given an arbitrary string, create a Google Maps
# query using the configured hints
def create_gmaps_query(details, channel):
    details_list = details.split()
    loc_list = guild_dict[channel.guild.id]['city_channels'][channel.name].split()
    return "https://www.google.com/maps/search/?api=1&query={0}+{1}".format('+'.join(details_list), '+'.join(loc_list))


def get_raid_channel_dict(message):
    raid_channel_dict = guild_dict[message.guild.id]['raidchannel_dict']
    if message.channel.id in raid_channel_dict:
        return raid_channel_dict[message.channel.id]
    else:
        return None


# Given a User, check that it is Clembot's master
def check_master(user):
    return str(user) == config['master']


def check_guild_owner(user, guild):
    return str(user) == str(guild.owner)


# Given a violating message, raise an exception
# reporting unauthorized use of admin commands
def raise_admin_violation(message):
    raise Exception(_("Received admin command {command} from unauthorized user, {user}!").format(command=message.content, user=message.author))


def spellcheck(word):
    suggestion = spelling.correction(word)

    # If we have a spellcheck suggestion
    if suggestion != word:
        return _("Beep Beep! \"{entered_word}\" is not a Pokemon! Did you mean \"{corrected_word}\"?").format(entered_word=word, corrected_word=spelling.correction(word))
    else:
        return _("Beep Beep! \"{entered_word}\" is not a Pokemon! Check your spelling!").format(entered_word=word)

def spellcheck(word):
    suggestion = spelling.correction(word)
    return suggestion
    # If we have a spellcheck suggestion
    if suggestion != word:
        return _('Beep Beep! "{entered_word}" is not a Pokemon! Did you mean "{corrected_word}"?').format(entered_word=word, corrected_word=spelling.correction(word))
    else:
        return _('Beep Beep! "{entered_word}" is not a Pokemon! Check your spelling!').format(entered_word=word)

async def autocorrect(entered_word, destination, author):
    not_a_pokemon_msg = _("Beep Beep! **{word}** isn't a Pokemon!").format(word=entered_word.title())
    if spellcheck(entered_word) and (spellcheck(entered_word) != entered_word):
        not_a_pokemon_msg += _(' Did you mean **{correction}**?').format(correction=spellcheck(entered_word).title())
        question = await _send_error_message(destination, not_a_pokemon_msg)
        if author:
            try:
                timeout = False
                res, reactuser = await ask(question, destination, author.id)
            except TypeError:
                timeout = True
            await question.delete()
            if timeout or res.emoji == '❎':
                await destination.send(not_a_pokemon_msg)
                return None
            elif res.emoji == '✅':
                return spellcheck(entered_word)
            else:
                return None
        else:
            return None
    else:
        question = await destination.send(not_a_pokemon_msg)
        return



def do_template(message, author, guild):
    not_found = []

    def template_replace(match):
        if match.group(3):
            if match.group(3) == 'user':
                return '{user}'
            elif match.group(3) == 'server':
                return guild.name
            else:
                return match.group(0)
        if match.group(4):
            emoji = (':' + match.group(4)) + ':'
            return parse_emoji(guild, emoji)
        match_type = match.group(1)
        full_match = match.group(0)
        match = match.group(2)
        if match_type == '<':
            mention_match = re.search('(#|@!?|&)([0-9]+)', match)
            match_type = mention_match.group(1)[0]
            match = mention_match.group(2)
        if match_type == '@':
            member = guild.get_member_named(match)
            if match.isdigit() and (not member):
                member = guild.get_member(match)
            if (not member):
                not_found.append(full_match)
            return member.mention if member else full_match
        elif match_type == '#':
            channel = discord.utils.get(guild.channels, name=match)
            if match.isdigit() and (not channel):
                channel = guild.get_channel(match)
            if (not channel):
                not_found.append(full_match)
            return channel.mention if channel else full_match
        elif match_type == '&':
            role = discord.utils.get(guild.roles, name=match)
            if match.isdigit() and (not role):
                role = discord.utils.get(guild.roles, id=match)
            if (not role):
                not_found.append(full_match)
            return role.mention if role else full_match
    template_pattern = '{(@|#|&|<)([^{}]+)}|{(user|server)}|<*:([a-zA-Z0-9]+):[0-9]*>*'
    msg = re.sub(template_pattern, template_replace, message)
    return (msg, not_found)



async def ask(message, destination, user_list=None, *, react_list=['✅', '❎']):
    if user_list and type(user_list) != __builtins__.list:
        user_list = [user_list]
    def check(reaction, user):
        if user_list and type(user_list) is __builtins__.list:
            return (user.id in user_list) and (reaction.message.id == message.id) and (reaction.emoji in react_list)
        elif not user_list:
            return (user.id != message.guild.me.id) and (reaction.message.id == message.id) and (reaction.emoji in react_list)
    for r in react_list:
        await asyncio.sleep(0.25)
        await message.add_reaction(r)
    try:
        reaction, user = await Clembot.wait_for('reaction_add', check=check, timeout=60)
        return reaction, user
    except asyncio.TimeoutError:
        await message.clear_reactions()
        return


async def letter_case(iterable, find, *, limits=None):
    servercase_list = []
    lowercase_list = []
    for item in iterable:
        if not item.name:
            continue
        elif item.name and (not limits or item.name.lower() in limits):
            servercase_list.append(item.name)
            lowercase_list.append(item.name.lower())
    if find.lower() in lowercase_list:
        index = lowercase_list.index(find.lower())
        return servercase_list[index]
    else:
        return None


def get_category(channel, level):
    try:
        guild = channel.guild
        catsort = guild_dict[guild.id].get('categories', None)
        if catsort == None:
            return None
        elif catsort == "same":
            return channel.category
        elif catsort == "region":
            category = discord.utils.get(guild.categories,name=guild_dict[guild.id]['category_dict'][channel.name])
            return category
        elif catsort == "level":
            category = discord.utils.get(guild.categories,name=guild_dict[guild.id]['category_dict'][level])
            return category
        else:
            return None
    except Exception as error:
        logger.error(error)
        return None

@Clembot.command(hidden=True)
async def template(ctx, *, sample_message):
    """Sample template messages to see how they would appear."""
    embed = None
    (msg, errors) = do_template(sample_message, ctx.author, ctx.guild)
    if errors:
        if msg.startswith('[') and msg.endswith(']'):
            embed = discord.Embed(
                colour=ctx.guild.me.colour, description=msg[1:(- 1)])
            embed.add_field(name='Warning', value='The following could not be found:\n{}'.format(
                '\n'.join(errors)))
            await ctx.channel.send(embed=embed)
        else:
            msg = '{}\n\n**Warning:**\nThe following could not be found: {}'.format(
                msg, ', '.join(errors))
            await ctx.channel.send(msg)
    elif msg.startswith('[') and msg.endswith(']'):
        await ctx.channel.send(embed=discord.Embed(colour=ctx.guild.me.colour, description=msg[1:(- 1)].format(user=ctx.author.mention)))
    else:
        await ctx.channel.send(msg.format(user=ctx.author.mention))


async def expiry_check(channel):
    logger.info("Expiry_Check - " + channel.name)
    guild = channel.guild
    global active_raids
    if channel not in active_raids:
        active_raids.append(channel)
        logger.info("Expire_Channel - Channel Added To Watchlist - " + channel.name)
        await asyncio.sleep(0.5)  # wait for assume
        while True:
            try:
                if guild_dict[guild.id]['raidchannel_dict'][channel.id]['active'] is True:
                    if guild_dict[guild.id]['raidchannel_dict'][channel.id]['exp'] is not None:
                        # print("{channel} => {expiry} vs {current}".format(channel=channel.name,expiry=guild_dict[guild.id]['raidchannel_dict'][channel.id]['exp'],current=fetch_current_time(channel.guild.id)))

                        if guild_dict[guild.id]['raidchannel_dict'][channel.id]['exp'] <= fetch_current_time(channel.guild.id):
                            if guild_dict[guild.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
                                pokemon = guild_dict[guild.id]['raidchannel_dict'][channel.id]['pokemon']
                                if pokemon:
                                    logger.info("Expire_Channel - Egg Auto Hatched - " + channel.name)
                                    try:
                                        active_raids.remove(channel)
                                    except ValueError:
                                        logger.info("Expire_Channel - Channel Removal From Active Raid Failed - Not in List - " + channel.name)
                                    await _eggtoraid(pokemon.lower(), channel)
                                    break
                            event_loop.create_task(expire_channel(channel))
                            try:
                                active_raids.remove(channel)
                            except ValueError:
                                logger.info("Expire_Channel - Channel Removal From Active Raid Failed - Not in List - " + channel.name)
                            logger.info("Expire_Channel - Channel Expired And Removed From Watchlist - " + channel.name)
                            break
            except KeyError:
                pass

            await asyncio.sleep(30)
            continue


async def expire_channel(channel):
    try:
        guild = channel.guild
        alreadyexpired = False
        # print("Expire_Channel - " + channel.name)
        logger.info("Expire_Channel - " + channel.name)
        # If the channel exists, get ready to delete it.
        # Otherwise, just clean up the dict since someone
        # else deleted the actual channel at some point.
        channel_exists = Clembot.get_channel(channel.id)
        channel = channel_exists

        if channel :
            is_archived = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('archive', False)
            if is_archived:
                logger.info("Expire_Channel - Channel Skipped as it is marked as Archived - " + channel.name)
                return

        if (channel_exists == None) and (not Clembot.is_closed()):
            try:
                del guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]
            except KeyError:
                pass
            return
        else:
            dupechannel = False
            if guild_dict[guild.id]['raidchannel_dict'][channel.id]['active'] == False:
                alreadyexpired = True
            else:
                guild_dict[guild.id]['raidchannel_dict'][channel.id]['active'] = False
            logger.info("Expire_Channel - Channel Expired - " + channel.name)
            try:
                testvar = guild_dict[guild.id]['raidchannel_dict'][channel.id]['duplicate']
            except KeyError:
                guild_dict[guild.id]['raidchannel_dict'][channel.id]['duplicate'] = 0
            if guild_dict[guild.id]['raidchannel_dict'][channel.id]['duplicate'] >= 3:
                dupechannel = True
                guild_dict[guild.id]['raidchannel_dict'][channel.id]['duplicate'] = 0
                guild_dict[guild.id]['raidchannel_dict'][channel.id]['exp'] = fetch_current_time(channel.guild.id)
                if not alreadyexpired:
                    await channel.send( _("""This channel has been successfully reported as a duplicate and will be deleted in 1 minute. Check the channel list for the other raid channel to coordinate in! If this was in error, reset the raid with **!timerset**"""))
                delete_time = convert_to_epoch(fetch_channel_expire_time(channel.id)) + timedelta(minutes=1).seconds - convert_to_epoch(fetch_current_time(channel.guild.id))
            elif guild_dict[guild.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
                if not alreadyexpired:
                    maybe_list = []
                    trainer_dict = copy.deepcopy(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['trainer_dict'])
                    for trainer in trainer_dict.keys():
                        if trainer_dict[trainer]['status'] == 'maybe':
                            user = channel.guild.get_member(trainer)
                            maybe_list.append(user.mention)
                    new_name = 'hatched-' + channel.name
                    await channel.edit(name=new_name)
                    await channel.send( _("""**This egg has hatched!**\n\n...or the time has just expired. Trainers {trainer_list}: Update the raid to the pokemon that hatched using **!raid <pokemon>** or reset the hatch timer with **!timerset**.""").format(trainer_list=", ".join(maybe_list)))
                delete_time = convert_to_epoch(fetch_channel_expire_time(channel.id)) + timedelta(minutes=45).seconds - convert_to_epoch(fetch_current_time(channel.guild.id))
                expiremsg = _("**This level {level} raid egg has expired!**").format(level=guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['egglevel'])
            else:
                if (not alreadyexpired):
                    new_name = 'expired-' + channel.name
                    await channel.edit(name=new_name)
                    await channel.send( _("""This channel timer has expired! The channel has been deactivated and will be deleted in 5 minutes."""))
                delete_time = convert_to_epoch(fetch_channel_expire_time(channel.id)) + timedelta(minutes=5).seconds - convert_to_epoch(fetch_current_time(channel.guild.id))
                expiremsg = _("**This {pokemon} raid has expired!**").format(pokemon=guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['pokemon'].capitalize())
            if delete_time:
                await asyncio.sleep(delete_time)
            # If the channel has already been deleted from the dict, someone
            # else got to it before us, so don't do anything.
            # Also, if the channel got reactivated, don't do anything either.

            try:
                if (guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['active'] == False) and (not Clembot.is_closed()):
                    if dupechannel:
                        try:
                            report_channel = Clembot.get_channel(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['reportcity'])
                            reportmsg = await report_channel.get_message( guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['raidreport'])
                            await reportmsg.delete()
                        except:
                            pass
                    else:
                        try:
                            report_channel = Clembot.get_channel(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['reportcity'])
                            reportmsg = await report_channel.get_message( guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['raidreport'])
                            await reportmsg.edit(embed=discord.Embed(description=expiremsg, colour=channel.guild.me.colour))
                        except:
                            pass
                    try:
                        del guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]
                    except KeyError:
                        pass
                        # channel doesn't exist anymore in guilddict
                    channel_exists = Clembot.get_channel(channel.id)
                    if channel_exists == None:
                        return
                    else:
                        await channel_exists.delete()
                        logger.info("Expire_Channel - Channel Deleted - " + channel.name)
            except Exception as error:
                print(error)
                pass
    except Exception as error:
        print(error)

@Clembot.command(pass_context=True, hidden=True, aliases=["archive"])
async def _archive(ctx):

    message = ctx.message
    channel = message.channel
    guild = message.guild

    egg_level = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('egglevel',0)

    # if egg_level != 'EX':
    #     return await _send_error_message(channel, "Beep Beep! **{0}** Only EX raids can be **Archived**.".format(message.author.display_name))

    is_archived = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('archive', False)

    if is_archived:
        guild_dict[guild.id]['raidchannel_dict'][channel.id]['archive'] = False
        await _send_message(channel, "Beep Beep! **{0}** The channel is not marked for **Archival** anymore!".format(message.author.display_name))
    else:
        guild_dict[guild.id]['raidchannel_dict'][channel.id]['archive'] = True
        await _send_message(channel, "Beep Beep! **{0}** The channel has been marked for **Archival**, it will not be deleted automatically!".format(message.author.display_name))

    return None

async def channel_cleanup(loop=True):
    while (not Clembot.is_closed()):
        global active_raids
        guilddict_chtemp = copy.deepcopy(guild_dict)
        logger.info('Channel_Cleanup ------ BEGIN ------')
        # for every server in save data
        for guildid in guilddict_chtemp.keys():
            guild = Clembot.get_guild(guildid)
            log_str = 'Channel_Cleanup - Server: ' + str(guildid)
            log_str = log_str + ' - CHECKING FOR SERVER'
            if guild == None:
                logger.info(log_str + ': NOT FOUND')
                continue
            logger.info(((log_str + ' (') + guild.name) +
                        ')  - BEGIN CHECKING SERVER')
            # clear channel lists
            dict_channel_delete = []
            discord_channel_delete = []

            add_contest_to_guild_dict(guildid)
            for channelid in guilddict_chtemp[guildid].get('contest_channel',[]):
                try:
                    channel = Clembot.get_channel(channelid)
                    if channel is None:
                        del guild_dict[guildid]['contest_channel'][channelid]
                        logger.info("Channel_Cleanup - Server: " + guild.name + ": Channel:" + channel.name + " CLEANED UP DICT - DOESN'T EXIST IN DISCORD")
                except Exception as error:
                    continue

            # check every raid channel data for each server
            for channelid in guilddict_chtemp[guildid]['raidchannel_dict']:
                channel = Clembot.get_channel(channelid)
                log_str = 'Channel_Cleanup - Server: ' + guild.name
                log_str = (log_str + ': Channel:') + str(channelid)
                logger.info(log_str + ' - CHECKING')
                channelmatch = Clembot.get_channel(channelid)
                if channelmatch == None:
                    # list channel for deletion from save data
                    dict_channel_delete.append(channelid)
                    logger.info(log_str + " - DOESN'T EXIST IN DISCORD")
                # otherwise, if meowth can still see the channel in discord
                else:
                    logger.info(
                        ((log_str + ' (') + channel.name) + ') - EXISTS IN DISCORD')
                    # if the channel save data shows it's not an active raid
                    if guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['active'] == False:
                        if guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['type'] == 'egg':
                            # and if it has been expired for longer than 45 minutes already
                            if guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['exp'] < fetch_current_time(channel.guild.id) - timedelta(minutes=45):
                                # list the channel to be removed from save data
                                dict_channel_delete.append(channelid)
                                # and list the channel to be deleted in discord
                                discord_channel_delete.append(channel)
                                logger.info(
                                    log_str + ' - 15+ MIN EXPIRY NONACTIVE EGG')
                                continue
                            # and if it has been expired for longer than 5 minutes already
                        elif guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['exp'] < fetch_current_time(channel.guild.id) - timedelta(minutes=5):
                                # list the channel to be removed from save data
                            dict_channel_delete.append(channelid)
                                # and list the channel to be deleted in discord
                            discord_channel_delete.append(channel)
                            logger.info(
                                log_str + ' - 5+ MIN EXPIRY NONACTIVE RAID')
                            continue
                        event_loop.create_task(expire_channel(channel))
                        logger.info(
                            log_str + ' - = RECENTLY EXPIRED NONACTIVE RAID')
                        continue
                    # if the channel save data shows it as an active raid still
                    elif guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['active'] == True:
                        # if it's an exraid
                        if guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['type'] == 'exraid':
                            logger.info(log_str + ' - EXRAID')
                            continue
                        if guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['type'] == 'raidparty':
                            logger.info(log_str + ' - RAID PARTY')
                        # or if the expiry time for the channel has already passed within 5 minutes
                        elif guilddict_chtemp[guildid]['raidchannel_dict'][channelid]['exp'] < fetch_current_time(channel.guild.id):
                            # list the channel to be sent to the channel expiry function
                            event_loop.create_task(expire_channel(channel))
                            logger.info(log_str + ' - RECENTLY EXPIRED')

                            continue

                        elif channel not in active_raids:
                            # if channel is still active, make sure it's expiry is being monitored
                            event_loop.create_task(expiry_check(channel))
                            logger.info(
                                log_str + ' - MISSING FROM EXPIRY CHECK')
                            continue
            # for every channel listed to have save data deleted
            for c in dict_channel_delete:
                try:
                    # attempt to delete the channel from save data
                    del guild_dict[guildid]['raidchannel_dict'][c]
                    logger.info(
                        'Channel_Cleanup - Channel Savedata Cleared - ' + str(c))
                except KeyError:
                    pass
            # for every channel listed to have the discord channel deleted
            for c in discord_channel_delete:
                try:
                    # delete channel from discord
                    await c.delete()
                    logger.info(
                        'Channel_Cleanup - Channel Deleted - ' + c.name)
                except:
                    logger.info(
                        'Channel_Cleanup - Channel Deletion Failure - ' + c.name)
                    pass
        # save server_dict changes after cleanup
        logger.info('Channel_Cleanup - SAVING CHANGES')
        try:
            await _save()
        except Exception as err:
            logger.info('Channel_Cleanup - SAVING FAILED' + err)
        logger.info('Channel_Cleanup ------ END ------')
        await asyncio.sleep(600)
        continue


async def message_cleanup(loop=True):
    while (not Clembot.is_closed()):
        logger.info('message_cleanup ------ BEGIN ------')
        guilddict_temp = copy.deepcopy(guild_dict)
        for guildid in guilddict_temp.keys():
            questreport_dict = guilddict_temp[guildid].get('questreport_dict',{})
            wildreport_dict = guilddict_temp[guildid].get('wildreport_dict',{})
            report_dict_dict = {
                'questreport_dict':questreport_dict,
                'wildreport_dict':wildreport_dict,
            }
            report_edit_dict = {}
            report_delete_dict = {}
            for report_dict in report_dict_dict:
                for reportid in report_dict_dict[report_dict].keys():
                    if report_dict_dict[report_dict][reportid]['exp'] <= time.time():
                        report_channel = Clembot.get_channel(report_dict_dict[report_dict][reportid]['reportchannel'])
                        if report_channel:
                            user_report = report_dict_dict[report_dict][reportid].get('reportmessage',None)
                            if user_report:
                                report_delete_dict[user_report] = {"action":"delete","channel":report_channel}
                            if report_dict_dict[report_dict][reportid]['expedit'] == "delete":
                                report_delete_dict[reportid] = {"action":report_dict_dict[report_dict][reportid]['expedit'],"channel":report_channel}
                            else:
                                report_edit_dict[reportid] = {"action":report_dict_dict[report_dict][reportid]['expedit'],"channel":report_channel}
                        del guild_dict[guildid][report_dict][reportid]
            for messageid in report_delete_dict.keys():
                try:
                    report_message = await report_delete_dict[messageid]['channel'].get_message(messageid)
                    logger.info('message_cleanup - DELETE ' + report_message.content)
                    print(report_message)
                    await report_message.delete()

                except discord.errors.NotFound:
                    pass
            for messageid in report_edit_dict.keys():
                try:
                    report_message = await report_edit_dict[messageid]['channel'].get_message(messageid)
                    await report_message.edit(content=report_edit_dict[messageid]['action']['content'],embed=discord.Embed(description=report_edit_dict[messageid]['action']['embedcontent'], colour=report_message.embeds[0].colour.value))
                except discord.errors.NotFound:
                    pass
        # save server_dict changes after cleanup
        logger.info('message_cleanup - SAVING CHANGES')
        try:
            await _save()
        except Exception as err:
            logger.info('message_cleanup - SAVING FAILED' + err)
        logger.info('message_cleanup ------ END ------')
        await asyncio.sleep(600)
        continue

@Clembot.command(pass_context=True, hidden=True)
async def timestamp(ctx):
    await _send_message(ctx.channel, str(time.time()))

@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def mysetup(ctx):
    text=[]
    current_guild = ctx.message.guild

    user = ctx.message.guild.me

    for permission in user.guild_permissions:
        if permission[1] == True:
            text.append("{permission}".format(permission=permission[0]) )

    raid_embed = discord.Embed(colour=discord.Colour.gold())
    raid_embed.add_field(name="**Username:**", value=_("{option}").format(option=user.name))
    raid_embed.add_field(name="**Roles:**", value=_("{roles}").format(roles=" \ ".join(text)))
    raid_embed.set_thumbnail(url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=user, format="jpg")))
    await ctx.message.channel.send(embed=raid_embed)

@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def cleanup(ctx):
    # await ctx.channel.delete()

    await channel_cleanup()


async def guild_cleanup(loop=True):
    while (not Clembot.is_closed()):
        guilddict_srvtemp = copy.deepcopy(guild_dict)
        logger.info("Server_Cleanup ------ BEGIN ------")

        guilddict_srvtemp = guild_dict
        dict_guild_list = []
        bot_guild_list = []
        dict_guild_delete = []

        for guildid in guilddict_srvtemp.keys():
            guild = Clembot.get_guild(guildid)
            dict_guild_list.append(guild)
        for guild in Clembot.guilds:
            bot_guild_list.append(guild)
        guild_diff = set(dict_guild_list) - set(bot_guild_list)
        for s in guild_diff:
            dict_guild_delete.append(s)

        for s in dict_guild_delete:
            try:
                del guild_dict[s]
                logger.info("Server_Cleanup - Cleared " + s.name + " from save data")
            except KeyError:
                pass

        logger.info("Server_Cleanup - SAVING CHANGES")
        try:
            await _save()
        except Exception as err:
            logger.info("Server_Cleanup - SAVING FAILED" + err)
        logger.info("Server_Cleanup ------ END ------")
        await asyncio.sleep(1800)  # 1800 default
        continue


async def _print(owner, message):
    if 'launcher' in sys.argv[1:]:
        if 'debug' not in sys.argv[1:]:
            await owner.send(message)
    # print(message)
    logger.info(message)


async def maint_start():
    try:
        event_loop.create_task(guild_cleanup())
        event_loop.create_task(channel_cleanup())
        event_loop.create_task(message_cleanup())
        logger.info("Maintenance Tasks Started")
    except KeyboardInterrupt as e:
        tasks.cancel()


event_loop = asyncio.get_event_loop()

"""

======================

End helper functions

======================

"""

"""
Clembot tracks raiding commands through the raidchannel_dict.
Each channel contains the following fields:
'trainer_dict' : a dictionary of all trainers interested in the raid.
'exp'          : an instance of time.struct_time tracking when the raid ends.
'active'       : a Boolean indicating whether the raid is still active.

The trainer_dict contains "trainer" elements, which have the following fields:
'status' : a string indicating either "omw" or "waiting"
'count'  : the number of trainers in the party
"""

team_msg = " or ".join(["**!team {0}**".format(team) for team in config['team_dict'].keys()])


@Clembot.event
async def on_ready():
    Clembot.owner = discord.utils.get(Clembot.get_all_members(), id=config["master"])
    await _print(Clembot.owner, _("Starting up..."))  # prints to the terminal or cmd prompt window upon successful connection to Discord
    Clembot.uptime = datetime.datetime.now()
    owners = []
    msg_success = 0
    msg_fail = 0
    guilds = len(Clembot.guilds)
    users = 0
    for guild in Clembot.guilds:
        users += len(guild.members)
        try:
            if guild.id not in guild_dict:
                guild_dict[guild.id] = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict': {}}
        except KeyError:
            guild_dict[guild.id] = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict': {}}

        owners.append(guild.owner)

    embed = discord.Embed(colour=discord.Colour.green(), description="Beep Beep! That's right!").set_author(name=_("Clembot Startup Notification"), icon_url=Clembot.user.avatar_url)
    embed.add_field(name="**Servers Connected**", value=_(" {guilds}").format(guilds=guilds), inline=True)
    embed.add_field(name="**Members Found**", value=_(" {members}").format(members=users), inline=True)
    await Clembot.owner.send( embed=embed)

    await maint_start()


@Clembot.event
async def on_guild_join(guild):
    owner = guild.owner
    guild_dict[guild.id] = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict': {}}
    await owner.send( _("Beep Beep! I'm Clembot, a Discord helper bot for Pokemon Go communities, and someone has invited me to your guild! Type **!help** to see a list of things I can do, and type **!configure** in any channel of your guild to begin!"))


@Clembot.event
async def on_guild_remove(guild):
    try:
        if guild.id in guild_dict:
            try:
                del guild_dict[guild.id]
            except KeyError:
                pass
    except KeyError:
        pass

@Clembot.event
async def on_member_join(member):
    """Welcome message to the guild and some basic instructions."""
    guild = member.guild
    if guild_dict[guild.id]['done'] == False or guild_dict[guild.id]['welcome'] == False:
        return

    # Build welcome message

    admin_message = _(" If you have any questions just ask an admin.")

    welcomemessage = _("Beep Beep! Welcome to {guild_name}, {new_member_name}! ")
    if guild_dict[guild.id]['team'] == True:
        welcomemessage += _("Set your team by typing {team_command}.").format(team_command=team_msg)
    welcomemessage += admin_message

    if guild_dict[guild.id]['welcomechan'] == "dm":
        await member.send( welcomemessage.format(guild_name=guild.name, new_member_name=member.mention))

    else:
        default = discord.utils.get(guild.channels, name=guild_dict[guild.id]['welcomechan'])
        if not default:
            pass
        else:
            await default.send(welcomemessage.format(guild_name=guild.name, new_member_name=member.mention))


"""

Admin commands

"""


async def _save():
    with tempfile.NamedTemporaryFile('wb', dir=os.path.dirname(os.path.join('data', 'guilddict')), delete=False) as tf:
        pickle.dump(guild_dict, tf, -1)
        tempname = tf.name
    try:
        os.remove(os.path.join('data', 'guilddict_backup'))
    except OSError as e:
        pass
    try:
        os.rename(os.path.join('data', 'guilddict'), os.path.join('data', 'guilddict_backup'))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
    os.rename(tempname, os.path.join('data', 'guilddict'))


@Clembot.command(pass_context=True)
@checks.is_owner()
async def reload_json(ctx):
    load_config()
    await ctx.message.add_reaction('?')


@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def exit(ctx):
    """Exit after saving.

    Usage: !exit.
    Calls the save function and quits the script."""
    try:
        await _save()
    except Exception as err:
        await _print(Clembot.owner, _("Error occured while trying to save!"))
        await _print(Clembot.owner, err)

    await ctx.message.channel.send( "Shutting down...")
    Clembot._shutdown_mode = 0
    await Clembot.logout()


@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def restart(ctx):
    """Restart after saving.

    Usage: !restart.
    Calls the save function and restarts Clembot."""

    # args = ctx.message.clean_content.split()
    # if len(args) > 1:
    #     bot_name = args[1]
    #     if bot_name.lower() != ctx.message.guild.me.display_name.lower():
    #         return
    # else:
    #     return
    try:
        await _save()
    except Exception as err:
        await _print(Clembot.owner, _("Error occured while trying to save!"))
        await _print(Clembot.owner, err)

    await ctx.message.channel.send( "Restarting...")
    Clembot._shutdown_mode = 26
    await Clembot.logout()


@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def save(ctx):
    """Save persistent state to file.

    Usage: !save
    File path is relative to current directory."""
    try:
        await _save()
        print("CONFIG SAVED")
    except Exception as err:
        await _print(Clembot.owner, _("Error occured while trying to save!"))
        await _print(Clembot.owner, err)


@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_guild=True)
async def outputlog(ctx):
    """Get current Clembot log.

    Usage: !outputlog
    Output is a link to hastebin."""
    with open(os.path.join('logs', 'clembot.log'), 'r') as logfile:
        logdata = logfile.read()
    logdata = logdata.encode('ascii', errors='replace').decode('utf-8')
    outputlog_message = await _send_message(ctx.message.channel, hastebin.post(logdata))
    await asyncio.sleep(20)
    await ctx.message.delete()
    await outputlog_message.delete()

@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def welcome(ctx, user: discord.Member = None):
    """Test welcome on yourself or mentioned member.

    Usage: !welcome [@member]"""
    if not user:
        user = ctx.message.author
    await on_member_join(user)


@Clembot.group(pass_context=True, hidden=True, name="set")
async def _set(ctx):
    """Changes a setting."""
    if ctx.invoked_subcommand is None:
        pages = bot.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)


@Clembot.group(pass_context=True, hidden=True, name="get")
@commands.has_permissions(manage_guild=True)
async def _get(ctx):
    """Changes a setting."""
    if ctx.invoked_subcommand is None:
        pages = bot.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)


@_set.command(pass_context=True, hidden=True, aliases=["config"])
@checks.is_owner()
async def _set_config(ctx, ):
    try:
        message = ctx.message
        args = ctx.message.content
        args_split = args.split(" ")
        del args_split[0]
        key = args_split[1]

        if len(args_split) >= 3:
            key = args_split[1]
            value = "".join(args_split[2:])
            gymsql.save_clembot_config(key,value)

        content = "Beep Beep! **{0}** has been set as **{1}**.".format(key, gymsql.find_clembot_config(key))

        await ctx.message.channel.send(content)
    except Exception as error:
        print(error)

@_get.command(pass_context=True, hidden=True, aliases=["config"])
@checks.is_owner()
async def _get_config(ctx):
    try:
        message = ctx.message
        args = ctx.message.content
        args_split = args.split()

        if len(args_split) > 2 :
            key = args_split[1]
            content = "Beep Beep! **{0}**, **{1}** has the current value as **{2}**.".format(ctx.message.author.display_name, key, gymsql.find_clembot_config(key))
        else:
            content = "Beep Beep! **{0}**, current values are :\n{1}".format(ctx.message.author.display_name, json.dumps(gymsql.find_all_clembot_config(), indent =2 ))
        del args_split[0]
        await _send_message(ctx.message.channel, content)
    except Exception as error:
        print(error)



@_get.command(pass_context=True, hidden=True, aliases=["configuration"])
@checks.is_owner()
async def _get_configuration(ctx):
    try:
        message = ctx.message
        guild_dict_temp = copy.deepcopy(guild_dict[ctx.message.guild.id])

        guild_dict_temp['raidchannel_dict'] = {}
        guild_dict_temp['wildreport_dict'] = {}
        guild_dict_temp['questreport_dict'] = {}
        guild_dict_temp['trainers'] = {}
        guild_dict_temp['notifications'] = {}
        guild_dict_temp['contest_channel'] = {}

        want_channel_name_list = []

        for channel_id in guild_dict_temp['want_channel_list']:

            channel = Clembot.get_channel(channel_id)
            if channel:
                want_channel_name_list.append("{0} = {1} ".format(channel_id, channel.name))

        guild_dict_temp['want_channel_name_list'] = want_channel_name_list
        guild_dict_temp['want_channel_list'] = {}

        print(json.dumps(guild_dict_temp, indent=2))


        content = ctx.message.guild.name + "\n" + json.dumps(guild_dict_temp, indent=2)
        await _send_message(ctx.message.channel, content)
    except Exception as error:
        print(error)
        await _send_error_message(ctx.message.channel, error)


@_set.command(pass_context=True, hidden=True, aliases=["bingo-event"])
@checks.is_owner()
async def _set_bingo_event(ctx):
    try:
        message = ctx.message
        args = ctx.message.content
        args_split = args.split(" ")
        del args_split[0]

        new_configuration={"bingo-event":None}

        if len(args_split) == 2:
            key = args_split[0]
            value = args_split[1]
            allowed_pokemon = gymsql.find_clembot_config("bingo-event-pokemon")
            if allowed_pokemon:
                if value in allowed_pokemon:
                    new_configuration[key] = value
                else:
                    return await message.channel.send("Beep Beep! **{0}** is not an eligible for **{1}**. Eligible options are : **{2}**.".format(value, "bingo-event" , allowed_pokemon))
            else :
                return await message.channel.send("Beep Beep! **bingo-event-pokemon** is not defined.")

        configuration = _update_guild_config(message.guild.id, new_configuration)

        message = ctx.message
        content = "Beep Beep! The bingo-event is set to **{0}**.".format(_get_guild_config_for(message.guild.id, "bingo-event"))

        await ctx.message.channel.send(content)
    except Exception as error:
        print(error)




@_set.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_guild=True)
async def prefix(ctx, prefix=None):
    """Changes guild prefix."""
    if prefix == "clear":
        prefix = None

    _set_prefix(Clembot, ctx.message.guild, prefix)

    if prefix is not None:
        await ctx.message.channel.send( "Prefix has been set to: `{}`".format(prefix))
    else:
        default_prefix = Clembot.config["default_prefix"]
        await ctx.message.channel.send( "Prefix has been reset to default: `{}`".format(default_prefix))

@_get.command()
@commands.has_permissions(manage_guild=True)
async def perms(ctx, channel_id = None):
    """Show Meowth's permissions for the guild and channel."""
    channel = discord.utils.get(ctx.bot.get_all_channels(), id=channel_id)
    guild = channel.guild if channel else ctx.guild
    channel = channel or ctx.channel
    guild_perms = guild.me.guild_permissions
    chan_perms = channel.permissions_for(guild.me)
    req_perms = discord.Permissions(268822608)

    embed = discord.Embed(colour=ctx.guild.me.colour)
    embed.set_author(name='Bot Permissions', icon_url="https://i.imgur.com/wzryVaS.png")

    wrap = functools.partial(textwrap.wrap, width=20)
    names = [wrap(channel.name), wrap(guild.name)]
    if channel.category:
        names.append(wrap(channel.category.name))
    name_len = max(len(n) for n in names)
    def same_len(txt):
        return '\n'.join(txt + ([' '] * (name_len-len(txt))))
    names = [same_len(n) for n in names]
    chan_msg = [f"**{names[0]}** \n{channel.id} \n"]
    guild_msg = [f"**{names[1]}** \n{guild.id} \n"]
    def perms_result(perms):
        data = []
        meet_req = perms >= req_perms
        result = "**PASS**" if meet_req else "**FAIL**"
        data.append(f"{result} - {perms.value} \n")
        true_perms = [k for k, v in dict(perms).items() if v is True]
        false_perms = [k for k, v in dict(perms).items() if v is False]
        req_perms_list = [k for k, v in dict(req_perms).items() if v is True]
        true_perms_str = '\n'.join(true_perms)
        if not meet_req:
            missing = '\n'.join([p for p in false_perms if p in req_perms_list])
            data.append(f"**MISSING** \n{missing} \n")
        if true_perms_str:
            data.append(f"**ENABLED** \n{true_perms_str} \n")
        return '\n'.join(data)
    guild_msg.append(perms_result(guild_perms))
    chan_msg.append(perms_result(chan_perms))
    embed.add_field(name='GUILD', value='\n'.join(guild_msg))
    if channel.category:
        cat_perms = channel.category.permissions_for(guild.me)
        cat_msg = [f"**{names[2]}** \n{channel.category.id} \n"]
        cat_msg.append(perms_result(cat_perms))
        embed.add_field(name='CATEGORY', value='\n'.join(cat_msg))
    embed.add_field(name='CHANNEL', value='\n'.join(chan_msg))

    try:
        await ctx.send(embed=embed)
    except discord.errors.Forbidden:
        # didn't have permissions to send a message with an embed
        try:
            msg = "I couldn't send an embed here, so I've sent you a DM"
            await ctx.send(msg)
        except discord.errors.Forbidden:
            # didn't have permissions to send a message at all
            pass
        await ctx.author.send(embed=embed)


@_get.command(pass_context=True, hidden=True, aliases=["bingo-event"])
@commands.has_permissions(manage_guild=True)
async def _get_bingo_event(ctx):
    try:
        message = ctx.message
        content = "Beep Beep! The bingo-event is set to **{0}**.".format(_get_guild_config_for(message.guild.id, "bingo-event"))

        await ctx.message.channel.send(content)
    except Exception as error:
        print(error)

@_get.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_guild=True)
async def prefix(ctx):
    """Get guild prefix."""
    prefix = _get_prefix(Clembot, ctx.message)
    await ctx.message.channel.send( "Prefix for this guild is: `{}`".format(prefix))



@_set.command()
async def silph(ctx, silph_user: str = None):
    """Links a server member to a Silph Road Travelers Card."""
    if not silph_user:
        await ctx.send(_('Silph Road Travelers Card cleared!'))
        try:
            del guild_dict[ctx.guild.id]['trainers'][ctx.author.id]['silphid']
        except:
            pass
        return

    silph_cog = ctx.bot.cogs.get('Silph')
    if not silph_cog:
        return await ctx.send(
            _("The Silph Extension isn't accessible at the moment, sorry!"))

    async with ctx.message.channel.typing():
        card = await silph_cog.get_silph_card(silph_user)
        if not card:
            return await ctx.send(_('Silph Card for {silph_user} not found.').format(silph_user=silph_user))

    if not card.discord_name:
        return await ctx.send(
            _('No Discord account found linked to this Travelers Card!'))

    if card.discord_name != str(ctx.author):
        return await ctx.send(
            _('This Travelers Card is linked to another Discord account!'))

    try:
        offset = ctx.bot.guild_dict[ctx.guild.id]['configure_dict']['settings']['offset']
    except KeyError:
        offset = None

    trainers = guild_dict[ctx.guild.id].get('trainers', {})
    author = trainers.get(ctx.author.id,{})
    author['silphid'] = silph_user
    trainers[ctx.author.id] = author
    guild_dict[ctx.guild.id]['trainers'] = trainers

    await ctx.send(
        _('This Travelers Card has been successfully linked to you!'), embed=card.embed(offset))




@_set.command()
async def pokebattler(ctx, pbid: int = 0):
    if not pbid:
        await ctx.send(_('Pokebattler ID cleared!'))
        try:
            del guild_dict[ctx.guild.id]['trainers'][ctx.author.id]['pokebattlerid']
        except:
            pass
        return
    trainers = guild_dict[ctx.guild.id].get('trainers',{})
    author = trainers.get(ctx.author.id,{})
    author['pokebattlerid'] = pbid
    trainers[ctx.author.id] = author
    guild_dict[ctx.guild.id]['trainers'] = trainers
    await ctx.send(_(f'Pokebattler ID set to {pbid}!'))



@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_guild=True)
async def announce(ctx, *, announce=None):
    """Repeats your message in an embed from Clembot.

    Usage: !announce [announcement]
    If the announcement isn't added at the same time as the command, Clembot will wait 3 minutes for a followup message containing the announcement."""
    message = ctx.message
    channel = message.channel
    guild = message.guild
    author = message.author
    if announce == None:
        announcewait = await channel.send( "I'll wait for your announcement!")
        announcemsg = await Clembot.wait_for('message', timeout=180, check=(lambda reply: reply.author == message.author))
        await announcewait.delete()
        if announcemsg != None:
            announce = announcemsg.content
            await announcemsg.delete()
        else:
            confirmation = await channel.send( "Beep Beep! You took too long to send me your announcement! Retry when you're ready.")
    embeddraft = discord.Embed(colour=guild.me.colour, description=announce)
    title = 'Announcement'
    if Clembot.user.avatar_url:
        embeddraft.set_author(name=title, icon_url=Clembot.user.avatar_url)
    else:
        embeddraft.set_author(name=title)
    draft = await channel.send( embed=embeddraft)

    reaction_list = ['❔', '✅', '❎']
    owner_msg_add = ''
    if checks.is_owner_check(ctx):
        owner_msg_add = "🌎 to send it to all guilds, "
        reaction_list.insert(0, '🌎')

    def check(reaction, user):
        if user.id == author.id:
            if (str(reaction.emoji) in reaction_list) and (reaction.message.id == rusure.id):
                return True
        return False

    rusure = await channel.send( _("That's what you sent, does it look good? React with {}❔ to send to another channel, ✅ to send it to this channel, or ❎ to cancel").format(owner_msg_add))
    res = await ask(rusure, channel, author.id, react_list=reaction_list)
    if res:
        await rusure .delete()
        if res[0].emoji == "❎":
            confirmation = await channel.send( _("Announcement Cancelled."))
            await draft .delete()
        elif res[0].emoji == "✅":
            confirmation = await channel.send( _("Announcement Sent."))
        elif res[0].emoji == "❔":
            channelwait = await channel.send( 'What channel would you like me to send it to?')
            channelmsg = await Clembot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
            if channelmsg.content.isdigit():
                sendchannel = Clembot.get_channel(int(channelmsg.content))
            elif channelmsg.raw_channel_mentions:
                sendchannel = Clembot.get_channel(channelmsg.raw_channel_mentions[0])
            else:
                sendchannel = discord.utils.get(guild.text_channels, name=channelmsg.content)
            if (channelmsg != None) and (sendchannel != None):
                announcement = await sendchannel.send( embed=embeddraft)
                confirmation = await channel.send( _('Announcement Sent.'))
            elif sendchannel == None:
                confirmation = await channel.send( "Beep Beep! That channel doesn't exist! Retry when you're ready.")
            else:
                confirmation = await channel.send( "Beep Beep! You took too long to send me your announcement! Retry when you're ready.")
            await channelwait .delete()
            await channelmsg .delete()
            await draft .delete()
        elif (res[0].emoji == '🌎') and checks.is_owner_check(ctx):
            failed = 0
            sent = 0
            count = 0
            recipients = {

            }

            embeddraft.set_footer(text="For support, contact us on our Discord guild. https://discord.gg/AUzEXRU")
            embeddraft.colour = discord.Colour.lighter_grey()
            for guild in Clembot.guilds:
                recipients[guild.name] = guild.owner
            for (guild, destination) in recipients.items():

                try:
                    await destination.send(embed=embeddraft)
                except discord.HTTPException:
                    failed += 1
                    logger.info('Announcement Delivery Failure: {} - {}'.format(destination.name, guild))
                else:
                    sent += 1
                count += 1
            logger.info('Announcement sent to {} server owners: {} successful, {} failed.'.format(count, sent, failed))
            confirmation = await channel.send('Announcement sent to {} server owners: {} successful, {} failed.'.format(count, sent, failed))
        await asyncio.sleep(10)
        await confirmation.delete()
    else:
        await rusure.delete()
        confirmation = await channel.send( _('Announcement Timed Out.'))
        await asyncio.sleep(10)
        await confirmation.delete()
    await asyncio.sleep(30)
    await message.delete()



@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_guild=True)
async def configure(ctx):
    'Clembot Configuration\n\n    Usage: !configure\n    Clembot will DM you instructions on how to configure Clembot for your server.\n    If it is not your first time configuring, you can choose a section to jump to.'
    guild = ctx.message.guild
    owner = ctx.message.author
    guild_dict_check = {
        'want_channel_list': [],
        'offset': 0,
        'welcome': False,
        'welcomechan': '',
        'wantset': False,
        'raidset': False,
        'wildset': False,
        'team': False,
        'want': False,
        'other': False,
        'done': False,
        'raidchannel_dict': {

        }
    }
    guild_dict_temp = copy.deepcopy(guild_dict[guild.id])
    firstconfig = False
    configcancel = False
    if guild_dict_check == guild_dict_temp:
        firstconfig = True
    try:
        if guild_dict_temp['other']:
            pass
        else:
            pass
    except KeyError:
        guild_dict_temp['other'] = False
    try:
        if guild_dict_temp['want_channel_list']:
            pass
        else:
            pass
    except KeyError:
        guild_dict_temp['want_channel_list'] = []
    configmessage = "That's Right! Welcome to the configuration for Clembot the Pokemon Go Helper Bot! I will be guiding you through some steps to get me setup on your server.\n\n**Role Setup**\nBefore you begin the configuration, please make sure my role is moved to the top end of the server role hierarchy. It can be under admins and mods, but must be above team ands general roles. [Here is an example](http://i.imgur.com/c5eaX1u.png)"
    if firstconfig == False:
        if guild_dict_temp['other']:
            configreplylist = ['all', 'team', 'welcome', 'main', 'regions', 'raid', 'wild', 'want', 'timezone', 'allmain']
            configmessage += "\n\n**Welcome Back**\nThis isn't your first time configuring. You can either reconfigure everything by replying with **all** or reply with one of the following to configure that specific setting:\n\n**all** - To redo configuration\n**team** - For Team Assignment configuration\n**welcome** - For Welcome Message configuration\n**main** - For main command configuration\n**raid** - for raid command configuration\n**wild** - for wild command configuration\n**regions** - For configuration of reporting channels or map links\n**want** - for want/unwant command configuration and channel\n**timezone** - For timezone configuration\n**allmain** - For main, regions, raid, wild, want, timezone configuration"
            configmessage += '\n\nReply with **cancel** at any time throughout the questions to cancel the configure process.'
            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=configmessage).set_author(name=_('Clembot Configuration - {0}').format(guild), icon_url=Clembot.user.avatar_url))
        else:
            configreplylist = ['all', 'team', 'welcome', 'main', 'allmain']
            configmessage += "\n\n**Welcome Back**\nThis isn't your first time configuring. You can either reconfigure everything by replying with **all** or reply with one of the following to configure that specific setting:\n\n**all** - To redo configuration\n**team** - For Team Assignment configuration\n**welcome** - For Welcome Message configuration\n**main** - For main command configuration\n**allmain** - For main, regions, raid, wild, want, timezone configuration"
            configmessage += '\n\nReply with **cancel** at any time throughout the questions to cancel the configure process.'
            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=configmessage).set_author(name=_('Clembot Configuration - {0}').format(guild), icon_url=Clembot.user.avatar_url))
        while True:
            def check(m):
                return m.guild == None and m.author == owner
            configreply = await Clembot.wait_for('message', check=check)
            if configreply.content.lower() in configreplylist:
                configgoto = configreply.content.lower()
                break
            elif configreply.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            elif configreply.content.lower() not in configreplylist:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with one of the choices above."))
                continue
    elif firstconfig == True:
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=configmessage).set_author(name=_('Clembot Configuration - {0}').format(guild), icon_url=Clembot.user.avatar_url))
    if (configcancel == False) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'team')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Team assignment allows users to assign their Pokemon Go team role using the **!team** command. If you have a bot that handles this already, you may want to disable this feature.\n\nIf you are to use this feature, ensure existing team roles are as follows: mystic, valor, instinct. These must be all lowercase letters. If they don't exist yet, I'll make some for you instead.\n\nRespond with: **N** to disable, **Y** to enable:").set_author(name='Team Assignments', icon_url=Clembot.user.avatar_url))
        while True:
            teamreply = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if teamreply.content.lower() == 'y':
                guild_dict_temp['team'] = True
                high_roles = []
                guild_roles = []
                lowercase_roles = []
                for role in guild.roles:
                    if role.name.lower() in config['team_dict'] and role.name not in guild_roles:
                        guild_roles.append(role.name)
                lowercase_roles = [element.lower() for element in guild_roles]
                for team in config['team_dict'].keys():
                    temp_role = discord.utils.get(guild.roles, name=team)
                    if temp_role == None:
                        try:
                            await guild.create_role(name=team, hoist=False, mentionable=True)
                        except discord.errors.HTTPException:
                            pass
                await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Team Assignments enabled!'))
                break
            elif teamreply.content.lower() == 'n':
                guild_dict_temp['team'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Team Assignments disabled!'))
                break
            elif teamreply.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure welcome
    if (configcancel == False) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'welcome')):
        welcomeconfig = 'I can welcome new members to the server with a short message. Here is an example:\n\n'
        if guild_dict_temp['team'] == True:
            welcomeconfig += _("Welcome to {server_name}, {owner_name.mention}! Set your team by typing '**!team mystic**' or '**!team valor**' or '**!team instinct**' without quotations. If you have any questions just ask an admin.").format(server_name=guild.name, owner_name=owner)
        else:
            welcomeconfig += _('Welcome to {server_name}, {owner_name.mention}! If you have any questions just ask an admin.').format(server_name=guild, owner_name=owner)
        welcomeconfig += '\n\nThis welcome message can be in a specific channel or a direct message. If you have a bot that handles this already, you may want to disable this feature.\n\nRespond with: **N** to disable, **Y** to enable:'
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=welcomeconfig).set_author(name='Welcome Message', icon_url=Clembot.user.avatar_url))
        while True:
            welcomereply = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if welcomereply.content.lower() == 'y':
                guild_dict_temp['welcome'] = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Welcome Message enabled!'))
                await owner.send(embed=discord.Embed(
                    colour=discord.Colour.lighter_grey(),
                    description=("Would you like a custom welcome message? "
                                 "You can reply with **N** to use the default message above or enter your own below.\n\n"
                                 "I can read all [discord formatting](https://support.discordapp.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline-) "
                                 "and I have the following template tags:\n\n"
                                 "**{@member}** - Replace member with user name or ID\n"
                                 "**{#channel}** - Replace channel with channel name or ID\n"
                                 "**{&role}** - Replace role name or ID (shows as @deleted-role DM preview)\n"
                                 "**{user}** - Will mention the new user\n"
                                 "**{server}** - Will print your server's name\n"
                                 "Surround your message with [] to send it as an embed. **Warning:** Mentions within embeds may be broken on mobile, this is a Discord bug.")).set_author(name="Welcome Message", icon_url=Clembot.user.avatar_url))
                while True:
                    welcomemsgreply = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and (message.author == owner)))
                    if welcomemsgreply.content.lower() == 'n':
                        guild_dict_temp['welcomemsg'] = 'default'
                        await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description="Default welcome message set"))
                        break
                    elif welcomemsgreply.content.lower() == "cancel":
                        configcancel = True
                        await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                        return
                    elif len(welcomemsgreply.content) > 500:
                        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Please shorten your message to less than 500 characters."))
                        continue
                    else:
                        welcomemessage, errors = do_template(welcomemsgreply.content, owner, guild)
                        if errors:
                            if welcomemessage.startswith("[") and welcomemessage.endswith("]"):
                                embed = discord.Embed(colour=guild.me.colour, description=welcomemessage[1:-1].format(user=owner.mention))
                                embed.add_field(name='Warning', value='The following could not be found:\n{}'.format('\n'.join(errors)))
                                await owner.send(embed=embed)
                            else:
                                await owner.send("{msg}\n\n**Warning:**\nThe following could not be found: {errors}".format(msg=welcomemessage, errors=', '.join(errors)))
                            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Please check the data given and retry a new welcome message, or reply with **N** to use the default."))
                            continue
                        else:
                            if welcomemessage.startswith("[") and welcomemessage.endswith("]"):
                                embed = discord.Embed(colour=guild.me.colour, description=welcomemessage[1:-1].format(user=owner.mention))
                                res = await ask(embed, owner, owner.id)
                            else:
                                res = await ask(welcomemessage.format(user=owner.mention), owner, owner.id)
                        if res == '❎':
                            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Please enter a new welcome message, or reply with **N** to use the default."))
                            continue
                        else:
                            guild_dict_temp['welcomemsg'] = welcomemessage
                            await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description="Welcome Message set to:\n\n{}".format(guild_dict_temp['welcomemsg'])))
                            break
                    break
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Which channel in your server would you like me to post the Welcome Messages? You can also choose to have them sent to the new member via Direct Message (DM) instead.\n\nRespond with: **channel-name** of a channel in your server or **DM** to Direct Message:").set_author(name="Welcome Message Channel", icon_url=Clembot.user.avatar_url))
                while True:
                    welcomechannelreply = await Clembot.wait_for('message',check=lambda message: message.guild == None and message.author == owner)
                    if welcomechannelreply.content.lower() == "dm":
                        guild_dict_temp['welcomechan'] = "dm"
                        await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description="Welcome DM set"))
                        break
                    elif " " in welcomechannelreply.content.lower():
                        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Channel names can't contain spaces, sorry. Please double check the name and send your response again."))
                        continue
                    elif welcomechannelreply.content.lower() == "cancel":
                        configcancel = True
                        await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                        return
                    else:
                        guild_channel_list = []
                        for channel in guild.channels:
                            guild_channel_list.append(channel.name)
                        diff = set([welcomechannelreply.content.lower().strip()]) - set(guild_channel_list)
                        if (not diff):
                            guild_dict_temp['welcomechan'] = welcomechannelreply.content.lower()
                            await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Welcome Channel set'))
                            break
                        else:
                            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="The channel you provided isn't in your server. Please double check your channel name and resend your response."))
                            continue
                    break
                break
            elif welcomereply.content.lower() == 'n':
                guild_dict_temp['welcome'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Welcome Message disabled!'))
                break
            elif welcomereply.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main
    if (configcancel == False) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'main') or (configgoto == 'allmain')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Main Functions include:\n - **!want** and creating tracked Pokemon roles \n - **!wild** Pokemon reports\n - **!raid** reports and channel creation for raid management.\nIf you don't want __any__ of the Pokemon tracking or Raid management features, you may want to disable them.\n\nRespond with: **N** to disable, or **Y** to enable:").set_author(name='Main Functions', icon_url=Clembot.user.avatar_url))
        while True:
            otherreply = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if otherreply.content.lower() == 'y':
                guild_dict_temp['other'] = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Main Functions enabled'))
                break
            elif otherreply.content.lower() == 'n':
                guild_dict_temp['other'] = False
                guild_dict_temp['raidset'] = False
                guild_dict_temp['wildset'] = False
                guild_dict_temp['wantset'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Main Functions disabled'))
                break
            elif otherreply.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main-raid
    if (configcancel == False) and (guild_dict_temp['other'] == True) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'raid') or (configgoto == 'allmain')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description='Do you want **!raid** reports enabled? If you want __only__ the **!wild** feature for reports, you may want to disable this.\n\nRespond with: **N** to disable, or **Y** to enable:').set_author(name='Raid Reports', icon_url=Clembot.user.avatar_url))
        while True:
            raidconfigset = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if raidconfigset.content.lower() == 'y':
                guild_dict_temp['raidset'] = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Raid Reports enabled'))
                break
            elif raidconfigset.content.lower() == 'n':
                guild_dict_temp['raidset'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Raid Reports disabled'))
                break
            elif raidconfigset.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main-wild
    if (configcancel == False) and (guild_dict_temp['other'] == True) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'wild') or (configgoto == 'allmain')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description='Do you want **!wild** reports enabled? If you want __only__ the **!raid** feature for reports, you may want to disable this.\n\nRespond with: **N** to disable, or **Y** to enable:').set_author(name='Wild Reports', icon_url=Clembot.user.avatar_url))
        while True:
            wildconfigset = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if wildconfigset.content.lower() == 'y':
                guild_dict_temp['wildset'] = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Wild Reports enabled'))
                break
            elif wildconfigset.content.lower() == 'n':
                guild_dict_temp['wildset'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Wild Reports disabled'))
                break
            elif wildconfigset.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main-channels
    if (configcancel == False) and (guild_dict_temp['other'] == True) and ((guild_dict_temp['wildset'] == True) or (guild_dict_temp['raidset'] == True)) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'regions') or (configgoto == 'allmain')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Pokemon raid or wild reports are contained within one or more channels. Each channel will be able to represent different areas/communities. I'll need you to provide a list of channels in your server you will allow reports from in this format: `channel-name, channel-name, channel-name`\n\nIf you do not require raid and wild reporting, you may want to disable this function.\n\n**Current Reporting Channels : **`{current_regions}` \n\n**New Reporting Channels** (Respond with: **N** to disable, or the **channel-name** list to enable, each seperated with a comma and space):".format(current_regions=", ".join(guild_dict[guild.id].get('city_channels',{}).keys()))).set_author(name='Reporting Channels', icon_url=Clembot.user.avatar_url))
        citychannel_dict = {

        }
        while True:
            citychannels = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if citychannels.content.lower() == 'n':
                guild_dict_temp['wildset'] = False
                guild_dict_temp['raidset'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Reporting Channels disabled'))
                break
            elif citychannels.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                citychannel_list = citychannels.content.lower().split(', ')
                guild_channel_list = []
                for channel in guild.channels:
                    guild_channel_list.append(channel.name)
                diff = set(citychannel_list) - set(guild_channel_list)
                if (not diff):
                    await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Reporting Channels enabled'))
                    break
                else:
                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The channel list you provided doesn't match with your servers channels.\n\nThe following aren't in your server: {invalid_channels}\n\nPlease double check your channel list and resend your reponse.").format(invalid_channels=', '.join(diff))))
                    continue
    if (configcancel == False) and (guild_dict_temp['other'] == True) and ((guild_dict_temp['wildset'] == True) or (guild_dict_temp['raidset'] == True)) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'regions') or (configgoto == 'allmain')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description='For each report, I generate Google Maps links to give people directions to raids and spawns! To do this, I need to know which suburb/town/region each report channel represents, to ensure we get the right location in the map. For each report channel you provided, I will need its corresponding general location using only letters and spaces, with each location seperated by a comma and space.\n\nExample: `kansas city mo, hull uk, sydney nsw australia`\n\nEach location will have to be in the same order as you provided the channels in the previous question.\n\n**Current Reporting Cities : **`{current_cities}` \n\n**New Reporting Cities** (Respond with: **location info, location info, location info** each matching the order of the previous channel list):'.format(current_cities=", ".join(guild_dict[guild.id].get('city_channels',{}).values()))).set_author(name='Report Locations', icon_url=Clembot.user.avatar_url))
        while True:
            cities = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if cities.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            city_list = cities.content.split(', ')
            if len(city_list) == len(citychannel_list):
                for i in range(len(citychannel_list)):
                    citychannel_dict[citychannel_list[i]] = city_list[i]
                break
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The number of cities doesn't match the number of channels you gave me earlier!\n\nI'll show you the two lists to compare:\n\n{channellist}\n{citylist}\n\nPlease double check that your locations match up with your provided channels and resend your response.").format(channellist=', '.join(citychannel_list), citylist=', '.join(city_list))))
                continue
        guild_dict_temp['city_channels'] = citychannel_dict
        await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Report Locations are set'))
        guild_catlist = []
        for cat in guild.categories:
            guild_catlist.append(cat.name)
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="How would you like me to categorize the raid channels I create? Your options are **none** if you don't want them categorized, **same** if you want them in the same category as the reporting channel, **region** if you want them categorized by region, or **level** if you want them categorized by level."))
        while True:
            category_dict = {}
            categories = await Clembot.wait_for('message', check=lambda message: message.guild == None and message.author == owner)
            if categories.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            elif categories.content.lower() == 'none':
                guild_dict_temp['categories'] = None
                break
            elif categories.content.lower() == 'same':
                guild_dict_temp['categories'] = 'same'
                break
            elif categories.content.lower() == 'region':
                while True:
                    guild_dict_temp['categories'] = 'region'
                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(),description="You have configured the following channels as raid reporting channels: {citychannel_list}\n\n**Current Regions : **`{current_regions}` \n\nIn the same order as they appear above, please give the names of the categories you would like raids reported in each channel to appear in. You do not need to use different categories for each channel, but they do need to be pre-existing categories. Separate each category name with a comma.".format(citychannel_list=citychannels.content.lower(), current_regions=", ".join(guild_dict[guild.id]['category_dict'].values()))))
                    regioncats = await Clembot.wait_for('message', check=lambda message: message.guild == None and message.author == owner)
                    if regioncats.content.lower() == "cancel":
                        configcancel = True
                        await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                        return
                    regioncat_list = regioncats.content.split(', ')
                    if len(regioncat_list) == len(citychannel_list):
                        catdiff = set(regioncat_list) - set(guild_catlist)
                        if (not catdiff):
                            for i in range(len(citychannel_list)):
                                category_dict[citychannel_list[i]] = regioncat_list[i]
                            break
                        else:
                            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(),description="The category list you provided doesn't match with your server's categories.\n\nThe following aren't in your server: {invalid_categories}\n\nPlease double check your category list and resend your response.".format(invalid_categories=', '.join(catdiff))))
                            continue
                    else:
                        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The number of categories doesn't match the number of channels you gave me earlier!\n\nI'll show you the two lists to compare:\n\n{channellist}\n{catlist}\n\nPlease double check that your categories match up with your provided channels and resend your response.").format(channellist=', '.join(citychannel_list), catlist=', '.join(regioncat_list))))
                        continue
                    break
            elif categories.content.lower() == 'level':
                guild_dict_temp['categories'] = 'level'
                while True:
                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(),description="Pokemon Go currently has six levels of raids. Please provide the names of the categories you would like each level of raid to appear in. Use the following order: 1, 2, 3, 4, 5, EX \n\n You do not need to use different categories for each level, but they do need to be pre-existing categories. Separate each category name with a comma."))
                    levelcats = await Clembot.wait_for('message', check=lambda message: message.guild == None and message.author == owner)
                    if levelcats.content.lower() == "cancel":
                        configcancel = True
                        await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                        return
                    levelcat_list = levelcats.content.split(', ')
                    if len(levelcat_list) == 6:
                        catdiff = set(levelcat_list) - set(guild_catlist)
                        if not catdiff:
                            level_list = ["1",'2','3','4','5',"EX"]
                            for i in range(6):
                                category_dict[level_list[i]] = levelcat_list[i]
                            break
                        else:
                            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(),description="The category list you provided doesn't match with your server's categories.\n\nThe following aren't in your server: {invalid_categories}\n\nPlease double check your category list and resend your response.".format(invalid_categories=', '.join(catdiff))))
                            continue
                    else:
                        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The number of categories doesn't match the number of raid levels! Make sure you give me exactly six categories, one for each level of raid. You can use the same category for multiple levels if you want, but I need to see six category names.")))
                        continue
            else:
                await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(),description="Sorry, I didn't understand your answer! Try again."))
                continue
            break
        guild_dict_temp['category_dict'] = category_dict
    if (configcancel == False) and (guild_dict_temp['other'] == True) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'want') or (configgoto == 'allmain')):

        existing_want_channel_list = []
        for channel_id in guild_dict_temp['want_channel_list']:
            try:
                want_channel = discord.utils.get(guild.channels, id=channel_id)
                existing_want_channel_list.append(want_channel.name)
            except:
                pass

        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="The **!want** and **!unwant** commands let you add or remove roles for Pokemon that will be mentioned in reports. This let you get notifications on the Pokemon you want to track. I just need to know what channels you want to allow people to manage their pokemon with the **!want** and **!unwant** command. If you pick a channel that doesn't exist, I'll make it for you.\n\nIf you don't want to allow the management of tracked Pokemon roles, then you may want to disable this feature.\n\n**Current Want Channels : **`{current_regions}` \n\n**New Want Channels** (Respond with: **N** to disable, or the **channel-name** list to enable, each seperated by a comma and space) :".format(current_regions=', '.join(existing_want_channel_list))).set_author(name='Pokemon Notifications', icon_url=Clembot.user.avatar_url))

        while True:
            wantchs = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if wantchs.content.lower() == 'n':
                guild_dict_temp['wantset'] = False
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='Pokemon Notifications disabled'))
                break
            elif wantchs.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                want_list = wantchs.content.lower().split(', ')
                guild_channel_list = []
                for channel in guild.channels:
                    guild_channel_list.append(channel.name)
                diff = set(want_list) - set(guild_channel_list)
                if (not diff):
                    guild_dict_temp['wantset'] = True
                    await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Pokemon Notifications enabled'))
                    while True:
                        try:
                            for want_channel_name in want_list:
                                want_channel = discord.utils.get(guild.channels, name=want_channel_name)
                                if want_channel == None:
                                    want_channel = await guild.create_text_channel(want_channel_name)
                                if want_channel.id not in guild_dict_temp['want_channel_list']:
                                    guild_dict_temp['want_channel_list'].append(want_channel.id)
                            break
                        except:
                            await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("You didn't give me enough permissions to create channels! Please check my permissions and that my role is above general roles. Let me know if you'd like me to check again.\n\nRespond with: **Y** to try again, or **N** to skip and create the missing channels yourself.")))
                            while True:
                                wantpermswait = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
                                if wantpermswait.content.lower() == 'n':
                                    break
                                elif wantpermswait.content.lower() == 'y':
                                    break
                                elif wantpermswait.content.lower() == 'cancel':
                                    configcancel = True
                                    await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                                    return
                                else:
                                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **Y** to try again, or **N** to skip and create the missing channels yourself."))
                                    continue
                            if wantpermswait.content.lower() == 'y':
                                continue
                            break
                else:
                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The channel list you provided doesn't match with your servers channels.\n\nThe following aren't in your server:{invalid_channels}\n\nPlease double check your channel list and resend your reponse.").format(invalid_channels=', '.join(diff))))
                    continue
                break
    if (configcancel == False) and (guild_dict_temp['other'] == True) and (guild_dict_temp['raidset'] == True) and ((firstconfig == True) or (configgoto == 'all') or (configgoto == 'timezone') or (configgoto == 'allmain')):
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("To help coordinate raids reports for you, I need to know what timezone you're in! The current 24-hr time UTC is {utctime}. How many hours off from that are you?\n\nRespond with: A number from **-12** to **12**:").format(utctime=strftime('%H:%M', time.gmtime()))).set_author(name='Timezone Configuration', icon_url=Clembot.user.avatar_url))
        while True:
            offsetmsg = await Clembot.wait_for('message', check=(lambda message: (message.guild == None) and message.author == owner))
            if offsetmsg.content.lower() == 'cancel':
                configcancel = True
                await owner.send(embed=discord.Embed(colour=discord.Colour.red(), description='**CONFIG CANCELLED!**\n\nNo changes have been made.'))
                return
            else:
                try:
                    offset = float(offsetmsg.content)
                except ValueError:
                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I couldn't convert your answer to an appropriate timezone!.\n\nPlease double check what you sent me and resend a number strarting from **-12** to **12**."))
                    continue
                if (not ((- 12) <= offset <= 14)):
                    await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I couldn't convert your answer to an appropriate timezone!.\n\nPlease double check what you sent me and resend a number strarting from **-12** to **12**."))
                    continue
                else:
                    break
        guild_dict_temp['offset'] = offset
        await owner.send(embed=discord.Embed(colour=discord.Colour.green(), description='Timezone set'))
    guild_dict_temp['done'] = True
    if configcancel == False:
        guild_dict[guild.id] = guild_dict_temp
        await owner.send(embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Alright! Your settings have been saved and I'm ready to go! If you need to change any of these settings, just type **!configure** in your server again."))



"""

End admin commands

"""


async def _uptime(bot):
    """Shows info about Clembot"""
    time_start = bot.uptime
    time_now = datetime.datetime.now()
    ut = (relativedelta(time_now, time_start))
    ut.years, ut.months, ut.days, ut.hours, ut.minutes
    if ut.years >= 1:
        uptime = "{yr}y {mth}m {day}d {hr}:{min}".format(yr=ut.years, mth=ut.months, day=ut.days, hr=ut.hours, min=ut.minutes)
    elif ut.months >= 1:
        uptime = "{mth}m {day}d {hr}:{min}".format(mth=ut.months, day=ut.days, hr=ut.hours, min=ut.minutes)
    elif ut.days >= 1:
        uptime = "{day} days {hr} hrs {min} mins".format(day=ut.days, hr=ut.hours, min=ut.minutes)
    elif ut.hours >= 1:
        uptime = "{hr} hrs {min} mins {sec} secs".format(hr=ut.hours, min=ut.minutes, sec=ut.seconds)
    else:
        uptime = "{min} mins {sec} secs".format(min=ut.minutes, sec=ut.seconds)

    return uptime


@Clembot.command(pass_context=True, hidden=True, name="uptime")
async def cmd_uptime(ctx):
    """Shows Clembot's uptime"""
    guild = ctx.message.guild
    channel = ctx.message.channel
    embed_colour = guild.me.colour or discord.Colour.lighter_grey()
    uptime_str = await _uptime(Clembot)
    embed = discord.Embed(colour=embed_colour, icon_url=Clembot.user.avatar_url)
    embed.add_field(name="Uptime", value=uptime_str)
    try:
        await channel.send( embed=embed)
    except discord.HTTPException:
        await channel.send( "I need the `Embed links` permission to send this")


@Clembot.group(pass_context=True, hidden=True)
async def about(ctx):
    try:
        if ctx.invoked_subcommand is not None:
            return

        if len(ctx.message.mentions) > 0:
            author = ctx.message.mentions[0]
            if author:
                await _about_user(author, ctx.message.channel)
                return

        """Shows info about Clembot"""
        original_author_repo = "https://github.com/FoglyOgly"
        original_author_name = "FoglyOgly"

        author_repo = "https://github.com/TrainingB"
        author_name = "TrainingB"
        bot_repo = author_repo + "/Clembot"
        guild_url = "https://discord.gg/{invite}".format(invite=INVITE_CODE)
        owner = Clembot.owner
        channel = ctx.message.channel
        uptime_str = await _uptime(Clembot)
        yourguild = ctx.message.guild.name
        yourmembers = len(ctx.message.guild.members)
        embed_colour = ctx.message.guild.me.colour or discord.Colour.lighter_grey()

        about = ("I'm Clembot! A Pokemon Go helper bot for Discord!\n\n"
                 "[{author_name}]({author_repo}) has been working on me and I am evovled from [{original_author_name}]({original_author_repo})'s famous bot Meowth!\n\n"
                 "[Join our guild]({guild_invite}) if you have any questions or feedback.\n\n"
                 "".format(original_author_name=original_author_name, original_author_repo=original_author_repo, author_name=author_name, author_repo=author_repo, guild_invite=guild_url))

        member_count = 0
        guild_count = 0
        for guild in Clembot.guilds:
            guild_count += 1
            member_count += len(guild.members)

        embed = discord.Embed(title="For support, Click here to contact Clembot's discord guild.", url="https://discord.gg/" + INVITE_CODE, colour=embed_colour, icon_url=Clembot.user.avatar_url)
        embed.add_field(name="About Clembot", value=about, inline=False)
        embed.add_field(name="Owner", value=owner)
        if guild_count > 1:
            embed.add_field(name="Servers", value=guild_count)
            embed.add_field(name="Members", value=member_count)
        embed.add_field(name="Your Server", value=yourguild)
        embed.add_field(name="Your Members", value=yourmembers)
        embed.add_field(name="Uptime", value=uptime_str)
        embed.set_footer(text="This message will be auto-deleted after 40 seconds".format(invite=INVITE_CODE))

        try:
            about_msg = await channel.send( embed=embed)
        except discord.HTTPException:
            about_msg = await channel.send( "I need the `Embed links` permission to send this")

        await asyncio.sleep(40)
        await about_msg.delete()
        await ctx.message.delete()
    except Exception as error:
        print(error)

@about.command(pass_context=True)
async def me(ctx):
    author = ctx.message.author

    await _about_user(author, ctx.message.channel)


async def _about_user(user, target_channel):
    text = []
    for role in user.roles:
        text.append(role.name)

    raid_embed = discord.Embed(colour=discord.Colour.gold())
    raid_embed.add_field(name="**Username:**", value=_("{option}").format(option=user.name))
    raid_embed.add_field(name="**Roles:**", value=_("{roles}").format(roles=" \ ".join(text)))
    raid_embed.set_thumbnail(url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=user, format="jpg")))
    await target_channel.send(embed=raid_embed)


@Clembot.command(pass_context=True, hidden=True, aliases=["about-me"])
async def _about_me(ctx):
    author = ctx.message.author

    await _about_user(author, ctx.message.channel)


@Clembot.command(pass_context=True, hidden=True)
async def analyze(ctx, *, count: str = None):
    limit = 200

    try:
        if count:
            if count.isdigit():
                count = int(count)
                limit = count

        channel = ctx.message.channel
        await ctx.message .delete()

        map_users = {}
        counter = 1
        async for message in channel.history(limit=None):
            if len(message.attachments) > 0:
                map_users.update({message.author.mention: map_users.get(message.author.mention, 0) + 1})
                counter = counter + 1
                if counter > limit:
                    break

        sorted_map = dict(sorted(map_users.items(), key=lambda x: x[1], reverse=True))

        text = json.dumps(sorted_map, indent=4)

        parts = [text[i:i + 1800] for i in range(0, len(text), 1800)]

        await ctx.message.author.send(content=f"Results from {ctx.message.guild.name}.{ctx.message.channel.name} requested by {ctx.message.author.display_name}")
        for message_text in parts:
            await ctx.message.author.send( content=message_text)

    except Exception as error:
        await ctx.message.author.send(content=error)
        print(error)


@Clembot.command(pass_context=True, hidden=True)
@checks.teamset()
@checks.nonraidchannel()
async def team(ctx):
    """Set your team role.

    Usage: !team <team name>
    The team roles have to be created manually beforehand by the guild administrator."""

    guild = ctx.message.guild
    toprole = guild.me.top_role.name
    position = guild.me.top_role.position
    high_roles = []

    for team in config['team_dict'].keys():
        temp_role = discord.utils.get(ctx.message.guild.roles, name=team)
        if temp_role.position > position:
            high_roles.append(temp_role.name)

    if high_roles:
        await ctx.message.channel.send( _("Beep Beep! My roles are ranked lower than the following team roles: **{higher_roles_list}**\nPlease get an admin to move my roles above them!").format(higher_roles_list=', '.join(high_roles)))
        return

    role = None
    team_split = ctx.message.clean_content.lower().split()
    del team_split[0]
    entered_team = team_split[0]
    role = discord.utils.get(ctx.message.guild.roles, name=entered_team)

    # Check if user already belongs to a team role by
    # getting the role objects of all teams in team_dict and
    # checking if the message author has any of them.
    for team in config['team_dict'].keys():
        temp_role = discord.utils.get(ctx.message.guild.roles, name=team)
        # If the role is valid,
        if temp_role:
            # and the user has this role,
            if temp_role in ctx.message.author.roles:
                # then report that a role is already assigned
                await _send_error_message (ctx.message.channel, _("Beep Beep! You already have a team role!"))
                return
        # If the role isn't valid, something is misconfigured, so fire a warning.
        else:
            await _send_error_message (ctx.message.channel,_("Beep Beep! **{team_role}** is not configured as a role on this guild. Please contact an admin for assistance.").format(team_role=team))
    # Check if team is one of the three defined in the team_dict

    if entered_team not in config['team_dict'].keys():
        await _send_error_message (ctx.message.channel, _("Beep Beep! **{entered_team}** isn't a valid team! Try {available_teams}").format(entered_team=entered_team, available_teams=team_msg))
        return
    # Check if the role is configured on the guild
    elif role is None:
        await _send_error_message(ctx.message.channel, _("Beep Beep! The **{entered_team}** role isn't configured on this guild! Contact an admin!").format(entered_team=entered_team))
    else:
        try:
            await ctx.message.author.add_roles(role)
            await _send_message(ctx.message.channel, _("Beep Beep! Added **{member}** to Team **{team_name}**!").format(member=ctx.message.author.mention, team_name=role.name.capitalize()))
        except discord.Forbidden:
            await _send_error_message(ctx.message.channel, _("Beep Beep! I can't add roles!"))


@Clembot.command(pass_context=True, hidden=True)
async def sprite(ctx):
    message = ctx.message
    guild = message.guild
    channel = message.channel
    want_split = message.clean_content.lower().split()
    del want_split[0]
    entered_want = " ".join(want_split)
    if entered_want not in pkmn_info['pokemon_list']:
        await channel.send( _("Beep Beep! {member} No sprite found!").format(member=ctx.message.author.mention))
        return

    want_number = pkmn_info['pokemon_list'].index(entered_want) + 1
    want_img_url = get_pokemon_image_url(want_number)  # This part embeds the sprite
    want_embed = discord.Embed(colour=guild.me.colour)
    want_embed.set_thumbnail(url=want_img_url)
    await channel.send( embed=want_embed)

def _want_roles(guild):
    cleancount = 0
    allowed_want_list = []
    for role in guild.roles:
        if role.name in pkmn_info['pokemon_list']:
            allowed_want_list.append(role.name)
    return allowed_want_list



@Clembot.command()
@commands.has_permissions(manage_guild=True)
async def cleanroles(ctx):
    cleancount = 0
    for role in ctx.guild.roles:
        if role.members == [] and role.name in get_raidlist():
            await role.delete()
            cleancount += 1
    await ctx.message.channel.send("Removed {cleancount} empty roles".format(cleancount=cleancount))



@Clembot.command(pass_context=True, hidden=True)
@checks.wantset()
@checks.nonraidchannel()
@checks.wantchannel()
async def want(ctx):
    """Add a Pokemon to your wanted list.

    Usage: !want <species>
    Clembot will mention you if anyone reports seeing
    this species in their !wild or !raid command."""

    """Behind the scenes, Clembot tracks user !wants by
    creating a guild role for the Pokemon species, and
    assigning it to the user."""
    message = ctx.message
    guild = message.guild
    channel = message.channel
    want_split = message.clean_content.lower().split()
    del want_split[0]

    if len(want_split) < 1:
        help_embed = get_help_embed("Subscribe for Pokemon notifications.", "!want pokemon", "Available Roles: ", _want_roles(ctx.message.guild), "message")
        await ctx.channel.send(embed=help_embed)
        return


    entered_want = " ".join(want_split)
    old_entered_want = entered_want
    if entered_want not in pkmn_info['pokemon_list']:
        entered_want = await autocorrect(entered_want, message.channel, message.author)

    if entered_want == None:
        return


    role = discord.utils.get(guild.roles, name=entered_want)
    # Create role if it doesn't exist yet
    if role is None:
        if entered_want not in get_raidlist():
            if entered_want not in pkmn_info['pokemon_list']:
                await _send_error_message(channel, _("Beep Beep! **{member}** {entered_want} is not a pokemon. Please use a valid pokemon name.").format(member=ctx.message.author.mention, entered_want=edisplay_name))
            else:
                await _send_error_message(channel, _("Beep Beep! **{member}** only specific pokemon are allowed to be notified!\nYou can type **!want** to see available pokemon for subscription. Please contact an admin if you want **{entered_want}** to be included.").format(member=ctx.message.author.display_name, entered_want=entered_want))
            return
        role = await guild.create_role(name=entered_want, hoist=False, mentionable=True)
        await asyncio.sleep(0.5)

    # If user is already wanting the Pokemon,
    # print a less noisy message
    if role in ctx.message.author.roles:
        await channel.send("Beep Beep! **{member}**, I already know you want **{pokemon}**!".format(member=ctx.message.author.display_name, pokemon=entered_want.capitalize()))
    else:
        await ctx.message.author.add_roles(role)
        want_number = pkmn_info['pokemon_list'].index(entered_want) + 1
        want_img_url = "https://raw.githubusercontent.com/TrainingB/Clembot/master/images/pkmn/{0}_.png".format(str(want_number).zfill(3))  # This part embeds the sprite
        want_img_url = get_pokemon_image_url(want_number)  # This part embeds the sprite
        want_embed = discord.Embed(colour=guild.me.colour)
        want_embed.set_thumbnail(url=want_img_url)
        await channel.send(_("Beep Beep! Got it! {member} wants {pokemon}").format(member=ctx.message.author.mention, pokemon=entered_want.capitalize()), embed=want_embed)




@Clembot.group(pass_context=True, hidden=True)
@checks.wantset()
@checks.nonraidchannel()
@checks.wantchannel()
async def unwant(ctx):
    """Remove a Pokemon from your wanted list.

    Usage: !unwant <species>
    You will no longer be notified of reports about this Pokemon."""

    """Behind the scenes, Clembot removes the user from
    the guild role for the Pokemon species."""
    message = ctx.message
    guild = message.guild
    channel = message.channel
    if ctx.invoked_subcommand is None:
        unwant_split = message.clean_content.lower().split()
        del unwant_split[0]
        entered_unwant = " ".join(unwant_split)
        role = discord.utils.get(guild.roles, name=entered_unwant)
        if role is None:
            await channel.send(_("Beep Beep! {member} unwant works on only specific pokemon! Please contact an admin if you want {entered_want} to be included.").format(member=ctx.message.author.mention, entered_want=entered_unwant))
            return

        if entered_unwant not in pkmn_info['pokemon_list']:
            await channel.send(spellcheck(entered_unwant))
            return
        else:
            # If user is not already wanting the Pokemon,
            # print a less noisy message
            if role not in ctx.message.author.roles:
                await message.add_reaction('✅')
            else:
                await message.author.remove_roles(role)
                unwant_number = pkmn_info['pokemon_list'].index(entered_unwant) + 1
                await message.add_reaction('✅')



@unwant.command(pass_context=True, hidden=True)
@checks.wantset()
@checks.nonraidchannel()
@checks.wantchannel()
async def all(ctx):
    """Remove all Pokemon from your wanted list.

    Usage: !unwant all
    All Pokemon roles are removed."""

    """Behind the scenes, Clembot removes the user from
    the guild role for the Pokemon species."""
    message = ctx.message
    guild = message.guild
    channel = message.channel
    author = message.author
    await channel.trigger_typing()
    count = 0
    roles = author.roles
    remove_roles = []
    for role in roles:
        if role.name in pkmn_info['pokemon_list']:
            remove_roles.append(role)
            await message.author.remove_roles(role)
            count += 1
        continue

    await author.remove_roles(*remove_roles)

    if count == 0:
        await channel.send( content=_("{0}, you have no pokemon in your want list.").format(author.mention, count))
        return
    await channel.send( content=_("{0}, I've removed {1} pokemon from your want list.").format(author.mention, count))
    return


@Clembot.command(pass_context=True, hidden=True, aliases=["w"])
@checks.wildset()
@checks.citychannel()
async def wild(ctx):
    """Report a wild Pokemon spawn location.

    Usage: !wild <species> <location>
    Clembot will insert the details (really just everything after the species name) into a
    Google maps link and post the link to the same channel the report was made in."""
    await _wild(ctx.message)


async def _wild(message):
    try:
        timestamp = (message.created_at + datetime.timedelta(hours=guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))
        wild_split = message.clean_content.lower().split()
        del wild_split[0]
        if len(wild_split) <= 1:
            await message.channel.send( _("Beep Beep! Give more details when reporting! Usage: **!wild <pokemon name> <location>**"))
            return
        else:
            content = ' '.join(wild_split)
            entered_wild = content.split(' ', 1)[0]
            entered_wild = get_name(entered_wild).lower() if entered_wild.isdigit() else entered_wild.lower()
            wild_details = content.split(' ', 1)[1]
            if entered_wild not in pkmn_info['pokemon_list']:
                entered_wild2 = ' '.join([content.split(' ', 2)[0], content.split(' ', 2)[1]]).lower()
                if entered_wild2 in pkmn_info['pokemon_list']:
                    entered_wild = entered_wild2
                    try:
                        wild_details = content.split(' ', 2)[2]
                    except IndexError:
                        await message.channel.send( _("Beep Beep! Give more details when reporting! Usage: **!wild <pokemon name> <location>**"))
                        return
            wild_gmaps_link = create_gmaps_query(wild_details, message.channel)
            rgx = '[^a-zA-Z0-9]'
            pkmn_match = next((p for p in pkmn_info['pokemon_list'] if re.sub(rgx, '', p) == re.sub(rgx, '', entered_wild)), None)

            if pkmn_match:
                entered_wild = pkmn_match
            else:
                entered_wild = await autocorrect(entered_wild, message.channel, message.author)
            wild = discord.utils.get(message.guild.roles, name=entered_wild)

            if wild is None:
                title_or_mention = "**{0}**".format(entered_wild.capitalize())
            else:
                title_or_mention = "**{0}**".format(wild.mention)

            # if wild is None:
            #     wild = await guild.create_role(name=entered_wild, hoist=False, mentionable=True)
            #     await asyncio.sleep(0.5)

            wild_number = pkmn_info['pokemon_list'].index(entered_wild) + 1
            expiremsg = _('**This {pokemon} has despawned!**').format(pokemon=entered_wild.title())

            wild_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(wild_number).zfill(3))

            wild_img_url = get_pokemon_image_url(wild_number)  # This part embeds the sprite
            wild_embed = discord.Embed(title=_("Beep Beep! Click here for my directions to the wild {pokemon}!").format(pokemon=entered_wild.capitalize()), description=_("Ask {author} if my directions aren't perfect!").format(author=message.author.display_name), url=wild_gmaps_link, colour=message.guild.me.colour)
            wild_embed.add_field(name=_('**Details:**'), value=_('{pokemon} ({pokemonnumber}) {type}').format(pokemon=entered_wild.capitalize(), pokemonnumber=str(wild_number), type=''.join(get_type(message.guild, wild_number))), inline=False)
            # wild_embed.add_field(name='**Reactions:**', value= "🏎: I'm on my way!\n 💨 The Pokemon despawned!".format(parse_emoji(message.guild, ':dash:')))
            wild_embed.add_field(name='**Reactions:**', value="🏎: I'm on my way!\n💨: The Pokemon despawned!")

            if message.author.avatar:
                wild_embed.set_footer(text=_('Reported by @{author} - {timestamp}').format(author=message.author.display_name, timestamp=timestamp), icon_url='https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}'.format(user=message.author, format='jpg', size=32))
            else:
                wild_embed.set_footer(text=_('Reported by @{author} - {timestamp}').format(author=message.author.display_name, timestamp=timestamp), icon_url=message.author.default_avatar_url)
            wild_embed.set_thumbnail(url=wild_img_url)
            wildreportmsg = await message.channel.send(content=_("Beep Beep! Wild {pokemon} reported by {member}! Details: {location_details}").format(pokemon=title_or_mention, member=message.author.mention, location_details=wild_details) , embed=wild_embed)

            await asyncio.sleep(0.25)
            await wildreportmsg.add_reaction('🏎')
            await asyncio.sleep(0.25)
            await wildreportmsg.add_reaction('💨')
            await asyncio.sleep(0.25)
            wild_dict = copy.deepcopy(guild_dict[message.guild.id].get('wildreport_dict',{}))
            wild_dict[wildreportmsg.id] = {
                'exp':time.time() + 3600,
                'expedit': {"content":wildreportmsg.content,"embedcontent":expiremsg},
                'reportmessage':message.id,
                'reportchannel':message.channel.id,
                'reportauthor':message.author.id,
                'location':wild_details,
                'pokemon':entered_wild,
                'omw': []
            }
            guild_dict[message.guild.id]['wildreport_dict'] = wild_dict

            record_reported_by(message.guild.id, message.author.id, 'wild_reports')

    except Exception as error:
        print(error)



@Clembot.event
async def on_raw_reaction_add(emoji, message_id=None, channel_id=None, user_id=None):
    if not message_id or not channel_id or not user_id:
        return
    channel = Clembot.get_channel(channel_id)
    message = await channel.get_message(message_id)
    guild = message.guild
    user = guild.get_member(user_id)
    try:
        if message_id in guild_dict[guild.id].setdefault('wildreport_dict',{}) and user_id != Clembot.user.id:
            wild_dict = guild_dict[guild.id].setdefault('wildreport_dict',{})[message_id]
            if str(emoji) == '🏎':
                wild_dict['omw'].append(user.mention)
                guild_dict[guild.id]['wildreport_dict'][message_id] = wild_dict
            elif str(emoji) == '💨':
                if wild_dict['omw']:
                    await channel.send(f"{' '.join(wild_dict['omw'])}: the {wild_dict['pokemon'].title()} has despawned!")
                await expire_wild(message)

        if channel.id in guild_dict[guild.id]['raidchannel_dict'] and message.id == guild_dict[guild.id]['raidchannel_dict'][channel.id]['ctrsmessage'] and user_id != Clembot.user.id:
            ctrs_dict = guild_dict[guild.id]['raidchannel_dict'][channel.id]['ctrs_dict']
            for i in ctrs_dict:
                if ctrs_dict[i]['emoji'] == str(emoji):
                    newembed = ctrs_dict[i]['embed']
                    moveset = i
                    break
            else:
                return
            await message.edit(embed=newembed)
            await message.remove_reaction(emoji, user)
            guild_dict[guild.id]['raidchannel_dict'][channel.id]['moveset'] = moveset
    except Exception as error:
        logger.error(error)

async def expire_wild(message):
    guild = message.channel.guild
    channel = message.channel
    wild_dict = guild_dict[guild.id]['wildreport_dict']
    try:
        expiremsg = _('**This {pokemon} has despawned!**').format(pokemon=guild_dict[guild.id]['wildreport_dict'][message.id]['pokemon'].title())
        await message.edit(embed=discord.Embed(description=expiremsg, colour=message.embeds[0].colour.value))
        await message.clear_reactions()
    except discord.errors.NotFound:
        pass
    try:
        user_message = await channel.get_message(wild_dict[message.id]['reportmessage'])
        await user_message.delete()
    except discord.errors.NotFound:
        pass
    del guild_dict[guild.id]['wildreport_dict'][message.id]

async def autocorrect(entered_word, destination, author):
    msg = _("Beep Beep! **{word}** isn't a Pokemon!").format(word=entered_word.title())
    if spellcheck(entered_word) and (spellcheck(entered_word) != entered_word):
        msg += _(' Did you mean **{correction}**?').format(correction=spellcheck(entered_word).title())
        question = await destination.send(msg)
        if author:
            try:
                timeout = False
                res, reactuser = await ask(question, destination, author.id)
            except TypeError:
                timeout = True
            await question.delete()
            if timeout or res.emoji == '❎':
                return
            elif res.emoji == '✅':
                return spellcheck(entered_word)
            else:
                return
        else:
            return
    else:
        question = await destination.send(msg)
        return


@Clembot.command(pass_context=True)
async def hide(ctx):
    await _hideChannel(ctx.message.channel)


async def _hideChannel(channel):
    try:
        print("hide: {channel}".format(channel=channel.name))

        readable = discord.PermissionOverwrite()
        readable.read_messages = False

        await Clembot.edit_channel_permissions(channel, channel.guild.default_role, readable)
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True)
async def lock(ctx):
    await _lockChannel(ctx.message.channel)


def _readOnly():
    readable = discord.PermissionOverwrite()
    readable.read_messages = True

    return readable


async def _lockChannel(channel):
    try:
        writeable = discord.PermissionOverwrite()
        writeable.send_messages = True

        readable = discord.PermissionOverwrite()
        readable.read_messages = True
        readable.send_messages = False

        await Clembot.edit_channel_permissions(channel, channel.guild.me, writeable)
        await Clembot.edit_channel_permissions(channel, channel.guild.default_role, readable)
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True)
async def unlock(ctx):
    await _unlockChannel(ctx.message.channel)


async def _unlockChannel(channel):
    try:
        writeable = discord.PermissionOverwrite()
        writeable.send_messages = True
        writeable.read_messages = True
        await Clembot.edit_channel_permissions(channel, channel.guild.default_role, writeable)
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True)
@commands.has_permissions(manage_guild=True)
async def contest(ctx):
    await _contest(ctx.message)
    return


# ---------------------------- Raid Notification Module --------------------------------------

def _reset_role_notification_map(guild_id):
    notifications_map = {'notifications': {'roles': [], 'gym_role_map': {}}}
    guild_dict[guild_id].update(notifications_map)


async def _get_roles_mention_for_notifications(guild, gym_code):
    role_ids = []

    channel_mentions = []

    if 'notifications' in guild_dict[guild.id]:
        role_id = guild_dict[guild.id]['notifications']['gym_role_map'].get(gym_code, None)

        if role_id in guild_dict[guild.id]['notifications']['roles']:
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                channel_mentions.append(role.mention)

    return channel_mentions


def _get_role_for_notification(guild_id, gym_code):
    role_id = None
    if 'notifications' in guild_dict[guild_id]:
        role_id = guild_dict[guild_id]['notifications']['gym_role_map'].get(gym_code, None)

        if role_id in guild_dict[guild_id]['notifications']['roles']:
            return role_id

    return None


def _is_role_registered(guild_id, role_id):
    if role_id in guild_dict[guild_id]['notifications']['roles']:
        return True

    return False


def add_notifications_guild_dict(guild_id):
    if 'notifications' not in guild_dict[guild_id]:
        _reset_role_notification_map(guild_id)

        return
    return


@Clembot.command(pass_context=True, aliases=["reset-register"])
@commands.has_permissions(manage_guild=True)
async def _reset_register(ctx):
    _reset_role_notification_map(ctx.message.guild.id)
    await ctx.message.channel.send( "Beep Beep! The notifications register has been reset!")


@Clembot.command(pass_context=True, aliases=["show-register"])
@commands.has_permissions(manage_guild=True)
async def _show_register(ctx):

    add_notifications_guild_dict(ctx.guild.id)

    notifications = copy.deepcopy(guild_dict[ctx.guild.id]['notifications'])
    new_notifications_map = {'notifications': {'roles': [], 'gym_role_map': {}}}
    print(notifications)
    role_map = {}


    for role_id in notifications['roles']:
        role = discord.utils.get(ctx.message.guild.roles, id=role_id)
        if role:
            new_notifications_map['notifications']['roles'].append(role.name)
            role_map[role_id] = role.name

    await _send_message(ctx.message.channel, "**Registered Roles**\n{}".format(json.dumps(new_notifications_map['notifications']['roles'], indent=4, sort_keys=True)))

    role_gym_map = {}


    for gym_code in notifications['gym_role_map'].keys():
        role_name = role_map[notifications['gym_role_map'][gym_code]]

        role_gym_map.setdefault(role_name, []).append(gym_code)

    await _send_message(ctx.message.channel, "**Registered Gyms**\n{}".format(json.dumps(role_gym_map, indent=4, separators=[',',':'],sort_keys=True)))



def _get_subscription_roles(guild):

    add_notifications_guild_dict(guild.id)

    notifications = copy.deepcopy(guild_dict[guild.id]['notifications'])
    role_list = []

    for role_id in notifications['roles']:
        role = discord.utils.get(guild.roles, id=role_id)
        if role:
            role_list.append(role.name)

    return role_list


@Clembot.command(pass_context=True, hidden=True, aliases=["find-gym"])
@commands.has_permissions(manage_guild=True)
async def find_gym(ctx):
    await _find_gym(ctx.message)


async def _find_gym(message):

    command_option = "-all"
    is_option_all = False
    try :
        message = message

        args = message.content
        args_split = args.split()
        if args_split.__contains__(command_option):
            args_split.remove(command_option)
            is_option_all = True

        del args_split[0]

        gym_code = args_split[0].upper()

        if 0 < len(args_split) < 3 :
            city = _read_channel_city(message)
            gym_dict = gymsql.find_gym(city,args_split[0])
            if len(gym_dict) == 0:
                return await message.channel.send(content="Beep Beep...! I couldn't find a match for {gym_code} in {city_code}".format(gym_code=gym_code, city_code=city))

            if is_option_all:
                output_gym_dict = gym_dict
            else:
                output_gym_dict = {your_key: gym_dict[your_key] for your_key in ['gym_code_key', 'gym_name', 'original_gym_name', 'city_state_key']}


            embed_title = _("**Gym Name**: {gymcode} [{citycode}]!").format(gymcode=gym_dict['gym_name'],citycode=city)
            embed_desription = json.dumps(output_gym_dict, indent=4, sort_keys=True)

            raid_embed = discord.Embed(title=embed_title, description=embed_desription)

            embed_map_image_url = fetch_gmap_image_link(gym_dict['latitude'] + "," + gym_dict['longitude'])
            raid_embed.set_image(url=embed_map_image_url)

            if gym_dict['gym_image']:
                raid_embed.set_thumbnail(url=gym_dict['gym_image'])
            roster_message = "here are the gym details! "

            return await message.channel.send(content=_("Beep Beep! {member} {message}".format(member=message.author.mention, message=roster_message)), embed=raid_embed)
        else:
            await message.channel.send(content="Beep Beep...! provide gym-code for lookup")
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True, aliases=["register-role"])
@commands.has_permissions(manage_guild=True)
async def _register_role(ctx):
    """
registers a role and a gym
    """
    message = ctx.message
    guild = message.guild
    channel = message.channel
    args = message.clean_content.lower().split()
    del args[0]

    if len(args) == 0:
        await channel.send( content=_("Beep Beep! No role-name provided. Please use `!register-role role-name` to create/register the role!"))

    role_name = args[0]

    role = discord.utils.get(guild.roles, name=role_name)
    # Create role if it doesn't exist yet
    if role is None:

        create_role = await ask_confirmation(message, "{role_name} doesn't exist! Do you want me to create a new role?".format(role_name=role_name),
                               "Creating a new role {role_name}...".format(role_name=role_name),
                               "No changes made!",
                               "Request timed out!")

        if create_role == False:
            return
        try :
            role = await guild.create_role(name=role_name, hoist=False, mentionable=True)
            await asyncio.sleep(0.5)
        except Exception as error:
            print(error)

    add_notifications_guild_dict(message.guild.id)
    guild_dict[guild.id]['notifications']['roles'].append(role.id)
    await channel.send( content=_("Beep Beep! {role_name} has been registered for notifications. Please use `!register-gym role-name gym-code` to register the gym under a role!").format(role_name=role.mention))

    return

@Clembot.command(pass_context=True, hidden=True, aliases=["deregister-gym"])
@commands.has_permissions(manage_guild=True)
async def _deregister_gym(ctx):
    """
registers a role and a gym
    """
    message = ctx.message
    guild = message.guild
    channel = message.channel
    args = message.clean_content.lower().split()
    del args[0]

    add_notifications_guild_dict(message.guild.id)

    role_name = args[0]
    del args[0]

    role = discord.utils.get(guild.roles, name=role_name)
    # Create role if it doesn't exist yet
    if role is None:
        await channel.send( content=_("Beep Beep! I couldn't find the role **{role_name}**. Please use `!register-role role-name` to create/register the role!".format(role_name=role_name)))
        return

    if role.id not in guild_dict[guild.id]['notifications']['roles']:
        await channel.send( content=_("Beep Beep! The role {role_name} is not registered for notifications. Please use `!register-role role-name` to create/register the role!"))
        return

    if len(args) == 0 or len(args) > 1:
        await channel.send( content=_("Beep Beep! Please provide a gym-code to register. `!register role-name gym-code`"))
        return

    gym_code = args[0].upper()
    gym_info = get_gym_info_wrapper(message, gym_code=gym_code)

    if gym_info == None:
        await channel.send( content=_("Beep Beep! Hmmm... I could not find this gym code!"))
        return

    # {'notifications': {'roles': [], 'gym_role_map': {}}}
    gym_role_map = {gym_code: role.id}
    try:
        del guild_dict[message.guild.id]['notifications']['gym_role_map'][gym_code]
    except Exception:
        pass
    # guild_dict[message.guild.id]['notifications']['gym_role_map'].update(gym_role_map)

    await channel.send( content=_("Beep Beep! {gym_code} will not send out a notification for {role}!").format(gym_code=gym_code.upper(), role=role.mention))

    return


@Clembot.command(pass_context=True, hidden=True, aliases=["register-gym"])
@commands.has_permissions(manage_guild=True)
async def _register_gym(ctx):
    """
registers a role and a gym
    """
    message = ctx.message
    guild = message.guild
    channel = message.channel
    args = message.clean_content.lower().split()
    del args[0]

    add_notifications_guild_dict(message.guild.id)

    role_name = args[0]
    del args[0]

    role = discord.utils.get(guild.roles, name=role_name)
    # Create role if it doesn't exist yet
    if role is None:
        await channel.send( content=_("Beep Beep! I couldn't find the role **{role_name}**. Please use `!register-role role-name` to create/register the role!".format(role_name=role_name)))
        return

    if role.id not in guild_dict[guild.id]['notifications']['roles']:
        await channel.send( content=_("Beep Beep! The role {role_name} is not registered for notifications. Please use `!register-role role-name` to create/register the role!"))
        return

    if len(args) == 0 or len(args) > 1:
        await channel.send( content=_("Beep Beep! Please provide a gym-code to register. `!register role-name gym-code`"))
        return

    list_of_accepted_gyms = []

    for gym_code in args:
        gym_code = args[0].upper()
        gym_info = get_gym_info_wrapper(message, gym_code=gym_code)

        if gym_info == None:
            await channel.send( content=_("Beep Beep! Hmmm... I could not find this gym code!"))
            return

        # {'notifications': {'roles': [], 'gym_role_map': {}}}
        gym_role_map = {gym_code: role.id}
        guild_dict[message.guild.id]['notifications']['gym_role_map'].update(gym_role_map)

        list_of_accepted_gyms.append(gym_info['gym_name'])


    await _send_message(ctx.message.channel, _("Beep Beep! **{member}**, Any raid reported at **{gym_names}** will notify {role}").format(member=ctx.message.author.display_name, gym_code=gym_code.upper(), role=role.mention, gym_names=", ".join(list_of_accepted_gyms)))

    return


def get_gym_by_code_message(gym_code, message):
    return get_gym_info_wrapper(message,gym_code)

def get_gym_info_wrapper(message, gym_code):

    city_state = _read_channel_city(message)
    gym_info_new_format = gymsql.get_gym_by_code(gym_code_key=gym_code, city_state_key=city_state)

    if gym_info_new_format:
        return gymsql.convert_into_gym_info(gym_info_new_format)

    return None



@Clembot.command(pass_context=True, hidden=True, aliases=["subscribe"])
async def _subscribe(ctx):
    try:
        """Behind the scenes, Clembot tracks user !wants by
        creating a guild role for the Pokemon species, and
        assigning it to the user."""
        message = ctx.message
        guild = message.guild
        channel = message.channel
        args = message.clean_content.lower().split()
        del args[0]

        if len(args) < 1:

            help_embed = get_help_embed("Subscribe to roles for notifications.", "!subscribe role", "Available Roles: ", _get_subscription_roles(ctx.message.guild), "message")
            await message.channel.send(embed=help_embed)

            return

        role_name = args[0]

        role = discord.utils.get(guild.roles, name=role_name)

        if role is None:
            raise Exception(_("Beep Beep! {member}, Hmmm... I can not find the {role}!").format(role=role_name))

        if _is_role_registered(guild.id, role.id) == False:
            raise Exception(_("Beep Beep! {member}, {role} has not been registered for notifications. Please ask an admin to use `!register-role`!").format(member=ctx.message.author.display_name, role=role_name))

        await ctx.message.author.add_roles(role)
        await _send_message(channel, _("Beep Beep! **{member}**, You have successfully subscribed for **{role}**.".format(role=role_name, member=ctx.message.author.display_name)))
    except Exception as error:
        print(error)
        logger.info(error)

        await _send_error_message(error, channel)

@Clembot.command(pass_context=True, hidden=True, aliases=["unsubscribe"])
async def _unsubscribe(ctx):
    """Remove a Pokemon from your wanted list.

    Usage: !unwant <species>
    You will no longer be notified of reports about this Pokemon."""

    """Behind the scenes, Clembot removes the user from
    the guild role for the Pokemon species."""

    try:
        message = ctx.message
        guild = message.guild
        channel = message.channel

        args = message.clean_content.lower().split()
        del args[0]

        if len(args) > 1:
            await _send_error_message(channel, _("Beep Beep! **{member}**, Please provide the role-name. Usage `!unsubscribe role-name`").format(member=ctx.message.author.display_name))
            return
        role_name = args[0]

        role = discord.utils.get(guild.roles, name=role_name)

        if role is None:
            await _send_error_message(channel, _("Beep Beep! **{member}**, No role found with name **{role}**!").format(member=ctx.message.author.display_name, role=role_name))
            return

        if _is_role_registered(guild.id, role.id) == False:
            await _send_error_message(channel, _("Beep Beep! **{member}**, **{role}** has not been registered for notifications.").format(member=ctx.message.author.display_name, role=role_name))
            return

        if role not in ctx.message.author.roles:
            await _send_message(channel, _("Beep Beep! **{member}**, Your subscribtion for **{role}** has been removed!".format(role=role_name, member=ctx.message.author.display_name)))
        else:
            await message.author.remove_roles(role)
            await _send_message(channel, _("Beep Beep! **{member}**, Your subscribtion for **{role}** has been removed!".format(role=role_name, member=ctx.message.author.display_name)))
    except Exception as error:
        print(error)
        logger.info(error)

        await _send_error_message(error, channel)

# ---------------------------- Raid Notification Module --------------------------------------



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
        if message.author.id != Clembot.owner.id:
            await message.author.send(embed=embed)

        await contest_channel.send( "Beep Beep! {reporter} can start the contest anytime using `!ready` command".format(reporter=message.author.mention))

        add_contest_to_guild_dict(message.guild.id)
        contest_channel_dict = {contest_channel.id: {'pokemon': pokemon, 'started': False, 'reported_by': message.author.id, 'option': option}}

        guild_dict[message.guild.id]['contest_channel'].update(contest_channel_dict)

    except Exception as error:
        print(error)

    return


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
                await Clembot.owner.send( embed=embed)
                if message.author.id != Clembot.owner.id:
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

def is_egg_level_valid(text):
    if text in ['1','2','3','4','5']:
        return True
    return False

def is_pokemon_valid(entered_raid):
    if entered_raid.lower() in pkmn_info['pokemon_list']:
        return True
    return False

raidegg_SYNTAX_ATTRIBUTE = ['command', 'egg', 'gym_info', 'timer', 'location']

exraid_SYNTAX_ATTRIBUTE = ['command', 'gym_info' , 'location']

raid_SYNTAX_ATTRIBUTE = ['command', 'pokemon', 'gym_info', 'timer', 'location']

nest_SYNTAX_ATTRIBUTE = ['command', 'pokemon', 'gym_info', 'link']

rsvp_SYNTAX_ATTRIBUTE =['command', 'count', 'mentions']

@checks.cityeggchannel()
@Clembot.command(pass_context=True)
@checks.raidset()
async def newraid(ctx):
    """Report an ongoing raid.

    Usage: !raid <species> <location> [minutes]
    Clembot will insert the details (really just everything after the species name) into a
    Google maps link and post the link to the same channel the report was made in.
    Clembot's message will also include the type weaknesses of the boss.

    Finally, Clembot will create a separate channel for the raid report, for the purposes of organizing the raid."""
    await _newraid(ctx.message)


async def _newraid(message):
    fromegg = False
    if message.channel.name not in guild_dict[message.guild.id]['city_channels'].keys():
        if message.channel.id in guild_dict[message.channel.guild.id]['raidchannel_dict'] and guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['type'] == 'egg':
            fromegg = True
            eggdetails = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]
            egglevel = eggdetails['egglevel']
        else:
            await message.channel.send( _("Beep Beep! Please restrict raid reports to a city channel!"))
            return


    argument_text = message.clean_content.lower()
    parameters = Parser.parse_arguments(argument_text, raid_SYNTAX_ATTRIBUTE, {'pokemon' : is_pokemon_valid, 'gym_info' : get_gym_by_code_message}, {'message' : message})
    logger.info(parameters)

    if fromegg and parameters['length'] > 2:
        await message.channel.send(_("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
        return

    entered_raid = None
    if parameters.get('pokemon', None):
        pokemon_list = parameters['pokemon']
        if len(pokemon_list) < 0 :
            await message.channel.send(_("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
            return
        entered_raid = parameters['pokemon'][0]
    else:
        entered_raid = parameters['others'][0]
        spellcheck_message = await message.channel.send(spellcheck(entered_raid))
        await asyncio.sleep(15)
        await spellcheck_message.delete()
        return

    if parameters.get('timer', None):
        raidexp = parameters['timer']
    else:
        raidexp = False


    if raidexp is not False:
        if _timercheck(raidexp, raid_timer):
            await message.channel.send( _("Beep Beep...that's too long. Raids currently last no more than {raid_timer} minutes...".format(raid_timer=raid_timer)))
            return

    channel_role = None
    gym_info = None
    if parameters.get('gym_info', None):
        gym_info = parameters['gym_info']
        raid_details = gym_info['gym_name']
        channel_role_id = _get_role_for_notification(message.channel.guild.id, gym_info['gym_code'])
        channel_role = discord.utils.get(message.channel.guild.roles, id=channel_role_id)
    else:
        raid_details = " ".join(parameters.get('others'))



    if fromegg is True:
        eggdetails = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]
        egglevel = eggdetails['egglevel']
        if raid_split[0] == 'assume':
            if config['allow_assume'][egglevel] == "False":
                await message.channel.send( _("Beep Beep! **!raid assume** is not allowed in this level egg."))
                return
            if guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['active'] == False:
                await _eggtoraid(raid_split[1].lower(), message.channel)
                return
            else:
                await _eggassume(" ".join(raid_split), message.channel)
                return
        elif guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['active'] == False:
                await _eggtoraid(" ".join(raid_split).lower(), message.channel)
                return
        else:
            await message.channel.send( _("Beep Beep! Please wait until the egg has hatched before changing it to an open raid!"))
            return
    elif len(raid_split) <= 1:
        await message.channel.send(_("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
        return


    if entered_raid not in pkmn_info['pokemon_list']:
        await message.channel.send(spellcheck(entered_raid))
        return
    if entered_raid not in get_raidlist() and entered_raid in pkmn_info['pokemon_list']:
        await message.channel.send( _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
        return

    region_prefix = get_region_prefix(message)
    if region_prefix:
        prefix =  region_prefix + "-"
    else:
        prefix = ""


    if gym_info:
        raid_gmaps_link = gym_info['gmap_link']
        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(gym_info['gym_name'])
        channel_role_id = _get_role_for_notification(message.channel.guild.id, gym_info['gym_code'])
        channel_role = discord.utils.get(message.channel.guild.roles, id=channel_role_id)
    else:
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(raid_details)

    raid_channel = None
    try :
        raid_channel_category = get_category(message.channel, get_level(entered_raid))
        raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=dict(message.channel.overwrites), category=raid_channel_category)
    except Exception as error:
        print(error)
        return
    raid = discord.utils.get(message.guild.roles, name=entered_raid)
    if raid is None:
        # raid = await Clembot.create_role(guild=message.guild, name=entered_raid, hoist=False, mentionable=True)
        # await asyncio.sleep(0.5)
        raid_role = "**" + entered_raid.capitalize() + "**"
    else:
        raid_role = raid.mention
    raid_number = pkmn_info['pokemon_list'].index(entered_raid) + 1
    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(raid_number).zfill(3))
    raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
    raid_embed.add_field(name="**Details:**", value=_("{pokemon} ({pokemonnumber}) {type}").format(pokemon=entered_raid.capitalize(), pokemonnumber=str(raid_number), type="".join(get_type(message.guild, raid_number)), inline=True))
    raid_embed.add_field(name="**Weaknesses:**", value=_("{weakness_list}").format(weakness_list=weakness_to_str(message.guild, get_weaknesses(entered_raid))), inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    content = _("Beep Beep! {pokemon} raid reported by {member}! Details: {location_details}. Coordinate in {raid_channel}").format(pokemon=entered_raid.capitalize(), member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention)
    raidreport = await message.channel.send( content= content, embed=raid_embed)

    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! {pokemon} raid reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
This channel will be deleted five minutes after the timer expires.
** **
Please type `!beep status` if you need a refresher of Clembot commands! 
""").format(pokemon=raid_role, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

    raidmessage = await raid_channel.send( content=raidmsg, embed=raid_embed)

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': fetch_current_time(message.channel.guild.id) + timedelta(minutes=raid_timer),  # raid timer minutes from now
        'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
        'active': True,
        'raidmessage' : raidmessage.id,
        'raidreport' : raidreport.id,
        'address': raid_details,
        'type': 'raid',
        'pokemon': entered_raid,
        'egglevel': -1,
        'suggested_start': False
        }

    if channel_role:
        await raid_channel.send( content=_("Beep Beep! A raid has been reported for {channel_role}.").format(channel_role=channel_role.mention))

    if raidexp is not False:
        await _timerset(raid_channel, raidexp)
    else:
        await raid_channel.send( content=_("Beep Beep! Hey {member}, if you can, set the time left on the raid using **!timerset <minutes>** so others can check it with **!timer**.").format(member=message.author.mention))
    event_loop.create_task(expiry_check(raid_channel))




@Clembot.command(pass_context=True, aliases=['raid', 'r', 'egg', 'raidegg'])
@checks.cityeggchannel()
@checks.raidset()
async def __raid(ctx, pokemon, *, location:commands.clean_content(fix_channel_mentions=True)="", weather=None, timer=None):
    """Report an ongoing raid or a raid egg.

    Usage: !raid <species/level> <location> [weather] [minutes]
    Meowth will insert <location> into a
    Google maps link and post the link to the same channel the report was made in.
    Meowth's message will also include the type weaknesses of the boss.

    Finally, Meowth will create a separate channel for the raid report, for the purposes of organizing the raid."""
    try:
        if pokemon.isdigit():
            await _raidegg(ctx.message)
        else:
            await _raid(ctx.message)

    except Exception as error:
        print(error)
#
# @checks.cityeggchannel()
# @Clembot.command()
# @checks.raidset()
# async def raid(ctx):
#     """Report an ongoing raid.
#
#     Usage: !raid <species> <location> [minutes]
#     Clembot will insert the details (really just everything after the species name) into a
#     Google maps link and post the link to the same channel the report was made in.
#     Clembot's message will also include the type weaknesses of the boss.
#
#     Finally, Clembot will create a separate channel for the raid report, for the purposes of organizing the raid."""
#     await _raid(ctx.message)
#

async def _raid(message):
    fromegg = False
    if message.channel.name not in guild_dict[message.guild.id]['city_channels'].keys():
        if message.channel.id in guild_dict[message.channel.guild.id]['raidchannel_dict'] and guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['type'] == 'egg':
            fromegg = True
            eggdetails = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]
            egglevel = eggdetails['egglevel']
        else:
            await message.channel.send( _("Beep Beep! Please restrict raid reports to a city channel!"))
            return
    raid_split = message.clean_content.lower().split()
    del raid_split[0]
    if fromegg is True:
        eggdetails = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]
        egglevel = eggdetails['egglevel']
        if raid_split[0] == 'assume':
            if config['allow_assume'][egglevel] == "False":
                await message.channel.send( _("Beep Beep! **!raid assume** is not allowed in this level egg."))
                return
            if guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['active'] == False:
                await _eggtoraid(raid_split[1].lower(), message.channel)
                return
            else:
                await _eggassume(" ".join(raid_split), message.channel)
                return
        elif guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['active'] == False:
                await _eggtoraid(" ".join(raid_split).lower(), message.channel)
                return
        else:
            await message.channel.send( _("Beep Beep! Please wait until the egg has hatched before changing it to an open raid!"))
            return
    elif len(raid_split) <= 1:
        await message.channel.send( _("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
        return
    entered_raid = re.sub("[\@]", "", raid_split[0].lower())
    entered_raid = get_name(entered_raid).lower() if entered_raid.isdigit() else entered_raid
    del raid_split[0]

    gym_info = None

    gym_code = raid_split[-1].upper()

    gym_info = get_gym_info_wrapper(message, gym_code=gym_code)

    if gym_info:
        del raid_split[-1]
    if len(raid_split) >= 1 and raid_split[-1].isdigit():
        raidexp = int(raid_split[-1])
        del raid_split[-1]
    elif len(raid_split) >= 1 and ":" in raid_split[-1]:
        raid_split[-1] = re.sub(r"[a-zA-Z]", "", raid_split[-1])
        if raid_split[-1].split(":")[0] == "":
            endhours = 0
        else:
            endhours = int(raid_split[-1].split(":")[0])
        if raid_split[-1].split(":")[1] == "":
            endmins = 0
        else:
            endmins = int(raid_split[-1].split(":")[1])
        raidexp = 60 * endhours + endmins
        del raid_split[-1]
    else:
        raidexp = False

    if raidexp is not False:
        if _timercheck(raidexp, 45):
            await message.channel.send( _("Beep Beep...that's too long. Raids currently last no more than 45 minutes..."))
            return

    if entered_raid not in pkmn_info['pokemon_list']:
        entered_raid = await autocorrect(entered_raid, message.channel, message.author)

    if entered_raid not in get_raidlist() and entered_raid in pkmn_info['pokemon_list']:
        await message.channel.send( _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
        return

    raid_details = " ".join(raid_split)
    raid_details = raid_details.strip()
    if raid_details == '':
        if gym_info:
            raid_details = gym_info['gym_name']
        else:
            await message.channel.send( _("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
            return

    if gym_info is None and 2 <= raid_details.__len__() <= 6:
        raid_details_gym_code = raid_details.upper()
        # raid_details_gym_info = gymutil.get_gym_info(raid_details_gym_code, city_state=get_city_list(message))
        raid_details_gym_info = get_gym_info_wrapper(message, gym_code=raid_details_gym_code)
        if raid_details_gym_info:
            gym_info = raid_details_gym_info

    channel_role = None
    region_prefix = get_region_prefix(message)
    if region_prefix:
        prefix =  region_prefix + "-"
    else:
        prefix = ""
    if gym_info:
        raid_gmaps_link = gym_info['gmap_link']
        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(gym_info['gym_name'])
        channel_role_id = _get_role_for_notification(message.channel.guild.id, gym_info['gym_code'])
        channel_role = discord.utils.get(message.channel.guild.roles, id=channel_role_id)
    else:
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(raid_details)

    raid_channel = None
    try :
        raid_channel_category = get_category(message.channel, get_level(entered_raid))
        raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=dict(message.channel.overwrites), category=raid_channel_category)
    except Exception as error:
        print(error)
        return
    raid = discord.utils.get(message.guild.roles, name=entered_raid)
    if raid is None:
        # raid = await Clembot.create_role(guild=message.guild, name=entered_raid, hoist=False, mentionable=True)
        # await asyncio.sleep(0.5)
        raid_role = "**" + entered_raid.capitalize() + "**"
    else:
        raid_role = raid.mention
    raid_number = pkmn_info['pokemon_list'].index(entered_raid) + 1
    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(raid_number).zfill(3))
    raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
    raid_embed.add_field(name="**Details:**", value=_("{pokemon} ({pokemonnumber}) {type}").format(pokemon=entered_raid.capitalize(), pokemonnumber=str(raid_number), type="".join(get_type(message.guild, raid_number)), inline=True))
    raid_embed.add_field(name="**Weaknesses:**", value=_("{weakness_list}").format(weakness_list=weakness_to_str(message.guild, get_weaknesses(entered_raid))), inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    content = _("Beep Beep! {pokemon} raid reported by {member}! Details: {location_details}. Coordinate in {raid_channel}").format(pokemon=entered_raid.capitalize(), member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention)
    raidreport = await message.channel.send( content= content, embed=raid_embed)

    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! {pokemon} raid reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
This channel will be deleted five minutes after the timer expires.
** **
Please type `!beep status` if you need a refresher of Clembot commands! 
""").format(pokemon=raid_role, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

    raidmessage = await raid_channel.send( content=raidmsg, embed=raid_embed)
    # countersmessage = await raid_channel.send(content="Use **!counters** or **!moveset** to see the movesets/counters for raid boss.")

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': fetch_current_time(message.channel.guild.id) + timedelta(minutes=raid_timer),  # raid timer minutes from now
        'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
        'active': True,
        'raidmessage' : raidmessage.id,
        'raidreport' : raidreport.id,
        'address': raid_details,
        'type': 'raid',
        'pokemon': entered_raid,
        'egglevel': -1,
        'suggested_start': False,
        'counters_dict' : {},
        'weather' : None,
        'moveset' : 0,
        'countersmessage' : None
        }


    if channel_role:
        await raid_channel.send( content=_("Beep Beep! A raid has been reported for {channel_role}.").format(channel_role=channel_role.mention))
        # channel_mentions = _get_roles_mention_for_notifications(message.guild,gym_info['gym_code'])
        # if channel_mentions:
        #     await raid_channel.send(content=_("Beep Beep! A raid has been reported for {channel_role}.").format(channel_role=channel_mentions))




    if raidexp is not False:
        await _timerset(raid_channel, raidexp)
    else:
        await raid_channel.send( content=_("Beep Beep! Hey {member}, if you can, set the time left on the raid using **!timerset <minutes>** so others can check it with **!timer**.").format(member=message.author.mention))

    record_reported_by(message.guild.id, message.author.id, 'raid_reports')


    event_loop.create_task(expiry_check(raid_channel))



async def old_fetch_counters_dict(pkmn , weather:None):

    try:

        weather = 'clear'
        emoji_dict = {0: '0\u20e3', 1: '1\u20e3', 2: '2\u20e3', 3: '3\u20e3', 4: '4\u20e3', 5: '5\u20e3', 6: '6\u20e3', 7: '7\u20e3', 8: '8\u20e3', 9: '9\u20e3', 10: '10\u20e3'}
        counters_and_movesets = {}
        ctrs_dict = {}
        ctrs_index = 0
        ctrs_dict[ctrs_index] = {}
        ctrs_dict[ctrs_index]['moveset'] = "Unknown Moveset"
        ctrs_dict[ctrs_index]['emoji'] = '0\u20e3'
        img_url = 'https://raw.githubusercontent.com/FoglyOgly/Meowth/discordpy-v1/images/pkmn/{0}_.png?cache={1}'.format(str(get_number(pkmn)).zfill(3),CACHE_VERSION)
        level = get_level(pkmn) if get_level(pkmn).isdigit() else "5"
        url = "https://fight.pokebattler.com/raids/defenders/{pkmn}/levels/RAID_LEVEL_{level}/attackers/".format(pkmn=pkmn.replace('-','_').upper(),level=level)
        url += "levels/30/"
        weather_list = [_('none'), _('extreme'), _('clear'), _('sunny'), _('rainy'),
                        _('partlycloudy'), _('cloudy'), _('windy'), _('snow'), _('fog')]
        match_list = ['NO_WEATHER','NO_WEATHER','CLEAR','CLEAR','RAINY',
                            'PARTLY_CLOUDY','OVERCAST','WINDY','SNOW','FOG']
        if not weather:
            index = 0
        else:
            index = weather_list.index(weather)
        weather = match_list[index]
        url += "strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=OVERALL&"
        url += "weatherCondition={weather}&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE".format(weather=weather)
        title_url = url.replace('https://fight', 'https://www')
        hyperlink_icon = 'https://i.imgur.com/fn9E5nb.png'
        pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'
        print(url)
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                data = await resp.json()

        # print(json.dumps(data, indent=4))
        data = data['attackers'][0]

        print(json.dumps(data, indent=4))

        raid_cp = data['cp']
        atk_levels = '30'
        ctrs = data['randomMove']['defenders'][-6:]
        def clean(txt):
            return txt.replace('_', ' ').title()
        title = _('{pkmn} | {weather} | Unknown Moveset').format(pkmn=pkmn.title(),weather=weather_list[index].title())
        stats_msg = _("**CP:** {raid_cp}\n").format(raid_cp=raid_cp)
        stats_msg += _("**Weather:** {weather}\n").format(weather=clean(weather))
        stats_msg += _("**Attacker Level:** {atk_levels}").format(atk_levels=atk_levels)
        ctrs_embed = discord.Embed(colour=guild.me.colour)
        ctrs_embed.set_author(name=title,url=title_url,icon_url=hyperlink_icon)
        ctrs_embed.set_thumbnail(url=img_url)
        ctrs_embed.set_footer(text=_('Results courtesy of Pokebattler'), icon_url=pbtlr_icon)
        ctrindex = 1

        for ctr in reversed(ctrs):
            ctr_name = clean(ctr['pokemonId'])
            moveset = ctr['byMove'][-1]
            moves = _("{move1} | {move2}").format(move1=clean(moveset['move1'])[:-5], move2=clean(moveset['move2']))
            name = _("#{index} - {ctr_name}").format(index=ctrindex, ctr_name=ctr_name)
            ctrs_embed.add_field(name=name,value=moves)
            ctrindex += 1



        for moveset in data['byMove']:
            ctrs_index += 1
            move1 = moveset['move1'][:-5].lower().title().replace('_', ' ')
            move2 = moveset['move2'].lower().title().replace('_', ' ')
            movesetstr = f'{move1} | {move2}'
            ctrs = moveset['defenders'][-6:]
            moveset_title = _(f'{pkmn.title()} | {weather_list[index].title()} | {movesetstr}')
            ctrs_embed = discord.Embed(colour=guild.me.colour)
            ctrs_embed.set_author(name=moveset_title,url=title_url,icon_url=hyperlink_icon)
            ctrs_embed.set_thumbnail(url=img_url)
            ctrs_embed.set_footer(text=_('Results courtesy of Pokebattler'), icon_url=pbtlr_icon)
            ctrindex = 1
            counters_list = []
            for ctr in reversed(ctrs):
                ctr_name = clean(ctr['pokemonId'])
                moveset = ctr['byMove'][-1]
                moves = _("{move1} | {move2}").format(move1=clean(moveset['move1'])[:-5], move2=clean(moveset['move2']))
                name = _("#{index} - {ctr_name}").format(index=ctrindex, ctr_name=ctr_name)
                counters_list.append({'index' :  ctrindex, 'counter' : ctr_name, 'mvoeset' : moves})
                ctrs_embed.add_field(name=name,value=moves)
                ctrindex += 1
            # 'embed': ctrs_embed,
            ctrs_dict[ctrs_index] = {'moveset': movesetstr, 'emoji': emoji_dict[ctrs_index]} #'counters': counters_list}

        moveset_list = []
        for moveset in ctrs_dict:
            moveset_list.append(f"{ctrs_dict[moveset]['emoji']}: {ctrs_dict[moveset]['moveset']}\n")
        # for moveset in ctrs_dict:
            # ctrs_split = int(round(len(moveset_list)/2+0.1))

            # ctrs_dict[moveset]['embed'].add_field(name="**Possible Movesets:**", value=f"{''.join(moveset_list[:ctrs_split])}", inline=True)
            # ctrs_dict[moveset]['embed'].add_field(name="\u200b", value=f"{''.join(moveset_list[ctrs_split:])}",inline=True)
            # ctrs_dict[moveset]['embed'].add_field(name=_("Results with Level 30 attackers"), value=_("[See your personalized results!](https://www.pokebattler.com/raids/{pkmn})").format(pkmn=pkmn.replace('-','_').upper()),inline=False)

        ctrs_embed = discord.Embed(colour=guild.me.colour)
        ctrs_embed.set_author(name=title, url=title_url, icon_url=hyperlink_icon)
        ctrs_embed.set_thumbnail(url=img_url)
        ctrs_embed.set_footer(text=_('Results courtesy of Pokebattler. This message will be auto-deleted in 2 minutes'), icon_url=pbtlr_icon)



        description = ""
        text=""
        for moveset in ctrs_dict:
            text = text+"{0} - {1}\n".format(ctrs_dict[moveset]['emoji'], ctrs_dict[moveset]['moveset'])

        # ctrs_embed.add_field(name="Counters", value="*Please choose the moveset by using the emoji...*")
        ctrs_embed.add_field(name="Possible Movesets", value=text)



        text = json.dumps(ctrs_dict, indent=0)
        print(text)

        await _send_message(ctx.channel, text)

        moveset_message = await ctx.channel.send(embed=ctrs_embed)
        asyncio.sleep(120)
        await moveset_message.delete()

    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True, aliases= ["moveset"])
async def _get_moveset(ctx, pkmn): # guild, pkmn, weather=None):
    try:
        message = ctx.message
        guild = ctx.message.guild
        raid_channel = ctx.message.channel

        raid_dict = guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id]

        if checks.check_raidchannel(ctx):

            weather = guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id].get('weather',None)
            moveset_index = guild_dict[message.guild.id]['raidchannel_dict'][ctx.message.channel.id].get('moveset',0)

            counters_dict = guild_dict[message.guild.id]['raidchannel_dict'][ctx.message.channel.id].get('counters_dict', {})

            if counters_dict :
                moveset_dict = counters_dict['movesets'].get(moveset_index)
            else :
                counters_dict = await _fetch_moveset_and_counters(ctx, pkmn, weather)
                if not counters_dict:
                    return await _send_error_message(ctx.channel, "Beep Bepp! **{0}** No reponse recieved from Pokebattler.".format(ctx.message.author.display_name))
                moveset_dict = counters_dict['movesets']
                moveset_dict_index = counters_dict['movesets'].get(moveset_index)
                raid_boss_moveset = moveset_dict_index['moveset']
            # 'counters_dict': {}, 'weather': None, 'moveset': 0, 'countersmessage': None}

            if moveset_index == 0:
                img_url = 'https://raw.githubusercontent.com/FoglyOgly/Meowth/discordpy-v1/images/pkmn/{0}_.png?cache={1}'.format(str(get_number(pkmn)).zfill(3), CACHE_VERSION)
                hyperlink_icon = 'https://i.imgur.com/fn9E5nb.png'
                pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'

                moveset_embed = discord.Embed(colour=guild.me.colour)
                moveset_embed.set_author(name="", url="", icon_url=hyperlink_icon)
                moveset_embed.set_thumbnail(url=img_url)
                moveset_embed.set_footer(text=_('Results courtesy of Pokebattler. This message will be auto-deleted in 2 minutes'), icon_url=pbtlr_icon)

                description = ""
                text = ""
                for index,moveset in moveset_dict.items():

                    text = text + "{0} - {1}\n".format(moveset['emoji'], moveset['moveset'])

                moveset_embed.add_field(name="Possible Movesets", value=text)


                await ctx.channel.send(embed=moveset_embed)

            else :
                await _send_message(ctx.channel, "**{0}** The moveset for current raid boss is {1}.".format(ctx.message.author.display_name, raid_boss_moveset))

        else:
            await _send_error_message (ctx.channel, "**{}** please use the command in the raid channel.".format(ctx.message.author.display_name))
    except Exception as error:
        print(error)



@Clembot.command(pass_context=True, hidden=True, aliases= ["movesets"])
async def _test_get_moveset(ctx, pkmn): # guild, pkmn, weather=None):

    counters_dict = await _fetch_moveset_and_counters(ctx, pkmn, 'fog')

    counters_dict = await _fetch_moveset_and_counters(ctx, pkmn, 'clear', counters_dict)

    counters_dict = await _fetch_moveset_and_counters(ctx, pkmn, 'rainy', counters_dict)
    print(counters_dict)

async def _fetch_moveset_and_counters(ctx, pkmn, weather='clear', counters_and_movesets = {}):
    try:
        message = ctx.message
        # rc_dict = guild_dict[message.guild.id]['raidchannel_dict'][ctx.message.channel.id]

        guild = ctx.guild

        emoji_dict = {0: '0\u20e3', 1: '1\u20e3', 2: '2\u20e3', 3: '3\u20e3', 4: '4\u20e3', 5: '5\u20e3', 6: '6\u20e3', 7: '7\u20e3', 8: '8\u20e3', 9: '9\u20e3', 10: '10\u20e3'}

        ctrs_dict = {}
        ctrs_index = 0
        ctrs_dict[ctrs_index] = {}
        ctrs_dict[ctrs_index]['moveset'] = "Unknown Moveset"
        ctrs_dict[ctrs_index].setdefault('emoji',{})['0'] = '0\u20e3'
        img_url = 'https://raw.githubusercontent.com/FoglyOgly/Meowth/discordpy-v1/images/pkmn/{0}_.png?cache={1}'.format(str(get_number(pkmn)).zfill(3),CACHE_VERSION)
        level = get_level(pkmn) if get_level(pkmn).isdigit() else "5"
        url = "https://fight.pokebattler.com/raids/defenders/{pkmn}/levels/RAID_LEVEL_{level}/attackers/".format(pkmn=pkmn.replace('-','_').upper(),level=level)
        url += "levels/30/"
        weather_list = [_('none'), _('extreme'), _('clear'), _('sunny'), _('rainy'),
                        _('partlycloudy'), _('cloudy'), _('windy'), _('snow'), _('fog')]
        match_list = ['NO_WEATHER','NO_WEATHER','CLEAR','CLEAR','RAINY',
                            'PARTLY_CLOUDY','OVERCAST','WINDY','SNOW','FOG']
        if not weather:
            index = 0
        else:
            index = weather_list.index(weather)
        weather = match_list[index]
        url += "strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=OVERALL&"
        url += "weatherCondition={weather}&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE".format(weather=weather)
        title_url = url.replace('https://fight', 'https://www')
        hyperlink_icon = 'https://i.imgur.com/fn9E5nb.png'
        pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'
        print(url)
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                data = await resp.json()

        # print(json.dumps(data, indent=4))
        data = data['attackers'][0]

        raid_cp = data['cp']
        atk_levels = '30'
        ctrs = data['randomMove']['defenders'][-6:]


        def clean(txt):
            return txt.replace('_', ' ').title()

        ctrindex = 1

        ctrs_weather_random_moveset = {}

        if counters_and_movesets :
            counters_and_movesets.setdefault('counters', {})[weather] = {}
        else:
            counters_and_movesets = {}
            counters_and_movesets['pokemon'] = pkmn
            counters_and_movesets['raid_cp'] = raid_cp
            counters_and_movesets['atk_levels'] = '30'
            counters_and_movesets['movesets'] = {}
            counters_and_movesets['movesets'][0] = {}
            counters_and_movesets['movesets'][0]['emoji'] = emoji_dict[0]
            counters_and_movesets['movesets'][0]['moveset']= "Unknown Moveset"
            moveset_index = 1

            # fetch possible movesets for raid-boss
            for moveset in data['byMove']:
                move1 = moveset['move1'][:-5].lower().title().replace('_', ' ')
                move2 = moveset['move2'].lower().title().replace('_', ' ')
                movesetstr = f'{move1} | {move2}'

                counters_and_movesets['movesets'][moveset_index] = {}
                counters_and_movesets['movesets'][moveset_index]['emoji'] =  emoji_dict[moveset_index]
                counters_and_movesets['movesets'][moveset_index]['moveset'] = movesetstr
                moveset_index += 1

            counters_and_movesets.setdefault('counters', {})[weather] = {}


        # fetch counters for random moveset
        for ctr in reversed(ctrs):
            ctrs_weather_random_moveset_ranked = {}
            ctr_name = clean(ctr['pokemonId'])
            moveset = ctr['byMove'][-1]


            ctrs_weather_random_moveset_ranked['pokemonId'] = clean(ctr['pokemonId'])
            ctrs_weather_random_moveset_ranked.setdefault('moveset',{})['move1'] = clean(moveset['move1'])[:-5]
            ctrs_weather_random_moveset_ranked['moveset']['move2'] = clean(moveset['move2'])

            ctrs_weather_random_moveset[ctrindex] = ctrs_weather_random_moveset_ranked
            ctrindex += 1

        counters_and_movesets['counters'][weather] = {}
        counters_and_movesets['counters'][weather]['Unknown Moveset'] = ctrs_weather_random_moveset


        # fetch counters with moveset possibilities
        ctrs_weather_with_moveset = {}

        for moveset in data['byMove']:
            ctrs_index += 1

            move1 = moveset['move1'][:-5].lower().title().replace('_', ' ')
            move2 = moveset['move2'].lower().title().replace('_', ' ')
            movesetstr = f'{move1} | {move2}'

            counters_and_movesets['counters'][weather][movesetstr] = {}
            ctrs_weather_with_moveset = {}

            ctrs = moveset['defenders'][-6:]
            ctrindex = 1
            counters_list = []
            for ctr in reversed(ctrs):
                ctrs_weather_random_moveset_ranked = {}

                ctr_name = clean(ctr['pokemonId'])
                moveset = ctr['byMove'][-1]

                ctrs_weather_random_moveset_ranked['pokemonId'] = clean(ctr['pokemonId'])
                ctrs_weather_random_moveset_ranked.setdefault('moveset', {})['move1'] = clean(moveset['move1'])[:-5]
                ctrs_weather_random_moveset_ranked['moveset']['move2'] = clean(moveset['move2'])

                ctrs_weather_with_moveset[ctrindex] = ctrs_weather_random_moveset_ranked
                ctrindex += 1

            counters_and_movesets['counters'][weather][movesetstr] = ctrs_weather_with_moveset

            ctrs_dict[ctrs_index] = {'moveset': movesetstr, 'emoji': emoji_dict[ctrs_index]}

        text = json.dumps(counters_and_movesets, indent=2)
        print(text)

        return counters_and_movesets


    except Exception as error:
        print(error)
        logger.error(error)






@Clembot.command(aliases=["re"])
@checks.nonraidchannel()
async def research(ctx, *, args = None):
    """Report Field research
    Guided report method with just !research. If you supply arguments in one
    line, avoid commas in anything but your separations between pokestop,
    quest, reward. Order matters if you supply arguments. If a pokemon name
    is included in reward, a @mention will be used if role exists.

    Usage: !research [pokestop, quest, reward]"""
    try:
        message = ctx.message
        channel = message.channel
        author = message.author

        guild = message.guild
        timestamp = (message.created_at + datetime.timedelta(hours=guild_dict[message.channel.guild.id]['offset']))
        print(message.created_at )
        print(timestamp)
        to_midnight = 24*60*60 - ((timestamp-timestamp.replace(hour=0, minute=0, second=0, microsecond=0)).seconds)
        error = False
        research_id = '%04x' % randrange(16 ** 4)
        research_embed = discord.Embed(colour=discord.Colour.gold()).set_thumbnail(url='https://raw.githubusercontent.com/TrainingB/Clembot/v1-rewrite/images/field-research.png?cache={0}'.format(CACHE_VERSION))
        research_embed.set_footer(text=_('Reported by @{author} - {timestamp} | {research_id}').format(author=author.display_name, timestamp=timestamp.strftime(_('%I:%M %p (%H:%M)')), research_id=research_id), icon_url=author.avatar_url_as(format=None, static_format='jpg', size=32))
        while True:
            if args:
                research_split = message.clean_content.replace("!research ","").split(", ")
                if len(research_split) != 3:
                    error = _("entered an incorrect amount of arguments.\n\nUsage: **!research** or **!research <pokestop>, <quest>, <reward>**")
                    break
                location, quest, reward = research_split
                research_embed.add_field(name=_("**Location:**"),value='\n'.join(textwrap.wrap(location.title(), width=30)),inline=True)
                research_embed.add_field(name=_("**Quest:**"),value='\n'.join(textwrap.wrap(quest.title(), width=30)),inline=True)
                research_embed.add_field(name=_("**Reward:**"),value='\n'.join(textwrap.wrap(reward.title(), width=30)),inline=True)
                break
            else:
                research_embed.add_field(name=_('**New Research Report**'), value=_("Beep Beep! I'll help you report a research quest!\n\nFirst, I'll need to know what **pokestop** you received the quest from. Reply with the name of the **pokestop**. You can reply with **cancel** to stop anytime."), inline=False)
                pokestopwait = await channel.send(embed=research_embed)
                try:
                    pokestopmsg = await Clembot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
                except asyncio.TimeoutError:
                    pokestopmsg = None
                await pokestopwait.delete()
                if not pokestopmsg:
                    error = _("took too long to respond")
                    break
                elif pokestopmsg.clean_content.lower().strip()  == 'cancel':
                    error = _("cancelled the report")
                    break
                elif pokestopmsg:
                    location = pokestopmsg.clean_content
                await pokestopmsg.delete()
                research_embed.add_field(name=_("**Location:**"),value='\n'.join(textwrap.wrap(location.title(), width=30)),inline=True)
                research_embed.set_field_at(0, name=research_embed.fields[0].name, value=_("Great! Now, reply with the **quest** that you received from **{location}**. You can reply with **cancel** to stop anytime.\n\nHere's what I have so far:").format(location=location), inline=False)
                questwait = await channel.send(embed=research_embed)
                try:
                    questmsg = await Clembot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
                except asyncio.TimeoutError:
                    questmsg = None
                await questwait.delete()
                if not questmsg:
                    error = _("took too long to respond")
                    break
                elif questmsg.clean_content.lower().strip() == 'cancel':
                    error = _("cancelled the report")
                    break
                elif questmsg:
                    quest = questmsg.clean_content
                await questmsg.delete()
                research_embed.add_field(name=_("**Quest:**"),value='\n'.join(textwrap.wrap(quest.title(), width=30)),inline=True)
                research_embed.set_field_at(0, name=research_embed.fields[0].name, value=_("Fantastic! Now, reply with the **reward** for the **{quest}** quest that you received from **{location}**. You can reply with **cancel** to stop anytime.\n\nHere's what I have so far:").format(quest=quest, location=location), inline=False)
                rewardwait = await channel.send(embed=research_embed)
                try:
                    rewardmsg = await Clembot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
                except asyncio.TimeoutError:
                    rewardmsg = None
                await rewardwait.delete()
                if not rewardmsg:
                    error = _("took too long to respond")
                    break
                elif rewardmsg.clean_content.lower().strip() == 'cancel':
                    error = _("cancelled the report")
                    break
                elif rewardmsg:
	                reward = rewardmsg.clean_content
                await rewardmsg.delete()
                research_embed.add_field(name=_("**Reward:**"),value='\n'.join(textwrap.wrap(reward.title(), width=30)),inline=True)
                research_embed.remove_field(0)
                break
        if not error:
            roletest = ""
            pkmn_match = next((p for p in pkmn_info['pokemon_list'] if re.sub('[^a-zA-Z0-9]', '', p) == re.sub('[^a-zA-Z0-9]', '', reward.lower())), None)
            if pkmn_match:
                role = discord.utils.get(guild.roles, name=pkmn_match)
                if role:
                    roletest = _("{pokemon} - ").format(pokemon=role.mention)
            research_msg = _("A Field Research has been reported!").format(roletest=roletest,author=author.display_name)


            research_embed.__setattr__('title', research_msg)
            confirmation = await channel.send(embed=research_embed)
            research_dict = copy.deepcopy(guild_dict[guild.id].get('questreport_dict',{}))
            research_dict[confirmation.id] = {
                'research_id' : research_id,
                'exp':time.time() + to_midnight,
                'expedit':"delete",
                'reportmessage':message.id,
                'reportchannel':channel.id,
                'reportauthor':author.id,
                'reportauthorname':author.name,
                'location':location,
                'quest':quest,
                'reward':reward
            }
            guild_dict[guild.id]['questreport_dict'] = research_dict
            try:
                await message.delete()
            except Exception:
                pass
            record_reported_by(message.guild.id, message.author.id, 'research_reports')
        else:
            research_embed.clear_fields()
            research_embed.add_field(name='**Research Report Cancelled**', value=_("Beep Beep! Your report has been cancelled because you {error}! Retry when you're ready.").format(error=error), inline=False)
            confirmation = await channel.send(embed=research_embed)
            await asyncio.sleep(10)
            await confirmation.delete()
            await message.delete()




    except Exception as error:
        print(error)
        logger.info(error)
        print(traceback.print_exc())





# Print raid timer
async def print_raid_timer(channel_id):
    channel = Clembot.get_channel(channel_id)
    localexpire = fetch_channel_expire_time(channel_id)
    # localexpire = localexpiresecs - timedelta(hours=guild_dict[channel.guild.id]['offset'])
    timerstr = ""
    if guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
        raidtype = "egg"
        raidaction = "hatch"
    else:
        raidtype = "raid"
        raidaction = "end"
    if not guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['active']:
        timerstr += _("Beep Beep! This {raidtype}'s timer has already expired as of {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
    else:
        if guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['egglevel'] == "EX" or guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['type'] == "exraid":
            if guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['manual_timer']:
                timerstr += _("Beep Beep! This {raidtype} will {raidaction} on {expiry_day} at {expiry_time} ({expiry_time24})!").format(
                    raidtype=raidtype, raidaction=raidaction, expiry_day=localexpire.strftime("%B %d"), expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
            else:
                timerstr += _("Beep Beep! No one told me when the {raidtype} will {raidaction}, so I'm assuming it will {raidaction} on {expiry_day} at {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, raidaction=raidaction, expiry_day=localexpire.strftime("%B %d"), expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
        else:
            if guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['manual_timer']:
                timerstr += _("Beep Beep! This {raidtype} will {raidaction} at {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, raidaction=raidaction, expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
            else:
                timerstr += _("Beep Beep! No one told me when the {raidtype} will {raidaction}, so I'm assuming it will {raidaction} at {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, raidaction=raidaction, expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))

    return timerstr


@Clembot.command(pass_context=True, hidden=True)
@checks.raidchannel()
async def timerset(ctx, timer):
    """Set the remaining duration on a raid.

    Usage: !timerset <minutes>
    Works only in raid channels, can be set or overridden by anyone.
    Clembot displays the end time in HH:MM local time."""
    message = ctx.message
    channel = message.channel
    guild = message.guild
    if checks.check_raidactive(ctx) and not checks.check_exraidchannel(ctx):
        if guild_dict[guild.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
            raidtype = "Raid Egg"
            maxtime = egg_timer
        else:
            raidtype = "Raid"
            maxtime = raid_timer
        if timer.isdigit():
            raidexp = int(timer)
        elif ":" in timer:
            h, m = re.sub(r"[a-zA-Z]", "", timer).split(":", maxsplit=1)
            if h is "": h = "0"
            if m is "": m = "0"
            if h.isdigit() and m.isdigit():
                raidexp = 60 * int(h) + int(m)
            else:
                await channel.send( "Beep Beep! I couldn't understand your time format. Try again like this: **!timerset <minutes>**")
                return
        else:
            await channel.send( "Beep Beep! I couldn't understand your time format. Try again like this: **!timerset <minutes>**")
            return
        if _timercheck(raidexp, maxtime):
            await channel.send( _("Beep Beep...that's too long. {raidtype}s currently last no more than {maxtime} minutes...").format(raidtype=raidtype.capitalize(), maxtime=str(maxtime)))
            return
        await _timerset(channel, raidexp)

    if checks.check_exraidchannel(ctx):
        if checks.check_eggchannel(ctx):
            tzlocal = tz.tzoffset(None, guild_dict[guild.id]['offset'] * 3600)
            now = fetch_current_time(ctx.message.guild.id)
            timer_split = message.clean_content.lower().split()
            del timer_split[0]
            try:
                end = datetime.datetime.strptime(" ".join(timer_split) + " " + str(now.year), '%m/%d %I:%M %p %Y')
            except ValueError:
                return await _send_error_message(channel, _("Beep Beep! Your timer wasn't formatted correctly. **!timerset mm/dd HH:MM AM/PM** can be used to set the timer for the channel."))
            except Exception as error:
                print(error)
                return await _send_error_message(channel, _("Beep Beep! Your timer wasn't formatted correctly. **!timerset mm/dd HH:MM AM/PM** can be used to set the timer for the channel."))
            diff = convert_to_epoch(end) - convert_to_epoch(now)
            total = (diff / 60)
            if total > 0:
                await _timerset(channel, int(total), end)
            elif now > end:
                return await _send_error_message(channel, _("Beep Beep! Please enter a time in the future."))
        else:
            return await _send_error_message(channel, _("Beep Beep! Timerset isn't supported for exraids after they have hatched."))


def _timercheck(time, maxtime):
    return time > maxtime


def convert_to_epoch(current_time):
    return calendar.timegm(current_time.utctimetuple())

async def _timerset(channel, exptime, expire_datetime=None):
    guild = channel.guild
    exptime = int(exptime)
    # Clembot saves the timer message in the channel's 'exp' field.

    if expire_datetime:
        expire = expire_datetime
    else:
        expire = fetch_current_time(channel.guild.id) + timedelta(minutes=exptime)

    # Update timestamp
    guild_dict[guild.id]['raidchannel_dict'][channel.id]['exp'] = expire
    # Reactivate channel
    if not guild_dict[guild.id]['raidchannel_dict'][channel.id]['active']:
        await channel.send( "The channel has been reactivated.")
    guild_dict[guild.id]['raidchannel_dict'][channel.id]['active'] = True
    # Mark that timer has been manually set
    guild_dict[guild.id]['raidchannel_dict'][channel.id]['manual_timer'] = True
    # Send message
    timerstr = await print_raid_timer(channel.id)
    await channel.send( timerstr)
    # Trigger expiry checking
    event_loop.create_task(expiry_check(channel))


@Clembot.command(pass_context=True, hidden=True)
@checks.raidchannel()
async def timer(ctx):
    """Have Clembot resend the expire time message for a raid.

    Usage: !timer
    The expiry time should have been previously set with !timerset."""
    timerstr = await print_raid_timer(ctx.message.channel.id)
    await ctx.message.channel.send( timerstr)


# =-=-=-=--=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=--=-=-=-=-
# Code added for start time

def print_24_hour(timestamp):
    return timestamp.strftime("%I:%M %p")


def print_12_hour(timestamp):
    return timestamp.strftime("%I:%M %p")


def print_time(timestamp):
    return timestamp.strftime("%I:%M %p") + " (" + timestamp.strftime("%H:%M") + ")"


def convert_into_time(time_as_text, require_am_pm=True):
    time_format = ['%I:%M %p', '%I:%M%p']

    for format in time_format:
        try:
            start_time = time.strptime(time_as_text, format)
            break
        except ValueError:
            start_time = None
            continue

    if start_time == None and require_am_pm == False:
        try:
            start_time = time.strptime(time_as_text, '%H:%M')
        except ValueError:
            start_time = None
            pass

    return start_time


def convert_to_epoch(current_time):
    return calendar.timegm(current_time.utctimetuple())


def fetch_channel_expire_time(channel_id) -> datetime:
    channel = Clembot.get_channel(channel_id)
    if channel:
        expire_at = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['exp']
        return expire_at
    return None


def fetch_channel_start_time(channel_id) -> datetime:
    channel = Clembot.get_channel(channel_id)
    if channel:
        start_at = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['suggested_start']
        return start_at
    return None


def fetch_current_time(guild_id):
    offset = guild_dict[guild_id]['offset']
    current_time = datetime.datetime.utcnow() + timedelta(hours=offset)
    return current_time


def convert_into_current_time(channel, time_hour_and_min_only):
    offset = guild_dict[channel.guild.id]['offset']
    current_time = datetime.datetime.utcnow() + timedelta(hours=offset)

    start_time = current_time.replace(hour=time_hour_and_min_only.tm_hour, minute=time_hour_and_min_only.tm_min)
    return start_time


def validate_raid_start_time(raid_starts_at, raid_reported_at, raid_expires_at):
    try:
        if raid_reported_at <= raid_starts_at <= raid_expires_at:
            return True
    except Exception as error:
        print(error)

    return False


async def validate_start_time(channel, start_time):
    raid_expires_at = fetch_channel_expire_time(channel.id)

    offset = guild_dict[channel.guild.id]['offset']
    current_datetime = datetime.datetime.utcnow() + timedelta(hours=offset)

    suggested_start_time = convert_into_current_time(channel, start_time)

    is_raid_egg = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['type'] == "egg"

    # modified time for raidegg
    if is_raid_egg:
        current_datetime = raid_expires_at
        raid_expires_at = raid_expires_at + timedelta(minutes=egg_timer)

    if suggested_start_time:
        if suggested_start_time > raid_expires_at:
            await channel.send( ("Beep Beep...! start time cannot be after raid expiry time!"))
            return None
        elif suggested_start_time < current_datetime:
            if is_raid_egg:
                await channel.send( ("Beep Beep...! start time cannot be before the egg hatches!"))
            else:
                await channel.send( ("Beep Beep...! start time cannot be in past!"))
            return None
    else:
        return None

    return suggested_start_time


@Clembot.command(pass_context=True, hidden=True)
async def embed(ctx):
    message = ctx.message
    raid_img_url = "https://cdn.discordapp.com/attachments/354694475089707039/371000826522632192/15085243648140.png"

    bosslist1 = ["Line 1", "Line 2"]
    bosslist2 = ["Line 1", "Line 2"]

    raid_title = _("Beep Beep! Here is the current member status!")

    raid_embed = discord.Embed(title=raid_title, url="", colour=message.guild.me.colour)

    raid_embed.add_field(name="**Interested:**", value=_("{bosslist1}").format(bosslist1="\n".join(bosslist1)), inline=True)
    raid_embed.add_field(name="**Coming:**", value=_("{bosslist2}").format(bosslist2="\n".join(bosslist2)), inline=True)
    raid_embed.add_field(name="**Here:**", value=_("{bosslist2}").format(bosslist2="\n".join(bosslist2)), inline=True)
    raid_embed.set_footer(text=_("Reported by {author}").format(author=message.author.display_name), icon_url=message.author.avatar_url)
    raid_embed.set_thumbnail(url=raid_img_url)
    raidreport = await message.channel.send( content=_("Beep Beep! {member} here you go!").format(member=message.author.mention), embed=raid_embed)

    return



@Clembot.command(pass_context=True, hidden=True, aliases=["reset-start"])
@checks.raidchannel()
async def _reset_start(ctx):

    if ctx.message.channel.id in guild_dict[ctx.message.guild.id]['raidchannel_dict']:
        try:
            if guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['type'] == 'exraid':
                await ctx.message.channel.send( _("start isn't supported for exraids."))
                return
        except KeyError:
            pass

        try:
            guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['suggested_start'] = False
            confirmation_message = await ctx.message.channel.send( _("Beep Beep! {member} start time has been cleared!").format(member=ctx.message.author.mention))
        except Exception as error:
            print(error)
        return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidchannel()
async def start(ctx):
    """Set the remaining duration on a raid.

    Usage: !start <hh:mm>
    Works only in raid channels, can be set or overridden by anyone.
    Clembot displays the end time in HH:MM local time."""
    if ctx.message.channel.id in guild_dict[ctx.message.guild.id]['raidchannel_dict']:
        try:
            if guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['type'] == 'exraid':
                await ctx.message.channel.send( _("start isn't supported for exraids."))
                return
        except KeyError:
            pass
        args = ctx.message.content.lstrip("!start ")
        start_time = convert_into_time(args, False)

        if start_time is None:
            await ctx.message.channel.send( _("Beep Beep... I couldn't understand your time format. Try again like this: `!start HH:MM AM/PM`"))
            return

        raid_starts_at = await validate_start_time(ctx.message.channel, start_time)
        if raid_starts_at:
            try:
                guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['suggested_start'] = raid_starts_at
                await ctx.message.channel.send( _("Beep Beep! {member} suggested the start time : {starttime}").format(member=ctx.message.author.mention, starttime=print_24_hour(raid_starts_at)))
            except Exception as error:
                print(error)
            return


async def print_start_time(channel_id):
    channel = Clembot.get_channel(channel_id)
    timerstr = ""
    if not guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['suggested_start']:
        timerstr = ("Beep Beep! No start time has been suggested for this raid!")
    else:
        start_time = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['suggested_start']
        timerstr += _("Beep Beep! The suggested start time for this raid is {start_time}!").format(start_time=print_24_hour(start_time))

    return timerstr


"""
Behind-the-scenes functions for raid management.
Triggerable through commands or through emoji
"""


def _input_to_status(text):

    status = None

    maybe_list = ['i','interested']

    if text in maybe_list:
        status = 'maybe'

    return status

def _add_rsvp_to_dict(trainer_dict, member_id, status, count=None):

    if not trainer_dict:
        trainer_dict = {}

    if not count:
        count = 1

    if member_id not in trainer_dict:
        trainer_dict[member_id] = {}

    trainer_dict[member_id]['status'] = status
    trainer_dict[member_id]['count'] = count

    return trainer_dict



STATUS_MESSAGE = {}
STATUS_MESSAGE['waiting'] = "at the raid"
STATUS_MESSAGE['maybe'] = "interested"
STATUS_MESSAGE['omw'] = "on the way"


async def _maybe(message, count, member=None):

    if member:
        trainer = member
    else:
        trainer = message.author

    trainer_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict']

    # Add trainer name to trainer list
    if trainer.id not in trainer_dict:
        trainer_dict[trainer.id] = {}
    trainer_dict[trainer.id]['status'] = "maybe"
    trainer_dict[trainer.id]['count'] = count
    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

    if count == 1:
        # await message.channel.send( _("Beep Beep! {member} is interested!").format(member=message.author.mention))
        embed_msg = _("Beep Beep! {member} is interested!").format(member=trainer.mention)
    else:
        # await message.channel.send( _("Beep Beep! {member} is interested with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count))
        embed_msg = _("Beep Beep! {member} is interested with a total of {trainer_count} trainers!").format(member=trainer.mention, trainer_count=count)

    await message.channel.send( embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.gold()))


async def _coming(message, count):
    trainer_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict']

    # Add trainer name to trainer list
    if message.author.id not in trainer_dict:
        trainer_dict[message.author.id] = {}
    trainer_dict[message.author.id]['status'] = "omw"
    trainer_dict[message.author.id]['count'] = count
    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

    if count == 1:
        # await message.channel.send( _("Beep Beep! {member} is on the way!").format(member=message.author.mention))
        embed_msg = _("{member} is on the way!").format(member=message.author.mention)
    else:
        # await message.channel.send( _("Beep Beep! {member} is on the way with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count))
        embed_msg = _("{member} is on the way with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count)

    await message.channel.send( embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.gold()))


async def _here(message, count):
    trainer_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict']
    # Add trainer name to trainer list
    if message.author.id not in trainer_dict:
        trainer_dict[message.author.id] = {}
    trainer_dict[message.author.id]['status'] = "waiting"
    trainer_dict[message.author.id]['count'] = count
    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

    if count == 1:
        # await message.channel.send( _("Beep Beep! {member} is at the raid!").format(member=message.author.mention))
        embed_msg = _("Beep Beep! {member} is at the raid!").format(member=message.author.mention)
    else:
        # await message.channel.send( _("Beep Beep! {member} is at the raid with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count))
        embed_msg = _("Beep Beep! {member} is at the raid with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count)

    await message.channel.send( embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.green()))


def _get_trainer_names_from_dict(message, status, mentions=False, trainer_dict=None):
    if not trainer_dict:
        trainer_dict = copy.deepcopy(guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'])
    name_list = []
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == status:
            # user = Clembot.get_user_info(trainer)
            user = message.channel.guild.get_member(trainer)
            if mentions:
                # name_list.append("**<@!{trainer}>**".format(trainer=trainer))
                name_list.append(user.mention)
                # name_list.append("**<@!" + message.author.id + ">**")
            else:
                user_name = user.nick if user.nick else user.name
                count = trainer_dict[trainer]['count']
                if count > 1:
                    name_list.append("**{trainer} ({count})**".format(trainer=user_name, count=count))
                else:
                    name_list.append("**{trainer}**".format(trainer=user_name))

    if len(name_list) > 0:
        return ', '.join(name_list)
    return None


def get_count_from_channel(message, status, trainer_dict=None):
    if not trainer_dict:
        rc_d = guild_dict[message.guild.id]['raidchannel_dict']
        r = message.channel.id
        trainer_dict = rc_d[r]['trainer_dict']

    count = 0
    for trainer in trainer_dict.values():
        if trainer['status'] == status:
            count += int(trainer['count'])

    return count


def channel_status_embed(message, embed_msg_desc, colour=None):
    if colour is None:
        colour = discord.Colour.green()

    raid_embed = discord.Embed(description=embed_msg_desc, colour=colour)
    raid_embed.add_field(name="Interested / On the way / At the raid", value="{interested} / {coming} / {here}".format(here=get_count_from_channel(message, "waiting"), coming=get_count_from_channel(message, "omw"), interested=get_count_from_channel(message, "maybe")), inline=True)

    return raid_embed


async def _cancel(message):
    author = message.author
    channel = message.channel
    guild = message.guild
    try:
        t_dict = guild_dict[guild.id]['raidchannel_dict'][channel.id]['trainer_dict'][author.id]
    except KeyError:
        # await channel.send( _("Beep Beep! {member} has no status to cancel!").format(member=author.mention))
        embed_msg = _("Beep Beep! {member} has no status to cancel!").format(member=author.mention)

        await message.channel.send( embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.red()))

        return

    if t_dict['status'] == "maybe":
        if t_dict['count'] == 1:
            # await channel.send( _("Beep Beep! {member} is no longer interested!").format(member=author.mention))
            embed_msg = _("Beep Beep! {member} is no longer interested!").format(member=author.mention)
        else:
            # await channel.send( _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer interested!").format(member=author.mention, trainer_count=t_dict['count']))
            embed_msg = _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer interested!").format(member=author.mention, trainer_count=t_dict['count'])
    if t_dict['status'] == "waiting":
        if t_dict['count'] == 1:
            # await channel.send( _("Beep Beep! {member} has left the raid!").format(member=author.mention))
            embed_msg = _("Beep Beep! {member} has left the raid!").format(member=author.mention)
        else:
            # await channel.send( _("Beep Beep! {member} and their total of {trainer_count} trainers have left the raid!").format(member=author.mention, trainer_count=t_dict['count']))
            embed_msg = _("Beep Beep! {member} and their total of {trainer_count} trainers have left the raid!").format(member=author.mention, trainer_count=t_dict['count'])
    if t_dict['status'] == "omw":
        if t_dict['count'] == 1:
            # await channel.send( _("Beep Beep! {member} is no longer on their way!").format(member=author.mention))
            embed_msg = _("Beep Beep! {member} is no longer on their way!").format(member=author.mention)
        else:
            # await channel.send( _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer on their way!").format(member=author.mention, trainer_count=t_dict['count']))
            embed_msg = _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer on their way!").format(member=author.mention, trainer_count=t_dict['count'])
    t_dict['status'] = None

    await message.channel.send( embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.dark_red()))


@Clembot.event
async def on_message(message):
    try:
    # print(guild_dict)
        if message.guild is not None:
            content_without_prefix = message.content.replace(_get_prefix(Clembot, message), '')
            ar_message = guild_dict.setdefault(message.guild.id,{}).setdefault('auto-responses', {}).setdefault(message.channel.id,{}).get(content_without_prefix, None)

            if ar_message:
                return await message.channel.send(ar_message)

            if 'contest_channel' in guild_dict[message.guild.id]:
                if message.channel.id in guild_dict[message.guild.id]['contest_channel'] and guild_dict[message.guild.id]['contest_channel'][message.channel.id].get('started', False) == True:
                    await contestEntry(message)
                    return

            raid_status = guild_dict[message.guild.id]['raidchannel_dict'].get(message.channel.id, None)
            if raid_status is not None:
                is_active_channel = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id].get('active',False)
                if is_active_channel:
                    trainer_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict']
                    # if message.author.id in trainer_dict:
                    #     count = trainer_dict[message.author.id]['count']
                    # else:
                    #     count = 1
                    # omw_emoji = parse_emoji(message.guild, config['omw_id'])
                    # if message.content.startswith(omw_emoji):
                    #     emoji_count = message.content.count(omw_emoji)
                    #     await _coming(message, emoji_count)
                    #     return
                    # here_emoji = parse_emoji(message.guild, config['here_id'])
                    # if message.content.startswith(here_emoji):
                    #     emoji_count = message.content.count(here_emoji)
                    #     await _here(message, emoji_count)
                    #     return
                    if "/maps" in message.content:
                        if message.content.startswith("!update") == False:
                            await process_map_link(message)
                            return
        messagelist = message.content.split(" ")
        message.content = messagelist.pop(0).lower() + " " + " ".join(messagelist)
        await Clembot.process_commands(message)
    except Exception as error:
        print("error while processing message {message} : {error}".format(message=message.content,error=error) )

def extract_link_from_text(text):
    newloc = None
    mapsindex = text.find("/maps")
    newlocindex = text.rfind("http", 0, mapsindex)

    if newlocindex == -1:
        return newloc
    newlocend = text.find(" ", newlocindex)
    if newlocend == -1:
        newloc = text[newlocindex:]
    else:
        newloc = text[newlocindex:newlocend + 1]

    return newloc


async def process_map_link(message, newloc=None):
    if newloc == None:
        newloc = extract_link_from_text(message.content)

    if newloc == None:
        return

    if guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['type'] == 'raidparty':
        await _add(message, newloc)
        return

    reportcityid = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['reportcity']
    oldraidmsgid = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidmessage']
    oldreportmsgid = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidreport']

    reportcitychannel = Clembot.get_channel(reportcityid)

    oldraidmsg = await message.channel.get_message(oldraidmsgid)
    oldreportmsg = await reportcitychannel.get_message(oldreportmsgid)
    oldembed = oldraidmsg.embeds[0]
    newembed = discord.Embed(title=oldembed.title, url=newloc, colour=message.guild.me.colour)

    for field in oldembed.fields:
        newembed.add_field(name=field.name, value=field.value, inline=field.inline)
    newembed.set_footer(text=oldembed.footer.text, icon_url=oldembed.footer.icon_url)
    newembed.set_thumbnail(url=oldembed.thumbnail.url)
    try:
        await oldraidmsg.edit(new_content=oldraidmsg.content, embed=newembed)
    except:
        pass
    try:
        oldreportmsg.edit(new_content=oldreportmsg.content, embed=newembed)
    except:
        pass

    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidmessage'] = oldraidmsg.id
    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidreport'] = oldreportmsg.id
    otw_list = []
    trainer_dict = copy.deepcopy(guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'])
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == 'omw':
            user = await Clembot.get_user_info(trainer)
            otw_list.append(user.mention)
    await message.channel.send( content=_("Beep Beep! Someone has suggested a different location for the raid! Trainers {trainer_list}: make sure you are headed to the right place!").format(trainer_list=", ".join(otw_list)), embed=newembed)

    return



@Clembot.command(pass_context=True, hidden=True, aliases=["ex"])
@checks.cityraidchannel()
@checks.raidset()
async def exraid(ctx):
    """Report an upcoming EX raid.

    Usage: !exraid <location>
    Clembot will insert the details (really just everything after the species name) into a
    Google maps link and post the link to the same channel the report was made in.
    Clembot's message will also include the type weaknesses of the boss.

    Finally, Clembot will create a separate channel for the raid report, for the purposes of organizing the raid."""
    await __exraid(ctx)


async def __exraid(ctx):
    message = ctx.message
    argument_text = ctx.message.clean_content.lower()
    parameters = Parser.parse_arguments(argument_text, exraid_SYNTAX_ATTRIBUTE, {'gym_info' : get_gym_by_code_message}, {'message' : ctx.message})
    logger.info(parameters)
    print(parameters)

    if parameters['length'] <= 1:
        await message.channel.send(_("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return

    raidexp = None
    channel_role = None
    gym_info = None
    if parameters.get('gym_info', None):
        gym_info = parameters['gym_info']
        raid_details = gym_info['gym_name']
        channel_role_id = _get_role_for_notification(message.channel.guild.id, gym_info['gym_code'])
        channel_role = discord.utils.get(message.channel.guild.roles, id=channel_role_id)
        location_prefix = " ".join(parameters.get('others',[]))

        if len(location_prefix) >= 1:
            location_prefix = "-" + location_prefix + "-"

    else:
        location_prefix = ""
        raid_details = " ".join(parameters.get('others'))

    egg_level = 'EX'
    egg_info = raid_info['raid_eggs'][egg_level]
    egg_img = egg_info['egg_img']
    boss_list = []
    mon_in_one_line = 0
    for p in egg_info['pokemon']:
        p_name = get_name(p)
        p_type = get_type(message.guild, p)
        boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))

    region_prefix = get_region_prefix(message)
    if region_prefix:
        prefix = region_prefix + "-"
    else:
        prefix = ""

    if gym_info:
        raid_gmaps_link = gym_info['gmap_link']
    else:
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)

    raid_details = sanitize_channel_name(location_prefix) + sanitize_channel_name(raid_details)
    raid_channel_name = prefix + egg_level + "-" + raid_details

    try:
        raid_channel_category = get_category(message.channel, egg_level)
        raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=dict(message.channel.overwrites), category=raid_channel_category)
    except Exception as error:
        print(error)
        await message.channel.send(content=_("Beep Beep! An error occurred while creating the channel. {error}").format(error=error))
        return

    raid_img_url = get_egg_image_url(egg_level)
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
    if len(egg_info['pokemon']) > 1:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
        raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
    else:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)

    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    try:
        raidreport = await message.channel.send(content=_("Beep Beep! Level {level} raid egg reported by {member}! Details: {location_details}. Coordinate in {raid_channel}").format(level=egg_level, member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
    except Exception as error:
        print(error)
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _(
"""
Beep Beep! Level {level} raid egg reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
** **
Please type `!beep status` if you need a refresher of Clembot commands! 
""").format(level=egg_level, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

    raidmessage = await raid_channel.send(content=raidmsg, embed=raid_embed)

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': fetch_current_time(message.channel.guild.id) + timedelta(minutes=egg_timer) + timedelta(days=14),  # One hour from now
        'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
        'active': True,
        'raidmessage': raidmessage.id,
        'raidreport': raidreport.id,
        'address': raid_details,
        'type': 'egg',
        'pokemon': '',
        'egglevel': 'EX',
        'suggested_start': False}

    await raid_channel.send(content=_('Beep Beep! Hey {member}, if you can, set the time left until the egg hatches using **!timerset <date and time>** so others can check it with **!timer**. **<date and time>** can just be written exactly how it appears on your EX Raid Pass.').format(member=message.author.mention))

    if channel_role:
        await raid_channel.send(content=_("Beep Beep! A raid has been reported for {channel_role}.").format(channel_role=channel_role.mention))

    if len(raid_info['raid_eggs'][egg_level]['pokemon']) == 1:
        await _eggassume("assume " + get_name(raid_info['raid_eggs'][egg_level]['pokemon'][0]), raid_channel)

    record_reported_by(message.guild.id, message.author.id, 'egg_reports')

    event_loop.create_task(expiry_check(raid_channel))
    return


async def _exraid(ctx):
    message = ctx.message
    channel = message.channel
    fromegg = False
    exraid_split = message.clean_content.lower().split()
    del exraid_split[0]
    if len(exraid_split) <= 0:
        await channel.send( _("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return
    raid_details = " ".join(exraid_split)
    raid_details = raid_details.strip()
    if raid_details == '':
        await channel.send( _("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return

    raid_gmaps_link = create_gmaps_query(raid_details, message.channel)

    egg_info = raid_info['raid_eggs']['EX']
    egg_img = egg_info['egg_img']
    boss_list = []
    for p in egg_info['pokemon']:
        p_name = get_name(p)
        p_type = get_type(message.guild, p)
        boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))

    region_prefix = get_region_prefix(message)
    if region_prefix:
        prefix = region_prefix + "-"
    else:
        prefix = ""

    raid_channel_name = prefix + "ex-raid-egg-" + sanitize_channel_name(raid_details)
    raid_channel_overwrite_list = channel.overwrites
    clembot_overwrite = (Clembot.user, discord.PermissionOverwrite(send_messages=True))
    everyone_overwrite = (channel.guild.default_role, discord.PermissionOverwrite(send_messages=False))
    for overwrite in raid_channel_overwrite_list:
        if isinstance(overwrite[0], discord.Role):
            if overwrite[0].permissions.manage_guild:
                continue
        overwrite[1].send_messages = False
    raid_channel_overwrite_list.append(clembot_overwrite )
    raid_channel_overwrite_list.append(everyone_overwrite)
    raid_channel_overwrites = dict(raid_channel_overwrite_list)
    raid_channel_category = get_category(message.channel,"EX")
    raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=raid_channel_overwrites,category=raid_channel_category)

    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/eggs/{}".format(str(egg_img))
    raid_img_url = get_pokemon_image_url(5)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
    if len(egg_info['pokemon']) > 1:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
        raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
    else:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist}").format(bosslist="".join(boss_list)), inline=True)
        raid_embed.add_field(name="\u200b", value="\u200b", inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    raidreport = await channel.send( content=_("Beep Beep! EX raid egg reported by {member}! Details: {location_details}. Use the **!invite** command to gain access and coordinate in {raid_channel}").format(member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! EX raid reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!

To update your status, choose from the following commands:
**!interested, !coming, !here, !cancel**
If you are bringing more than one trainer/account, add the number of accounts total on your first status update.
Example: `!coming 5`

To see the list of trainers who have given their status:
**!list interested, !list coming, !list here**
Alternatively **!list** by itself will show all of the above.

**!location** will show the current raid location.
**!location new <address>** will let you correct the raid address.
Sending a Google Maps link will also update the raid location.

Message **!starting** when the raid is beginning to clear the raid's 'here' list.""").format(member=message.author.mention, citychannel=channel.mention, location_details=raid_details)
    raidmessage = await raid_channel.send( content=raidmsg, embed=raid_embed)

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel] = {
        'reportcity': channel.id,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': raidmessage.id,
        'raidreport': raidreport.id,
        'address': raid_details,
        'type': 'egg',
        'pokemon': '',
        'egglevel': 'EX',
        'suggested_start': False
    }

    await raid_channel.send( content=_("Beep Beep! Hey {member}, if you can, set the time the EX Raid begins using **!timerset <date and time>** so others can check it with **!timer**. **<date and time>** should look exactly as it appears on your invitation.").format(member=message.author.mention))

    event_loop.create_task(expiry_check(raid_channel))


@Clembot.command(pass_context=True, hidden=True)
@checks.citychannel()
@checks.raidset()
async def raidparty(ctx):
    """Creates a raidparty channel.

    Usage: !raidparty <channel-name>
    Finally, Clembot will create a separate channel for the raid party, for the purposes of organizing the raid."""

    await _raidparty(ctx.message)


async def _raidparty(message):
    args = message.clean_content[len("!raidparty"):]
    args_split = args.split(" ")
    del args_split[0]
    if len(args_split) < 1:
        await _send_error_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!raidparty <channel-name>**"))
        return
    raid_details = " ".join(args_split)
    raid_details = raid_details.strip()

    region_prefix = get_region_prefix(message)
    if region_prefix:
        prefix = region_prefix + "-"
    else:
        prefix = ""
    if len(raid_details) == 0 :
        raid_channel_name = prefix + "raid-party"
    else:
        raid_channel_name = prefix + sanitize_channel_name(raid_details)
    raid_channel_overwrites = message.channel.overwrites
    # clembot_overwrite = (Clembot.user, discord.PermissionOverwrite(send_messages=True))
    #
    # raid_channel_overwrites.update(clembot_overwrite)

    try:
        raid_channel_category = get_category(message.channel, None)
        raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=dict(raid_channel_overwrites) , category=raid_channel_category)
    except Exception as error:
        print(error)

    raidreport = await _send_message(message.channel, _("Beep Beep! A **raid-party** has been reported by **{member}**! Coordinate in {raid_channel}").format(member=message.author.display_name, raid_channel=raid_channel.mention))
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! A raid-party is happening and {member} will be organizing it here in {raid_channel}! Coordinate here!
** **
`!beep raidparty` lists all the command Clembot has to offer for a raid party!
`!beep raidowner` lists all the command which can be used to manage the raid party!
    """).format(member=message.author.mention, raid_channel=raid_channel.mention)

    raidmessage = await raid_channel.send( content=raidmsg)

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': None,
        'raidreport': raidreport.id,
        'address': raid_details,
        'type': 'raidparty',
        'pokemon': None,
        'egglevel': -1,
        'suggested_start': False,
        'roster': [],
        'roster_index': None,
        'started_by' : message.author.id
    }


    return


numbers = {
    "0": ":zero:",
    "1": ":one:",
    "2": ":two:",
    "3": ":three:",
    "4": ":four:",
    "5": ":five:",
    "6": ":six:",
    "7": ":seven:",
    "8": ":eight:",
    "9": ":nine:"
}


def emojify_numbers(number):
    number_emoji = ""

    reverse = "".join(reversed(str(number)))

    for digit in reverse[::-1]:
        number_emoji = number_emoji + numbers.get(digit)

    return number_emoji





# @Clembot.command(pass_context=True, hidden=True)
# @checks.citychannel()
# @checks.raidset()
# async def raidegg(ctx):
#     await _raidegg(ctx.message)


async def _raidegg(message):

        if message.channel.id in guild_dict[message.guild.id]['raidchannel_dict'].keys():
            await _send_error_message(message.channel, "Please use this command in a region channel.")
            return
        argument_text = message.clean_content.lower()
        parameters = Parser.parse_arguments(argument_text, raidegg_SYNTAX_ATTRIBUTE, {'egg' : is_egg_level_valid, 'gym_info' : get_gym_by_code_message}, {'message' : message})
        logger.info(parameters)
        print(parameters)
        if parameters['length'] <= 2:
            await message.channel.send(_("Beep Beep! Give more details when reporting! Usage: **!raidegg <level> <location>**"))
            return

        if parameters.get('egg', None):
            egg_level = parameters['egg']
        else:
            await message.channel.send(_("Beep Beep! Give more details when reporting! Use at least: **!raidegg <level> <location>**. Type **!help** raidegg for more info."))
            return

        if parameters.get('timer', None) == None:
            raidexp = False
        else:
            raidexp = parameters['timer']

        if raidexp is not False:
            if _timercheck(raidexp, egg_timer):
                await message.channel.send(_("Beep Beep...that's too long. Raid Eggs currently last no more than {egg_timer} minutes...".format(egg_timer=egg_timer)))
                return

        channel_role = None
        gym_info = None
        if parameters.get('gym_info', None):
            gym_info = parameters['gym_info']
            raid_details = gym_info['gym_name']
            channel_role_id = _get_role_for_notification(message.channel.guild.id, gym_info['gym_code'])
            channel_role = discord.utils.get(message.channel.guild.roles, id=channel_role_id)
        else:
            raid_details = " ".join(parameters.get('others'))


        if egg_level > 5 or egg_level == 0:
            await message.channel.send(_("Beep Beep! Raid egg levels are only from 1-5!"))
            return
        else:
            egg_level = str(egg_level)
            egg_info = raid_info['raid_eggs'][egg_level]
            egg_img = egg_info['egg_img']
            boss_list = []
            mon_in_one_line = 0
            for p in egg_info['pokemon']:
                p_name = get_name(p)
                p_type = get_type(message.guild, p)
                boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))

            region_prefix = get_region_prefix(message)
            if region_prefix:
                prefix = region_prefix + "-"
            else:
                prefix = ""

            if gym_info:
                raid_gmaps_link = gym_info['gmap_link']
                raid_channel_name = prefix + "level-" + egg_level + "-egg-" + sanitize_channel_name(gym_info['gym_name'])
            else:
                raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
                raid_channel_name = prefix + "level-" + egg_level + "-egg-" + sanitize_channel_name(raid_details)
            try:
                raid_channel_category = get_category(message.channel, egg_level)
                raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=dict(message.channel.overwrites), category=raid_channel_category)
            except Exception as error:
                print(error)
                await message.channel.send(content=_("Beep Beep! An error occurred while creating the channel. {error}").format(error=error))
                return

            raid_img_url = get_egg_image_url(egg_level)
            raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
            if len(egg_info['pokemon']) > 1:
                raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
                raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
            else:
                raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)

            raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
            raid_embed.set_thumbnail(url=raid_img_url)
            try:
                raidreport = await message.channel.send(content=_("Beep Beep! Level {level} raid egg reported by {member}! Details: {location_details}. Coordinate in {raid_channel}").format(level=egg_level, member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
            except Exception as error:
                print(error)
            await asyncio.sleep(1)  # Wait for the channel to be created.

            raidmsg = _("""Beep Beep! Level {level} raid egg reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
Please type `!beep status` if you need a refresher of Clembot commands! 
""").format(level=egg_level, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

            raidmessage = await raid_channel.send(content=raidmsg, embed=raid_embed)

            guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
                'reportcity': message.channel.id,
                'trainer_dict': {},
                'exp': fetch_current_time(message.channel.guild.id) + timedelta(minutes=egg_timer),  # One hour from now
                'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
                'active': True,
                'raidmessage': raidmessage.id,
                'raidreport': raidreport.id,
                'address': raid_details,
                'type': 'egg',
                'pokemon': '',
                'egglevel': egg_level,
                'suggested_start': False}

            if raidexp is not False:
                await _timerset(raid_channel, raidexp)
            else:
                await raid_channel.send(content=_("Beep Beep! Hey {member}, if you can, set the time left until the egg hatches using **!timerset <minutes>** so others can check it with **!timer**.").format(member=message.author.mention))

            if channel_role:
                await raid_channel.send(content=_("Beep Beep! A raid has been reported for {channel_role}.").format(channel_role=channel_role.mention))

            if len(raid_info['raid_eggs'][egg_level]['pokemon']) == 1:
                await _eggassume("assume " + get_name(raid_info['raid_eggs'][egg_level]['pokemon'][0]), raid_channel)
            elif egg_level == "5" and get_number(guild_dict[raid_channel.guild.id]['configuration']['settings'].get('regional', None)) in raid_info['raid_eggs']["5"]['pokemon']:
                await _eggassume('assume ' + guild_dict[raid_channel.guild.id]['configuration']['settings']['regional'], raid_channel)

            guild_dict[message.channel.guild.id].setdefault("configuration", {}).setdefault("settings", {})["regional"]

            record_reported_by(message.guild.id, message.author.id, 'egg_reports')

            event_loop.create_task(expiry_check(raid_channel))




async def _eggassume(args, raid_channel):
    eggdetails = guild_dict[raid_channel.guild.id]['raidchannel_dict'][raid_channel.id]
    egglevel = eggdetails['egglevel']
    if config['allow_assume'][egglevel] == "False":
        await raid_channel.send( _("Beep Beep! **!raid assume** is not allowed in this level egg."))
        return
    entered_raid = re.sub("[\@]", "", args.lstrip("assume").lstrip(" ").lower())
    if entered_raid not in pkmn_info['pokemon_list']:
        await raid_channel.send( spellcheck(entered_raid))
        return
    else:
        if entered_raid not in get_raidlist():
            await raid_channel.send( _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
            return
        else:
            if get_number(entered_raid) not in raid_info['raid_eggs'][egglevel]['pokemon']:
                await raid_channel.send( _("Beep Beep! The Pokemon {pokemon} does not hatch from level {level} raid eggs!").format(pokemon=entered_raid.capitalize(), level=egglevel))
                return

    eggdetails['pokemon'] = entered_raid
    raidrole = discord.utils.get(raid_channel.guild.roles, name=entered_raid)
    if raidrole is None:
        raidrole = await raid_channel.guild.create_role(name=entered_raid, hoist=False, mentionable=True)
        # await asyncio.sleep(0.5)
        raid_role = "**{pokemon}**".format(pokemon=entered_raid.capitalize())
    else:
        raid_role = raidrole.mention
        await raid_channel.send( _("Beep Beep! This egg will be assumed to be {pokemon} when it hatches!").format(pokemon=raid_role))
    guild_dict[raid_channel.guild.id]['raidchannel_dict'][raid_channel.id] = eggdetails
    return


async def _eggtoraid(entered_raid, channel):
    try:
        eggdetails = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]
        egglevel = eggdetails['egglevel']
        reportcity = eggdetails['reportcity']
        reportcitychannel = Clembot.get_channel(reportcity)
        manual_timer = eggdetails['manual_timer']
        trainer_dict = eggdetails['trainer_dict']
        egg_address = eggdetails['address']
        notes = eggdetails.get('notes', [])
        archive = eggdetails.get('archive',False)
        try:
            egg_report = await reportcitychannel.get_message(eggdetails['raidreport'])
            raid_message = await channel.get_message(eggdetails['raidmessage'])
            raid_messageauthor = raid_message.mentions[0]
        except Exception as error:
            print(error)

        if eggdetails.get('egglevel',None):
            suggested_start = eggdetails['suggested_start']
            raidexp = eggdetails['exp'] + timedelta(minutes=raid_timer)
            hatchtype = "raid"
            raidreportcontent = _("Beep Beep! The egg has hatched into a {pokemon} raid! Details: {location_details}. Coordinate in {raid_channel}").format(pokemon=entered_raid.capitalize(), location_details=egg_address, raid_channel=channel.mention)

        if entered_raid not in pkmn_info['pokemon_list']:
            await channel.send( spellcheck(entered_raid))
            return
        else:
            if entered_raid not in get_raidlist():
                await channel.send( _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
                return
            else:
                if get_number(entered_raid) not in raid_info['raid_eggs'][egglevel]['pokemon']:
                    await channel.send( _("Beep Beep! The Pokemon {pokemon} does not hatch from level {level} raid eggs!").format(pokemon=entered_raid.capitalize(), level=egglevel))
                    return

        region_prefix = get_region_prefix_by_channel_id(guild_id=channel.guild.id, channel_id=reportcitychannel.id)
        if region_prefix:
            prefix = region_prefix + "-"
        else:
            prefix = ""

        raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(egg_address)
        oldembed = raid_message.embeds[0]
        raid_gmaps_link = oldembed.url
        raid = discord.utils.get(channel.guild.roles, name=entered_raid)
        if raid is None:
            # raid = await Clembot.create_role(guild=channel.guild, name=entered_raid, hoist=False, mentionable=True)
            # await asyncio.sleep(0.5)
            raid_role = "**" + entered_raid.capitalize() + "**"
        else:
            raid_role = raid.mention

        raid_number = pkmn_info['pokemon_list'].index(entered_raid) + 1
        raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(raid_number).zfill(3))
        raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite
        raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the raid!"), url=raid_gmaps_link, colour=channel.guild.me.colour)
        raid_embed.add_field(name="**Details:**", value=_("{pokemon} ({pokemonnumber}) {type}").format(pokemon=entered_raid.capitalize(), pokemonnumber=str(raid_number), type="".join(get_type(channel.guild, raid_number)), inline=True))
        raid_embed.add_field(name="**Weaknesses:**", value=_("{weakness_list}").format(weakness_list=weakness_to_str(channel.guild, get_weaknesses(entered_raid))), inline=True)
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=raid_messageauthor.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=raid_messageauthor, format="jpg", size=32)))
        raid_embed.set_thumbnail(url=raid_img_url)
        try:
            await channel.edit(name=raid_channel_name) # topic=raidexp.strftime('Ends on %B %d at %I:%M %p (%H:%M)')
        except Exception as error:
            print(error)
        raidmsg = _("""
Beep Beep! The egg reported by {member} in {citychannel} hatched into a {pokemon} raid! Details: {location_details}. Coordinate here!
This channel will be deleted five minutes after the timer expires.
** **
Please type `!beep raid` if you need a refresher of Clembot commands! 
    """).format(member=raid_messageauthor.mention, citychannel=reportcitychannel.mention, pokemon=raid_role, location_details=egg_address)

        try:
            await raid_message.edit(new_content=raidmsg, embed=raid_embed, content=raidmsg)
            raid_message_id = raid_message.id
        except (discord.errors.NotFound, AttributeError):
            raid_message_id = None

        try:
            await egg_report.edit(new_content=raidreportcontent, embed=raid_embed, content=raidreportcontent)
            egg_report_id = egg_report.id
        except (discord.errors.NotFound, AttributeError):
            egg_report_id = None


        guild_dict[channel.guild.id]['raidchannel_dict'][channel.id] = {
            'archive' : archive,
            'reportcity': reportcity,
            'trainer_dict': trainer_dict,
            'exp': raidexp,
            'manual_timer': manual_timer,
            'active': True,
            'raidmessage' : raid_message_id,
            'raidreport' : egg_report_id,
            'address': egg_address,
            'type': hatchtype,
            'pokemon': entered_raid,
            'egglevel': egglevel,
            'notes' : notes,
            'suggested_start': suggested_start
        }

        trainer_list = []
        trainer_dict = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['trainer_dict']
        for trainer in trainer_dict.keys():
            if trainer_dict[trainer]['status'] == 'maybe' or trainer_dict[trainer]['status'] == 'omw' or trainer_dict[trainer]['status'] == 'waiting':
                user = await Clembot.get_user_info(trainer)
                trainer_list.append(user.mention)

                # or len(raid_info['raid_eggs']['EX']['pokemon']) > 1
        try:
            if eggdetails.get('egglevel', None):
                await channel.send( content=_("Beep Beep! Trainers {trainer_list}: The raid egg has just hatched into a {pokemon} raid!").format(trainer_list=", ".join(trainer_list), pokemon=raid_role), embed=raid_embed)
        except Exception as error:
            print(error)
    except Exception as mainerror:
        print(error)
    event_loop.create_task(expiry_check(channel))




def get_guild_local_leaderboard(guild_id):
    configuration = gymsql.read_guild_configuration(guild_id=guild_id)
    leaderboard_type = None
    if configuration:
        leaderboard_type = configuration.get('leaderboard-type',None)

    return leaderboard_type


@Clembot.command(pass_context=True, hidden=True)
async def gymhelp(ctx):
    await ctx.message.channel.send( _("Beep Beep! We've moved this command to `!beep gym`."))


def get_region_prefix_by_channel_id(guild_id, channel_id):
    configuration = gymsql.read_guild_configuration(guild_id=guild_id)

    if configuration:
        if configuration.get('add_region_prefix',None):
            channel_configuration = gymsql.read_guild_configuration(guild_id=guild_id, channel_id=channel_id)
            if channel_configuration:
                return channel_configuration.get('region_prefix',"")

    return ""

def get_region_prefix(message):
    configuration = gymsql.read_guild_configuration(guild_id=message.guild.id)

    if configuration:
        if configuration.get('add_region_prefix',None):
            channel_configuration = gymsql.read_guild_configuration(guild_id=message.guild.id, channel_id=message.channel.id)
            if channel_configuration:
                return channel_configuration.get('region_prefix',"")

    return ""

async def _get_channel_config(message):
    content = "Beep Beep! No guild configuration found!"

    configuration = gymsql.read_guild_configuration(message.guild.id, message.channel.id)
    if configuration:
        content = "Beep Beep! Server Configuration : \n{configuration}".format(configuration=configuration)

    await message.channel.send( content=content)


@Clembot.command(pass_context=True, hidden=True, aliases=["get-channel-config"])
@checks.guildowner_or_permissions(manage_guild=True)
async def get_channel_config(ctx):
    await _get_channel_config(ctx.message)


# !set-guild-config add_region_prefix SO
@Clembot.command(pass_context=True, hidden=True, aliases=["set-channel-config"])
@checks.guildowner_or_permissions(manage_guild=True)
async def set_channel_config(ctx):
    args = ctx.message.content
    args_split = args.split(" ")
    del args_split[0]

    new_configuration={}

    if len(args_split) == 2:
        key = args_split[0]
        value = args_split[1]
        new_configuration[key] = value

    configuration = gymsql.read_guild_configuration(ctx.message.guild.id, ctx.message.channel.id)


    if configuration:
        configuration.update(new_configuration)
    else:
        configuration = new_configuration


    configuration = gymsql.save_guild_configuration(guild_id=ctx.message.guild.id, channel_id=ctx.message.channel.id, configuration=configuration)

    if configuration:
        await _get_channel_config(ctx.message)
    else:
        await ctx.message.channel.send( content="Beep Beep! I couldn't set the configuration successfully.")


def _update_guild_config(guild_id, new_configuration):
    configuration = gymsql.read_guild_configuration(guild_id)

    if configuration:
        configuration.update(new_configuration)
    else:
        configuration = new_configuration

    configuration = gymsql.save_guild_configuration(guild_id=guild_id, configuration=configuration)

    return configuration


def _get_guild_config_for(guild_id, config_key):
    configuration = gymsql.read_guild_configuration(guild_id)
    if configuration:
        return configuration.get(config_key,None)
    return None


def _get_bingo_event_pokemon(guild_id, config_key):
    # bingo_event_pokemon = _get_guild_config_for(guild_id,config_key)
    # if bingo_event_pokemon:
    #     return bingo_event_pokemon

    bingo_event_pokemon = gymsql.find_clembot_config(config_key)
    return bingo_event_pokemon

async def _get_guild_config(message):
    content = "Beep Beep! No guild configuration found!"

    configuration = gymsql.read_guild_configuration(message.guild.id)
    if configuration:
        content = "Beep Beep! Server Configuration : \n{configuration}".format(configuration=json.dumps(configuration, indent=2, sort_keys=True))

    await _send_message(message.channel, content)


@Clembot.command(pass_context=True, hidden=True, aliases=["get-guild-config"])
@checks.guildowner_or_permissions(manage_guild=True)
async def get_guild_config(ctx):
    await _get_guild_config(ctx.message)


# !set-guild-config add_region_prefix SO
@Clembot.command(pass_context=True, hidden=True, aliases=["set-guild-config"])
@checks.guildowner_or_permissions(manage_guild=True)
async def set_guild_config(ctx):
    args = ctx.message.content
    args_split = args.split()
    del args_split[0]

    new_configuration={}

    if len(args_split) == 2:
        key = args_split[0]
        value = args_split[1]
        new_configuration[key]=value


    configuration = gymsql.read_guild_configuration(ctx.message.guild.id)

    if configuration:
        configuration.update(new_configuration)
    else:
        configuration = new_configuration

    configuration = gymsql.save_guild_configuration(guild_id=ctx.message.guild.id, configuration=configuration)

    if configuration:
        await _get_guild_config(ctx.message)
    else:
        await ctx.message.channel.send( content="Beep Beep! I couldn't set the configuration successfully.")




@Clembot.command(pass_context=True, hidden=True, aliases=["set-guild-city"])
@checks.guildowner_or_permissions(manage_guild=True)
async def _set_guild_city(ctx):
    args = ctx.message.content
    args_split = args.split(" ")
    del args_split[0]

    city_state = "".join(args_split).upper()

    new_city_state = gymsql.save_guild_city(ctx.message.guild.id, city_state)

    if new_city_state:
        await _get_guild_city(ctx.message)
    else:
        await ctx.message.channel.send( content="Beep Beep! I couldn't set the Reporting City successfully.")


@Clembot.command(pass_context=True, hidden=True, aliases=["set-city"])
async def _set_city(ctx):
    args = ctx.message.content
    args_split = args.split(" ")
    del args_split[0]

    city_state = "".join(args_split).upper()

    new_city_state = gymsql.save_channel_city(ctx.message.guild.id, ctx.message.channel.id, city_state)

    if new_city_state:
        return_message = await _get_city(ctx.message)
    else:
        return_message = await ctx.message.channel.send( content="Beep Beep! I couldn't set the Reporting City successfully.")

    await asyncio.sleep(5)
    await ctx.message.delete()


@Clembot.command(pass_context=True, hidden=True, aliases=["get-city"])
async def get_city(ctx):
    await _get_city(ctx.message)


@Clembot.command(pass_context=True, hidden=True, aliases=["get-guild-city"])
@checks.guildowner_or_permissions(manage_guild=True)
async def get_guild_city(ctx):
    await _get_guild_city(ctx.message)


async def _get_city(message):
    content = "Beep Beep! Reporting City for this channel / guild has not been set."

    channel_city = gymsql.read_channel_city(message.guild.id, message.channel.id)
    if channel_city:
        content = "Beep Beep! **{member}** Reporting City for this channel is **{channel_city}**.".format(member=message.author.display_name,channel_city=channel_city)
    else:
        guild_city = gymsql.read_guild_city(message.guild.id)
        if guild_city:
            content = "Beep Beep! **{member}** Reporting City for this guild is **{guild_city}**.".format(member=message.author.display_name, guild_city=guild_city)

    return await _send_message(message.channel, content)


async def _get_guild_city(message):
    guild_city = gymsql.read_guild_city(message.guild.id)
    content = "Beep Beep! **{member}** Reporting City for this guild is **{guild_city}**.".format(member=message.author.display_name, guild_city=guild_city)

    return await _send_message(message.channel, content)


@Clembot.command(pass_context=True, hidden=True)
async def gymlookup(ctx):
    """looks up gym information based on gym code.

    Usage: !gymlookup <prefix>
    Clembot will search and will list all gyms which start with the provided prefix."""

    await _gymlookup(ctx.message)


async def _gymlookup(message):
    return await _send_error_message(message.channel, "Beep Beep... **{member}** this command has been moved to **!gyms**.".format(member=message.author.display_name))


@Clembot.command(pass_context=True, hidden=False)
async def status(ctx):
    try:

        raid_channel_dict = get_raid_channel_dict(ctx.message)

        if raid_channel_dict is None:
            await ctx.message.channel.send( content="Beep Beep! This channel is not active anymore, feel free to tag any admin to clean it up!")
            return
        status_map = copy.deepcopy(guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id])
        exp = status_map.pop('exp',None)
        if exp:
            status_map['exp'] = exp.strftime("%Y-%m-%d %H:%M:%S")

        suggested_start = status_map.pop('suggested_start')
        if suggested_start:
            status_map['suggested_start'] = suggested_start.strftime("%Y-%m-%d %H:%M:%S")
        await ctx.message.channel.send( content=json.dumps(status_map, indent=4, sort_keys=True))

    except Exception as error:
        await ctx.message.channel.send( content=error)


@Clembot.command(pass_context=True, hidden=True)
async def gyms(ctx):
    await _gyms(ctx.message)


async def _gyms(message):
    args = message.content
    args_split = args.split(" ")
    del args_split[0]

    gym_code = args_split[0].upper()

    if len(gym_code) < 1:
        await _send_error_message(message.channel, "Beep Beep... **{member}** I need at-least one character for lookup!".format(member=message.author.display_name))
        return

    city = _read_channel_city(message)
    gym_message_output = ""
    try:

        list_of_gyms = await _get_gym_info_list(message, gym_code)

        if len(list_of_gyms) < 1:
            await _send_error_message(message.channel, "Beep Beep... **{member}** I could not find any gym starting with **{gym_code}** for **{city}**!".format(member=message.author.display_name, city=city, gym_code=gym_code))
            return

        gym_message_output = "Beep Beep! **{member}** Here is a list of gyms for **{city}** :\n\n".format(member=message.author.display_name, city=city)

        for gym_info in list_of_gyms:
            new_gym_info = "**{gym_code}** - {gym_name}\n".format(gym_code=gym_info.get('gym_code_key').ljust(6), gym_name=gym_info.get('gym_name'))

            if len(gym_message_output) + len(new_gym_info) > 1990:
                await _send_message(message.channel, gym_message_output)
                gym_message_output = ""

            gym_message_output += new_gym_info

        if gym_message_output:
            await _send_message(message.channel, gym_message_output)
        else:
            await _send_error_message(message.channel, "Beep Beep... **{member}** No matches found for **{gym_code}** in **{city}**!".format(member=message.author.display_name,gym_code=gym_code, city=city))
    except Exception as error:
        print(error)
        await _send_error_message(message.channel, "Beep Beep...**{member}** No matches found for **{gym_code}** in **{city}**!".format(member=message.author.display_name,gym_code=gym_code, city=city))


def _read_channel_city(message):
    city = gymsql.read_channel_city(guild_id=message.guild.id, channel_id=message.channel.id)
    if city == None:
        try:
            parent_city_id = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id].get('reportcity', 0)
            city = gymsql.read_channel_city(guild_id=message.guild.id, channel_id=parent_city_id)
        except Exception:
            pass
        if city == None:
            city = gymsql.read_guild_city(guild_id=message.guild.id)
    if city:
        return city
    return None

def get_help_embed(description, usage, available_value_title, available_values, mode="message"):

    if mode == "message":
        color = discord.Colour.green()
    else:
        color = discord.Colour.red()

    help_embed = discord.Embed( description="**{0}**".format(description), colour=color)

    help_embed.add_field(name="**Usage :**", value = "**{0}**".format(usage))
    help_embed.add_field(name="**{0} :**".format(available_value_title), value=_("**{0}**".format(", ".join(available_values))), inline=False)

    return help_embed


async def _send_error_message(channel, description):

    color = discord.Colour.red()
    error_embed = discord.Embed(description="{0}".format(description), colour=color)
    return await channel.send(embed=error_embed)

async def _send_message(channel, description):
    try:

        error_message = "The output contains more than 2000 characters."
        if len(description) >= 2000:
            discord.Embed(description="{0}".format(error_message), colour=color)

        color = discord.Colour.green()
        message_embed = discord.Embed(description="{0}".format(description), colour=color)

        return await channel.send(embed=message_embed)
    except Exception as error:
        print(error)

async def _send_embed(channel, description=None, title=None, additional_fields={}, footer=None):

        embed = discord.Embed(description=description, colour=discord.Colour.gold(), title=title)

        for label, value in additional_fields.items():
            embed.add_field(name="**{0}**".format(label), value=value)

        if footer:
            embed.set_footer(text=footer)

        try:
            return await channel.send(embed=embed)
        except Exception as error:
            return await channel.send(error)

def get_beep_embed(title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

    if mode == "message":
        color = discord.Colour.green()
    else:
        color = discord.Colour.red()

    help_embed = discord.Embed( title = title, description=f"{description}", colour=color)

    # help_embed.add_field(name="**Usage :**", value = "**{0}**".format(usage))
    # help_embed.add_field(name="**{0} :**".format(available_value_title), value=_("**{0}**".format(", ".join(available_values))), inline=False)
    help_embed.set_footer(text=footer)
    return help_embed

@Clembot.command(pass_context=True, hidden=True, aliases=["import-gymx"])
@commands.has_permissions(manage_channels=True)
async def _importx(ctx, *, gym_list_in_json_text):
    try:

        gym_info_1 = {}
        gym_info_1['Name'] = 'Gym Name'
        # gym_info_1['OriginalName'] = 'Gym Original Name (if different)'
        gym_info_1['Latitude'] = 00.00000
        gym_info_1['Longitude'] = 00.00000
        gym_info_1['CityState'] = 'CITY,STATE'

        gym_info_list = [ gym_info_1 ]

        args = ctx.message.clean_content.split()

        if len(args) == 1:
            return await _send_message(ctx.message.channel, "Beep Beep! **{member}**, please provide gym information is following format. \n```!import-gym \n{gym_info}```\n You can use https://www.csvjson.com/csv2json to convert CSV to JSON.".format(member=ctx.message.author.display_name, gym_info=json.dumps(gym_info_list, indent=4)))


        gym_info_text = ctx.message.clean_content[len("!import-gym"):]

        gym_info_list = json.loads(gym_info_text)

        list_of_msg = []

        for gym_info_1 in gym_info_list:

            gym_name_words = gym_info_1['Name'].upper().split(' ')
            words_1 = words_2 = words_3 = ''
            words_1 = gym_name_words[0]
            if len(gym_name_words) >= 2:
                words_2 = gym_name_words[1]

            if len(gym_name_words) >= 3:
                words_3 = gym_name_words[2]

            gym_code_key = words_1[:2] + words_2[:2] + words_3[:2]

            city,state = gym_info_1['CityState'].split(",")

            gmap_url = "https://www.google.com/maps/place/{0},{1}".format(gym_info_1['Latitude'],gym_info_1['Longitude'])

            gym_info_to_save = {}
            gym_info_to_save['city_state_key'] = city+state
            gym_info_to_save['gym_code_key'] = gym_code_key
            gym_info_to_save['gym_name'] = gym_info_1['Name']
            gym_info_to_save['original_gym_name'] = gym_info_1.get('OriginalName',gym_info_1['Name'])
            gym_info_to_save['gmap_url'] = gmap_url
            gym_info_to_save['latitude'] = gym_info_1['Latitude']
            gym_info_to_save['longitude'] = gym_info_1['Longitude']
            gym_info_to_save['region_code_key'] = city+state
            gym_info_to_save['word_1'] = words_1[:2]
            gym_info_to_save['word_2'] = words_2[:2]
            gym_info_to_save['word_3'] = words_3[:2]
            gym_info_to_save['gym_location_city'] = city
            gym_info_to_save['gym_location_state'] = state

            message_text = "Beep Beep! **{0}**, Gym **{1}** has been added successfully.".format(ctx.message.author.display_name, gym_info_to_save['original_gym_name'])

            gym_info_already_saved = gymsql.find_gym(city+state,gym_code_key)
            if gym_info_already_saved:
                message_text = "Beep Beep! **{0}**, Gym **{1}** already exists for **{2}**.".format(ctx.message.author.display_name, gym_info_to_save['original_gym_name'], city+state)
                confirmation_msg = await _send_error_message(ctx.message.channel, message_text)
            else:
                gymsql.insert_gym_info(gym_info_to_save)
                confirmation_msg = await _send_message(ctx.message.channel, message_text)

            list_of_msg.append(confirmation_msg)

        # await asyncio.sleep(5)
        # for msg in list_of_msg:
            # await msg.delete()
            # await asyncio.sleep(2)

        await asyncio.sleep(15)
        await ctx.message.delete()

    except Exception as error:
        return await _send_error_message(ctx.message.channel, error)
        print(error)


@Clembot.command(pass_context=True, hidden=True)
async def nest(ctx):
    try:
        message=ctx.message

        argument_text = message.clean_content
        parameters = Parser.parse_arguments(argument_text, nest_SYNTAX_ATTRIBUTE, {'link': extract_link_from_text, 'pokemon': is_pokemon_valid, 'gym_info' : get_gym_by_code_message}, {'message' : message})

        if parameters.get('length') <= 2:
            return await _send_error_message(ctx.message.channel, "**{0}**, Please use **!beep nest** to see the correct usage.".format(message.author.display_name))

        pokemon = parameters.get('pokemon', [None])[0]
        if pokemon == None:
           return await _send_error_message(ctx.message.channel, "**{0}**, Did you spell the pokemon right?".format(message.author.display_name))

        link = parameters.get('link', None)
        location_name = " ".join(parameters.get('others',['']))
        if link == None:
            gym_info = None
            if parameters.get('gym_info', None):
                gym_info = parameters['gym_info']
                location_name = gym_info['gym_name']
                link = gym_info['gmap_link']

        if link:
            embed_title = _("Beep Beep! Click here for the directions to {location}!".format(location=location_name))
        else:
            embed_title = _("Beep Beep! A nest has been reported!")


        raid_number = pkmn_info['pokemon_list'].index(pokemon.lower()) + 1
        raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite

        embed_desription = _("**Pokemon :** {pokemon}\n**Nest Reported at :** {location}\n").format(pokemon=pokemon.capitalize(), location=location_name)

        nest_embed = discord.Embed(title=embed_title, description=embed_desription, url=link, colour=discord.Colour.gold())
        nest_embed.set_thumbnail(url=raid_img_url)
        nest_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))

        await message.channel.send(embed=nest_embed)

    except Exception as error:
        print("{0} while processing message.".format(error))


    await asyncio.sleep(15)
    await ctx.message.delete()


@Clembot.command(pass_context=True, hidden=True)
async def gym(ctx):
    try:
        args = ctx.message.content
        args_split = args.split(" ")
        del args_split[0]

        gym_code = args_split[0].upper()

        if gym_code:

            gym_info = await _get_gym_info(ctx.message, gym_code)
            if gym_info:
                await _update_channel_with_link(ctx.message, gym_info['gmap_url'])
                guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['address'] = gym_info['gym_name']
                await _change_channel_name(ctx.message, gym_info)
            # else:
            #     gym_info = await _get_gym_info_old(ctx.message, gym_code)
            #     if gym_info:
            #         await _update_channel_with_link(ctx.message, gym_info['gmap_link'])



        else:
            await _send_error_message(ctx.message.channel, "Beep Beep... I will need a gym-code to search for a gym. Use **!gyms** with a letter to bring up all gyms starting from that letter!")
            return
    except Exception as error:
        print(error)
        logger.info(error)

async def _generate_gym_embed_old(message, gym_info):
    try:
        gym_location = gym_info['gmap_link']
        gym_name = gym_info['gym_name']
        gym_code = gym_info['gym_code']
        embed_title = _("Click here for direction to {gymname}!").format(gymname=gym_name)

        embed_desription = _("Gym Code : {gymcode}\nGym Name: {gymname}").format(gymcode=gym_code, gymname=gym_name)

        raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title), url=gym_location, description=embed_desription)

        embed_map_image_url = fetch_gmap_image_link(gym_info['lat_long'])
        raid_embed.set_image(url=embed_map_image_url)
        roster_message = "here are the gym details! "
        raid_embed.set_footer(text="Note: Still using old gym-codes? lookup new gym-codes using !gyms command.")

        await message.channel.send( content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention, roster_message=roster_message), embed=raid_embed)
    except Exception as error:
        print(error)


async def _change_channel_name(message, gym_info):
    try:

        raid_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]

        region_prefix = get_region_prefix(message)
        if region_prefix:
            prefix = region_prefix + "-"
        else:
            prefix = ""

        if raid_dict['type'] == 'egg':
            egg_level = raid_dict['egglevel']
            raid_channel_name = prefix + "level-" + egg_level + "-egg-" + sanitize_channel_name(gym_info['gym_name'])
        else :
            entered_raid = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['pokemon']
            raid_channel_name = prefix + entered_raid + "-" + sanitize_channel_name(gym_info['gym_name'])

        await message.channel.edit(name=raid_channel_name)
    except Exception as error:
        print(error)


async def _update_channel_with_link(message, link):
    try:

        gym_location_update = False
        if check_raid_channel(message.channel.id):
            gym_location_update = await ask_confirmation(message, "Do you want to update this raid's location?", "Updating raid's location...", "Thank you", "Too late! try again!")
        elif check_raidparty_channel(message.channel.id):
            gym_location_update = True

        if gym_location_update:
            await process_map_link(message, link)
    except Exception as error:
        print(error)


def check_raid_channel(channel_id):
    channel = Clembot.get_channel(channel_id)
    type = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['type']

    if type == 'raid' or type == 'egg':
        return True
    return False


def check_raidparty_channel(channel_id):
    channel = Clembot.get_channel(channel_id)
    type = guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['type']

    if type == 'raidparty':
        return True
    return False


# ---------------------------------------------------------------------------------------

beepmsg = _("""**{member}, !beep** can be used with following options:

**!beep report** - to see commands to report raid or raidegg.
**!beep raid** - for raid specific commands.
**!beep wild** - for wild reports and subscription commands.
**!beep gym** - for gym code related commands.
**!beep notification** - for notification related commands.

**!beep raidparty** - for raidparty related commands
**!beep raidowner** - for raidparty organizres

**!beep research** - for research quest reporting commands.
**!beep nest** - for nest reporting commands.

**!beep exraid** - for EX-raid reporting commands.

""")


beep_report = _(
"""**{member}** to report raids, eggs or wild pokemon use following commands:

**!raid <pokemon> <place or gym-code> [timer]** - to create a channel for pokemon raid at place with timer remaining.

**!raid <level> <place or gym-code> [timer]** - to create a channel for specified level egg at place with timer remaining.

*Note: **!r** can be used in place of **!raid***

**!raidparty <raid-party-channel-name>** - to create a channel for raid party where multiple raids are done by a group back to back. 

Also, see **!beep gym** for gym-code commands!
""")

beep_wild = _(
"""**{member}** here are the commands for wild reporting:

**!wild <pokemon> <location>** - to report a wild sighting of a pokemon at the location.

**!want** - brings up a list of pokemon which can be subscribed for notifications via raid or wild commands.

**!want <pokemon>** - to add a pokemon in your want list of subscription
**!unwant <pokemon>** - to remove a pokemon in your want list of subscription
""")

beep_raid = _("""
**{member}** here are the commands for a raid channel:

**!timer** - shows the expiry time for the raid.
**!timerset <minutes>** - set the expiry time for the raid.

**!raid <pokemon>** - to update egg channel into an open raid.

**!start HH:MM AM/PM** - to **suggest** a start time.
**!starting** - to clear the **here** list.

**!weather** - to see the current weather or a list of weather options.
**!weather <weather>** - to set the weather for the raid.

**!counters** - to bring counters information from PokeBattler.

**!mention [status] <message>** - to send a message to all trainers whose responded with status. If status is not given everyone in the channel is mentioend.

Also, see **!beep status** for additional raid commands!
""")


beep_status = _("""
**{member}** to update your status, choose from the following commands:

**!interested** or **!i** - to mark your status as **interested** for the raid
**!coming** or **!c** - to mark your status as **coming** for the raid
**!here** or **!h** - to mark your status as **here** for the raid
**!cancel** or **!x** - to **cancel** your status 

If you are bringing more than one trainer/account, add the number of accounts total on your first status update.
Example: **!coming 5** or **!c 5**

If you are RSVP for another trainer just tag them.
Example: **!c {bot} 2**

**!list** or **!l** - lists status of all members for the raid.

Also, see **!beep raid** for additional raid commands!
""")


beep_raidparty = ("""
**{member}** here are the commands to work with raid party. 

**!roster** - to print the current roster
**!where** - to see the pathshare path ( if applicable )
**!where <location #>** will tell directions for location #
**!current** will tell you current location of the raid party
**!next** will tell you where the raid party is headed next.
** ** 
to update your status, choose from the following commands:
** **
**!interested**, **!coming**, **!here** or **!cancel**
or alternatively use the shortcuts 
**!i**, **!c**, **!h** or **!x**
** **

Also, see **!beep raidowner** for Raid Party management commands!
""")

beep_raidowner = ("""**{member}** here are the commands to organize raid party:

**!raidparty <channel name>** creates a raid party channel
**!add <pokemon or egg> <gym-code or gym name or location> [eta]** adds a location into the roster

**!move** moves raid party to the next location in roster

**!update <location#> <gym-code>** - to update the gym code for location #
**!update <location#> <pokemon>** - to update the pokemon for location #
**!update <location#> <eta>** - to updates the eta for location #
**!remove <location#>** - to remove specified location from roster
**!reset** - to clean up the roster

**!raidover** - deletes the raid party channel.

Also, see **!beep raidparty** for commands which raid party participants can use!
""")

beep_gym = ("""
**{member}** you can use following commands for gym lookup. 

**!gym <gym-code>** brings up the google maps location of the gym.

Note : **gym-code** is **first two letters** of **first two or three words** of gym name with some exceptions

**!gyms <code>** looks up all gyms starting with code. 

**__Example:__**
**!gyms A** will bring up all gym code and gym names starting with **A**
**!gyms BU** will bring up all gym code and gym names starting with **BU**
""")

beep_notifications = ("""**{member}** here are the commands for notifications. 

**__Subscription__**
**!subscribe** shows a list of available roles
**!subscribe role-name** assigns you the role for raid-notifications
**!unsubscribe role-name** removes the role for raid-notifications

**__Admin Only__**
**!register-role role-name** registers a role for raid-notifications
**!register-gym role-name gym-code** associates a gym-code with raid-notifications role

**!show-register** to show the current register
**!reset-register** removes all raid-notifications roles
""")

beep_bingo = ("""**{member}** here are the commands for bingo. 

**!bingo-card** - to generate bingo-card for the contest
**!bingo** - to shout-out bingo when you think you have all boxes covered.
""")

beep_nest = ("""**{member}** here is the commands for nests reporting. 

**!nest <pokemon> <name-of-location> [url]** - to report a nest at location and google url
**!nest <pokemon> <gym-code>** - to report a nest using gym-code for location
""")


beep_research = ("""**{member}** here are the commands for reporting quests. 

**!research** - to report a research, *Clembot asks for further inputs*
**!research <pokestop> , <quest>, <reward>** - to report a research quest

**!list research** - to see the list of reported research quests in the channel

**!remove-research <research-id>** - to delete a research quest.

**Note:** research list is cleaned up automatically at midnight.
""")

beep_exraid = ("""**{member}** here are the commands for ex-raids. 

**!exraid <gym-code> [date]** creates an ex-raid channel with date in channel name.
**!exraid <location>** creates an ex-raid channel for location.

*Note: the date passed is just for the channel name. Timer needs to be set separately.*

**!timerset mm/dd HH:MM AM/PM** can be used to set the timer for the channel.

**!archive** switches the archival mode for an ex-raid channel. When set the channel is not deleted automatically.
""")

# ---------------------------------------------------------------------------------------

@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def dump(ctx):
    try:

        raid_channel_dict = copy.deepcopy(guild_dict[ctx.message.guild.id])

        output = jsonpickle.encode(raid_channel_dict)
        parsed = json.loads(output)

        await ctx.message.channel.send( content=json.dumps(parsed, indent=4, sort_keys=True))

    except Exception as error:
        await ctx.message.channel.send( content=error)


@Clembot.command(pass_context=True, hidden=True, aliases=["b","help"])
async def beep(ctx):
    try:
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."

        args = ctx.message.clean_content[len("!beep"):]
        args_split = args.split()

        if len(args_split) == 0:
            await ctx.message.channel.send(embed=get_beep_embed(title="Help - Commands", description=beepmsg.format(member=ctx.message.author.display_name), footer=footer))
        else:
            if args_split[0] == 'report':
                await ctx.message.channel.send( embed = get_beep_embed(title="Help - Raid Reporting", description = beep_report.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'wild':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Wild", description=beep_wild.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'raidparty':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Raid Party (Status)", description=beep_raidparty.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'raidowner':
                await ctx.message.channel.send( embed= get_beep_embed(title="Help - Raid Party (Organizer)", description=beep_raidowner.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'gym':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Gym Code", description=beep_gym.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'notification':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Raid Notifications", description=beep_notifications.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'bingo':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Bingo", description=beep_bingo.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'nest':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Nest", description=beep_nest.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'research':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Research", description=beep_research.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'raid':
                await ctx.message.channel.send(embed=get_beep_embed(title="Help - Raid Management", description=beep_raid.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'status' :
                await ctx.message.channel.send( embed = get_beep_embed(title="Help - Status Management", description = beep_status.format(member=ctx.message.author.display_name, bot=ctx.guild.me.mention), footer=footer))
            elif args_split[0] == 'exraid' :
                await ctx.message.channel.send( embed = get_beep_embed(title="Help - EX-Raid Reporting", description = beep_exraid.format(member=ctx.message.author.display_name), footer=footer))
            elif args_split[0] == 'notes' :
                await PropertiesHandler(Clembot)._help(ctx)
            elif args_split[0] == 'profile' :
                await ProfileManager(Clembot)._help(ctx)
            elif args_split[0] == 'trade' :
                await MyTradeManager._help(ctx)
            elif args_split[0] == 'react-role' :
                await ReactRoleManager(Clembot)._help(ctx)



    except Exception as error:
        print(error)

#         pokebattler integration
weather_list = ['none', 'extreme', 'clear', 'sunny', 'rainy', 'partlycloudy', 'cloudy', 'windy', 'snowy', 'foggy']


@Clembot.command()
@checks.activeraidchannel()
async def weather(ctx):
    "Sets the weather for the raid. \nUsage: !weather <weather> \nOnly usable in raid channels. \n Acceptable options: none, extreme, clear, rainy, partlycloudy, cloudy, windy, snowy, foggy"
    try:
        weather_split = ctx.message.clean_content.lower().split()

        if len(weather_split) >= 2:
            del weather_split[0]
            weather = weather_split[0]


            if weather.lower() not in weather_list:
                return await _send_error_message(ctx.channel, "Beep Beep! valid weather conditions are : {}".format(", ".join(weather_list)))
            else:
                guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id]['weather'] = weather.lower()
                emoji = get_weather(ctx.guild, weather)
                return await _send_message(ctx.channel,"Beep Beep! The current weather is set to **{0}**{1}!".format(weather, emoji))
        else:
            raid_weather = guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id].get('weather', None)
            if raid_weather:
                return await _send_message(ctx.channel,"Beep Beep! The current weather is **{0}**{1}!".format(raid_weather, get_weather(ctx.guild, raid_weather)))
            return await _send_error_message(ctx.channel, "Beep Beep! Please use **!weather <weather>** to set weather for the raid. valid weather conditions are : **{}**".format(", ".join(weather_list)))
    except Exception as error:
        await _send_error_message(ctx.channel, error)


@Clembot.command()
@checks.activeraidchannel()
async def counters(ctx, *, args = None):
    """Simulate a Raid battle with Pokebattler.

    Usage: !counters [pokemon] [weather] [user]
    See !help weather for acceptable values for weather.
    If [user] is a valid Pokebattler user id, Meowth will simulate the Raid with that user's Pokebox.
    Only usable in raid channels. Uses current boss and weather by default.
    """
    channel = ctx.channel
    guild = channel.guild
    if args:
        args_split = args.split()
        for arg in args_split:
            if arg.isdigit():
                user = arg
                break
        else:
            user = None
        rgx = '[^a-zA-Z0-9]'
        pkmn = next((str(p) for p in get_raidlist() if not str(p).isdigit() and re.sub(rgx, '', str(p)) in re.sub(rgx, '', args.lower())), None)
        if not pkmn:
            pkmn = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('pokemon', None)
        weather = next((w for w in weather_list if re.sub(rgx, '', w) in re.sub(rgx, '', args.lower())), None)
    else:
        pkmn = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('pokemon', None)
        weather = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('weather', None)
        user = None
    if not pkmn:
        await ctx.channel.send("Beep Beep! Enter a Pokemon that appears in raids, or wait for this raid egg to hatch!")
        return
    await _counters(ctx, pkmn, user, weather)


async def _counters(ctx, pkmn, user = None, weather = None):
    img_url = 'https://raw.githubusercontent.com/FoglyOgly/Meowth/master/images/pkmn/{0}_.png?cache={0}'.format(str(get_number(pkmn)).zfill(3),CACHE_VERSION)
    level = get_level(pkmn) if get_level(pkmn).isdigit() else "5"
    url = "https://fight.pokebattler.com/raids/defenders/{pkmn}/levels/RAID_LEVEL_{level}/attackers/".format(pkmn=pkmn.replace('-','_').upper(),level=level)
    if user:
        url += "users/{user}/".format(user=user)
        userstr = "user #{user}'s".format(user=user)
    else:
        url += "levels/30/"
        userstr = "Level 30"
    if not weather:
        weather = "NO_WEATHER"
    else:

        match_list = ['NO_WEATHER','NO_WEATHER','CLEAR','CLEAR','RAINY',
                        'PARTLY_CLOUDY','OVERCAST','WINDY','SNOW','FOG']
        index = weather_list.index(weather)
        weather = match_list[index]
    url += "strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=OVERALL&"
    url += "weatherCondition={weather}&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE".format(weather=weather)
    async with ctx.typing():
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                data = await resp.json()

        title_url = url.replace('https://fight', 'https://www')
        colour = ctx.guild.me.colour
        hyperlink_icon = 'https://i.imgur.com/fn9E5nb.png'
        pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'
        data = data['attackers'][0]
        raid_cp = data['cp']
        atk_levels = '30'
        ctrs = data['randomMove']['defenders'][-6:]
        index = 1
        def clean(txt):
            return txt.replace('_', ' ').title()
        title = '{pkmn} | {weather}'.format(pkmn=pkmn.title(),weather=clean(weather))
        stats_msg = "**CP:** {raid_cp}\n".format(raid_cp=raid_cp)
        stats_msg += "**Weather:** {weather}\n".format(weather=clean(weather))
        stats_msg += "**Attacker Level:** {atk_levels}".format(atk_levels=atk_levels)
        ctrs_embed = discord.Embed(colour=colour)
        ctrs_embed.set_author(name=title,url=title_url,icon_url=hyperlink_icon)
        ctrs_embed.set_thumbnail(url=img_url)
        ctrs_embed.set_footer(text='Results courtesy of Pokebattler', icon_url=pbtlr_icon)
        for ctr in reversed(ctrs):
            ctr_name = clean(ctr['pokemonId'])
            moveset = ctr['byMove'][-1]
            moves = "{move1} | {move2}".format(move1=clean(moveset['move1'])[:-5], move2=clean(moveset['move2']))
            name = "#{index} - {ctr_name}".format(index=index, ctr_name=ctr_name)
            ctrs_embed.add_field(name=name,value=moves)
            index += 1
        ctrs_embed.add_field(name="Results with {userstr} attackers".format(userstr=userstr), value="[See your personalized results!](https://www.pokebattler.com/raids/{pkmn})".format(pkmn=pkmn.replace('-','_').upper()))
        await ctx.channel.send(embed=ctrs_embed)


@Clembot.command()
@checks.activeraidchannel()
async def countersold(ctx, *, entered_pkmn = None):
    """Simulate a Raid battle with Pokebattler.

    Usage: !counters
    Only usable in raid channels. Uses current boss and weather.
    """
    try:
        channel = ctx.channel
        guild = channel.guild
        pkmn = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('pokemon', None)
        if not pkmn:
            pkmn = entered_pkmn.lower() if entered_pkmn.lower() in get_raidlist() else None
        weather = guild_dict[guild.id]['raidchannel_dict'][channel.id].get('weather', None)
        if pkmn:
            img_url = 'https://raw.githubusercontent.com/FoglyOgly/Meowth/master/images/pkmn/{0}_.png?cache={1}'.format(str(get_number(pkmn)).zfill(3),CACHE_VERSION)
            level = get_level(pkmn) if get_level(pkmn).isdigit() else "5"
            if not weather:
                weather = "NO_WEATHER"
            else:
                weather_list = ['none', 'extreme', 'clear', 'sunny', 'rainy', 'partlycloudy', 'cloudy', 'windy', 'snowy', 'foggy']
                match_list = ['NO_WEATHER', 'NO_WEATHER', 'CLEAR', 'CLEAR', 'RAINY', 'PARTLY_CLOUDY', 'OVERCAST', 'WINDY', 'SNOW', 'FOG']
                if not weather.lower() in weather_list:
                    msg = "Please pick a valid weather option."
                    await ctx.embed(msg, msg_type='error')
                    return
                index = weather_list.index(weather)
                weather = match_list[index]
            url = "https://fight.pokebattler.com/raids/defenders/"
            url += "{pkmn}/levels/RAID_LEVEL_{level}/".format(pkmn=pkmn.replace('-', '_').upper(), level=level)
            url += "attackers/levels/30/strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=OVERALL&"
            url += "weatherCondition={weather}&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE".format(weather=weather)

            print(url)
            async with ctx.typing():
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(url) as resp:
                        data = await resp.json()

                title_url = url.replace('https://fight', 'https://www')
                colour = guild.me.colour
                hyperlink_icon = 'https://i.imgur.com/fn9E5nb.png'
                pbtlr_icon = 'https://www.pokebattler.com/favicon-32x32.png'
                data = data['attackers'][0]
                raid_cp = data['cp']
                atk_levels = '30'
                ctrs = data['randomMove']['defenders'][-6:]
                index = 1

                def clean(txt):
                    return txt.replace('_', ' ').title()

                title = '{pkmn} | {weather}'.format(pkmn=pkmn.title(), weather=clean(weather))
                stats_msg = "**CP:** {raid_cp}\n".format(raid_cp=raid_cp)
                stats_msg += "**Weather:** {weather}\n".format(weather=clean(weather))
                stats_msg += "**Attacker Level:** {atk_levels}".format(atk_levels=atk_levels)
                ctrs_embed = discord.Embed(colour=colour)
                ctrs_embed.set_author(name=title, url=title_url, icon_url=hyperlink_icon)
                ctrs_embed.set_thumbnail(url=img_url)
                ctrs_embed.set_footer(text='Results courtesy of Pokebattler', icon_url=pbtlr_icon)
                for ctr in reversed(ctrs):
                    ctr_name = clean(ctr['pokemonId'])
                    moveset = ctr['byMove'][-1]
                    moves = "{move1} | {move2}".format(move1=clean(moveset['move1'])[:-5], move2=clean(moveset['move2']))
                    name = "#{index} - {ctr_name}".format(index=index, ctr_name=ctr_name)
                    ctrs_embed.add_field(name=name, value=moves)
                    index += 1
                ctrs_embed.add_field(name="Results with Level 30 attackers", value="[See your personalized results!](https://www.pokebattler.com/raids/{pkmn})".format(pkmn=pkmn.replace('-', '_').upper()))
                await ctx.channel.send(embed=ctrs_embed)
        else:
            await ctx.channel.send("Beep Beep! Enter a Pokemon that appears in raids, or wait for this raid egg to hatch!")
    except Exception as error:
        await ctx.channel.send(error)





def validate_count(count_value):

    try:
        count = int(count_value)
    except Exception as error:
        raise ValueError("I can't understand how many are in your group, please use a number to specify the party size.")

    if 1 <= count <= 20:
        return count
    else :
        raise ValueError("Group size is limited between 1-20.")





async def _process_rsvp(message, status):
    try:
        arguments = message.content
        trainer_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict']

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

            args = arguments.split()
            del args[0]
            last_mention = None
            for arg in args:
                if last_mention and arg.isdigit():
                    party_status[last_mention] = validate_count(arg)
                    last_mention = None
                elif arg.startswith('#'):
                    last_mention = arg
                    existing_party_size = trainer_dict.setdefault(int(last_mention.replace('#', '')),{}).get('count', 1)
                    party_status[last_mention] = existing_party_size
                else:
                    raise ValueError("Only acceptable options are group size or mentions of trainers in group.")

        else:

            last_mention = '#' + str(message.author.id)
            mentions_list.append(message.author.mention)
            if len(args) > 1:
                party_status[last_mention] = validate_count(args[1])
            else:
                existing_party_size = trainer_dict.setdefault(int(last_mention.replace('#', '')),{}).get('count', 1)
                party_status[last_mention] = existing_party_size

        total_trainer_rsvp = 0
        for user_id, party_size in party_status.items():
            trainer_dict = _add_rsvp_to_dict(trainer_dict, int(user_id.replace('#','')), status, party_size)
            total_trainer_rsvp += party_size

        guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

        trainer_count_message = "" if total_trainer_rsvp == 1 else " with a total of {trainer_count} trainers".format(trainer_count=total_trainer_rsvp)
        conjuction = "is" if len(party_status) == 1 else "are"


        embed_msg = _("{member} {conjuction} {status_message}{trainer_count_message}!").format(member=", ".join(mentions_list) , conjuction=conjuction, status_message=STATUS_MESSAGE[status], trainer_count_message=trainer_count_message)

        await _send_rsvp_embed(message, trainer_dict, description=embed_msg)

    except ValueError as valueerror:
        await _send_error_message(message.channel, "Beep Beep! **{}** {}".format(message.author.display_name, valueerror))

    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True, aliases=["c","o"])
@checks.raidchannel()
async def coming(ctx):
    """Indicate you are on the way to a raid.

    Usage: !coming [message]
    Works only in raid channels. If message is omitted, checks for previous !maybe
    command and takes the count from that. If it finds none, assumes you are a group
    of 1.
    Otherwise, this command expects at least one word in your message to be a number,
    and will assume you are a group with that many people."""

    await _process_rsvp(ctx.message, "omw")


@Clembot.command(pass_context=True, hidden=True, aliases=["h"])
@checks.raidchannel()
async def here(ctx, *, count: str = None):
    """Indicate you have arrived at the raid.

    Usage: !here [message]
    Works only in raid channels. If message is omitted, and
    you have previously issued !coming, then preserves the count
    from that command. Otherwise, assumes you are a group of 1.
    Otherwise, this command expects at least one word in your message to be a number,
    and will assume you are a group with that many people."""

    await _process_rsvp(ctx.message, "waiting")


@Clembot.command(pass_context=True, hidden=True, aliases=["i", "maybe"])
@checks.raidchannel()
async def interested(ctx, *, count: str = None):
    """Indicate you are interested in the raid.

    Usage: !interested [message]
    Works only in raid channels. If message is omitted, assumes you are a group of 1.
    Otherwise, this command expects at least one word in your message to be a number,
    and will assume you are a group with that many people."""

    await _process_rsvp(ctx.message, "maybe")


@Clembot.command(pass_context=True, hidden=True, aliases=["x"])
@checks.raidchannel()
async def cancel(ctx):
    """Indicate you are no longer interested in a raid.

    Usage: !cancel
    Works only in raid channels. Removes you and your party
    from the list of trainers who are "otw" or "here"."""
    await _cancel(ctx.message)


@Clembot.command(pass_context=True, hidden=True, aliases=["s"])
@checks.activeraidchannel()
async def starting(ctx):
    """Signal that a raid is starting.

    Usage: !starting
    Works only in raid channels. Sends a message and clears the waiting list. Users who are waiting
    for a second group must reannounce with the :here: emoji or !here."""

    ctx_startinglist = []
    id_startinglist = []

    trainer_dict = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']

    # Add all waiting trainers to the starting list
    for trainer in trainer_dict:
        if trainer_dict[trainer]['status'] == "waiting":
            user = await Clembot.get_user_info(trainer)
            ctx_startinglist.append(user.mention)
            id_startinglist.append(trainer)

    # Go back and delete the trainers from the waiting list
    for trainer in id_startinglist:
        del trainer_dict[trainer]
    guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'] = trainer_dict
    guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['suggested_start'] = False

    starting_str = _("Beep Beep! The group that was waiting is starting the raid! Trainers {trainer_list}, please respond with {here_emoji} or **!here** if you are waiting for another group!").format(trainer_list=", ".join(ctx_startinglist), here_emoji=parse_emoji(ctx.message.guild, config['here_id']))
    if len(ctx_startinglist) == 0:
        starting_str = _("Beep Beep! How can you start when there's no one waiting at this raid!?")
    await ctx.message.channel.send( starting_str)


RAID_list_options = ['timer','rsvp','weather','interested','coming','here']

RAID_PARTY_list_options = ['rsvp','interested','coming','here']

RSVP_options = ['description','rsvp']

@Clembot.group(pass_context=True, hidden=True, aliases=["lists, list"])
async def list(ctx):
    """Lists all raid info for the current channel.

    Usage: !list
    Works only in raid or city channels. Calls the interested, waiting, and here lists. Also prints
    the raid timer. In city channels, lists all active raids."""
    try:
        if ctx.invoked_subcommand is None:
            listmsg = ""
            message = ctx.message
            guild = ctx.message.guild
            channel = ctx.message.channel
            args = ctx.message.clean_content.lower().split()
            if len(args) > 1:
                return await _send_error_message(ctx.message.channel, "Beep Beep! **{0}**, Please use **!list**.".format(ctx.message.author.display_name))
            exp = None
            if checks.check_citychannel(ctx):
                activeraidnum = 0
                cty = channel.name
                rc_d = guild_dict[guild.id]['raidchannel_dict']

                raid_dict = {}
                egg_dict = {}
                exraid_list = []
                for r in rc_d:
                    reportcity = Clembot.get_channel(rc_d[r]['reportcity'])
                    if not reportcity:
                        continue

                    if reportcity.name == cty and rc_d[r]['active'] and discord.utils.get(guild.text_channels, id=r):
                        exp = rc_d[r]['exp']
                        type = rc_d[r]['type']
                        level = rc_d[r]['egglevel']
                        if type == 'egg' and level.isdigit():
                            egg_dict[r] = exp
                        elif type == 'exraid' or level == "EX" :
                            if convert_to_epoch(fetch_channel_expire_time(r)) > convert_to_epoch(fetch_current_time(reportcity.guild.id)):
                                exraid_list.append(r)
                            else:
                                activeraidnum -= 1
                        elif type == 'raidparty':
                            activeraidnum -= 1
                            # ignore raid party
                        else:
                            raid_dict[r] = exp

                        activeraidnum += 1

                def list_output(r):
                    rchan = Clembot.get_channel(r)
                    # now = datetime.datetime.utcnow() + datetime.timedelta(hours=guild_dict[guild.id]['offset'])
                    # end = now + datetime.timedelta(seconds=rc_d[r]['exp']-time.time())
                    # now = fetch_current_time(rchan.guild.id)
                    end = fetch_channel_expire_time(rchan.id)
                    output = ""
                    ctx_waitingcount = 0
                    ctx_omwcount = 0
                    ctx_maybecount = 0
                    for trainer in rc_d[r]['trainer_dict'].values():
                        if trainer['status'] == "waiting":
                            ctx_waitingcount += trainer['count']
                        elif trainer['status'] == "omw":
                            ctx_omwcount += trainer['count']
                        elif trainer['status'] == "maybe":
                            ctx_maybecount += trainer['count']
                    if rc_d[r]['manual_timer'] == False:
                        assumed_str = " (assumed)"
                    else:
                        assumed_str = ""
                    if rc_d[r]['type'] == 'egg' and rc_d[r]['egglevel'].isdigit() and int(rc_d[r]['egglevel']) > 0:
                        expirytext = " - Hatches: {expiry}{is_assumed}".format(expiry=end.strftime("%I:%M %p (%H:%M)"), is_assumed=assumed_str)
                    elif rc_d[r]['egglevel'] == "EX" or rc_d[r]['type'] == "exraid":
                        expirytext = " - Hatches: {expiry}{is_assumed}".format(expiry=end.strftime("%B %d at %I:%M %p (%H:%M)"), is_assumed=assumed_str)
                    else:
                        expirytext = " - Expires at: {expiry}{is_assumed}".format(expiry=end.strftime("%I:%M %p (%H:%M)"), is_assumed=assumed_str)
                    output += (_("    {raidchannel}{expiry_text}\n").format(raidchannel=rchan.mention, expiry_text=expirytext))
                    output += (_("    {interestcount} interested, {comingcount} coming, {herecount} here.\n").format(raidchannel=rchan.mention, interestcount=ctx_maybecount, comingcount=ctx_omwcount, herecount=ctx_waitingcount))
                    return output

                if activeraidnum:
                    listmsg += (_("Beep Beep! Here's the current raids for {0}\n\n").format(cty.capitalize()))
                try:
                    if raid_dict:
                        listmsg += (_("**Active Raids:**\n").format(cty.capitalize()))
                        for rr, e in sorted(raid_dict.items(), key=itemgetter(1)):
                            listmsg += list_output(rr)
                        listmsg += "\n"

                    if egg_dict:
                        listmsg += (_("**Raid Eggs:**\n").format(cty.capitalize()))
                        for rr, e in sorted(egg_dict.items(), key=itemgetter(1)):
                            listmsg += list_output(rr)
                        listmsg += "\n"

                    if exraid_list:
                        listmsg += (_("**EXRaids:**\n").format(cty.capitalize()))
                        for rr in exraid_list:
                            listmsg += list_output(rr)

                    if activeraidnum == 0:
                        await channel.send( _("Beep Beep! No active raids! Report one with **!raid <name> <location>**."))
                        return
                    else:
                        await channel.send( listmsg)
                    return
                except Exception as error:
                    print(error)

            if checks.check_raidpartychannel(ctx):
                if checks.check_raidactive(ctx):
                    return await channel.send(embed=_generate_rsvp_embed_master(message, RAID_PARTY_list_options))
                    return

            if checks.check_raidchannel(ctx):
                if checks.check_raidactive(ctx):
                    return await channel.send(embed=_generate_rsvp_embed_master(message, RAID_list_options))

    except Exception as error:
        print(error)
    return






@list.command(pass_context=True, hidden=True)
@checks.nonraidchannel()
async def research(ctx):
    """List the quests for the channel

    Usage: !list research"""
    listmsg = _('**Beep Beep!**')
    listmsg += await _researchlist(ctx)
    await _send_message(ctx.channel, description=listmsg)

async def _researchlist(ctx):
    try:
        args = ctx.message.clean_content.lower().split()
        filter_text = None if len(args) < 3 else args[2]

        research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict',{}))
        questmsg = ""
        for questid in research_dict:
            if research_dict[questid]['reportchannel'] == ctx.message.channel.id:
                if not filter_text or filter_text in research_dict[questid]['quest'].title().lower():
                    try:
                        questreportmsg = await ctx.message.channel.get_message(questid)
                        questauthor = ctx.channel.guild.get_member(research_dict[questid]['reportauthor'])
                        if questauthor :
                            author_display_name = questauthor.display_name
                        else:
                            author_display_name = research_dict[questid]['reportauthorname']
                        research_id = research_dict[questid]['research_id']
                        questmsg += _('\n🔰')
                        if ctx.message.author.bot:
                            questmsg += _("**[{research_id}]** - {location} / {quest} / {reward} / {author}".format(research_id=research_id,location=research_dict[questid]['location'].title(),quest=research_dict[questid]['quest'].title(),reward=research_dict[questid]['reward'].title(), author=author_display_name))
                        else:
                            questmsg += _("**[{research_id}]** - **Location**: {location}, **Quest**: {quest}, **Reward**: {reward}, **Reported By**: {author}".format(research_id=research_id, location=research_dict[questid]['location'].title(), quest=research_dict[questid]['quest'].title(), reward=research_dict[questid]['reward'].title(), author=author_display_name))
                    except discord.errors.NotFound:
                        pass
        if questmsg:
            listmsg = _(' **Here\'s the current research reports for {channel}**\n{questmsg}').format(channel=ctx.message.channel.name.capitalize(),questmsg=questmsg)
        else:
            if len(args) < 3 :
                listmsg = _(" There are no research reports. Report one with **!research**")
            else:
                listmsg = _(" There are no research reports with **{quest}**. Report one with **!research**".format(quest=filter_text))
        return listmsg
    except Exception as error:
        logger.error(error)

@Clembot.command(pass_context=True, hidden=True, aliases=["remove-research"])
async def _remove_research(ctx, research_id=None):
    if research_id is None:
        return await _send_error_message(ctx.channel, "Please provide the 4 char code for the research quest!")
    research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict', {}))
    questmsg = ""
    delete_quest_id = None
    for questid in research_dict:
        if research_dict[questid]['reportchannel'] == ctx.message.channel.id:
            try:
                quest_research_id = research_dict[questid]['research_id']
                quest_reported_by = research_dict[questid]['reportauthor']
                if quest_research_id == research_id:
                    record_error_reported_by(ctx.message.guild.id, quest_reported_by, 'research_reports')
                    del research_dict[questid]
                    guild_dict[ctx.guild.id]['questreport_dict'] = research_dict
                    research_report = await ctx.channel.get_message(questid)
                    if research_report:
                        await research_report.delete()
                    return await _send_message(ctx.channel, "**{0}** Research # **{1}** has been removed.".format(ctx.message.author.display_name,research_id))
                    break
            except discord.errors.NotFound:
                pass
    return await _send_error_message(ctx.channel, "**{0}** No Research found with **{1}** .".format(ctx.message.author.display_name, research_id))

@Clembot.command(pass_context=True, hidden=True, aliases=["research-status"])
async def _research_status(ctx, research_id=None):

    questmsg = ""
    delete_quest_id = None
    research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict', {}))

    print(json.dumps(research_dict, indent=2))

    if research_id is None:
        return await _send_error_message(ctx.channel, "Please provide the 4 char code for the research quest!")

    for questid in research_dict:
        if research_dict[questid]['reportchannel'] == ctx.message.channel.id:
            try:
                quest_research_id = research_dict[questid]['research_id']
                quest_reported_by = research_dict[questid]['reportauthor']
                if quest_research_id == research_id:
                    quest_research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict', {})).get(questid,{})
                    return await _send_message(ctx.channel, json.dumps(quest_research_dict, indent=2))

            except discord.errors.NotFound:
                pass
    return await _send_error_message(ctx.channel, "**{0}** No Research found with **{1}** .".format(ctx.message.author.display_name, research_id))

async def _send_rsvp_embed(message, trainer_dict, description = None):





    return await message.channel.send(embed=_generate_rsvp_embed_master(message, options=RSVP_options, trainer_dict=trainer_dict, description=description))

def _generate_rsvp_embed(message, trainer_dict):
    embed_msg = ""

    embed = discord.Embed(description=embed_msg, colour=discord.Colour.gold())

    embed.add_field(name="**Interested / On the way / At the raid**", value="{maybe} / {omw} / {waiting}".format(waiting=get_count_from_channel(message, "waiting", trainer_dict=trainer_dict), omw=get_count_from_channel(message, "omw",trainer_dict=trainer_dict), maybe=get_count_from_channel(message, "maybe", trainer_dict=trainer_dict)), inline=True)

    maybe = _get_trainer_names_from_dict(message, "maybe", trainer_dict=trainer_dict)
    if maybe:
        embed.add_field(name="**Interested**", value=maybe)

    omw = _get_trainer_names_from_dict(message, "omw", trainer_dict=trainer_dict)
    if omw:
        embed.add_field(name="**On the way**", value=omw)

    waiting = _get_trainer_names_from_dict(message, "waiting", trainer_dict=trainer_dict)
    if waiting:
        embed.add_field(name="**At the raid**", value=waiting)

    return embed



async def _generate_list_embed(message):
    embed_msg = ""

    embed = discord.Embed(description=embed_msg, colour=discord.Colour.gold())

    embed.add_field(name="**Interested / On the way / At the raid**", value="{maybe} / {omw} / {waiting}".format(waiting=get_count_from_channel(message, "waiting"), omw=get_count_from_channel(message, "omw"), maybe=get_count_from_channel(message, "maybe")), inline=True)

    maybe = _get_trainer_names_from_dict(message, "maybe")
    if maybe:
        embed.add_field(name="**Interested**", value=maybe)

    omw = _get_trainer_names_from_dict(message, "omw")
    if omw:
        embed.add_field(name="**On the way**", value=omw)

    waiting = _get_trainer_names_from_dict(message, "waiting")
    if waiting:
        embed.add_field(name="**At the raid**", value=waiting)

    await message.channel.send( embed=embed)


def _generate_rsvp_embed_master(message, options = RAID_list_options, trainer_dict = None, description=None):
    trainer_dict = None

    if not trainer_dict:
        trainer_dict = copy.deepcopy(guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict'])

    additional_fields = {}

    rc_d = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]
    for option in options:
        if option == 'timer':
            raid_time_value = fetch_channel_expire_time(message.channel.id).strftime("%I:%M %p (%H:%M)")
            raid_time_label = "Raid Expires At"
            if rc_d['type'] == 'egg' :
                raid_time_label = "Egg Hatches At"
                if rc_d['egglevel'] == 'EX':
                    raid_time_value = fetch_channel_expire_time(message.channel.id).strftime("%B %d %I:%M %p (%H:%M)")

            start_time = fetch_channel_start_time(message.channel.id)
            start_time_label = "None"
            if start_time:
                raid_time_label = raid_time_label + " / Suggested Start Time"
                raid_time_value = raid_time_value + " / " + start_time.strftime("%I:%M %p (%H:%M)")

            additional_fields[raid_time_label] = raid_time_value

        if option == 'rsvp':
            aggregated_label = "Interested / On the way / At the raid"
            aggregated_status = "{maybe} / {omw} / {waiting}".format(waiting=get_count_from_channel(message, "waiting"), omw=get_count_from_channel(message, "omw"), maybe=get_count_from_channel(message, "maybe"))
            additional_fields[aggregated_label] = aggregated_status



        elif option == 'interested':
            trainer_names = _get_trainer_names_from_dict(message, "maybe")
            if trainer_names:
                additional_fields['Interested'] = trainer_names
        elif option == 'coming':
            trainer_names = _get_trainer_names_from_dict(message, "omw")
            if trainer_names:
                additional_fields['On the way'] = trainer_names
        elif option == 'here':
            trainer_names = _get_trainer_names_from_dict(message, "waiting")
            if trainer_names:
                additional_fields['At the raid'] = trainer_names
    footer = None

    return _create_rsvp_embed(message, description, additional_fields, footer)


def _create_rsvp_embed(message, description=None, additional_fields = {}, footer = None):

    embed = discord.Embed(description=description, colour=discord.Colour.gold())

    for label, value in additional_fields.items():
        embed.add_field(name="**{0}**".format(label), value= value, inline=True)

    if footer:
        embed.set_footer(text=footer)

    return embed



#------------------
    # raid_time_value = fetch_channel_expire_time(ctx.message.channel.id).strftime("%I:%M %p (%H:%M)")
    #
    # raid_time_label = "**Raid Expires At**"
    # if rc_d['type'] == 'egg' :
    #     raid_time_label = "**Egg Hatches At**"
    #     if rc_d['egglevel'] == 'EX':
    #         raid_time_value = fetch_channel_expire_time(ctx.message.channel.id).strftime("%B %d %I:%M %p (%H:%M)")
    #
    # start_time = fetch_channel_start_time(ctx.message.channel.id)
    # start_time_label = "None"
    # if start_time:
    #     raid_time_label = raid_time_label + " **/ Suggested Start Time**"
    #     raid_time_value = raid_time_value + " / " + start_time.strftime("%I:%M %p (%H:%M)")
    #
    # embed.add_field(name=raid_time_label, value=raid_time_value)
    #
    # embed.add_field(name="**Interested / On the way / At the raid**", value="{maybe} / {omw} / {waiting}".format(waiting=get_count_from_channel(ctx.message, "waiting"), omw=get_count_from_channel(ctx.message, "omw"), maybe=get_count_from_channel(ctx.message, "maybe")), inline=True)
    #
    # weather = rc_d.get('weather', None)
    # if weather:
    #     embed.add_field(name="Weather", value="{0} ({1})".format(get_weather(ctx.guild,weather), weather.capitalize()))
    #
    # maybe = _get_trainer_names_from_dict(ctx.message, "maybe")
    # if maybe:
    #     embed.add_field(name="**Interested**", value=maybe)
    #
    # omw = _get_trainer_names_from_dict(ctx.message, "omw")
    # if omw:
    #     embed.add_field(name="**On the way**", value=omw)
    #
    # waiting = _get_trainer_names_from_dict(ctx.message, "waiting")
    # if waiting:
    #     embed.add_field(name="**At the raid**", value=waiting)
    #
    # await channel.send( embed=embed)
    #
    # listmsg += await _interest(ctx)
    # listmsg += "\n" + await _otw(ctx)
    # listmsg += "\n" + await _waiting(ctx)
    # if rc_d['type'] != 'exraid':
    #     listmsg += "\n" + await print_raid_timer(channel.id)
    # listmsg += "\n" + await print_start_time(channel.id)


#-------------------

    return embed






















@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def omw(ctx):
    await ctx.message.channel.send( content=_("Beep Beep! Hey {member}, I don't know if you meant **!coming** to say that you are coming or **!list coming** to see the other trainers on their way").format(member=ctx.message.author.mention))


@list.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def interested(ctx):
    """Lists the number and users who are interested in the raid.

    Usage: !list interested
    Works only in raid channels."""
    listmsg = await _interest(ctx)
    await ctx.message.channel.send( listmsg)


@list.command(pass_context=True, hidden=True, ailases=["coming"])
@checks.activeraidchannel()
async def _list_coming(ctx):
    """Lists the number and users who are coming to a raid.

    Usage: !list coming
    Works only in raid channels."""
    listmsg = await _otw(ctx)
    await ctx.message.channel.send( listmsg)


@list.command(pass_context=True, hidden=True, ailases=["here"])
@checks.activeraidchannel()
async def _list_here(ctx):
    """List the number and users who are present at a raid.
    Usage: !list here
    Works only in raid channels."""
    listmsg = await _waiting(ctx)
    await ctx.message.channel.send( listmsg)


@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_guild=True)
@checks.raidchannel()
async def clearstatus(ctx):
    """Clears raid channel status lists.

    Usage: !clearstatus
    Only usable by admins."""
    try:
        guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'] = {}
        await ctx.message.channel.send( "Beep Beep! Raid status lists have been cleared!")
    except KeyError:
        pass


async def ask_confirmation(message, rusure_message, yes_message, no_message, timed_out_message):
    author = message.author
    channel = message.channel

    reaction_list = ['✅', '❎']
    # reaction_list = ['❔', '✅', '❎']

    rusure = await channel.send( _("Beep Beep! {message}".format(message=rusure_message)))
    await rusure.add_reaction( "✅")  # checkmark
    await rusure.add_reaction( "❎")  # cross

    def check(react, user):
        if user.id != author.id:
            return False
        return True

    # res = await Clembot.wait_for_reaction(reaction_list, message=rusure, check=check, timeout=60)
    try:
        reaction, user = await Clembot.wait_for('reaction_add', check=check, timeout=10)
    except asyncio.TimeoutError:
        await rusure.delete()
        confirmation = await channel.send(_("Beep Beep! {message}".format(message=timed_out_message)))
        await asyncio.sleep(3)
        await confirmation.delete()
        return False

    if reaction.emoji == "❎":
        await rusure.delete()
        confirmation = await channel.send( _("Beep Beep! {message}".format(message=no_message)))
        await asyncio.sleep(3)
        await confirmation.delete()
        return False
    elif reaction.emoji == "✅":
        await rusure.delete()
        confirmation = await channel.send( _("Beep Beep! {message}".format(message=yes_message)))
        await asyncio.sleep(3)
        await confirmation.delete()
        return True




@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def duplicate(ctx):
    """A command to report a raid channel as a duplicate.

    Usage: !duplicate
    Works only in raid channels. When three users report a channel as a duplicate,
    Clembot deactivates the channel and marks it for deletion."""
    channel = ctx.message.channel
    author = ctx.message.author
    guild = ctx.message.guild
    rc_d = guild_dict[guild.id]['raidchannel_dict'][channel.id]
    t_dict = rc_d['trainer_dict']
    can_manage = channel.permissions_for(author).manage_channels

    if can_manage:
        dupecount = 2
        rc_d['duplicate'] = dupecount
    else:
        if author.id in t_dict:
            try:
                if t_dict[author.id]['dupereporter']:
                    dupeauthmsg = await channel.send( _("Beep Beep! You've already made a duplicate report for this raid!"))
                    await asyncio.sleep(10)
                    await dupeauthmsg.delete()
                    return
                else:
                    t_dict[author.id]['dupereporter'] = True
            except KeyError:
                t_dict[author.id]['dupereporter'] = True
        else:
            t_dict[author.id] = {'status': '', 'dupereporter': True}
        try:
            dupecount = rc_d['duplicate']
        except KeyError:
            dupecount = 0
            rc_d['duplicate'] = dupecount

    dupecount += 1
    rc_d['duplicate'] = dupecount

    if dupecount >= 3:
        rusure = await channel.send( _("Beep Beep! Are you sure you wish to remove this raid?"))
        res = await ask(rusure, channel, author.id)
        if res is not None:
            if res[0].emoji == "❎":
                await rusure.delete()
                confirmation = await channel.send(_('Duplicate Report cancelled.'))
                logger.info((('Duplicate Report - Cancelled - ' + channel.name) + ' - Report by ') + author.display_name)
                dupecount = 2
                guild_dict[guild.id]['raidchannel_dict'][channel.id]['duplicate'] = dupecount
                await asyncio.sleep(10)
                await confirmation.delete()
                return
            elif res[0].emoji == "✅":
                await rusure.delete()
                await channel.send('Duplicate Confirmed')
                logger.info((('Duplicate Report - Channel Expired - ' + channel.name) + ' - Last Report by ') + author.display_name)

                raidmsg = await channel.get_message(rc_d['raidmessage'])
                reporter = raidmsg.mentions[0]
                if 'egg' in raidmsg.content:
                    record_error_reported_by(guild.id, reporter.id, 'egg_reports')
                else:
                    record_error_reported_by(guild.id, reporter.id, 'raid_reports')
                await expire_channel(channel)
                return
        else:
            await rusure.delete()
            confirmation = await channel.send(_('Duplicate Report Timed Out.'))
            logger.info((('Duplicate Report - Timeout - ' + channel.name) + ' - Report by ') + author.display_name)
            dupecount = 2
            guild_dict[guild.id]['raidchannel_dict'][channel.id]['duplicate'] = dupecount
            await asyncio.sleep(10)
            await confirmation.delete()
    else:
        rc_d['duplicate'] = dupecount
        confirmation = await channel.send(_('Duplicate report #{duplicate_report_count} / 3 received.').format(duplicate_report_count=str(dupecount)))
        logger.info((((('Duplicate Report - ' + channel.name) + ' - Report #') + str(dupecount)) + '- Report by ') + author.display_name)
        return


@Clembot.group(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def location(ctx):
    """Get raid location.

    Usage: !location
    Works only in raid channels. Gives the raid location link."""
    if ctx.invoked_subcommand is None:
        message = ctx.message
        guild = message.guild
        channel = message.channel
        rc_d = guild_dict[guild.id]['raidchannel_dict']
        raidmsgid = rc_d[channel.id]['raidmessage']
        location = rc_d[channel.id]['address']
        report_city = rc_d[channel.id]['reportcity']

        # report_channel = discord.utils.get(guild.channels, name=report_city)
        #
        # reportcitychannel = discord.utils.get(message.channel.guild.channels, name=reportcityid)

        raidmsg = await message.channel.get_message(raidmsgid)

        oldembed = raidmsg.embeds[0]
        locurl = oldembed['url']
        newembed = discord.Embed(title=oldembed['title'], url=locurl, colour=guild.me.colour)
        newembed.set_thumbnail(url=oldembed['thumbnail']['url'])
        locationmsg = await channel.send( content=_("Beep Beep! Here's the current location for the raid!\nDetails:{location}").format(location=location), embed=newembed)
        await asyncio.sleep(60)
        await locationmsg.delete()


@location.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def new(ctx):
    """Change raid location.

    Usage: !location new <new address>
    Works only in raid channels. Changes the google map links."""

    message = ctx.message
    location_split = message.content.lower().split()
    del location_split[0]
    del location_split[0]
    if len(location_split) < 1:
        await message.channel.send( _("Beep Beep! We're missing the new location details! Usage: **!location new <new address>**"))
        return
    else:
        report_city = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['reportcity']
        report_channel = discord.utils.get(message.guild.channels, name=report_city)

        details = " ".join(location_split)
        if "/maps" in message.content:
            mapsindex = message.content.find("/maps")
            newlocindex = message.content.rfind("http", 0, mapsindex)
            if newlocindex == -1:
                return
            newlocend = message.content.find(" ", newlocindex)
            if newlocend == -1:
                newloc = message.content[newlocindex:]
            else:
                newloc = message.content[newlocindex:newlocend + 1]
        else:
            newloc = create_gmaps_query(details, report_channel)

        guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['address'] = details
        oldraidmsg = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidmessage']
        oldreportmsg = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidreport']
        oldembed = oldraidmsg.embeds[0]
        newembed = discord.Embed(title=oldembed['title'], url=newloc, colour=message.guild.me.colour)
        newembed.add_field(name=oldembed['fields'][0]['name'], value=oldembed['fields'][0]['value'], inline=True)
        newembed.add_field(name=oldembed['fields'][1]['name'], value=oldembed['fields'][1]['value'], inline=True)
        newembed.set_footer(text=oldembed['footer']['text'], icon_url=oldembed['footer']['icon_url'])
        newembed.set_thumbnail(url=oldembed['thumbnail']['url'])
        newraidmsg = await oldraidmsg.edit(new_content=oldraidmsg.content, embed=newembed)
        newreportmsg = await oldreportmsg.edit(new_content=oldreportmsg.content, embed=newembed)
        guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidmessage'] = newraidmsg
        guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['raidreport'] = newreportmsg
        otw_list = []
        trainer_dict = guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id]['trainer_dict']
        for trainer in trainer_dict.keys():
            user = await Clembot.get_user_info(trainer)
            if trainer_dict[user.id]['status'] == 'omw':
                otw_list.append(user.mention)
        await message.channel.send( content=_("Beep Beep! Someone has suggested a different location for the raid! Trainers {trainer_list}: make sure you are headed to the right place!").format(trainer_list=", ".join(otw_list)), embed=newembed)
        return

coming_list = ["c", "coming", "o" , "omw"]
cancel_list = ["x", "cancel"]
maybe_list = ["i", "interested", "maybe"]
here_list = ["h", "here"]


def convert_command_to_status(text):
    status = None
    command_text = text.replace('!','')

    if command_text in coming_list:
        status = "omw"
    elif command_text in cancel_list:
        status = "cancel"
    elif command_text in maybe_list:
        status = "maybe"
    elif command_text in here_list:
        status = "waiting"

    return status


@Clembot.command(pass_context=True, hidden=True, aliases=["recover-rsvp"])
async def _recover_rsvp(ctx):
    try:
        message = ctx.message
        channel = ctx.message.channel
        guild = ctx.message.guild

        trainer_dict = {}
        async for message in channel.history(limit=500, reverse=True):
            if message.author.id != guild.me.id:
                if message.content.startswith('!'):
                    rsvp_status = convert_command_to_status(message.content.split()[0])
                    try:
                        rsvp_count = int(message.content.split()[1])
                    except Exception:
                        rsvp_count = None
                        pass

                    if rsvp_status:
                        trainer_dict = _add_rsvp_to_dict(trainer_dict, message.author.id, rsvp_status, rsvp_count)
                        print(trainer_dict)

        output_message = None
        if trainer_dict:
            output_message = await _send_rsvp_embed(ctx.message, trainer_dict)
            replace_dict = await ask_confirmation(ctx.message, "Replace the RSVP for the channel?", "Thanks for confirmation.", "No changes done!", "Request Timed out!")

            if replace_dict:
                add_to_raidchannel_dict(ctx.message)
                guild_dict[message.guild.id]['raidchannel_dict'][channel.id]['trainer_dict'] = trainer_dict

            await _send_message(channel, "Beep Beep! **{0}** the RSVP has been updated successfully!".format(message.author.display_name))

        else:
            output_message = await _send_error_message(ctx.message.channel, "No RSVP Detected!")

        await asyncio.sleep(15)
        await message.delete()
        await output_message.delete()

    except Exception as error:
        print(error)

@Clembot.command(pass_context=True, hidden=True, aliases=["mention","m"])
async def _mention(ctx):

    allowed = checks.check_raidchannel(ctx) or checks.check_exraidchannel(ctx) or checks.check_raidpartychannel(ctx) or checks.check_eggchannel(ctx)
    try:
        if not allowed:
            raise ValueError("Beep Beep! **{}**, **mention** can't be used in this channel.".format(ctx.message.author.display_name))

        args = ctx.message.clean_content.split()

        status_to_check = None if len(args) < 2 else convert_command_to_status(args[1])

        message_to_say = None if len(args) < 2 else args[2:] if status_to_check else args[1:]

        trainer_dict = copy.deepcopy(guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'])

        if not message_to_say:
            raise ValueError("Beep Beep! **{}**, please use **!mention [status] <message>**.".format(ctx.message.author.display_name))

        name_list = []
        for trainer in trainer_dict.keys():
            if status_to_check == None or trainer_dict[trainer]['status'] == status_to_check:
                user = await Clembot.get_user_info(trainer)
                name_list.append(user.mention)

        if len(name_list) == 0:
            raise ValueError("Beep Beep! **{}**, No trainers found to mention.".format(ctx.message.author.display_name))

        listmsg = (_("Beep Beep! {trainer_list} \n **{member}** said : {message}").format(member=ctx.message.author.mention, trainer_list=", ".join(name_list), message=" ".join(message_to_say)))

        await ctx.channel.send(listmsg)
    except Exception as error:
        await _send_error_message(ctx.channel, error)


async def _interest(ctx):
    ctx_maybecount = 0

    now = fetch_current_time(ctx.message.channel.guild.id)
    # Grab all trainers who are maybe and sum
    # up their counts
    trainer_dict = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']
    for trainer in trainer_dict.values():
        if trainer['status'] == "maybe":
            ctx_maybecount += trainer['count']

    # If at least 1 person is interested,
    # add an extra message indicating who it is.
    maybe_exstr = ""
    maybe_list = []
    name_list = []
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == 'maybe':
            user = await Clembot.get_user_info(trainer)
            name_list.append("**" + user.name + "**")
            maybe_list.append(user.mention)
    if ctx_maybecount > 0:
        if now.time() >= datetime.time(5, 0) and now.time() <= datetime.time(21, 0):
            maybe_exstr = _(" including {trainer_list} and the people with them! Let them know if there is a group forming").format(trainer_list=", ".join(maybe_list))
        else:
            maybe_exstr = _(" including {trainer_list} and the people with them! Let them know if there is a group forming").format(trainer_list=", ".join(maybe_list))
    listmsg = (_("Beep Beep! {trainer_count} interested{including_string}!").format(trainer_count=str(ctx_maybecount), including_string=maybe_exstr))

    return listmsg






async def _otw(ctx):
    ctx_omwcount = 0
    now = fetch_current_time(ctx.message.channel.guild.id)

    # Grab all trainers who are :omw: and sum
    # up their counts
    trainer_dict = copy.deepcopy(guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'])
    for trainer in trainer_dict.values():
        if trainer['status'] == "omw":
            ctx_omwcount += trainer['count']

    # If at least 1 person is on the way,
    # add an extra message indicating who it is.
    otw_exstr = ""
    otw_list = []
    name_list = []
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == 'omw':
            user = await Clembot.get_user_info(trainer)
            name_list.append("**" + user.name + "**")
            otw_list.append(user.mention)
    if ctx_omwcount > 0:
        otw_exstr = _(" including {trainer_list} and the people with them! Be considerate and wait for them if possible").format(trainer_list=", ".join(otw_list))

    listmsg = (_("Beep Beep! {trainer_count} on the way{including_string}!").format(trainer_count=str(ctx_omwcount), including_string=otw_exstr))
    return listmsg


async def _waiting(ctx):
    ctx_waitingcount = 0
    now = fetch_current_time(ctx.message.channel.guild.id)

    # Grab all trainers who are :here: and sum
    # up their counts
    trainer_dict = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']
    for trainer in trainer_dict.values():
        if trainer['status'] == "waiting":
            ctx_waitingcount += trainer['count']

    # If at least 1 person is waiting,
    # add an extra message indicating who it is.
    waiting_exstr = ""
    waiting_list = []
    name_list = []
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == 'waiting':
            user = await Clembot.get_user_info(trainer)
            name_list.append("**" + user.name + "**")
            waiting_list.append(user.mention)
    try:
        if ctx_waitingcount > 0:
            if now.time() >= datetime.time(5, 0) and now.time() <= datetime.time(21, 0):
                waiting_exstr = _(" including {trainer_list} and the people with them! Be considerate and let them know if and when you'll be there").format(trainer_list=", ".join(waiting_list))
            else:
                waiting_exstr = _(" including {trainer_list} and the people with them! Be considerate and let them know if and when you'll be there").format(trainer_list=", ".join(name_list))
    except Exception as error:
        print(error)
    listmsg = (_("Beep Beep! {trainer_count} waiting at the raid{including_string}!").format(trainer_count=str(ctx_waitingcount), including_string=waiting_exstr))
    return listmsg


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def interest(ctx):
    await ctx.message.channel.send( _("Beep Beep! We've moved this command to **!list interested**."))


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def otw(ctx):
    await ctx.message.channel.send( _("Beep Beep! We've moved this command to **!list coming**."))


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def waiting(ctx):
    await ctx.message.channel.send( _("Beep Beep! We've moved this command to **!list here**."))


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def update(ctx):
    try:
        roster = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
        if len(roster) <= 0:
            await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
            return

        args = ctx.message.clean_content[len("!update"):]
        args_split = args.lower().split()

        location_number = 0
        if len(args_split) > 0:
            if args_split[0].isdigit():
                location_number = int(args_split[0])

        if location_number == 0:
            await ctx.message.channel.send( content=_("Beep Beep! I couldn't understand the location #."))
            return

        del args_split[0]

        roster_loc = None
        for roster_loc_at in roster:
            if roster_loc_at['index'] == location_number:
                roster_loc = roster_loc_at
                break

        if roster_loc is None:
            await ctx.message.channel.send( content=_("Beep Beep! Location {location} doesn't exist on the roster!".format(location=emojify_numbers(location_number))))
            return

        # if len(args_split) > 1:
        #     await ctx.message.channel.send( content=_("Beep Beep! That's too much to update... use `!update <location#> <pokemon-name or gym-code or google map link>`"))
        #     return

        arg = args_split[0].lower()
        # gym_info = gymutil.get_gym_info(arg, city_state=get_city_list(ctx.message))
        gym_info = get_gym_info_wrapper(ctx.message, gym_code=arg)

        if gym_info:
            roster_loc['gym_name'] = gym_info['gym_name']
            roster_loc['gym_code'] = gym_info['gym_code']
            roster_loc['lat_long'] = gym_info['lat_long']
            roster_loc['gmap_link'] = gym_info['gmap_link']
            roster_loc['eta'] = None
            args_split.remove(arg.lower())

        elif arg in pkmn_info['pokemon_list']:
            roster_loc['pokemon'] = arg
            args_split.remove(arg.lower())
        else:
            gmap_link = extract_link_from_text("".join(args_split))
            if gmap_link:
                roster_loc['gmap_link'] = gmap_link
                roster_loc['gym_name'] = "location " + str(roster_loc['index'])
                roster_loc['gym_code'] = "location " + str(roster_loc['index'])
                roster_loc['lat_long'] = extract_lat_long_from(gmap_link)
            else:
                time_as_text = " ".join(args_split)
                eta = convert_into_time(time_as_text, False)
                if eta:
                    roster_loc['eta'] = time_as_text
                else:
                    await ctx.message.channel.send( content=_("Beep Beep! I am not sure what to update;... use `!update <location#> <pokemon-name | gym-code | google map link | eta>` "))
                    return

        await print_roster_with_highlight(ctx.message, location_number, "Beep Beep! Location {location} has been updated.".format(location=emojify_numbers(location_number)))
        return

    except Exception as error:
        await ctx.message.channel.send( content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def raidover(ctx):

    try:
        channel = ctx.message.channel
        message = ctx.message
        started_by = guild_dict[message.guild.id]['raidchannel_dict'][channel.id]['started_by']

        if ctx.message.author.id == started_by:

            clean_channel = await ask_confirmation(ctx.message, "Are you sure to delete the channel?", "The channel will be deleted shortly.", "No changes done!", "Request Timed out!")
            if clean_channel:
                await asyncio.sleep(30)
                try:
                    report_channel = Clembot.get_channel(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['reportcity'])
                    reportmsg = await report_channel.get_message(guild_dict[channel.guild.id]['raidchannel_dict'][channel.id]['raidreport'])
                    expiremsg = _("**This raidparty is over!**")
                    await reportmsg.edit(embed=discord.Embed(description=expiremsg, colour=channel.guild.me.colour))
                except Exception as error:
                    pass
                await ctx.message.channel.delete()


        else:
            await _send_error_message(channel, _("Beep Beep! Only raid reporter can clean up the channel!"))
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def pathshare(ctx):
    try:

        args = ctx.message.clean_content
        args_split = args.split()
        del args_split[0]

        pathshare_url = args_split[0]

        guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['pathshare_url'] = pathshare_url
        guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['pathshare_user'] = ctx.message.author.id

        await ctx.message.channel.send(_("Beep Beep! Pathshare URL has been set to {url}!".format(url=pathshare_url)))
    except Exception as error:
        print(error)





@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def add(ctx):
    try:
        roster = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
        first_index = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster_index']
        if first_index is None:
            first_index = 0

        args = ctx.message.clean_content[4:]
        args_split = args.split(" ")
        del args_split[0]

        roster_loc_mon = args_split[0].lower()
        if roster_loc_mon != "egg":
            if roster_loc_mon not in pkmn_info['pokemon_list']:
                await ctx.message.channel.send( spellcheck(roster_loc_mon))
                return
            if roster_loc_mon not in get_raidlist() and roster_loc_mon in pkmn_info['pokemon_list']:
                await ctx.message.channel.send( _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=roster_loc_mon.capitalize()))
                return
        del args_split[0]

        roster_loc_gym_code = args_split[0]
        # gym_info = gymutil.get_gym_info(roster_loc_gym_code, city_state=get_city_list(ctx.message))
        gym_info = get_gym_info_wrapper(ctx.message, gym_code=roster_loc_gym_code)

        if gym_info:
            del args_split[0]

        eta = None
        if len(args_split) > 0:
            time_as_text = args_split[-1]
            eta = convert_into_time(time_as_text, False)
            if eta:
                del args_split[-1]
            else:
                time_as_text = " ".join(args_split[-2:])
                eta = convert_into_time(time_as_text, False)
                if eta:
                    del args_split[-2:]

        roster_loc_label = " ".join(args_split)
        roster_loc = {}

        if len(roster) < 1:
            roster_loc['index'] = first_index + 1
        else:
            roster_loc['index'] = roster[-1]['index'] + 1

        roster_loc['pokemon'] = roster_loc_mon

        if gym_info:
            roster_loc['gym_name'] = gym_info['gym_name']
            roster_loc['gym_code'] = gym_info['gym_code']
            roster_loc['gmap_link'] = gym_info['gmap_link']
            roster_loc['lat_long'] = gym_info['lat_long']
        else:
            roster_loc['gym_name'] = roster_loc_label
            roster_loc['gym_code'] = roster_loc_label
            roster_loc['gmap_link'] = fetch_gmap_link(roster_loc_label, ctx.message.channel)
            roster_loc['lat_long'] = None

        if eta:
            roster_loc['eta'] = time_as_text

        roster.append(roster_loc)

        roster_message = _("Location {location_number} has been been added to roster!").format(location_number=emojify_numbers(roster_loc['index']))

        await print_roster(ctx.message, roster_message)
    except Exception as error:
        await ctx.message.channel.send( content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))


async def _add(message, gmap_link):
    author = message.author
    guild = message.guild
    channel = message.channel

    if author.id == "364905300244824065":
        return

    add_location = await ask_confirmation(message, "Do you want to add this location to roster?", "Location will be added to roster", "Clembot will ignore the location", "request timed out")

    if add_location == False:
        return

    try:
        roster = guild_dict[guild.id]['raidchannel_dict'][channel.id]['roster']
        first_index = guild_dict[guild.id]['raidchannel_dict'][channel.id]['roster_index']
        roster_loc = {}

        roster_loc_gym_link = None
        roster_loc_mon = "* * * "
        if gmap_link:
            roster_loc_gym_link = gmap_link

            if len(roster) < 1:
                if first_index:
                    roster_loc['index'] = first_index + 1
                else:
                    roster_loc['index'] = 1
            else:
                roster_loc['index'] = roster[-1]['index'] + 1

            roster_loc['pokemon'] = roster_loc_mon
            roster_loc['gmap_link'] = gmap_link
            roster_loc['gym_name'] = "location " + str(roster_loc['index'])
            roster_loc['gym_code'] = "location " + str(roster_loc['index'])
            roster_loc['lat_long'] = extract_lat_long_from(gmap_link)
            roster.append(roster_loc)

            roster_message = _("Location {location_number} has been been added to roster!").format(location_number=emojify_numbers(roster_loc['index']))

            await print_roster(message, roster_message)
    except Exception as error:
        await message.channel.send( content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))
    return


async def reindex_roster(roster):
    if len(roster) > 0:
        current_index = roster[0]['index']

        for roster_loc in roster:
            roster_loc['index'] = current_index
            current_index = current_index + 1
    return roster


@Clembot.command(pass_context=True, hidden=True, aliases=["remove"])
@checks.raidpartychannel()
async def _remove(ctx):
    roster = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

    if len(roster) < 1:
        await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return

    args = ctx.message.clean_content[len("!remove"):]
    args_split = args.split()

    location_number = 0
    if len(args_split) > 0:
        if args_split[0].isdigit():
            location_number = int(args_split[0])

    if location_number == 0:
        return

    first_roster_index = roster[0]['index']
    is_location_found = False
    for roster_loc in roster:
        if roster_loc['index'] == location_number:
            is_location_found = True
            roster.remove(roster_loc)
            roster_message = _("Location {location_number} has been removed from roster!").format(location_number=location_number)
            break

    if is_location_found:
        if len(roster) == 0:
            # guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster_index'] = first_roster_index
            await ctx.message.channel.send( content=_("Beep Beep! {member}, {roster_message}").format(member=ctx.message.author.mention, roster_message=roster_message))
        else:
            await reindex_roster(roster)
            await print_roster(ctx.message, roster_message)
    else:
        roster_message = _("Location {location_number} does not exist on roster!").format(location_number=emojify_numbers(location_number))
        await ctx.message.channel.send( content=_("Beep Beep! {member}, {roster_message}").format(member=ctx.message.author.mention, roster_message=roster_message))

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def move(ctx):
    roster = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
    if len(roster) < 1:
        await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return

    # if all roster items are visited already, keep the number for later usage!
    first_roster_index = roster[0]['index']

    del roster[0]

    if len(roster) == 0:
        guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster_index'] = first_roster_index
        await ctx.message.channel.send( content=_("Beep Beep! {member}, all the locations on this roster are done!").format(member=ctx.message.author.mention))
    else:
        await print_roster(ctx.message, _("raid party is moving to the next location in the roster!"))

    return
def get_roster_messages_with_highlight(roster, highlight_roster_loc):
    roster_msg = ""
    roster_msg_list = []
    index = 0
    try:
        for roster_loc in roster:
            if highlight_roster_loc == roster_loc['index']:
                marker = "**"
            else:
                marker = ""
            eta = roster_loc.get('eta', "")
            if eta:
                eta = " [{eta}]".format(eta=eta)
            else:
                eta = ""
            if len(roster_msg) > 1900:
                roster_msg_list.append(roster_msg)
                roster_msg = ""

            roster_msg += _("\n{marker1}{number} [{gym}]({link}) - {pokemon}{eta}{marker2}").format(number=emojify_numbers(roster_loc['index']), pokemon=roster_loc['pokemon'].capitalize(), gym=roster_loc['gym_name'], link=roster_loc['gmap_link'], eta=eta, marker1=marker, marker2=marker)

        roster_msg_list.append(roster_msg)
    except Exception as error:
        print(error)

    return roster_msg_list


def get_roster_with_highlight(roster, highlight_roster_loc):
    roster_msg = ""

    try:
        for roster_loc in roster:
            if highlight_roster_loc == roster_loc['index']:
                marker = "**"
            else:
                marker = ""
            eta = roster_loc.get('eta', "")
            if eta:
                eta = " [{eta}]".format(eta=eta)
            else:
                eta = ""
            if len(roster_msg) > 1900:
                roster_msg += "\n and more!"
                break
            else:
                roster_msg += _("\n{marker1}{number} [{gym}]({link}) - {pokemon}{eta}{marker2}").format(number=emojify_numbers(roster_loc['index']), pokemon=roster_loc['pokemon'].capitalize(), gym=roster_loc['gym_name'], link=roster_loc['gmap_link'], eta=eta, marker1=marker, marker2=marker)

    except Exception as error:
        print(error)

    return roster_msg


# **Note:** *<> are used for decoration only.*
# **For Raid Organizer**
# `!raidparty <channel name>` creates a raid party channel
# `!add <pokemon or egg> <gym-code or gym name or location>` adds a location into the roster
# `!move` moves raid party to the next location in roster
# `!remove <location#>` removes specified location from roster
# `!update <location#> <gym-code>` updates the gym code for location #
# `!update <location#> <pokemon>` updates the pokemon for location #
# `!reset` cleans up the roster
# *Alternatively you can always paste a link and add a location into roster!*


@Clembot.command(pass_context=True, hidden=True)
async def raidpartyhelp(ctx):
    await ctx.message.channel.send( _("Beep Beep! We've moved this command to `!beep raidparty`."))
    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def current(ctx):
    roster = guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

    if len(roster) < 1:
        await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return
    roster_index = roster[0]['index']
    roster_message = _("Raid Party is at location {location_number} on the roster!").format(location_number=emojify_numbers(roster_index))

    await print_roster_with_highlight(ctx.message, roster_index, roster_message)
    return

def add_to_raidchannel_dict(message):

    existing_dict = guild_dict[message.guild.id]['raidchannel_dict'].get(message.channel.id, {})

    reportcity = existing_dict.get('reportcity', message.channel.id)
    trainer_dict = existing_dict.get('trainer_dict', {})
    exp = existing_dict.get('exp', None)
    manual_timer = existing_dict.get('manual_timer', False)
    active = existing_dict.get('active', True)
    raidmessage = existing_dict.get('raidmessage', None)
    type = existing_dict.get('type', 'raidparty')
    pokemon = existing_dict.get('pokemon', None)
    egglevel = existing_dict.get('egglevel', -1)
    suggested_start = existing_dict.get('suggested_start', False)
    roster = existing_dict.get('roster', [])
    roster_index = existing_dict.get('roster_index', None)
    started_by = existing_dict.get('started_by', message.author.id)

    new_dict = {
        'reportcity': reportcity,
        'trainer_dict': trainer_dict,
        'exp': exp,
        'manual_timer': manual_timer,
        'active': active,
        'raidmessage': raidmessage,
        'type': type,
        'pokemon': pokemon,
        'egglevel': egglevel,
        'suggested_start': suggested_start,
        'roster': roster,
        'roster_index': roster_index,
        'started_by' : started_by
    }

    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id] = new_dict



@Clembot.command(pass_context=True, hidden=True)
async def makeitraidparty(ctx):
    message = ctx.message

    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': None,
        'type': 'raidparty',
        'pokemon': None,
        'egglevel': -1,
        'suggested_start': False,
        'roster': [],
        'roster_index': None,
        'started_by' : message.author.id
    }

    await message.channel.send( content=_("Beep Beep! It's a raid party channel now!"))

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def reset(ctx):
    message = ctx.message

    guild_dict[message.guild.id]['raidchannel_dict'][message.channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': None,
        'type': 'raidparty',
        'pokemon': None,
        'egglevel': -1,
        'suggested_start': False,
        'roster': [],
        'roster_index': None
    }

    await message.channel.send( content=_("Beep Beep! The roster has been cleared!"))

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def where(ctx):
    try:
        roster = guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

        args = ctx.message.clean_content[len("!where"):]
        args_split = args.split()

        location_number = 0
        if len(args_split) > 0:
            if args_split[0].isdigit():
                location_number = int(args_split[0])
        else:
            pathshare_url = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id].get('pathshare_url', None)
            pathshare_user = guild_dict[ctx.message.guild.id]['raidchannel_dict'][ctx.message.channel.id].get('pathshare_user')
            if pathshare_url == None:
                await ctx.message.channel.send( content=_("Beep Beep! Give more details! Usage: `!where <location #>`"))
            else:
                await ctx.message.channel.send(content=_("Beep Beep! <@!{raidcreator}>'s live location can be accessed at : {pathshare}".format(raidcreator=pathshare_user, pathshare=pathshare_url)))
            return

        if len(roster) < 1:
            await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
            return

        for roster_loc_at in roster:
            if roster_loc_at['index'] == location_number:
                roster_loc = roster_loc_at

                await print_roster_with_highlight(ctx.message, roster_loc['index'], "Location {location} - {gym} - {pokemon}".format(location=emojify_numbers(roster_loc['index']), pokemon=roster_loc['pokemon'].capitalize(), gym=roster_loc['gym_name']))
                return
        await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have location {location_number}.".format(location_number=emojify_numbers(location_number))))
        return

    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True, aliases= ["next"])
@checks.raidpartychannel()
async def _next_location(ctx):
    roster = guild_dict[ctx.message.channel.guild.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

    if len(roster) < 1:
        await ctx.message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return
    roster_index = roster[0]['index']

    if len(roster) < 2:
        status_message = _("Raid party is at **{current}/{total}** location. Next location doesn't exist on roster!").format(current=roster_index, total=roster_index)
        await ctx.message.channel.send( content=_("Beep Beep! {status_message}").format(status_message=status_message))
        return

    roster_index = roster[1]['index']

    roster_message = _("Raid Party will be headed next to location {location_number} on the roster!").format(location_number=emojify_numbers(roster_index))

    await print_roster_with_highlight(ctx.message, roster_index, roster_message)
    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def roster(ctx):
    await print_roster(ctx.message)


async def print_roster_with_highlight(message, highlight_roster_loc, roster_message=None):
    try:
        roster = guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster']

        if highlight_roster_loc:
            roster_index = highlight_roster_loc
        else:
            if len(roster) < 1:
                await message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
                return

        roster_msg = ""
        highlighted_loc = None
        lat_long = None
        for roster_loc in roster:
            if highlight_roster_loc == roster_loc['index']:
                highlighted_loc = roster_loc
                lat_long = roster_loc['lat_long']
                break

        if highlighted_loc['pokemon'] == 'egg':
            raid_img_url = get_egg_image_url(5)
        else:
            raid_number = pkmn_info['pokemon_list'].index(highlighted_loc['pokemon']) + 1
            raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite

        # raid_party_image_url = "https://cdn.discordapp.com/attachments/354694475089707039/371000826522632192/15085243648140.png"
        # raid_img_url = raid_party_image_url

        # "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png".format(str(raid_number))

        embed_title = _("Click here for directions for Location {highlight_roster_loc}!").format(highlight_roster_loc=emojify_numbers(highlight_roster_loc))
        roster_loc_gmap_link = highlighted_loc['gmap_link']
        embed_map_image_url = None

        embed_desription = "*location link doesn't support preview...*"
        if lat_long:
            embed_desription = ""

        raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title), url=roster_loc_gmap_link, image=raid_img_url, description=embed_desription)
        raid_embed.add_field(name="**Raid Boss:**", value=_("{raidboss}").format(raidboss=roster_loc['pokemon'].capitalize()), inline=True)
        raid_embed.add_field(name="**Location Details:**", value=_("{location}").format(location=roster_loc['gym_name']), inline=True)
        if 'eta' in roster_loc:
            if roster_loc['eta']:
                raid_embed.add_field(name="**ETA:**", value=_("{eta}").format(eta=roster_loc['eta']), inline=True)
        raid_embed.set_thumbnail(url=raid_img_url)
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=message.author.avatar_url)
        if lat_long:
            embed_map_image_url = fetch_gmap_image_link(lat_long)
            raid_embed.set_image(url=embed_map_image_url)

        await message.channel.send( content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention, roster_message=roster_message), embed=raid_embed)

    except Exception as error:
        print(error)
    return


async def print_roster(message, roster_message=None):
    roster = guild_dict[message.channel.guild.id]['raidchannel_dict'][message.channel.id]['roster']

    if len(roster) < 1:
        await message.channel.send( content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return

    roster_index = roster[0]['index']

    raid_party_image_url = "https://media.discordapp.net/attachments/419935483477622793/450201828802560010/latest.png"

    raid_img_url = raid_party_image_url
    # "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png".format(str(raid_number))

    if roster_index:
        current_roster = roster[0]
        embed_title = _("Raid Party is at Location#{index}. Click here for directions!").format(index=emojify_numbers(roster_index))
        raid_party_image_url = current_roster['gmap_link']
    else:
        embed_title = "Raid Party has not started yet!!"
        raid_party_image_url = ""

    roster_msg_list = get_roster_messages_with_highlight(roster, roster_index)
    roster_msg = roster_msg_list[0]

    raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title), url=raid_party_image_url, description=roster_msg)
    raid_embed.set_footer(text=_("Requested by @{author}").format(author=message.author.display_name), icon_url=message.author.avatar_url)
    raid_embed.set_thumbnail(url=raid_img_url)

    if roster_message:
        await message.channel.send( content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention, roster_message=roster_message), embed=raid_embed)
    else:
        await message.channel.send( content=_("Beep Beep! {member} here is the raid party roster: ").format(member=message.author.mention), embed=raid_embed)

    if len(roster_msg_list) > 1:
        for roster_msg in roster_msg_list[1:] :
            raid_embed = discord.Embed(description=roster_msg)
            raid_embed.set_footer(text=_("Requested by @{author}").format(author=message.author.display_name),icon_url=message.author.avatar_url)
            raid_embed.set_thumbnail(url=raid_img_url)
            await message.channel.send(embed=raid_embed)

    return


async def _generate_gym_embed(message, gym_info):
    embed_title = _("Click here for direction to {gymname}!").format(gymname=gym_info['gym_name'])

    embed_desription = _("**Gym Code :** {gymcode}\n**Gym Name :** {gymname}\n**City :** {city}").format(gymcode=gym_info['gym_code_key'], gymname=gym_info['original_gym_name'], city=gym_info['gym_location_city'])

    raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title), url=gym_info['gmap_url'], description=embed_desription)

    embed_map_image_url = fetch_gmap_image_link(gym_info['latitude'] + "," + gym_info['longitude'])
    raid_embed.set_image(url=embed_map_image_url)

    if gym_info['gym_image']:
        raid_embed.set_thumbnail(url=gym_info['gym_image'])
    roster_message = "here are the gym details! "

    await message.channel.send( content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention, roster_message=roster_message), embed=raid_embed)






async def _get_gym_info_list(message, gym_code):
    print("_get_gym_info_list")
    city = _read_channel_city(message)

    gym_info_list = gymsql.get_gym_list_by_code(city_state_key=city, gym_code_key=gym_code)

    if len(gym_info_list) == 0:
        await message.channel.send( content="Beep Beep...Hmmm, that's a gym-code I am not aware of! Type `**!gyms** with a letter to see all gyms starting from that letter!")
        return []

    return gym_info_list


async def _get_gym_info(message, gym_code):

    city = _read_channel_city(message)

    gym_info = gymsql.get_gym_by_code(city_state_key=city, gym_code_key=gym_code)
    print("_get_gym_info() : {gym_info}".format(gym_info=gym_info))
    if gym_info:
        await _generate_gym_embed(message, gym_info)
        return gym_info

    await _send_error_message(message.channel, "Beep Beep... **{member}** No gyms found with **{gym_code}** in **{city}**. Please use **!gyms** to see the list of gyms.".format(member=message.author.display_name, city=city,gym_code=gym_code))
    return None


@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def reloadconfig(ctx):
    try:
        load_config()
        await ctx.message.channel.send( content=_("Beep Beep! configuration reloaded!"))
    except Exception as error:
        await ctx.message.channel.send( content=_("Beep Beep! Error : {error}").format(error=str(error)))
    return

@Clembot.command(pass_context=True, hidden=True,aliases=["restore-gym"])
@commands.has_permissions(manage_guild=True)
async def _restore_gym(ctx):
    try:
        message = ctx.message
        message_text = message.content.replace("!restore-gym ","")

        gym_info = json.loads(message_text)

        gymsql.update_gym_info(gym_info)

        await ctx.message.channel.send("Beep Beep! Gym has been updated successfully.")
    except Exception as error:
        logger.error(error)
        await ctx.message.channel.send("Beep Beep! Error in gym update.")

@Clembot.command(pass_context=True, hidden=True,aliases=["add-gym"])
@commands.has_permissions(manage_guild=True)
async def _add_gym(ctx):
    try:
        message = ctx.message
        message_text = message.content.replace("!add-gym ","")

        gym_info = json.loads(message_text)
        city = _read_channel_city(message)
        gym_dict = gymsql.find_gym(city, gym_info['gym_code_key'])

        if gym_dict:
            return await ctx.message.channel.send("Beep Beep! The gym already exists with this code.")


        gymsql.insert_gym_info(gym_info)

        await ctx.message.channel.send("Beep Beep! Gym has been added successfully.")
    except Exception as error:
        logger.error(error)
        await ctx.message.channel.send("Beep Beep! Error in gym update.")


@Clembot.command(pass_context=True, hidden=True,aliases=["remove-gym"])
@commands.has_permissions(manage_guild=True)
async def _remove_gym(ctx):
    try:
        message = ctx.message
        args = ctx.message.content
        args_split = args.split(" ")
        del args_split[0]

        gym_code = args_split[0].upper()

        if 0 < len(args_split) < 2:
            city = _read_channel_city(ctx.message)
            gym_dict = gymsql.find_gym(city, args_split[0])
            if len(gym_dict) == 0:
                return await _send_error_message(message.channel, "Beep Beep...! **{member}** I couldn't find a match for {gym_code} in {city_code}".format(member=message.author.display_name,gym_code=gym_code, city_code=city))

            gymsql.delete_gym_info(city, args_split[0])
            return await _send_message(message.channel, "Beep Beep...! **{member}** The gym has been removed successfully.".format(member=message.author.display_name))
        else:
            await _send_error_message(message.channel, "Beep Beep...! **{message}** please provide gym-code for lookup.".format(member=message.author.display_name))
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True,aliases=["update-gym"])
@commands.has_permissions(manage_guild=True)
async def _update_gym(ctx):
    try :
        args = ctx.message.clean_content.split()
        del args[0]

        if len(args) < 3:
            return await _send_error_message(ctx.message.channel, "Beep Beep! **{0}** Correct usage is **!update-gym gym-code field-name value**".format(ctx.message.author.display_name))

        channel_city = _read_channel_city(ctx.message)
        gymsql.update_gym(channel_city, args[0], args[1], " ".join(args[2:]))

        gym_dict = gymsql.find_gym(channel_city, args[0])

        if gym_dict:
            return await _send_message(ctx.message.channel, json.dumps(gym_dict, indent=4, sort_keys=True))
        else:
            return await _send_error_message(ctx.message.channel, "Beep Beep! **{0}** No gym found by **{1}** in **{2}**!".format(ctx.message.author.display_name, args[0], channel_city))

        return
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True,aliases=["get-gym"])
@commands.has_permissions(manage_guild=True)
async def _get_gym(ctx):

    try:
        args = ctx.message.clean_content.split()
        del args[0]

        if len(args) < 1:
            await ctx.message.channel.send(content=_("Beep Beep! Please provide information as !get-gym gym-code"))
        city_state = _read_channel_city(ctx.message)
        response = gymsql.get_gym_by_code(city_state, args[0])
        await ctx.message.channel.send( content=json.dumps(response, indent=4, sort_keys=True))
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True,aliases=["get-card"])
async def _get_card(ctx):

    try:
        message = ctx.message

        event_pokemon = _get_bingo_event_pokemon(message.guild.id, "bingo-event")
        event_title_map = gymsql.find_clembot_config("bingo-event-title")
        timestamp = (message.created_at + datetime.timedelta(hours=guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))

        args = ctx.message.clean_content.split()
        bingo_card = bingo_generator.generate_card()
        response = bingo_generator.print_card_as_text(bingo_card)

        embed_msg = "**!{0}!**".format(event_title_map[event_pokemon])

        embed = discord.Embed(description=embed_msg, colour=discord.Colour.gold())

        embed.add_field(name="**For**", value="{user} at {timestamp}".format(user=ctx.message.author.mention, timestamp=timestamp), inline=True)

        embed.add_field(name="**Card**", value="{card}".format(card=response), inline=True)

        embed.set_footer(text="Generated for : {user} at {timestamp}".format(user=ctx.message.author.display_name, timestamp=timestamp))
        await ctx.message.channel.send(embed=embed)


    except Exception as error:
        print(error)

bingo = WowBingo()

@Clembot.command(pass_context=True, hidden=True,aliases=["bingo"])
async def _bingo_win(ctx):
    try:
        message = ctx.message
        print("_bingo_win called")

        event_title_map = gymsql.find_clembot_config("bingo-event-title")
        event_pokemon = _get_bingo_event_pokemon(message.guild.id, "bingo-event")

        timestamp = (message.created_at + datetime.timedelta(hours=guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))
        existing_bingo_card_record = gymsql.find_bingo_card(ctx.message.guild.id, ctx.message.author.id, event_pokemon)

        if existing_bingo_card_record:
            raid_embed = discord.Embed(title=_("**{0} Shoutout!**".format(event_title_map.get(event_pokemon,"BingO"))), description="", colour=discord.Colour.dark_gold())

            raid_embed.add_field(name="**Member:**", value=_("**{member}** believes the following Bingo card is completed as of **{timestamp}**.").format(member=message.author.display_name, timestamp=timestamp), inline=True)
            raid_embed.set_image(url=existing_bingo_card_record['bingo_card_url'])
            raid_embed.set_thumbnail(url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=message.author, format="jpg")))

            msg = 'Beep Beep! {0.author.mention} one of the moderators/admin will contact you for verification. Please follow the guidelines below to complete the submission.'.format(message)

            guidelines = ":one: Submit **2 photos** as specified (use any collage app on your phone). \n:two: A screenshot of **all 9 event pokemon renamed**. \nSee: https://goo.gl/nPcRr5 \n:three: A collage for **box#2, 4, 6, 8 pokemon** with height, weight and gender requirements. \nSee: https://goo.gl/YrSSvM "
            raid_embed.add_field(name="**Submission Guidelines**", value=guidelines)


            await message.channel.send(content=msg)
            await message.channel.send(embed=raid_embed)

        else:
            await message.channel.send("Beep Beep! {0} you will need to generate a bingo card first!".format(message.author.mention))

    except Exception as error:
        print(error)
    return


@Clembot.command(pass_context=True, hidden=True, aliases=["bingo-card"])
async def _bingo_card(ctx):
    print("_bingo_card() called")
    command_option = "-new"
    is_option_new = False
    try :
        message = ctx.message
        args = message.content
        args_split = args.split()
        if args_split.__contains__(command_option):
            args_split.remove(command_option)
            is_option_new = True

        message = ctx.message
        author = ctx.message.author

        if len(ctx.message.mentions) > 0:
            author = ctx.message.mentions[0]
        print("calling")
        event_title_map = gymsql.find_clembot_config("bingo-event-title")
        logger.info(event_title_map)
        event_pokemon = _get_bingo_event_pokemon(message.guild.id, "bingo-event")
        logger.info(event_pokemon)
        if event_pokemon == None:
            return await _send_error_message(message.channel, "Beep Beep! **{member}** The bingo-event is not set yet. Please contact an admin to run **!set bingo-event pokemon**".format(ctx.message.author.display_name))

        existing_bingo_card_record = gymsql.find_bingo_card(ctx.message.guild.id, author.id, event_pokemon)

        if is_option_new:
            existing_bingo_card_record = None


        if existing_bingo_card_record:
            bingo_card = json.loads(existing_bingo_card_record['bingo_card'])
            timestamp = existing_bingo_card_record['generated_at']
            file_url = existing_bingo_card_record['bingo_card_url']
        else:
            bingo_card = bingo_generator.generate_card(event_pokemon)
            timestamp = (message.created_at + datetime.timedelta(hours=guild_dict[message.channel.guild.id]['offset'])).strftime(_('%I:%M %p (%H:%M)'))
            file_path = bingo.generate_board(user_name=author.id, bingo_card=bingo_card, template_file="{0}.png".format(event_pokemon)) # bingo_template.get(message.guild.id,"bingo_template.png")
            repo_channel = await get_repository_channel(message)

            file_url_message = await repo_channel.send(file=discord.File(file_path), content="Generated for : {user} at {timestamp}".format(user=author.mention, timestamp=timestamp))
            file_url = file_url_message.attachments[0].url

        msg = 'Beep Beep! {0.author.mention} here is your Bingo Card; please take a screenshot for future use!'.format(message)

        embed_msg = "**!{0}!**".format(event_title_map.get(event_pokemon,"BingO"))
        embed = discord.Embed(title=embed_msg,colour=discord.Colour.gold())
        embed.set_image(url=file_url)
        embed.set_footer(text="Generated for : {user} at {timestamp}".format(user=author.display_name, timestamp=timestamp))

        await message.channel.send(msg)

        await ctx.message.channel.send(embed=embed)

        if not existing_bingo_card_record:
            gymsql.save_bingo_card(ctx.message.guild.id, author.id, event_pokemon, bingo_card, file_url, str(timestamp))
            os.remove(file_path)

    except Exception as error:
        print(error)
    return


async def get_repository_channel(message):
    try:
        bingo_card_repo_channel = None

        if 'bingo_card_repo' in guild_dict[message.guild.id]:
            bingo_card_repo_channel_id = guild_dict[message.guild.id]['bingo_card_repo']
            if bingo_card_repo_channel_id:
                bingo_card_repo_channel = Clembot.get_channel(bingo_card_repo_channel_id)

        if bingo_card_repo_channel == None:
            bingo_card_repo_category = get_category(message.channel, None)
            bingo_card_repo_channel = await message.guild.create_text_channel('bingo_card_repo', overwrites=dict(message.channel.overwrites), category=bingo_card_repo_category)

        bingo_card_repo = {'bingo_card_repo': bingo_card_repo_channel.id}
        guild_dict[message.guild.id].update(bingo_card_repo)
        return bingo_card_repo_channel

    except Exception as error:
        logger.error(error)


@Clembot.command(hidden=True)
async def profilex(ctx, user: discord.Member = None):
    """Displays a user's social and reporting profile.

    Usage:!profile [user]"""
    if not user:
        user = ctx.message.author
    silph = guild_dict[ctx.guild.id]['trainers'].setdefault(user.id,{}).get('silphid',None)
    if silph:
        silph = f"[Traveler Card](https://sil.ph/{silph.lower()})"
    embed = discord.Embed(title=f"{user.display_name}\'s Trainer Profile", colour=user.colour)
    embed.set_thumbnail(url=user.avatar_url)

    embed.add_field(name="Silph Road", value=f"{silph}", inline=True)
    embed.add_field(name="Pokebattler Id", value=f"{guild_dict[ctx.guild.id]['trainers'].setdefault(user.id,{}).get('pokebattlerid',None)}", inline=True)

    trainer_profile=guild_dict[ctx.guild.id]['trainers'].setdefault(user.id,{})

    leaderboard_list = ['lifetime']
    addtional_leaderboard = get_guild_local_leaderboard(ctx.guild.id)
    if addtional_leaderboard :
        leaderboard_list.append(addtional_leaderboard)

    for leaderboard in leaderboard_list:

        reports_text = "**Raids : {} | Eggs : {} | Wilds : {} | Research : {}**".format(trainer_profile.setdefault(leaderboard,{}).get('raid_reports',0) ,
                                                                                        trainer_profile.setdefault(leaderboard, {}).get('egg_reports',0) ,
                                                                                        trainer_profile.setdefault(leaderboard, {}).get('wild_reports',0),
                                                                                        trainer_profile.setdefault(leaderboard, {}).get('research_reports',0) )

        embed.add_field(name="Leaderboard : {}".format(leaderboard.capitalize()), value=f"{reports_text}", inline=True)

    await ctx.send(embed=embed)


@Clembot.command(pass_context=True, hidden=True, aliases=["reset-leaderboard"])
@checks.is_owner()
async def _reset_leaderboard(ctx, leaderboard_type=None):
    """Displays the top ten reporters of a server.

    Usage: !leaderboard [type]
    Accepted types: raids, eggs, exraids, wilds, research"""

    leaderboard_list = []

    addtional_leaderboard = get_guild_local_leaderboard(ctx.guild.id)
    if addtional_leaderboard :
        leaderboard_list.append(addtional_leaderboard)

    if not leaderboard_type:
        return await _send_error_message(ctx.channel, "Beep Beep! **{}**, please provide leaderboard to be cleared.".format(ctx.author.mention))

    if leaderboard_type not in leaderboard_list:
        return await _send_error_message(ctx.message.channel, _("Beep Beep! **{0}** Leaderboard type not supported. Please select from: **{1}**").format(ctx.message.author.display_name, ", ".join(leaderboard_list)))
    trainers = copy.deepcopy(guild_dict[ctx.guild.id]['trainers'])

    for trainer in trainers.keys():
        guild_dict[ctx.guild.id]['trainers'][trainer][leaderboard_type] = {}

    await _send_message(ctx.channel, "Beep Beep! **{}**, **{}** has been cleared.".format(ctx.author.mention, leaderboard_type))


@Clembot.command()
async def leaderboard(ctx, lb_type="lifetime" , r_type="total"):
    """Displays the top ten reporters of a server.

    Usage: !leaderboard [type]
    Accepted types: raids, eggs, exraids, wilds, research"""
    try:
        leaderboard = []
        rank = 1
        typelist = ["total", "raids", "wilds", "research", "eggs"]
        type = r_type.lower()

        leaderboard_list = ['lifetime']
        addtional_leaderboard = get_guild_local_leaderboard(ctx.guild.id)
        if addtional_leaderboard :
            leaderboard_list.append(addtional_leaderboard)

        leaderboard_type = lb_type if lb_type in leaderboard_list else 'lifetime'

        report_type = r_type if r_type in typelist else 'total'

        if leaderboard_type != lb_type and report_type == 'total':
            report_type = lb_type if lb_type in typelist else 'total'

        if r_type != type and leaderboard != leaderboard_type and leaderboard != type:
            return await _send_error_message(ctx.message.channel, _("Beep Beep! **{0}** Leaderboard type not supported. Please select from: **{1}**").format(ctx.message.author.display_name, ", ".join(typelist)))

        trainers = copy.deepcopy(guild_dict[ctx.guild.id]['trainers'])

        for trainer in trainers.keys():
            raids = trainers[trainer].setdefault(leaderboard_type,{}).setdefault('raid_reports', 0)
            wilds = trainers[trainer].setdefault(leaderboard_type,{}).setdefault('wild_reports', 0)
            exraids = trainers[trainer].setdefault(leaderboard_type,{}).setdefault('ex_reports', 0)
            eggs = trainers[trainer].setdefault(leaderboard_type,{}).setdefault('egg_reports', 0)
            research = trainers[trainer].setdefault(leaderboard_type,{}).setdefault('research_reports', 0)
            total_reports = raids + wilds + exraids + eggs + research
            trainer_stats = {'trainer':trainer, 'total':total_reports, 'raids':raids, 'wilds':wilds, 'research':research, 'eggs':eggs}
            if trainer_stats[type] > 0:
                leaderboard.append(trainer_stats)

        leaderboard = sorted(leaderboard, key=lambda x: x[report_type], reverse=True)[:10]
        embed = discord.Embed(colour=ctx.guild.me.colour)
        embed.set_author(name=_("Leaderboard Type: {leaderboard_type} ({report_type})").format(leaderboard_type=leaderboard_type.title(), report_type=report_type.title()), icon_url=Clembot.user.avatar_url)
        for trainer in leaderboard:
            user = ctx.guild.get_member(trainer['trainer'])
            if user:
                embed.add_field(name=f"{rank}. {user.display_name} - {type.title()}: **{trainer[type]}**", value=f"Raids: **{trainer['raids']}** | Eggs: **{trainer['eggs']}** | Wilds: **{trainer['wilds']}** | Research: **{trainer['research']}**", inline=False)
                rank += 1
        await ctx.send(embed=embed)
    except Exception as error:
        print(error)

@Clembot.command(pass_context=True, hidden=True, aliases=["pokedex"])
@checks.is_owner()
async def _pokedex(ctx, pokemon=None):
    if pokemon:
        return await _send_message(ctx.channel, "{}".format(get_number(pokemon.lower())))
    else:
        return await _send_error_message(ctx.channel, "!pokedex <pokemon>")

@Clembot.command(pass_context=True, hidden=True, aliases=["raid-boss"])
@checks.is_owner()
async def raid_boss(ctx, level=None, *, newlist=None):
    try:
        'Edits or displays raid_info.json\n\n    Usage: !raid_json [level] [list]'
        msg = ''
        if (not level) and (not newlist):
            for level in raid_info['raid_eggs']:
                msg += _('\n**Level {level} raid list:** `{raidlist}` \n').format(level=level, raidlist=raid_info['raid_eggs'][level]['pokemon'])
                for pkmn in raid_info['raid_eggs'][level]['pokemon']:
                    msg += '**{name}** ({number})'.format(name=get_name(pkmn), number=pkmn)
                    msg += ' '
                msg += '\n'
            return await _send_message(ctx.channel, msg)
        elif level.isdigit() and (not newlist):
            msg += _('**Level {level} raid list:** `{raidlist}` \n').format(level=level, raidlist=raid_info['raid_eggs'][level]['pokemon'])
            for pkmn in raid_info['raid_eggs'][level]['pokemon']:
                msg += '**{name}** ({number})'.format(name=get_name(pkmn), number=pkmn)
                msg += ' '
            msg += '\n'
            return await _send_message(ctx.channel, msg)
        elif level.isdigit() and newlist:
            newlist = newlist.strip('[]').replace(' ', '').split(',')
            intlist = [int(x) for x in newlist]
            msg += _('I will replace this:\n')
            msg += _('**Level {level} raid list:** `{raidlist}` \n').format(level=level, raidlist=raid_info['raid_eggs'][level]['pokemon'])
            for pkmn in raid_info['raid_eggs'][level]['pokemon']:
                msg += '**{name}** ({number})'.format(name=get_name(pkmn), number=pkmn)
                msg += ' '
            msg += _('\n\nWith this:\n')
            msg += _('**Level {level} raid list:** `{raidlist}` \n').format(level=level, raidlist=('[' + ', '.join(newlist)) + ']')
            for pkmn in newlist:
                msg += '**{name}** ({number})'.format(name=get_name(pkmn), number=pkmn)
                msg += ' '
            msg += _('\n\nContinue?')
            question = await _send_message(ctx.channel, msg)
            try:
                timeout = False
                res, reactuser = await ask(question, ctx.channel, ctx.author.id)
            except TypeError:
                timeout = True
            if timeout or res.emoji == '❎':
                await question.clear_reactions()
                return
            elif res.emoji == '✅':
                with open(os.path.join('data', 'raid_info.json'), 'r') as fd:
                    data = json.load(fd)
                tmp = data['raid_eggs'][level]['pokemon']
                data['raid_eggs'][level]['pokemon'] = intlist
                with open(os.path.join('data', 'raid_info.json'), 'w') as fd:
                    json.dump(data, fd, indent=2, separators=(', ', ': '))
                load_config()
                Clembot.raidlist = get_raidlist()
                await question.clear_reactions()
                await question.add_reaction('☑')
            else:
                return
    except Exception as error:
        print(error)


@list.command()
@checks.citychannel()
async def wild(ctx):
    """List the wilds for the channel

    Usage: !list wilds"""
    listmsg = _('**Beep Beep!**')
    listmsg += await _wildlist(ctx)
    await _send_message(ctx.channel, listmsg)

async def _wildlist(ctx):
    wild_dict = copy.deepcopy(guild_dict[ctx.guild.id]['wildreport_dict'])
    wildmsg = ""
    for wildid in wild_dict:
        if wild_dict[wildid]['reportchannel'] == ctx.message.channel.id:
            wildmsg += ('\n🔰')
            wildmsg += _("**Pokemon**: {pokemon}, **Location**: {location}".format(pokemon=wild_dict[wildid]['pokemon'].title(),location=wild_dict[wildid]['location'].title()))
    if wildmsg:
        listmsg = _(' **Here\'s the current wild reports for {channel}**\n{wildmsg}').format(channel=ctx.message.channel.name.capitalize(),wildmsg=wildmsg)
    else:
        listmsg = _(" There are no reported wild pokemon. Report one with **!wild <pokemon> <location>**")
    return listmsg



def record_reported_by(guild_id, author_id, report_type):

    leaderboard_list = ['lifetime']
    addtional_leaderboard = get_guild_local_leaderboard(guild_id)
    if addtional_leaderboard :
        leaderboard_list.append(addtional_leaderboard)

    for leaderboard in leaderboard_list:
        existing_reports = guild_dict[guild_id].setdefault('trainers', {}).setdefault(author_id, {}).setdefault(leaderboard, {}).setdefault(report_type, 0) + 1
        guild_dict[guild_id]['trainers'][author_id][leaderboard][report_type] = existing_reports


def record_error_reported_by(guild_id, author_id, report_type):

    leaderboard_list = ['lifetime']
    addtional_leaderboard = get_guild_local_leaderboard(guild_id)
    if addtional_leaderboard :
        leaderboard_list.append(addtional_leaderboard)

    for leaderboard in leaderboard_list:
        existing_reports = guild_dict[guild_id].setdefault('trainers', {}).setdefault(author_id, {}).setdefault(leaderboard, {}).setdefault(report_type, 0) - 1
        guild_dict[guild_id]['trainers'][author_id][leaderboard][report_type] = existing_reports


try:
    event_loop.run_until_complete(Clembot.start(config['bot_token']))
except discord.LoginFailure:
    logger.critical("Invalid token")
    event_loop.run_until_complete(Clembot.logout())
    Clembot._shutdown_mode = 0
except KeyboardInterrupt:
    logger.info("Keyboard interrupt detected. Quitting...")
    event_loop.run_until_complete(Clembot.logout())
    Clembot._shutdown_mode = 0
except Exception as e:
    logger.critical("Fatal exception", exc_info=e)
    event_loop.run_until_complete(Clembot.logout())
finally:
    pass

sys.exit(Clembot._shutdown_mode)


