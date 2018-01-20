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
from time import strftime

from discord.colour import Colour

from logs import init_loggers
import discord
from discord.ext import commands
import spelling
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
import pytesseract
import requests
from io import BytesIO
import checks
import hastebin
from operator import itemgetter
from errors import custom_error_handling

# --B--
# ---- dependencies
import gymutil
import time
from datetime import timedelta
import calendar
import copy
from random import *
import pytz
from pytz import timezone
import jsonpickle


tessdata_dir_config = "--tessdata-dir 'C:\\Program Files (x86)\\Tesseract-OCR\\tessdata' "
xtraconfig = "-l eng -c tessedit_char_blacklist=&|=+%#^*[]{};<> -psm 6"

if os.name == 'nt':
    tesseract_config = tessdata_dir_config + xtraconfig
else:
    tesseract_config = xtraconfig

logger = init_loggers()


def _get_prefix(bot, message):
    server = message.server
    try:
        set_prefix = bot.server_dict[server.id]["prefix"]
    except KeyError:
        set_prefix = None
    default_prefix = bot.config["default_prefix"]
    return set_prefix or default_prefix


Clembot = commands.Bot(command_prefix=_get_prefix)
Clembot.remove_command("help")
custom_error_handling(Clembot, logger)

try:
    with open(os.path.join('data', 'serverdict'), "rb") as fd:
        Clembot.server_dict = pickle.load(fd)
    logger.info("Serverdict Loaded Successfully")
except OSError:
    logger.info("Serverdict Not Found - Looking for Backup")
    try:
        with open(os.path.join('data', 'serverdict_backup'), "rb") as fd:
            Clembot.server_dict = pickle.load(fd)
        logger.info("Serverdict Backup Loaded Successfully")
    except OSError:
        logger.info("Serverdict Backup Not Found - Creating New Serverdict")
        Clembot.server_dict = {}
        with open(os.path.join('data', 'serverdict'), "wb") as fd:
            pickle.dump(Clembot.server_dict, fd, -1)
        logger.info("Serverdict Created")

server_dict = Clembot.server_dict




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
    gymutil.load_gyms()


load_config()

Clembot.config = config



poke_alarm_image_url = "/icons/{0}.png?width=80&height=80"
floatzel_image_url = "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png"
"""

======================

Helper functions

======================

"""


# --B--


def clembot_time_in_server_timezone(message):
    server_offset = server_dict[message.channel.server.id]['offset']
    clembot_offset = -8

    return time.time() + 3600 * (server_offset - clembot_offset)


def get_pokemon_image_url(pokedex_number):
    # url = icon_list.get(str(pokedex_number))
    url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/pkmn/{0}_.png?cache=0".format(str(pokedex_number).zfill(3))
    if url:
        return url
    else:
        return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=pokedex_number)

def get_egg_image_url(egg_level):
    # url = icon_list.get(str(pokedex_number))
    url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/eggs/{0}.png?cache=0".format(str(egg_level))
    if url:
        return url
    else:
        return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=egg_level)



def _set_prefix(bot, server, prefix):
    bot.server_dict[server.id]["prefix"] = prefix


def get_city_list(message):
    city_list = []
    try:
        city_channel = server_dict[message.server.id]['city_channels'].get(message.channel.name)

        if city_channel:
            city_list.append(city_channel.replace(" ", "").upper())
            return city_list

        for key in server_dict[message.server.id]['city_channels'].keys():
            city_name = server_dict[message.server.id]['city_channels'].get(key)
            city_key = city_name.replace(" ", "").upper()
            if city_list.__contains__(city_key):
                pass
            else:
                city_list.append(city_key)

    except Exception as error:
        print(error)

    return city_list


# @Clembot.command(pass_context=True, hidden=True)
# async def test(ctx):
#     await Clembot.send_message(ctx.message.channel,content=get_city_list(ctx))



# Given a Pokemon name, return a list of its
# weaknesses as defined in the type chart
def get_type(server, pkmn_number):
    pkmn_number = int(pkmn_number) - 1
    types = type_list[pkmn_number]
    ret = []
    for type in types:
        ret.append(parse_emoji(server, config['type_id_dict'][type.lower()]))
    return ret


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
def weakness_to_str(server, weak_list):
    ret = ""
    for weakness in weak_list:
        # Handle an "x2" postfix defining a double weakness
        x2 = ""
        if weakness[-2:] == "x2":
            weakness = weakness[:-2]
            x2 = "x2"

        # Append to string
        ret += parse_emoji(server, config['type_id_dict'][weakness]) + x2 + " "

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
# and <emoji_name> is in the server's emoji list, then
# return the string <:emoji name:emoji id>. Otherwise,
# just return the string unmodified.
def parse_emoji(server, emoji_string):
    if emoji_string[0] == ':' and emoji_string[-1] == ':':
        emoji = discord.utils.get(server.emojis, name=emoji_string.strip(':'))
        if emoji:
            emoji_string = "<:{0}:{1}>".format(emoji.name, emoji.id)
        else:
            emoji_string = "{0}".format(emoji_string.strip(':').capitalize())

    return emoji_string


def print_emoji_name(server, emoji_string):
    # By default, just print the emoji_string
    ret = "`" + emoji_string + "`"

    emoji = parse_emoji(server, emoji_string)
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
    key = "AIzaSyCoS20_EWol8TgnAiTk1417ybvUIRoEIQw"
    gmap_base_url = "https://maps.googleapis.com/maps/api/staticmap?center={0}&markers=color:red%7C{1}&maptype=roadmap&size=250x125&zoom=15&key={2}".format(lat_long, lat_long, key)

    return gmap_base_url

# fix for links for general location add
def fetch_gmap_link(gym_code, channel):
    try:
        details_list = gym_code.split()
        report_channel = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['reportcity']
        city_channel = server_dict[channel.server.id]['city_channels'][report_channel]
        loc_list = city_channel.split()
        return "https://www.google.com/maps/search/?api=1&query={0}+{1}".format('+'.join(details_list), '+'.join(loc_list))
    except Exception as error:
        return "https://www.google.com/maps/search/?api=1&query={0}+{1}"


# Given an arbitrary string, create a Google Maps
# query using the configured hints
def create_gmaps_query(details, channel):
    details_list = details.split()
    loc_list = server_dict[channel.server.id]['city_channels'][channel.name].split()
    return "https://www.google.com/maps/search/?api=1&query={0}+{1}".format('+'.join(details_list), '+'.join(loc_list))

def get_raid_channel_dict(message):
    raid_channel_dict = server_dict[message.server.id]['raidchannel_dict']
    if message.channel.id in raid_channel_dict:
        return raid_channel_dict[message.channel.id]
    else:
        return None


# Given a User, check that it is Clembot's master
def check_master(user):
    return str(user) == config['master']


def check_server_owner(user, server):
    return str(user) == str(server.owner)


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


async def expiry_check(channel):
    logger.info("Expiry_Check - "+channel.name)
    server = channel.server
    global active_raids
    if channel not in active_raids:
        active_raids.append(channel)
        logger.info("Expire_Channel - Channel Added To Watchlist - " + channel.name)
        await asyncio.sleep(0.5)  # wait for assume
        while True:
            try:
                if server_dict[server.id]['raidchannel_dict'][channel.id]['active'] is True:
                    if server_dict[server.id]['raidchannel_dict'][channel.id]['exp'] is not None:
                        # print("{channel} => {expiry} vs {current}".format(channel=channel.name,expiry=server_dict[server.id]['raidchannel_dict'][channel.id]['exp'],current=fetch_current_time(channel.server.id)))

                        if server_dict[server.id]['raidchannel_dict'][channel.id]['exp'] <= fetch_current_time(channel.server.id):
                            if server_dict[server.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
                                pokemon = server_dict[server.id]['raidchannel_dict'][channel.id]['pokemon']
                                if pokemon:
                                    logger.info("Expire_Channel - Egg Auto Hatched - "+channel.name)
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
    server = channel.server
    alreadyexpired = False
    #print("Expire_Channel - " + channel.name)
    logger.info("Expire_Channel - " + channel.name)
    # If the channel exists, get ready to delete it.
    # Otherwise, just clean up the dict since someone
    # else deleted the actual channel at some point.

    channel_exists = Clembot.get_channel(channel.id)
    if channel_exists is None and Clembot.is_logged_in and not Clembot.is_closed:
        try:
            del server_dict[channel.server.id]['raidchannel_dict'][channel.id]
        except KeyError:
            pass
        return
    else:
        dupechannel = False
        if server_dict[server.id]['raidchannel_dict'][channel.id]['active'] == False:
            alreadyexpired = True
        else:
            server_dict[server.id]['raidchannel_dict'][channel.id]['active'] = False
        logger.info("Expire_Channel - Channel Expired - " + channel.name)
        try:
            testvar = server_dict[server.id]['raidchannel_dict'][channel.id]['duplicate']
        except KeyError:
            server_dict[server.id]['raidchannel_dict'][channel.id]['duplicate'] = 0
        if server_dict[server.id]['raidchannel_dict'][channel.id]['duplicate'] >= 3:
            dupechannel = True
            server_dict[server.id]['raidchannel_dict'][channel.id]['duplicate'] = 0
            server_dict[server.id]['raidchannel_dict'][channel.id]['exp'] = fetch_current_time(channel.server.id)
            if not alreadyexpired:
                await Clembot.send_message(channel, _("""This channel has been successfully reported as a duplicate and will be deleted in 1 minute. Check the channel list for the other raid channel to coordinate in!
If this was in error, reset the raid with **!timerset**"""))
            delete_time = convert_to_epoch(fetch_channel_expire_time(channel.id)) + timedelta(minutes=1).seconds - convert_to_epoch(fetch_current_time(channel.server.id))
        elif server_dict[server.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
            if not alreadyexpired:
                maybe_list = []
                trainer_dict = copy.deepcopy(server_dict[channel.server.id]['raidchannel_dict'][channel.id]['trainer_dict'])
                for trainer in trainer_dict.keys():
                    if trainer_dict[trainer]['status'] == 'maybe':
                        user = await Clembot.get_user_info(trainer)
                        maybe_list.append(user.mention)
                await Clembot.send_message(channel, _("""**This egg has hatched!**\n\n...or the time has just expired. Trainers {trainer_list}: Update the raid to the pokemon that hatched using **!raid <pokemon>** or reset the hatch timer with **!timerset**. This channel will be deactivated until I get an update and I'll delete it in 15 minutes if I don't hear anything.""").format(trainer_list=", ".join(maybe_list)))
            delete_time = convert_to_epoch(fetch_channel_expire_time(channel.id)) + timedelta(minutes=15).seconds - convert_to_epoch(fetch_current_time(channel.server.id))
            expiremsg = _("**This level {level} raid egg has expired!**").format(level=server_dict[channel.server.id]['raidchannel_dict'][channel.id]['egglevel'])
        else:
            if not alreadyexpired:
                await Clembot.send_message(channel, _("""This channel timer has expired! The channel has been deactivated and will be deleted in 5 minutes.
To reactivate the channel, use **!timerset** to set the timer again."""))
            delete_time = convert_to_epoch(fetch_channel_expire_time(channel.id)) + timedelta(minutes=5).seconds - convert_to_epoch(fetch_current_time(channel.server.id))
            expiremsg = _("**This {pokemon} raid has expired!**").format(pokemon=server_dict[channel.server.id]['raidchannel_dict'][channel.id]['pokemon'].capitalize())
        if delete_time:
            await asyncio.sleep(delete_time)
        # If the channel has already been deleted from the dict, someone
        # else got to it before us, so don't do anything.
        # Also, if the channel got reactivated, don't do anything either.

        try:
            if server_dict[channel.server.id]['raidchannel_dict'][channel.id]['active'] == False and Clembot.is_logged_in and not Clembot.is_closed:
                if dupechannel:
                    try:
                        report_channel = discord.utils.get(channel.server.channels, name = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['reportcity'])
                        reportmsg = await Clembot.get_message(report_channel, server_dict[channel.server.id]['raidchannel_dict'][channel.id]['raidreport'])
                        await Clembot.delete_message(reportmsg)
                    except:
                        pass
                else:
                    try:
                        report_channel = discord.utils.get(channel.server.channels, name = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['reportcity'])
                        reportmsg = await Clembot.get_message(report_channel, server_dict[channel.server.id]['raidchannel_dict'][channel.id]['raidreport'])
                        await Clembot.edit_message(reportmsg, embed=discord.Embed(description=expiremsg,colour=channel.server.me.colour))
                    except:
                        pass
                try:
                    del server_dict[channel.server.id]['raidchannel_dict'][channel.id]
                except KeyError:
                    pass
                    # channel doesn't exist anymore in serverdict
                channel_exists = Clembot.get_channel(channel.id)
                if channel_exists is None:
                    return
                else:
                    await Clembot.delete_channel(channel_exists)
                    logger.info("Expire_Channel - Channel Deleted - " + channel.name)
        except:
            pass


async def channel_cleanup(loop=True):
    while Clembot.is_logged_in and not Clembot.is_closed:
        global active_raids
        serverdict_chtemp = copy.deepcopy(server_dict)
        logger.info("Channel_Cleanup ------ BEGIN ------")

        #for every server in save data
        for serverid in serverdict_chtemp.keys():
            server = Clembot.get_server(serverid)
            log_str = "Channel_Cleanup - Server: " + server.name
            logger.info(log_str + " - BEGIN CHECKING SERVER")

            # clear channel lists
            dict_channel_delete = []
            discord_channel_delete = []

            add_contest_to_server_dict(serverid)
            for channelid in serverdict_chtemp[serverid]['contest_channel']:
                try:
                    channel = Clembot.get_channel(channelid)
                    if channel is None:
                        del server_dict[serverid]['contest_channel'][channelid]
                        # logger.info("Channel_Cleanup - Server: " + server.name + ": Channel:" + channel.name + " CLEANED UP DICT - DOESN'T EXIST IN DISCORD")
                except Exception as error:
                    continue
            #check every raid channel data for each server
            for channelid in serverdict_chtemp[serverid]['raidchannel_dict']:
                channel = Clembot.get_channel(channelid)
                if channel is None:
                    del server_dict[serverid]['raidchannel_dict'][channelid]
                    # logger.info( "Channel_Cleanup - Server: " + server.name + ": Channel:" + channelid + " CLEANED UP DICT - DOESN'T EXIST IN DISCORD")
                    continue
                log_str = "Channel_Cleanup - Server: "+server.name
                log_str = log_str+": Channel:"+channel.name
                logger.info(log_str+" - CHECKING")

                channelmatch = Clembot.get_channel(channel.id)

                if channelmatch is None:
                    # list channel for deletion from save data
                    dict_channel_delete.append(channel)
                    logger.info(log_str + " - DOESN'T EXIST IN DISCORD")
                # otherwise, if clembot can still see the channel in discord
                else:
                    logger.info(log_str+" - EXISTS IN DISCORD")
                    #if the channel save data shows it's not an active raid
                    if serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['active'] == False:

                        if serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['type'] == 'egg':

                            # and if it has been expired for longer than 15 minutes already
                            if serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['exp'] < fetch_current_time(channel.server.id) - timedelta(minutes=15):
                                # list the channel to be removed from save data
                                dict_channel_delete.append(channel)

                                # and list the channel to be deleted in discord
                                discord_channel_delete.append(channel)

                                logger.info(log_str + " - 15+ MIN EXPIRY NONACTIVE EGG")
                                continue

                        else:

                            # and if it has been expired for longer than 5 minutes already
                            if serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['exp'] < fetch_current_time(channel.server.id) - timedelta(minutes=5):
                                # list the channel to be removed from save data
                                dict_channel_delete.append(channel)

                                # and list the channel to be deleted in discord
                                discord_channel_delete.append(channel)

                                logger.info(log_str + " - 5+ MIN EXPIRY NONACTIVE RAID")
                                continue

                        event_loop.create_task(expire_channel(channel))
                        logger.info(log_str + " - = RECENTLY EXPIRED NONACTIVE RAID")
                        continue

                    # if the channel save data shows it as an active raid still
                    elif serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['active'] == True:

                        # if it's an exraid
                        if serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['type'] == 'exraid':

                            logger.info(log_str + " - EXRAID")
                            continue

                        # and if it has been expired for longer than 5 minutes already
                        elif serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['exp'] and serverdict_chtemp[server.id]['raidchannel_dict'][channel.id]['exp'] < fetch_current_time(channel.server.id) - timedelta(minutes=5):

                            # list the channel to be removed from save data
                            dict_channel_delete.append(channel)

                            # and list the channel to be deleted in discord
                            discord_channel_delete.append(channel)

                            logger.info(log_str + " - 5+ MIN EXPIRY ACTIVE")
                            continue

                        # or if the expiry time for the channel has already passed within 5 minutes
                        elif serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['exp'] and serverdict_chtemp[serverid]['raidchannel_dict'][channelid]['exp'] <= fetch_current_time(channel.server.id):
                            # list the channel to be sent to the channel expiry function
                            event_loop.create_task(expire_channel(channel))

                            logger.info(log_str + " - RECENTLY EXPIRED")
                            continue

                        else:
                            # if channel is still active, make sure it's expiry is being monitored
                            if channel not in active_raids:
                                event_loop.create_task(expiry_check(channel))
                                logger.info(log_str + " - MISSING FROM EXPIRY CHECK")
                                continue

            # for every channel listed to have save data deleted
            for c in dict_channel_delete:
                try:
                    #attempt to delete the channel from save data
                    del server_dict[serverid]['raidchannel_dict'][c.id]
                    logger.info("Channel_Cleanup - Channel Savedata Cleared - " + c.name)
                except KeyError:
                    pass

                try:
                    # delete channel if it still exists in discord
                    await Clembot.delete_channel(c)
                    logger.info("Channel_Cleanup - Channel Deleted - " + c.name)
                except:
                    logger.info("Channel_Cleanup - Channel Deletion Failure - " + c.name)
                    pass

            # for every channel listed to have the discord channel deleted
            for c in discord_channel_delete:
                try:
                    # delete channel from discord
                    await Clembot.delete_channel(c)
                    logger.info("Channel_Cleanup - Channel Deleted - " + c.name)
                except:
                    logger.info("Channel_Cleanup - Channel Deletion Failure - " + c.name)
                    pass

        # save server_dict changes after cleanup
        logger.info("Channel_Cleanup - SAVING CHANGES")
        try:
            await _save()
        except Exception as err:
            logger.info("Channel_Cleanup - SAVING FAILED" + err)
        logger.info("Channel_Cleanup ------ END ------")

        await asyncio.sleep(600)  # 600 default
        continue

@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def cleanup():
    await channel_cleanup()

async def server_cleanup(loop=True):
    while Clembot.is_logged_in and not Clembot.is_closed:
        serverdict_srvtemp = copy.deepcopy(server_dict)
        logger.info("Server_Cleanup ------ BEGIN ------")

        serverdict_srvtemp = server_dict
        dict_server_list = []
        bot_server_list = []
        dict_server_delete = []

        for serverid in serverdict_srvtemp.keys():
            server = Clembot.get_server(serverid)
            dict_server_list.append(server)
        for server in Clembot.servers:
            bot_server_list.append(server)
        server_diff = set(dict_server_list) - set(bot_server_list)
        for s in server_diff:
            dict_server_delete.append(s)

        for s in dict_server_delete:
            try:
                del server_dict[s]
                logger.info("Server_Cleanup - Cleared "+s.name+" from save data")
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
            await Clembot.send_message(owner, message)
    #print(message)
    logger.info(message)


async def maint_start():
    try:
        event_loop.create_task(server_cleanup())
        event_loop.create_task(channel_cleanup())
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
    servers = len(Clembot.servers)
    users = 0
    for server in Clembot.servers:
        users += len(server.members)
        try:
            if server.id not in server_dict:
                server_dict[server.id] = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict' : {}}
        except KeyError:
            server_dict[server.id] = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict': {}}

        owners.append(server.owner)

    embed = discord.Embed(colour=discord.Colour.green(), description="Beep Beep! That's right!").set_author(name=_("Clembot Startup Notification"), icon_url=Clembot.user.avatar_url)
    embed.add_field(name="**Servers Connected**", value=_(" {servers}").format(servers=servers), inline=True)
    embed.add_field(name="**Members Found**", value=_(" {members}").format(members=users), inline=True)
    await Clembot.send_message(Clembot.owner, embed=embed)


    await maint_start()


@Clembot.event
async def on_server_join(server):
    owner = server.owner
    server_dict[server.id] = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict': {}}
    await Clembot.send_message(owner, _("Beep Beep! I'm Clembot, a Discord helper bot for Pokemon Go communities, and someone has invited me to your server! Type **!help** to see a list of things I can do, and type **!configure** in any channel of your server to begin!"))


@Clembot.event
async def on_server_remove(server):
    try:
        if server.id in server_dict:
            try:
                del server_dict[server.id]
            except KeyError:
                pass
    except KeyError:
        pass


@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_server=True)
async def configure(ctx):
    server = ctx.message.server
    owner = ctx.message.author
    server_dict_check = {'want_channel_list': [], 'offset': 0, 'welcome': False, 'welcomechan': '', 'wantset': False, 'raidset': False, 'wildset': False, 'team': False, 'want': False, 'other': False, 'done': False, 'raidchannel_dict': {}}
    server_dict_temp = copy.deepcopy(server_dict[server.id])
    firstconfig = False
    configcancel = False
    if server_dict_check == server_dict_temp:
        firstconfig = True
    try:
        if server_dict_temp['other']:
            pass
        else:
            pass
    except KeyError:
        server_dict_temp['other']=False
    try:
        if server_dict_temp['want_channel_list']:
            pass
        else:
            pass
    except KeyError:
        server_dict_temp['want_channel_list'] = []
    configmessage = "Beep Beep! That's Right! Welcome to the configuration for Clembot the Pokemon Go Helper Bot! I will be guiding you through some setup steps to get me setup on your server.\n\n**Role Setup**\nBefore you begin the configuration, please make sure my role is moved to the top end of the server role hierarchy. It can be under admins and mods, but must be above team ands general roles. [Here is an example](http://i.imgur.com/c5eaX1u.png)"
    if firstconfig == False:
        if server_dict_temp['other']:
            configreplylist = ['all','team','welcome','main','regions','raid','wild','want','timezone','allmain']
            configmessage += """\n\n**Welcome Back**\nThis isn't your first time configurating. You can either reconfigure everything by replying with **all** or reply with one of the following to configure that specific setting:\n\n**all** - To redo configuration\n**team** - For Team Assignment configuration\n**welcome** - For Welcome Message configuration\n**main** - For main command configuration\n**raid** - for raid command configuration\n**wild** - for wild command configuration\n**regions** - For configuration of reporting channels or map links\n**want** - for want/unwant command configuration and channel\n**timezone** - For timezone configuration\n**allmain** - For main, regions, raid, wild, want, timezone configuration"""
            configmessage += "\n\nReply with **cancel** at any time throughout the questions to cancel the configure process."
            await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=configmessage).set_author(name=_("Clembot Configuration - {0}").format(server), icon_url=Clembot.user.avatar_url))
        else:
            configreplylist = ['all', 'team', 'welcome', 'main', 'allmain']
            configmessage += """\n\n**Welcome Back**\nThis isn't your first time configurating. You can either reconfigure everything by replying with **all** or reply with one of the following to configure that specific setting:\n\n**all** - To redo configuration\n**team** - For Team Assignment configuration\n**welcome** - For Welcome Message configuration\n**main** - For main command configuration\n**allmain** - For main, regions, raid, wild, want, timezone configuration"""
            configmessage += "\n\nReply with **cancel** at any time throughout the questions to cancel the configure process."
            await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=configmessage).set_author(name=_("Clembot Configuration - {0}").format(server), icon_url=Clembot.user.avatar_url))
        while True:
            configreply = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if configreply.content.lower() in configreplylist:
                configgoto = configreply.content.lower()
                break
            elif configreply.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            elif configreply.content.lower() not in configreplylist:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with one of the choices above."))
                continue
    elif firstconfig == True:
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=configmessage).set_author(name=_("Clembot Configuration - {0}").format(server), icon_url=Clembot.user.avatar_url))
    # configure team
    if configcancel == False and (firstconfig == True or configgoto == "all" or configgoto == "team"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="""Team assignment allows users to assign their Pokemon Go team role using the **!team** command. If you have a bot that handles this already, you may want to disable this feature.\n\nIf you are to use this feature, ensure existing team roles are as follows: mystic, valor, instinct. These must be all lowercase letters. If they don't exist yet, I'll make some for you instead.\n\nRespond with: **N** to disable, **Y** to enable:""").set_author(name="Team Assignments", icon_url=Clembot.user.avatar_url))
        while True:
            teamreply = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if teamreply.content.lower() == "y":
                server_dict_temp['team'] = True
                for team in config['team_dict'].keys():
                    temp_role = discord.utils.get(server.roles, name=team)
                    if temp_role == None:
                        await Clembot.create_role(server=server, name=team, hoist=False, mentionable=True)
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Team Assignments enabled!"))
                break
            elif teamreply.content.lower() == "n":
                server_dict_temp['team'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Team Assignments disabled!"))
                break
            elif teamreply.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure welcome
    if configcancel == False and (firstconfig == True or configgoto == "all" or configgoto == "welcome"):
        welcomeconfig = "I can welcome new members to the server with a short message. Here is an example:\n\n"
        if server_dict_temp['team'] == True:
            welcomeconfig += _("Beep Beep! Welcome to {server_name}, {owner_name.mention}! Set your team by typing '**!team mystic**' or '**!team valor**' or '**!team instinct**' without quotations. If you have any questions just ask an admin.").format(server_name=server.name, owner_name=owner)
        else:
            welcomeconfig += _("Beep Beep! Welcome to {server_name}, {owner_name.mention}! If you have any questions just ask an admin.").format(server_name=server, owner_name=owner)
        welcomeconfig += "\n\nThis welcome message can be in a specific channel or a direct message. If you have a bot that handles this already, you may want to disable this feature.\n\nRespond with: **N** to disable, **Y** to enable:"
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=welcomeconfig).set_author(name="Welcome Message", icon_url=Clembot.user.avatar_url))
        while True:
            welcomereply = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if welcomereply.content.lower() == "y":
                server_dict_temp['welcome'] = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Welcome Message enabled!"))
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Which channel in your server would you like me to post the Welcome Messages? You can also choose to have them sent to the new member via Direct Message (DM) instead.\n\nRespond with: **channel-name** of a channel in your server or **DM** to Direct Message:").set_author(name="Welcome Message Channel", icon_url=Clembot.user.avatar_url))
                wchcheck = 0
                while True:
                    welcomechannelreply = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
                    if welcomechannelreply.content.lower() == "dm":
                        server_dict_temp['welcomechan'] = "dm"
                        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Welcome DM set"))
                        break
                    elif " " in welcomechannelreply.content.lower():
                        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Channel names can't contain spaces, sorry. Please double check the name and send your response again."))
                        continue
                    elif welcomechannelreply.content.lower() == "cancel":
                        configcancel = True
                        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                        return
                    else:
                        server_channel_list = []
                        for channel in server.channels:
                            server_channel_list.append(channel.name)
                        diff = set([welcomechannelreply.content.lower().strip()]) - set(server_channel_list)
                        if not diff:
                            server_dict_temp['welcomechan'] = welcomechannelreply.content.lower()
                            await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Welcome Channel set"))
                            break
                        else:
                            await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="The channel you provided isn't in your server. Please double check your channel name and resend your response."))
                            continue
                    break
                break
            elif welcomereply.content.lower() == "n":
                server_dict_temp['welcome'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Welcome Message disabled!"))
                break
            elif welcomereply.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main
    if configcancel == False and (firstconfig == True or configgoto == "all" or configgoto == "main" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Main Functions include:\n - **!want** and creating tracked Pokemon roles \n - **!wild** Pokemon reports\n - **!raid** reports and channel creation for raid management.\nIf you don't want __any__ of the Pokemon tracking or Raid management features, you may want to disable them.\n\nRespond with: **N** to disable, or **Y** to enable:").set_author(name="Main Functions", icon_url=Clembot.user.avatar_url))
        while True:
            otherreply = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if otherreply.content.lower() == "y":
                server_dict_temp['other'] = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Main Functions enabled"))
                break
            elif otherreply.content.lower() == "n":
                server_dict_temp['other'] = False
                server_dict_temp['raidset'] = False
                server_dict_temp['wildset'] = False
                server_dict_temp['wantset'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Main Functions disabled"))
                break
            elif otherreply.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main-raid
    if configcancel == False and server_dict_temp['other'] is True and (firstconfig == True or configgoto == "all" or configgoto == "raid" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Do you want **!raid** reports enabled? If you want __only__ the **!wild** feature for reports, you may want to disable this.\n\nRespond with: **N** to disable, or **Y** to enable:").set_author(name="Raid Reports", icon_url=Clembot.user.avatar_url))
        while True:
            raidconfigset = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if raidconfigset.content.lower() == "y":
                server_dict_temp['raidset'] = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Raid Reports enabled"))
                break
            elif raidconfigset.content.lower() == "n":
                server_dict_temp['raidset'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Raid Reports disabled"))
                break
            elif raidconfigset.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main-wild
    if configcancel == False and server_dict_temp['other'] is True and (firstconfig == True or configgoto == "all" or configgoto == "wild" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Do you want **!wild** reports enabled? If you want __only__ the **!raid** feature for reports, you may want to disable this.\n\nRespond with: **N** to disable, or **Y** to enable:").set_author(name="Wild Reports", icon_url=Clembot.user.avatar_url))
        while True:
            wildconfigset = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if wildconfigset.content.lower() == "y":
                server_dict_temp['wildset'] = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Wild Reports enabled"))
                break
            elif wildconfigset.content.lower() == "n":
                server_dict_temp['wildset'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Wild Reports disabled"))
                break
            elif wildconfigset.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **N** to disable, or **Y** to enable."))
                continue
    # configure main-channels
    if configcancel == False and server_dict_temp['other'] is True and (server_dict_temp['wildset'] is True or server_dict_temp['raidset'] is True) and (firstconfig == True or configgoto == "all" or configgoto == "regions" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Pokemon raid or wild reports are contained within one or more channels. Each channel will be able to represent different areas/communities. I'll need you to provide a list of channels in your server you will allow reports from in this format: `channel-name, channel-name, channel-name`\n\nIf you do not require raid and wild reporting, you may want to disable this function.\n\nRespond with: **N** to disable, or the **channel-name** list to enable, each seperated with a comma and space:").set_author(name="Reporting Channels", icon_url=Clembot.user.avatar_url))
        citychannel_dict = {}
        while True:
            citychannels = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if citychannels.content.lower() == "n":
                server_dict_temp['wildset'] = False
                server_dict_temp['raidset'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Reporting Channels disabled"))
                break
            elif citychannels.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                citychannel_list = citychannels.content.lower().split(', ')
                server_channel_list = []
                for channel in server.channels:
                    server_channel_list.append(channel.name)
                diff = set(citychannel_list) - set(server_channel_list)
                if not diff:
                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Reporting Channels enabled"))
                    break
                else:
                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The channel list you provided doesn't match with your servers channels.\n\nThe following aren't in your server: {invalid_channels}\n\nPlease double check your channel list and resend your reponse.").format(invalid_channels=", ".join(diff))))
                    continue
    # configure main-locations
    if configcancel == False and server_dict_temp['other'] is True and (server_dict_temp['wildset'] is True or server_dict_temp['raidset'] is True) and (firstconfig == True or configgoto == "all" or configgoto == "regions" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="""For each report, I generate Google Maps links to give people directions to raids and spawns! To do this, I need to know which suburb/town/region each report channel represents, to ensure we get the right location in the map. For each report channel you provided, I will need it's corresponding general location using only letters and spaces, with each location seperated by a comma and space.\n\nExample: `kansas city mo, hull uk, sydney nsw australia`\n\nEach location will have to be in the same order as you provided the channels in the previous question.\n\nRespond with: **location info, location info, location info** each matching the order of the previous channel list:""").set_author(name="Report Locations", icon_url=Clembot.user.avatar_url))
        while True:
            cities = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if cities.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            city_list = cities.content.split(', ')
            if len(city_list) == len(citychannel_list):
                for i in range(len(citychannel_list)):
                    citychannel_dict[citychannel_list[i]] = city_list[i]
                break
            else:
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The number of cities don't match the number of channels you gave me earlier!\n\nI'll show you the two lists to compare:\n\n{channellist}\n{citylist}\n\nPlease double check that your locations match up with your provided channels and resend your response.").format(channellist=(", ".join(citychannel_list)), citylist=(", ".join(city_list)))))
                continue
        server_dict_temp['city_channels'] = citychannel_dict
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Report Locations are set"))
    # configure main-want
    if configcancel == False and server_dict_temp['other'] is True and (firstconfig == True or configgoto == "all" or configgoto == "want" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="""The **!want** and **!unwant** commands let you add or remove roles for Pokemon that will be mentioned in reports. This let you get notifications on the Pokemon you want to track. I just need to know what channels you want to allow people to manage their pokemon with the **!want** and **!unwant** command. If you pick a channel that doesn't exist, I'll make it for you.\n\nIf you don't ant to allow the management of tracked Pokemon roles, then you may want to disable this feature.\n\nRepond with: **N** to disable, or the **channel-name** list to enable, each seperated by a comma and space.""").set_author(name="Pokemon Notifications", icon_url=Clembot.user.avatar_url))
        while True:
            wantchs = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if wantchs.content.lower() == "n":
                server_dict_temp['wantset'] = False
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="Pokemon Notifications disabled"))
                break
            elif wantchs.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                want_list = wantchs.content.lower().split(', ')
                server_channel_list = []
                for channel in server.channels:
                    server_channel_list.append(channel.name)
                diff = set(want_list) - set(server_channel_list)
                if not diff:
                    server_dict_temp['wantset'] = True
                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Pokemon Notifications enabled"))
                    while True:
                        try:
                            for want_channel_name in want_list:
                                want_channel = discord.utils.get(server.channels, name=want_channel_name)
                                if want_channel == None:
                                    want_channel = await Clembot.create_channel(server, want_channel_name)
                                if want_channel.id not in server_dict_temp['want_channel_list']:
                                    server_dict_temp['want_channel_list'].append(want_channel.id)
                            break
                        except:
                            await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("Beep Beep! You didn't give me enough permissions to create channels! Please check my permissions and that my role is above general roles. Let me know if you'd like me to check again.\n\nRespond with: **Y** to try again, or **N** to skip and create the missing channels yourself.")))
                            while True:
                                wantpermswait = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
                                if wantpermswait.content.lower() == "n":
                                    break
                                elif wantpermswait.content.lower() == "y":
                                    break
                                elif wantpermswait.content.lower() == "cancel":
                                    configcancel = True
                                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                                    return
                                else:
                                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I'm sorry I don't understand. Please reply with either **Y** to try again, or **N** to skip and create the missing channels yourself."))
                                    continue
                            if wantpermswait.content.lower() == "y":
                                continue
                            break
                else:
                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("The channel list you provided doesn't match with your servers channels.\n\nThe following aren't in your server:{invalid_channels}\n\nPlease double check your channel list and resend your reponse.").format(invalid_channels=", ".join(diff))))
                    continue
                break
    # configure main-timezone
    if configcancel == False and server_dict_temp['other'] is True and server_dict_temp['raidset'] is True and (firstconfig == True or configgoto == "all" or configgoto == "timezone" or configgoto == "allmain"):
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description=_("To help coordinate raids reports for you, I need to know what timezone you're in! The current 24-hr time UTC is {utctime}. How many hours off from that are you?\n\nRespond with: A number from **-12** to **12**:").format(utctime=strftime("%H:%M", time.gmtime()))).set_author(name="Timezone Configuration", icon_url=Clembot.user.avatar_url))
        while True:
            offsetmsg = await Clembot.wait_for_message(author=owner, check=lambda message: message.server is None)
            if offsetmsg.content.lower() == "cancel":
                configcancel = True
                await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.red(), description="**CONFIG CANCELLED!**\n\nNo changes have been made."))
                return
            else:
                try:
                    offset = float(offsetmsg.content)
                except ValueError:
                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I couldn't convert your answer to an appropriate timezone!.\n\nPlease double check what you sent me and resend a number strarting from **-12** to **12**."))
                    continue
                if not -12 <= offset <= 14:
                    await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="I couldn't convert your answer to an appropriate timezone!.\n\nPlease double check what you sent me and resend a number strarting from **-12** to **12**."))
                    continue
                else:
                    break
        server_dict_temp['offset'] = offset
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.green(), description="Timezone set"))
    server_dict_temp['done'] = True
    if configcancel == False:
        server_dict[server.id] = server_dict_temp
        await Clembot.send_message(owner, embed=discord.Embed(colour=discord.Colour.lighter_grey(), description="Beep Beep! Alright! Your settings have been saved and I'm ready to go! If you need to change any of these settings, just type **!configure** in your server again."))


@Clembot.event
async def on_member_join(member):
    """Welcome message to the server and some basic instructions."""
    server = member.server
    if server_dict[server.id]['done'] == False or server_dict[server.id]['welcome'] == False:
        return

    # Build welcome message

    admin_message = _(" If you have any questions just ask an admin.")

    welcomemessage = _("Beep Beep! Welcome to {server_name}, {new_member_name}! ")
    if server_dict[server.id]['team'] == True:
        welcomemessage += _("Set your team by typing {team_command}.").format(team_command=team_msg)
    welcomemessage += admin_message

    if server_dict[server.id]['welcomechan'] == "dm":
        await Clembot.send_message(member, welcomemessage.format(server_name=server.name, new_member_name=member.mention))

    else:
        default = discord.utils.get(server.channels, name=server_dict[server.id]['welcomechan'])
        if not default:
            pass
        else:
            await Clembot.send_message(default, welcomemessage.format(server_name=server.name, new_member_name=member.mention))


"""

Admin commands

"""


async def _save():
    with tempfile.NamedTemporaryFile('wb', dir=os.path.dirname(os.path.join('data', 'serverdict')), delete=False) as tf:
        pickle.dump(server_dict, tf, -1)
        tempname = tf.name
    try:
        os.remove(os.path.join('data', 'serverdict_backup'))
    except OSError as e:
        pass
    try:
        os.rename(os.path.join('data', 'serverdict'), os.path.join('data', 'serverdict_backup'))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
    os.rename(tempname, os.path.join('data', 'serverdict'))


@Clembot.command(pass_context=True)
@checks.is_owner()
async def reload_json(ctx):
    load_config()
    await Clembot.add_reaction(ctx.message, '?')


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

    await Clembot.send_message(ctx.message.channel, "Shutting down...")
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
    #     if bot_name.lower() != ctx.message.server.me.display_name.lower():
    #         return
    # else:
    #     return
    try:
        await _save()
    except Exception as err:
        await _print(Clembot.owner, _("Error occured while trying to save!"))
        await _print(Clembot.owner, err)

    await Clembot.send_message(ctx.message.channel, "Restarting...")
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
        logger.info("CONFIG SAVED")
    except Exception as err:
        await _print(Clembot.owner, _("Error occured while trying to save!"))
        await _print(Clembot.owner, err)


@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_server=True)
async def outputlog(ctx):
    """Get current Clembot log.

    Usage: !outputlog
    Output is a link to hastebin."""
    with open(os.path.join('logs', 'clembot.log'), 'r') as logfile:
        logdata = logfile.read()
    logdata = logdata.encode('ascii', errors='replace').decode('utf-8')
    await Clembot.send_message(ctx.message.channel, hastebin.post(logdata))


@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def welcome(ctx, user: discord.Member = None):
    """Test welcome on yourself or mentioned member.

    Usage: !welcome [@member]"""
    if not user:
        user = ctx.message.author
    await on_member_join(user)


@Clembot.group(pass_context=True, hidden=True, name="set")
@commands.has_permissions(manage_server=True)
async def _set(ctx):
    """Changes a setting."""
    if ctx.invoked_subcommand is None:
        pages = bot.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)


@_set.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_server=True)
async def prefix(ctx, prefix=None):
    """Changes server prefix."""
    if prefix == "clear":
        prefix = None

    _set_prefix(Clembot, ctx.message.server, prefix)

    if prefix is not None:
        await Clembot.send_message(ctx.message.channel, "Prefix has been set to: `{}`".format(prefix))
    else:
        default_prefix = Clembot.config["default_prefix"]
        await Clembot.send_message(ctx.message.channel, "Prefix has been reset to default: `{}`".format(default_prefix))


@Clembot.group(pass_context=True, hidden=True, name="get")
async def _get(ctx):
    """Get a setting value"""
    if ctx.invoked_subcommand is None:
        pages = bot.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            await bot.send_message(ctx.message.channel, page)


@_get.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_server=True)
async def prefix(ctx):
    """Get server prefix."""
    prefix = _get_prefix(Clembot, ctx.message)
    await Clembot.send_message(ctx.message.channel, "Prefix for this server is: `{}`".format(prefix))


@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_server=True)
async def announce(ctx, *, announce=None):
    """Repeats your message in an embed from Clembot.

    Usage: !announce [announcement]
    If the announcement isn't added at the same time as the command, Clembot will wait 3 minutes for a followup message containing the announcement."""
    message = ctx.message
    channel = message.channel
    server = message.server
    author = message.author
    if announce is None:
        announcewait = await Clembot.send_message(channel, "I'll wait for your announcement!")
        announcemsg = await Clembot.wait_for_message(author=ctx.message.author, timeout=180)
        await Clembot.delete_message(announcewait)
        if announcemsg is not None:
            announce = announcemsg.content
            await Clembot.delete_message(announcemsg)
        else:
            confirmation = await Clembot.send_message(channel, "Beep Beep! You took too long to send me your announcement! Retry when you're ready.")
    embeddraft = discord.Embed(colour=server.me.colour, description=announce)
    title = "Announcement"
    if Clembot.user.avatar_url:
        embeddraft.set_author(name=title, icon_url=Clembot.user.avatar_url)
    else:
        embeddraft.set_author(name=title)
    draft = await Clembot.send_message(channel, embed=embeddraft)

    def check(react, user):
        if user.id is not author.id:
            return False
        return True

    reaction_list = ['❔', '✅', '❎']
    owner_msg_add = ""
    if checks.is_owner_check(ctx):
        owner_msg_add = "🌎 to send it to all servers, "
        reaction_list.insert(0, '🌎')
    rusure = await Clembot.send_message(channel, _("That's what you sent, does it look good? React with {}❔ to send to another channel, ✅ to send it to this channel, or ❎ to cancel").format(owner_msg_add))
    for r in reaction_list:
        await asyncio.sleep(0.25)
        await Clembot.add_reaction(rusure, r)
    res = await Clembot.wait_for_reaction(reaction_list, message=rusure, check=check, timeout=60)
    if res is not None:
        await Clembot.delete_message(rusure)
        if res.reaction.emoji == "❎":
            confirmation = await Clembot.send_message(channel, _("Announcement Cancelled."))
            await Clembot.delete_message(draft)
        elif res.reaction.emoji == "✅":
            confirmation = await Clembot.send_message(channel, _("Announcement Sent."))
        elif res.reaction.emoji == "❔":
            channelwait = await Clembot.send_message(channel, "What channel would you like me to send it to?")
            channelmsg = await Clembot.wait_for_message(author=ctx.message.author, timeout=60)
            try:
                sendchannel = commands.ChannelConverter(ctx, str(channelmsg.content).strip()).convert()
            except commands.BadArgument:
                sendchannel = None
            if channelmsg is not None and sendchannel is not None:
                announcement = await Clembot.send_message(sendchannel, embed=embeddraft)
                confirmation = await Clembot.send_message(channel, _("Announcement Sent."))
            elif sendchannel is None:
                confirmation = await Clembot.send_message(channel, "Beep Beep! That channel doesn't exist! Retry when you're ready.")
            else:
                confirmation = await Clembot.send_message(channel, "Beep Beep! You took too long to send me your announcement! Retry when you're ready.")
            await Clembot.delete_message(channelwait)
            await Clembot.delete_message(channelmsg)
            await Clembot.delete_message(draft)
        elif res.reaction.emoji == "🌎" and checks.is_owner_check(ctx):
            failed = 0
            sent = 0
            count = 0
            for server in Clembot.servers:
                destination = server.owner
                embeddraft.set_footer(text="For support, contact us on our Discord server. Invite Code: AUzEXRU")
                embeddraft.colour = discord.Colour.lighter_grey()
                try:
                    await Clembot.send_message(destination, embed=embeddraft)
                except:
                    failed += 1
                    logger.info("Announcement Delivery Failure: {} - {}".format(destination.name, server.name))
                else:
                    sent += 1
                count += 1
            confirmation = await Clembot.send_message(channel, "Announcement sent to {} server owners: {} successful, {} failed.".format(count, sent, failed))
        await asyncio.sleep(10)
        await Clembot.delete_message(confirmation)
    else:
        await Clembot.delete_message(rusure)
        confirmation = await Clembot.send_message(channel, _("Announcement Timed Out."))
        await asyncio.sleep(10)
        await Clembot.delete_message(confirmation)
    await asyncio.sleep(30)
    await Clembot.delete_message(message)


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
    server = ctx.message.server
    channel = ctx.message.channel
    embed_colour = server.me.colour or discord.Colour.lighter_grey()
    uptime_str = await _uptime(Clembot)
    embed = discord.Embed(colour=embed_colour, icon_url=Clembot.user.avatar_url)
    embed.add_field(name="Uptime", value=uptime_str)
    try:
        await Clembot.send_message(channel, embed=embed)
    except discord.HTTPException:
        await Clembot.send_message(channel, "I need the `Embed links` permission to send this")


@Clembot.command(pass_context=True, hidden=True)
async def about(ctx):
    """Shows info about Clembot"""
    original_author_repo = "https://github.com/FoglyOgly"
    original_author_name = "FoglyOgly"

    author_repo = "https://github.com/TrainingB"
    author_name = "TrainingB"
    bot_repo = author_repo + "/Clembot"
    server_url = "https://discord.gg/hTfersw"
    owner = Clembot.owner
    channel = ctx.message.channel
    uptime_str = await _uptime(Clembot)
    embed_colour = ctx.message.server.me.colour or discord.Colour.lighter_grey()

    about = ("I'm Clembot! A Pokemon Go helper bot for Discord!\n\n"
             "I was made by [{original_author_name}]({original_author_repo}) and then [{author_name}]({author_repo}) evolved me further.\n\n"
             "[Join our server]({server_invite}) if you have any questions or feedback.\n\n"
             "".format(original_author_name=original_author_name, original_author_repo=original_author_repo, author_name=author_name, author_repo=author_repo, server_invite=server_url))

    member_count = 0
    server_count = 0
    for server in Clembot.servers:
        server_count += 1
        member_count += len(server.members)

    embed = discord.Embed(colour=embed_colour, icon_url=Clembot.user.avatar_url)
    embed.add_field(name="About Clembot", value=about, inline=False)
    embed.add_field(name="Owner", value=owner)
    embed.add_field(name="Servers", value=server_count)
    embed.add_field(name="Members", value=member_count)
    embed.add_field(name="Uptime", value=uptime_str)
    embed.set_footer(text="For support, contact us on our Discord server. Invite Code: AUzEXRU")

    try:
        await Clembot.send_message(channel, embed=embed)
    except discord.HTTPException:
        await Clembot.send_message(channel, "I need the `Embed links` permission to send this")


@Clembot.command(pass_context=True, hidden=True)
@checks.teamset()
@checks.nonraidchannel()
async def team(ctx):
    """Set your team role.

    Usage: !team <team name>
    The team roles have to be created manually beforehand by the server administrator."""

    server = ctx.message.server
    toprole = server.me.top_role.name
    position = server.me.top_role.position
    high_roles = []

    for team in config['team_dict'].keys():
        temp_role = discord.utils.get(ctx.message.server.roles, name=team)
        if temp_role.position > position:
            high_roles.append(temp_role.name)

    if high_roles:
        await Clembot.send_message(ctx.message.channel, _("Beep Beep! My roles are ranked lower than the following team roles: **{higher_roles_list}**\nPlease get an admin to move my roles above them!").format(higher_roles_list=', '.join(high_roles)))
        return

    role = None
    team_split = ctx.message.clean_content.lower().split()
    del team_split[0]
    entered_team = team_split[0]
    role = discord.utils.get(ctx.message.server.roles, name=entered_team)

    # Check if user already belongs to a team role by
    # getting the role objects of all teams in team_dict and
    # checking if the message author has any of them.
    for team in config['team_dict'].keys():
        temp_role = discord.utils.get(ctx.message.server.roles, name=team)
        # If the role is valid,
        if temp_role:
            # and the user has this role,
            if temp_role in ctx.message.author.roles:
                # then report that a role is already assigned
                await Clembot.send_message(ctx.message.channel, _("Beep Beep! You already have a team role!"))
                return
        # If the role isn't valid, something is misconfigured, so fire a warning.
        else:
            await Clembot.send_message(ctx.message.channel, _("Beep Beep! {team_role} is not configured as a role on this server. Please contact an admin for assistance.").format(team_role=team))
    # Check if team is one of the three defined in the team_dict

    if entered_team not in config['team_dict'].keys():
        await Clembot.send_message(ctx.message.channel, _("Beep Beep! \"{entered_team}\" isn't a valid team! Try {available_teams}").format(entered_team=entered_team, available_teams=team_msg))
        return
    # Check if the role is configured on the server
    elif role is None:
        await Clembot.send_message(ctx.message.channel, _("Beep Beep! The \"{entered_team}\" role isn't configured on this server! Contact an admin!").format(entered_team=entered_team))
    else:
        try:
            await Clembot.add_roles(ctx.message.author, role)
            await Clembot.send_message(ctx.message.channel, _("Beep Beep! Added {member} to Team {team_name}! {team_emoji}").format(member=ctx.message.author.mention, team_name=role.name.capitalize(), team_emoji=config['team_dict'][entered_team]))
        except discord.Forbidden:
            await Clembot.send_message(ctx.message.channel, _("Beep Beep! I can't add roles!"))


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
    creating a server role for the Pokemon species, and
    assigning it to the user."""
    message = ctx.message
    server = message.server
    channel = message.channel
    want_split = message.clean_content.lower().split()
    del want_split[0]
    entered_want = " ".join(want_split)
    if entered_want not in pkmn_info['raid_list']:
        if entered_want not in pkmn_info['pokemon_list']:
            await Clembot.send_message(channel, spellcheck(entered_want))
        else:
            await Clembot.send_message(channel, _("Beep Beep! {member} only raid bosses are allowed to be notified!").format(member=ctx.message.author.mention))
        return
    role = discord.utils.get(server.roles, name=entered_want)
    # Create role if it doesn't exist yet
    if role is None:
        role = await Clembot.create_role(server=server, name=entered_want, hoist=False, mentionable=True)
        await asyncio.sleep(0.5)

    # If user is already wanting the Pokemon,
    # print a less noisy message
    if role in ctx.message.author.roles:
        await Clembot.send_message(channel, content=_("Beep Beep! {member}, I already know you want {pokemon}!").format(member=ctx.message.author.mention, pokemon=entered_want.capitalize()))
    else:
        await Clembot.add_roles(ctx.message.author, role)
        want_number = pkmn_info['pokemon_list'].index(entered_want) + 1
        want_img_url = "https://raw.githubusercontent.com/TrainingB/Clembot/master/images/pkmn/{0}_.png".format(str(want_number).zfill(3))  # This part embeds the sprite
        want_img_url = get_pokemon_image_url(want_number)  # This part embeds the sprite
        want_embed = discord.Embed(colour=server.me.colour)
        want_embed.set_thumbnail(url=want_img_url)
        await Clembot.send_message(channel, content=_("Beep Beep! Got it! {member} wants {pokemon}").format(member=ctx.message.author.mention, pokemon=entered_want.capitalize()), embed=want_embed)


@Clembot.group(pass_context=True, hidden=True)
@checks.wantset()
@checks.nonraidchannel()
@checks.wantchannel()
async def unwant(ctx):
    """Remove a Pokemon from your wanted list.

    Usage: !unwant <species>
    You will no longer be notified of reports about this Pokemon."""

    """Behind the scenes, Clembot removes the user from
    the server role for the Pokemon species."""
    message = ctx.message
    server = message.server
    channel = message.channel
    if ctx.invoked_subcommand is None:
        unwant_split = message.clean_content.lower().split()
        del unwant_split[0]
        entered_unwant = " ".join(unwant_split)
        role = discord.utils.get(server.roles, name=entered_unwant)
        if entered_unwant not in pkmn_info['raid_list']:
            if entered_unwant not in pkmn_info['pokemon_list']:
                await Clembot.send_message(channel, spellcheck(entered_unwant))
            else:
                await Clembot.send_message(channel, _("Beep Beep! {member} only raid bosses are allowed to be notified!").format(member=ctx.message.author.mention))
            return
        else:
            # If user is not already wanting the Pokemon,
            # print a less noisy message
            if role not in ctx.message.author.roles:
                await Clembot.add_reaction(ctx.message, '✅')
            else:
                await Clembot.remove_roles(message.author, role)
                unwant_number = pkmn_info['pokemon_list'].index(entered_unwant) + 1
                await Clembot.add_reaction(message, '✅')


@unwant.command(pass_context=True, hidden=True)
@checks.wantset()
@checks.nonraidchannel()
@checks.wantchannel()
async def all(ctx):
    """Remove all Pokemon from your wanted list.

    Usage: !unwant all
    All Pokemon roles are removed."""

    """Behind the scenes, Clembot removes the user from
    the server role for the Pokemon species."""
    message = ctx.message
    server = message.server
    channel = message.channel
    author = message.author
    await Clembot.send_typing(channel)
    count = 0
    roles = author.roles
    remove_roles = []
    for role in roles:
        if role.name in pkmn_info['pokemon_list']:
            remove_roles.append(role)
            count += 1
        continue
    await Clembot.remove_roles(author, *remove_roles)
    if count == 0:
        await Clembot.send_message(channel, content=_("{0}, you have no pokemon in your want list.").format(author.mention, count))
        return
    await Clembot.send_message(channel, content=_("{0}, I've removed {1} pokemon from your want list.").format(author.mention, count))
    return


@Clembot.command(pass_context=True, hidden=True)
@checks.wildset()
@checks.citychannel()
async def wild(ctx):
    """Report a wild Pokemon spawn location.

    Usage: !wild <species> <location>
    Clembot will insert the details (really just everything after the species name) into a
    Google maps link and post the link to the same channel the report was made in."""
    await _wild(ctx.message)


async def _wild(message):
    wild_split = message.clean_content.lower().split()
    del wild_split[0]
    if len(wild_split) <= 1:
        await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
        return
    else:
        content = " ".join(wild_split)
        entered_wild = content.split(' ', 1)[0]
        wild_details = content.split(' ', 1)[1]
        if entered_wild not in pkmn_info['pokemon_list']:
            entered_wild2 = ' '.join([content.split(' ', 2)[0], content.split(' ', 2)[1]])
            if entered_wild2 in pkmn_info['pokemon_list']:
                entered_wild = entered_wild2
                try:
                    wild_details = content.split(' ', 2)[2]
                except IndexError:
                    await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!wild <pokemon name> <location>**"))
                    return
        wild_gmaps_link = create_gmaps_query(wild_details, message.channel)

    if entered_wild not in pkmn_info['pokemon_list']:
        await Clembot.send_message(message.channel, spellcheck(entered_wild))
        return
    else:
        wild = discord.utils.get(message.server.roles, name=entered_wild)
        if wild is None:
            wild = await Clembot.create_role(server=message.server, name=entered_wild, hoist=False, mentionable=True)
            await asyncio.sleep(0.5)
        wild_number = pkmn_info['pokemon_list'].index(entered_wild) + 1
        wild_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(wild_number).zfill(3))
        wild_img_url = get_pokemon_image_url(wild_number)  # This part embeds the sprite
        wild_embed = discord.Embed(title=_("Beep Beep! Click here for my directions to the wild {pokemon}!").format(pokemon=entered_wild.capitalize()), description=_("Ask {author} if my directions aren't perfect!").format(author=message.author.name), url=wild_gmaps_link, colour=message.server.me.colour)
        wild_embed.add_field(name="**Details:**", value=_("{pokemon} ({pokemonnumber}) {type}").format(pokemon=entered_wild.capitalize(), pokemonnumber=str(wild_number), type="".join(get_type(message.server, wild_number)), inline=True))
        wild_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
        wild_embed.set_thumbnail(url=wild_img_url)
        await Clembot.send_message(message.channel, content=_("Beep Beep! Wild {pokemon} reported by {member}! Details: {location_details}").format(pokemon=wild.mention, member=message.author.mention, location_details=wild_details), embed=wild_embed)


@Clembot.command(pass_context=True)
async def hide(ctx):
    await _hideChannel(ctx.message.channel)


async def _hideChannel(channel):
    try:
        print("hide: {channel}".format(channel=channel.name))

        readable = discord.PermissionOverwrite()
        readable.read_messages=False

        await Clembot.edit_channel_permissions(channel, channel.server.default_role, readable)
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
        readable.read_messages=True
        readable.send_messages=False

        await Clembot.edit_channel_permissions(channel, channel.server.me, writeable)
        await Clembot.edit_channel_permissions(channel, channel.server.default_role, readable)
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
        await Clembot.edit_channel_permissions(channel, channel.server.default_role, writeable)
    except Exception as error:
        print(error)


@Clembot.command(pass_context=True)
@commands.has_permissions(manage_server=True)
async def contest(ctx):
    await _contest(ctx.message)
    return


def add_contest_to_server_dict(serverid):
    if 'contest_channel' in server_dict[serverid]:
        return

    server_contest = {'contest_channel': {}}
    server_dict[serverid].update(server_contest)
    return

def generate_pokemon(option=None):

    if option is None:
        pokedex = randint(1, 383)
    else:
        option = option.upper()
        if option == 'TEST':
            pokedex = randint(1, 100)
        elif  option == 'GEN1':
            pokedex = randint(1, 151)
        elif  option == 'GEN2':
            pokedex = randint(152, 251)
        elif  option == 'GEN3':
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
                await Clembot.send_message(message.channel, "Beep Beep! valid options are : ALL,TEST,GEN1,GEN2,GEN3,GEN12")
                return

        everyone_perms = discord.PermissionOverwrite(read_messages=True,send_messages=False, add_reactions=True)
        my_perms = discord.PermissionOverwrite(read_messages=True,send_messages=True, manage_channel=True, manage_permissions=True, manage_messages=True, embed_links=True, attach_files=True, add_reactions=True, mention_everyone=True)

        channel_name = sanitize_channel_name(raid_split[0])

        if channel_name == "here":
            contest_channel = message.channel
        else:
            contest_channel = await Clembot.create_channel(message.server, channel_name)

        await Clembot.edit_channel_permissions(contest_channel, target=message.server.default_role, overwrite=everyone_perms)
        await Clembot.edit_channel_permissions(contest_channel, target=message.server.me, overwrite=my_perms)

        pokemon = generate_pokemon(option)

        await Clembot.send_message(message.channel, content=_("Beep Beep! A contest is about to take place in {channel}!".format(channel=contest_channel.mention)))

        raid_embed = discord.Embed(title=_("Beep Beep! A contest is about to take place in this channel!"), colour=discord.Colour.gold() , description="The first member to correctly guess (and spell) the randomly selected pokemon name will win!")
        raid_embed.add_field(name="**Option:**", value=_("{option}").format(option=option))
        raid_embed.add_field(name="**Rules:**", value=_("{rules}").format(rules="One pokemon per attempt per line!"))
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.name), icon_url=message.author.avatar_url)
        raid_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/396098777729204226/396103528554168320/imageedit_15_4199265561.png")
        await Clembot.send_message(contest_channel, embed=raid_embed)


        embed = discord.Embed(colour=discord.Colour.gold(), description="Beep Beep! A contest channel has been created!").set_author(name=_("Clembot Contest Notification - {0}").format(message.server), icon_url=Clembot.user.avatar_url)
        embed.add_field(name="**Channel:**", value=_(" {member}").format(member=contest_channel.name), inline=True)
        embed.add_field(name="**Option**", value=_(" {member}").format(member=option), inline=True)
        embed.add_field(name="**Pokemon**", value=_(" {member}").format(member=pokemon), inline=True)
        embed.add_field(name="**Server:**", value=_("{member}").format(member=message.server.name), inline=True)
        embed.add_field(name="**Reported By:**", value=_("{member}").format(member=message.author.name), inline=True)
        await Clembot.send_message(Clembot.owner, embed=embed)
        if message.author.id != Clembot.owner.id :
            await Clembot.send_message(message.author, embed=embed)


        await Clembot.send_message(contest_channel, "Beep Beep! {reporter} can start the contest anytime using `!ready` command".format(reporter=message.author.mention))

        add_contest_to_server_dict(message.server.id)
        contest_channel_dict = {contest_channel.id : {'pokemon' : pokemon, 'started': False, 'reported_by' : message.author.id , 'option' : option }}

        server_dict[message.server.id]['contest_channel'].update(contest_channel_dict)

    except Exception as error:
        print(error)

    return

@Clembot.command(pass_context=True)
async def renew(ctx):

    message = ctx.message
    if 'contest_channel' in server_dict[message.server.id]:
        if server_dict[message.server.id]['contest_channel'][message.channel.id].get('started', True) == False:
            if ctx.message.author.id == server_dict[message.server.id]['contest_channel'][message.channel.id].get('reported_by', 0):

                option = server_dict[message.server.id]['contest_channel'][message.channel.id].get('option', "ALL")

                pokemon = generate_pokemon(option)
                contest_channel_dict = {message.channel.id : {'pokemon' : pokemon, 'started': False, 'reported_by' : message.author.id , 'option' : option }}
                server_dict[message.server.id]['contest_channel'].update(contest_channel_dict)

                embed = discord.Embed(colour=discord.Colour.gold(), description="Beep Beep! A contest channel has been created!").set_author(name=_("Clembot Contest Notification - {0}").format(message.server), icon_url=Clembot.user.avatar_url)
                embed.add_field(name="**Channel:**", value=_(" {member}").format(member=message.channel.name), inline=True)
                embed.add_field(name="**Option**", value=_(" {member}").format(member=option), inline=True)
                embed.add_field(name="**Pokemon**", value=_(" {member}").format(member=pokemon), inline=True)
                embed.add_field(name="**Server:**", value=_("{member}").format(member=message.server.name), inline=True)
                embed.add_field(name="**Reported By:**", value=_("{member}").format(member=message.author.name), inline=True)

                await Clembot.delete_message(ctx.message)
                await Clembot.send_message(Clembot.owner, embed=embed)
                if message.author.id != Clembot.owner.id :
                    await Clembot.send_message(message.author, embed=embed)


@Clembot.command(pass_context=True)
async def ready(ctx):
    message = ctx.message
    if 'contest_channel' in server_dict[message.server.id]:
        if server_dict[message.server.id]['contest_channel'][message.channel.id].get('started', True) == False:
            if ctx.message.author.id == server_dict[message.server.id]['contest_channel'][message.channel.id].get('reported_by', 0):

                role = message.server.default_role
                args = ctx.message.clean_content.lower().split()
                del args[0]
                if len(args) > 0:
                    role_name = args[0]
                    role = discord.utils.get(ctx.message.server.roles, name=role_name)
                    if role is None:
                        role = message.server.default_role

                everyone_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=True)
                await Clembot.edit_channel_permissions(message.channel,target=role,overwrite=everyone_perms)

                contest_channel_started_dict = {'started': True}
                server_dict[message.server.id]['contest_channel'][message.channel.id].update(contest_channel_started_dict)

                raid_embed = discord.Embed(title=_("Beep Beep! The channel is open for submissions now!"), colour=discord.Colour.gold())
                raid_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/396098777729204226/396101362460524545/imageedit_14_9502845615.png")
                await Clembot.send_message(message.channel, embed=raid_embed)
            else:
                await Clembot.send_message(message.channel, content="Beep Beep! Only contest organizer can do this!")
            return


async def contestEntry(message, pokemon=None):

    if pokemon == None:
        pokemon = server_dict[message.server.id]['contest_channel'][message.channel.id]['pokemon']

    if pokemon.lower() == message.content.lower():
        del server_dict[message.server.id]['contest_channel'][message.channel.id]
        await Clembot.add_reaction(message, '✅')
        await Clembot.add_reaction(message, '🎉')

        raid_embed = discord.Embed(title=_("**We have a winner!🎉🎉🎉**"),description="", colour=discord.Colour.dark_gold())

        raid_embed.add_field(name="**Winner:**", value=_("{member}").format(member=message.author.mention), inline=True)
        raid_embed.add_field(name="**Winning Entry:**", value=_("{pokemon}").format(pokemon=pokemon), inline=True)
        raid_embed.set_thumbnail(url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=message.author, format="jpg")))
        # raid_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/396098777729204226/396106669622296597/imageedit_17_5142594467.png")

        await Clembot.send_message(message.channel, embed=raid_embed)

        await Clembot.send_message(message.channel, content=_("Beep Beep! Congratulations {winner}!").format(winner=message.author.mention))

    elif message.content.lower() in pkmn_info['pokemon_list']:
        await Clembot.add_reaction(message, '🔴')
    return

@checks.cityeggchannel()
@Clembot.command(pass_context=True)
@checks.raidset()
async def raid(ctx):
    """Report an ongoing raid.

    Usage: !raid <species> <location> [minutes]
    Clembot will insert the details (really just everything after the species name) into a
    Google maps link and post the link to the same channel the report was made in.
    Clembot's message will also include the type weaknesses of the boss.

    Finally, Clembot will create a separate channel for the raid report, for the purposes of organizing the raid."""
    await _raid(ctx.message)


async def _raid(message):
    fromegg = False
    if message.channel.name not in server_dict[message.server.id]['city_channels'].keys():
        if message.channel.id in server_dict[message.channel.server.id]['raidchannel_dict'] and server_dict[message.channel.server.id]['raidchannel_dict'][message.channel.id]['type'] == 'egg':
            fromegg = True
            eggdetails = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]
            egglevel = eggdetails['egglevel']
        else:
            await Clembot.send_message(message.channel, _("Beep Beep! Please restrict raid reports to a city channel!"))
            return
    raid_split = message.clean_content.lower().split()
    del raid_split[0]
    if fromegg is True:
        eggdetails = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]
        egglevel = eggdetails['egglevel']
        if raid_split[0] == 'assume':
            if config['allow_assume'][egglevel] == "False":
                await Clembot.send_message(message.channel, _("Beep Beep! **!raid assume** is not allowed in this level egg."))
                return
            if server_dict[message.channel.server.id]['raidchannel_dict'][message.channel.id]['active'] == False:
                await _eggtoraid(raid_split[1].lower(), message.channel)
                return
            else:
                await _eggassume(" ".join(raid_split), message.channel)
                return
        else:
            if server_dict[message.channel.server.id]['raidchannel_dict'][message.channel.id]['active'] == False:
                await _eggtoraid(" ".join(raid_split).lower(), message.channel)
                return
            else:
                await Clembot.send_message(message.channel, _("Beep Beep! Please wait until the egg has hatched before changing it to an open raid!"))
                return
    elif len(raid_split) <= 1:
        await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
        return
    entered_raid = re.sub("[\@]", "", raid_split[0].lower())
    entered_raid = get_name(entered_raid).lower() if entered_raid.isdigit() else entered_raid
    del raid_split[0]

    gym_info = None

    gym_code = raid_split[-1].upper()
    gym_info = gymutil.get_gym_info(gym_code, city_state=get_city_list(message))
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
            await Clembot.send_message(message.channel, _("Beep Beep...that's too long. Raids currently last no more than 45 minutes..."))
            return

    if entered_raid not in pkmn_info['pokemon_list']:
        await Clembot.send_message(message.channel, spellcheck(entered_raid))
        return
    if entered_raid not in pkmn_info['raid_list'] and entered_raid in pkmn_info['pokemon_list']:
        await Clembot.send_message(message.channel, _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
        return

    raid_details = " ".join(raid_split)
    raid_details = raid_details.strip()
    if raid_details == '':
        if gym_info:
            raid_details = gym_info['gym_name']
        else:
            await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!raid <pokemon name> <location>**"))
            return

    if gym_info is None and 2 <= raid_details.__len__() <= 6:
        raid_details_gym_code = raid_details.upper()
        raid_details_gym_info = gymutil.get_gym_info(raid_details_gym_code, city_state=get_city_list(message))
        if raid_details_gym_info:
            gym_info = raid_details_gym_info

    if gym_info:
        raid_gmaps_link = gym_info['gmap_link']
        raid_channel_name = entered_raid + "-" + sanitize_channel_name(gym_info['gym_name'])
    else:
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
        raid_channel_name = entered_raid + "-" + sanitize_channel_name(raid_details)

    raid_channel = await Clembot.create_channel(message.server, raid_channel_name, *message.channel.overwrites)
    raid = discord.utils.get(message.server.roles, name=entered_raid)
    if raid is None:
        raid = await Clembot.create_role(server=message.server, name=entered_raid, hoist=False, mentionable=True)
        await asyncio.sleep(0.5)
    raid_number = pkmn_info['pokemon_list'].index(entered_raid) + 1
    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(raid_number).zfill(3))
    raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the raid!"), url=raid_gmaps_link, colour=message.server.me.colour)
    raid_embed.add_field(name="**Details:**", value=_("{pokemon} ({pokemonnumber}) {type}").format(pokemon=entered_raid.capitalize(), pokemonnumber=str(raid_number), type="".join(get_type(message.server, raid_number)), inline=True))
    raid_embed.add_field(name="**Weaknesses:**", value=_("{weakness_list}").format(weakness_list=weakness_to_str(message.server, get_weaknesses(entered_raid))), inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    raidreport = await Clembot.send_message(message.channel, content=_("Beep Beep! {pokemon} raid reported by {member}! Details: {location_details}. Coordinate in {raid_channel}").format(pokemon=entered_raid.capitalize(), member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! {pokemon} raid reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
This channel will be deleted five minutes after the timer expires.
** **
Please type `!beep raid` if you need a refresher of Clembot commands! 
""").format(pokemon=raid.mention, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

    raidmessage = await Clembot.send_message(raid_channel, content=raidmsg, embed=raid_embed)
    print(server_dict[message.server.id]['raidchannel_dict'])
    server_dict[message.server.id]['raidchannel_dict'][raid_channel.id] = {
		'reportcity': message.channel.name,
		'trainer_dict': {},
		'exp': fetch_current_time(message.channel.server.id) + timedelta(minutes=raid_timer),  # raid timer minutes from now
        'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
        'active': True,
        'raidmessage' : raidmessage.id,
        'raidreport' : raidreport.id,
		'address': raid_details,
		'type': 'raid',
		'pokemon': entered_raid,
		'egglevel': '0',
		'suggested_start': False
		}
    print(server_dict[message.server.id]['raidchannel_dict'])
    if raidexp is not False:
        await _timerset(raid_channel, raidexp)
    else:
        await Clembot.send_message(raid_channel, content=_("Beep Beep! Hey {member}, if you can, set the time left on the raid using **!timerset <minutes>** so others can check it with **!timer**.").format(member=message.author.mention))
    event_loop.create_task(expiry_check(raid_channel))


# Print raid timer
async def print_raid_timer(channel_id):
    channel = Clembot.get_channel(channel_id)
    localexpire = fetch_channel_expire_time(channel_id)
    # localexpire = localexpiresecs - timedelta(hours=server_dict[channel.server.id]['offset'])
    timerstr = ""
    if server_dict[channel.server.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
        raidtype = "egg"
        raidaction = "hatch"
    else:
        raidtype = "raid"
        raidaction = "end"
    if not server_dict[channel.server.id]['raidchannel_dict'][channel.id]['active']:
        timerstr += _("Beep Beep! This {raidtype}'s timer has already expired as of {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
    else:
        if server_dict[channel.server.id]['raidchannel_dict'][channel.id]['egglevel'] == "EX" or server_dict[channel.server.id]['raidchannel_dict'][channel.id]['type'] == "exraid":
            if server_dict[channel.server.id]['raidchannel_dict'][channel.id]['manual_timer']:
                timerstr += _("Beep Beep! This {raidtype} will {raidaction} on {expiry_day} at {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, raidaction=raidaction, expiry_day=strftime("%B %d", localexpire), expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
            else:
                timerstr += _("Beep Beep! No one told me when the {raidtype} will {raidaction}, so I'm assuming it will {raidaction} on {expiry_day} at {expiry_time} ({expiry_time24})!").format(raidtype=raidtype, raidaction=raidaction, expiry_day=localexpire.strftime("%B %d"), expiry_time=localexpire.strftime("%I:%M %p"), expiry_time24=localexpire.strftime("%H:%M"))
        else:
            if server_dict[channel.server.id]['raidchannel_dict'][channel.id]['manual_timer']:
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
    server = message.server
    if checks.check_raidactive(ctx) and not checks.check_exraidchannel(ctx):
        if server_dict[server.id]['raidchannel_dict'][channel.id]['type'] == 'egg':
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
                await Clembot.send_message(channel, "Beep Beep! I couldn't understand your time format. Try again like this: **!timerset <minutes>**")
                return
        else:
            await Clembot.send_message(channel, "Beep Beep! I couldn't understand your time format. Try again like this: **!timerset <minutes>**")
            return
        if _timercheck(raidexp, maxtime):
            await Clembot.send_message(channel, _("Beep Beep...that's too long. {raidtype}s currently last no more than {maxtime} minutes...").format(raidtype=raidtype.capitalize(), maxtime=str(maxtime)))
            return
        await _timerset(channel, raidexp)

    if checks.check_exraidchannel(ctx):
        if checks.check_eggchannel(ctx):
            tzlocal = tz.tzoffset(None, server_dict[server.id]['offset'] * 3600)
            now = datetime.datetime.now()
            timer_split = message.clean_content.lower().split()
            del timer_split[0]
            try:
                end = datetime.strptime(" ".join(timer_split) + " " + str(now.year), '%m/%d %I:%M %p %Y').replace(tzinfo=tzlocal)
            except ValueError:
                await Clembot.send_message(channel, _("Beep Beep! Your timer wasn't formatted correctly. Change your **!timerset** to match the format on your EX Raid invite and try again."))
            diff = end - now
            total = (diff.total_seconds() / 60)
            if now <= end:
                await _timerset(channel, total)
            elif now > end:
                await Clembot.send_message(channel, _("Beep Beep! Please enter a time in the future."))
        else:
            await Clembot.send_message(channel, _("Beep Beep! Timerset isn't supported for exraids after they have hatched."))


def _timercheck(time, maxtime):
    return time > maxtime


async def _timerset(channel, exptime):
    server = channel.server
    exptime = int(exptime)
    # Clembot saves the timer message in the channel's 'exp' field.

    expire = fetch_current_time(channel.server.id) + timedelta(minutes=exptime)

    # Update timestamp
    server_dict[server.id]['raidchannel_dict'][channel.id]['exp'] = expire
    # Reactivate channel
    if not server_dict[server.id]['raidchannel_dict'][channel.id]['active']:
        await Clembot.send_message(channel, "The channel has been reactivated.")
    server_dict[server.id]['raidchannel_dict'][channel.id]['active'] = True
    # Mark that timer has been manually set
    server_dict[server.id]['raidchannel_dict'][channel.id]['manual_timer'] = True
    # Send message
    timerstr = await print_raid_timer(channel.id)
    await Clembot.send_message(channel, timerstr)
    # Trigger expiry checking
    event_loop.create_task(expiry_check(channel))


@Clembot.command(pass_context=True, hidden=True)
@checks.raidchannel()
async def timer(ctx):
    """Have Clembot resend the expire time message for a raid.

    Usage: !timer
    The expiry time should have been previously set with !timerset."""
    timerstr = await print_raid_timer(ctx.message.channel.id)
    await Clembot.send_message(ctx.message.channel, timerstr)


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
        expire_at = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['exp']
        return expire_at
    return None

def fetch_channel_start_time(channel_id) -> datetime:
    channel = Clembot.get_channel(channel_id)
    if channel:
        start_at = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['suggested_start']
        return start_at
    return None


def fetch_current_time(server_id):

    offset = server_dict[server_id]['offset']
    current_time = datetime.datetime.utcnow() + timedelta(hours=offset)
    return current_time


def convert_into_current_time(channel, time_hour_and_min_only):
    offset = server_dict[channel.server.id]['offset']
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

    offset = server_dict[channel.server.id]['offset']
    current_datetime = datetime.datetime.utcnow() + timedelta(hours=offset)

    suggested_start_time = convert_into_current_time(channel, start_time)

    is_raid_egg = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['type'] == "egg"

    # modified time for raidegg
    if is_raid_egg:
        current_datetime = raid_expires_at
        raid_expires_at = raid_expires_at + timedelta(minutes=egg_timer)

    if suggested_start_time:
        if suggested_start_time > raid_expires_at:
            await Clembot.send_message(channel, ("Beep Beep...! start time cannot be after raid expiry time!"))
            return None
        elif suggested_start_time < current_datetime:
            if is_raid_egg:
                await Clembot.send_message(channel, ("Beep Beep...! start time cannot be before the egg hatches!"))
            else:
                await Clembot.send_message(channel, ("Beep Beep...! start time cannot be in past!"))
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

    raid_embed = discord.Embed(title=raid_title, url="", colour=message.server.me.colour)

    raid_embed.add_field(name="**Interested:**", value=_("{bosslist1}").format(bosslist1="\n".join(bosslist1)), inline=True)
    raid_embed.add_field(name="**Coming:**", value=_("{bosslist2}").format(bosslist2="\n".join(bosslist2)), inline=True)
    raid_embed.add_field(name="**Here:**", value=_("{bosslist2}").format(bosslist2="\n".join(bosslist2)), inline=True)
    raid_embed.set_footer(text=_("Reported by {author}").format(author=message.author.name), icon_url=message.author.avatar_url)
    raid_embed.set_thumbnail(url=raid_img_url)
    raidreport = await Clembot.send_message(message.channel, content=_("Beep Beep! {member} here you go!").format(member=message.author.mention), embed=raid_embed)

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidchannel()
async def start(ctx):
    """Set the remaining duration on a raid.

    Usage: !start <hh:mm>
    Works only in raid channels, can be set or overridden by anyone.
    Clembot displays the end time in HH:MM local time."""
    if ctx.message.channel.id in server_dict[ctx.message.server.id]['raidchannel_dict']:
        try:
            if server_dict[ctx.message.channel.server.id]['raidchannel_dict'][ctx.message.channel.id]['type'] == 'exraid':
                await Clembot.send_message(ctx.message.channel, _("start isn't supported for exraids."))
                return
        except KeyError:
            pass
        args = ctx.message.content.lstrip("!start ")
        start_time = convert_into_time(args, False)

        if start_time is None:
            await Clembot.send_message(ctx.message.channel, _("Beep Beep... I couldn't understand your time format. Try again like this: `!start HH:MM AM/PM`"))
            return

        raid_starts_at = await validate_start_time(ctx.message.channel, start_time)
        if raid_starts_at:
            try:
                server_dict[ctx.message.channel.server.id]['raidchannel_dict'][ctx.message.channel.id]['suggested_start'] = raid_starts_at
                await Clembot.send_message(ctx.message.channel, _("Beep Beep! {member} suggested the start time : {starttime}").format(member=ctx.message.author.mention, starttime=print_24_hour(raid_starts_at)))
            except Exception as error:
                print(error)
            return


async def print_start_time(channel_id):
    channel = Clembot.get_channel(channel_id)
    timerstr = ""
    if not server_dict[channel.server.id]['raidchannel_dict'][channel.id]['suggested_start']:
        timerstr = ("Beep Beep! No start time has been suggested for this raid!")
    else:
        start_time = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['suggested_start']
        timerstr += _("Beep Beep! The suggested start time for this raid is {start_time}!").format(start_time=print_24_hour(start_time))

    return timerstr


"""
Behind-the-scenes functions for raid management.
Triggerable through commands or through emoji
"""


async def _maybe(message, count):
    trainer_dict = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict']

    # Add trainer name to trainer list
    if message.author.id not in trainer_dict:
        trainer_dict[message.author.id] = {}
    trainer_dict[message.author.id]['status'] = "maybe"
    trainer_dict[message.author.id]['count'] = count
    server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

    if count == 1:
        # await Clembot.send_message(message.channel, _("Beep Beep! {member} is interested!").format(member=message.author.mention))
        embed_msg = _("Beep Beep! {member} is interested!").format(member=message.author.mention)
    else:
        # await Clembot.send_message(message.channel, _("Beep Beep! {member} is interested with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count))
        embed_msg = _("Beep Beep! {member} is interested with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count)

    await Clembot.send_message(message.channel, embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.gold()))

async def _coming(message, count):
    trainer_dict = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict']

    # Add trainer name to trainer list
    if message.author.id not in trainer_dict:
        trainer_dict[message.author.id] = {}
    trainer_dict[message.author.id]['status'] = "omw"
    trainer_dict[message.author.id]['count'] = count
    server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

    if count == 1:
        # await Clembot.send_message(message.channel, _("Beep Beep! {member} is on the way!").format(member=message.author.mention))
        embed_msg = _("{member} is on the way!").format(member=message.author.mention)
    else:
        # await Clembot.send_message(message.channel, _("Beep Beep! {member} is on the way with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count))
        embed_msg = _("{member} is on the way with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count)

    await Clembot.send_message(message.channel, embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.gold()))


async def _here(message, count):
    trainer_dict = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict']
    # Add trainer name to trainer list
    if message.author.id not in trainer_dict:
        trainer_dict[message.author.id] = {}
    trainer_dict[message.author.id]['status'] = "waiting"
    trainer_dict[message.author.id]['count'] = count
    server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict'] = trainer_dict

    if count == 1:
        # await Clembot.send_message(message.channel, _("Beep Beep! {member} is at the raid!").format(member=message.author.mention))
        embed_msg = _("Beep Beep! {member} is at the raid!").format(member=message.author.mention)
    else:
        # await Clembot.send_message(message.channel, _("Beep Beep! {member} is at the raid with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count))
        embed_msg = _("Beep Beep! {member} is at the raid with a total of {trainer_count} trainers!").format(member=message.author.mention, trainer_count=count)

    await Clembot.send_message(message.channel, embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.green()))


def get_names_from_channel(message, status):
    trainer_dict = copy.deepcopy(server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict'])
    name_list = []
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == status:
            # user = Clembot.get_user_info(trainer)
            name_list.append("**<@!" + trainer + ">**")
            # name_list.append(user.mention)
        # name_list.append("**<@!" + message.author.id + ">**")
    if len(name_list) > 0:
        return ','.join(name_list)
    return None


def get_count_from_channel(message, status):
    rc_d = server_dict[message.server.id]['raidchannel_dict']
    r = message.channel.id
    count = 0
    for trainer in rc_d[r]['trainer_dict'].values():
        if trainer['status'] == status:
            count += trainer['count']

    return count


def channel_status_embed(message, embed_msg_desc, colour = None):

    if colour is None:
        colour = discord.Colour.green()

    raid_embed = discord.Embed(description=embed_msg_desc, colour=colour)
    raid_embed.add_field(name="Interested / On the way / At the raid", value="{interested} / {coming} / {here}".format(here=get_count_from_channel(message, "waiting"), coming=get_count_from_channel(message, "omw"), interested=get_count_from_channel(message, "maybe")), inline=True)

    return raid_embed


async def _cancel(message):
    author = message.author
    channel = message.channel
    server = message.server
    try:
        t_dict = server_dict[server.id]['raidchannel_dict'][channel.id]['trainer_dict'][author.id]
    except KeyError:
        # await Clembot.send_message(channel, _("Beep Beep! {member} has no status to cancel!").format(member=author.mention))
        embed_msg = _("Beep Beep! {member} has no status to cancel!").format(member=author.mention)

        await Clembot.send_message(message.channel, embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.red()))

        return

    if t_dict['status'] == "maybe":
        if t_dict['count'] == 1:
            # await Clembot.send_message(channel, _("Beep Beep! {member} is no longer interested!").format(member=author.mention))
            embed_msg = _("Beep Beep! {member} is no longer interested!").format(member=author.mention)
        else:
            # await Clembot.send_message(channel, _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer interested!").format(member=author.mention, trainer_count=t_dict['count']))
            embed_msg = _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer interested!").format(member=author.mention, trainer_count=t_dict['count'])
    if t_dict['status'] == "waiting":
        if t_dict['count'] == 1:
            # await Clembot.send_message(channel, _("Beep Beep! {member} has left the raid!").format(member=author.mention))
            embed_msg = _("Beep Beep! {member} has left the raid!").format(member=author.mention)
        else:
            # await Clembot.send_message(channel, _("Beep Beep! {member} and their total of {trainer_count} trainers have left the raid!").format(member=author.mention, trainer_count=t_dict['count']))
            embed_msg = _("Beep Beep! {member} and their total of {trainer_count} trainers have left the raid!").format(member=author.mention, trainer_count=t_dict['count'])
    if t_dict['status'] == "omw":
        if t_dict['count'] == 1:
            # await Clembot.send_message(channel, _("Beep Beep! {member} is no longer on their way!").format(member=author.mention))
            embed_msg = _("Beep Beep! {member} is no longer on their way!").format(member=author.mention)
        else:
            # await Clembot.send_message(channel, _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer on their way!").format(member=author.mention, trainer_count=t_dict['count']))
            embed_msg = _("Beep Beep! {member} and their total of {trainer_count} trainers are no longer on their way!").format(member=author.mention, trainer_count=t_dict['count'])
    t_dict['status'] = None

    await Clembot.send_message(message.channel,embed=channel_status_embed(message=message, embed_msg_desc=embed_msg, colour=discord.Colour.dark_red()))

@Clembot.event
async def on_message(message):
    #print(server_dict)
    if message.server is not None:
        if 'contest_channel' in server_dict[message.server.id]:
            if message.channel.id in server_dict[message.server.id]['contest_channel'] and server_dict[message.server.id]['contest_channel'][message.channel.id].get('started',False) == True:
                await contestEntry(message)
                return

        raid_status = server_dict[message.server.id]['raidchannel_dict'].get(message.channel.id, None)
        if raid_status is not None:
            if server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['active']:
                trainer_dict = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict']
                if message.author.id in trainer_dict:
                    count = trainer_dict[message.author.id]['count']
                else:
                    count = 1
                omw_emoji = parse_emoji(message.server, config['omw_id'])
                if message.content.startswith(omw_emoji):
                    emoji_count = message.content.count(omw_emoji)
                    await _coming(message, emoji_count)
                    return
                here_emoji = parse_emoji(message.server, config['here_id'])
                if message.content.startswith(here_emoji):
                    emoji_count = message.content.count(here_emoji)
                    await _here(message, emoji_count)
                    return
                if "/maps" in message.content:
                    if message.content.startswith("!update") == False:
                        await process_map_link(message)
                        return
    messagelist = message.content.split(" ")
    message.content = messagelist.pop(0).lower() + " " + " ".join(messagelist)
    await Clembot.process_commands(message)


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

    if server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['type'] == 'raidparty':
        await _add(message, newloc)
        return

    reportcityid = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['reportcity']
    oldraidmsgid = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidmessage']
    oldreportmsgid = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidreport']

    reportcitychannel = discord.utils.get(message.channel.server.channels, name=reportcityid)

    oldraidmsg = await Clembot.get_message(message.channel, oldraidmsgid)

    oldembed = oldraidmsg.embeds[0]
    newembed = discord.Embed(title=oldembed['title'], url=newloc, colour=message.server.me.colour)
    newembed.add_field(name=oldembed['fields'][0]['name'], value=oldembed['fields'][0]['value'], inline=True)
    newembed.add_field(name=oldembed['fields'][1]['name'], value=oldembed['fields'][1]['value'], inline=True)
    newembed.set_footer(text=oldembed['footer']['text'], icon_url=oldembed['footer']['icon_url'])
    newembed.set_thumbnail(url=oldembed['thumbnail']['url'])
    try:
        newraidmsg = await Clembot.edit_message(oldraidmsg, new_content=oldraidmsg.content, embed=newembed)
    except:
        pass
    try:
        oldreportmsg = await Clembot.get_message(reportcitychannel, oldreportmsgid)
        newreportmsg = await Clembot.edit_message(oldreportmsg, new_content=oldreportmsg.content, embed=newembed)
    except:
        pass


    server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidmessage'] = newraidmsg.id
    server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidreport'] = newreportmsg.id
    otw_list = []
    trainer_dict = copy.deepcopy(server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict'])
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == 'omw':
            user = await Clembot.get_user_info(trainer)
            otw_list.append(user.mention)
    await Clembot.send_message(message.channel, content=_("Beep Beep! Someone has suggested a different location for the raid! Trainers {trainer_list}: make sure you are headed to the right place!").format(trainer_list=", ".join(otw_list)), embed=newembed)
    return

@Clembot.command(pass_context=True, hidden=True)
async def dict(ctx):

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.cityexraidchannel()
@checks.raidset()
async def exraid(ctx):
    """Report an upcoming EX raid.

    Usage: !exraid <location>
    Clembot will insert the details (really just everything after the species name) into a
    Google maps link and post the link to the same channel the report was made in.
    Clembot's message will also include the type weaknesses of the boss.

    Finally, Clembot will create a separate channel for the raid report, for the purposes of organizing the raid."""
    await _exraid(ctx)


async def _exraid(ctx):
    message = ctx.message
    channel = message.channel
    fromegg = False
    exraid_split = message.clean_content.lower().split()
    del exraid_split[0]
    if len(exraid_split) <= 0:
        await Clembot.send_message(channel, _("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return
    raid_details = " ".join(exraid_split)
    raid_details = raid_details.strip()
    if raid_details == '':
        await Clembot.send_message(channel, _("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return

    raid_gmaps_link = create_gmaps_query(raid_details, message.channel)

    egg_info = raid_info['raid_eggs']['EX']
    egg_img = egg_info['egg_img']
    boss_list = []
    for p in egg_info['pokemon']:
        p_name = get_name(p)
        p_type = get_type(message.server, p)
        boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))
    raid_channel_name = "ex-raid-egg-" + sanitize_channel_name(raid_details)
    raid_channel_overwrites = channel.overwrites
    clembot_overwrite = (Clembot.user, discord.PermissionOverwrite(send_messages=True))
    for overwrite in raid_channel_overwrites:
        overwrite[1].send_messages = False
    raid_channel = await Clembot.create_channel(message.server, raid_channel_name, *raid_channel_overwrites, clembot_overwrite)
    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/eggs/{}".format(str(egg_img))
    raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.server.me.colour)
    if len(egg_info['pokemon']) > 1:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
        raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
    else:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist}").format(bosslist="".join(boss_list)), inline=True)
        raid_embed.add_field(name="\u200b", value="\u200b", inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    raidreport = await Clembot.send_message(channel, content=_("Beep Beep! EX raid egg reported by {member}! Details: {location_details}. Use the **!invite** command to gain access and coordinate in {raid_channel}").format(member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
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
    raidmessage = await Clembot.send_message(raid_channel, content=raidmsg, embed=raid_embed)

    server_dict[message.server.id]['raidchannel_dict'][raid_channel] = {
        'reportcity': channel.name,
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

    await Clembot.send_message(raid_channel, content=_("Beep Beep! Hey {member}, if you can, set the time the EX Raid begins using **!timerset <date and time>** so others can check it with **!timer**. **<date and time>** should look exactly as it appears on your invitation.").format(member=message.author.mention))

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
        await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!raidparty <channel-name>**"))
        return
    raid_details = " ".join(args_split)
    raid_details = raid_details.strip()

    raid_channel_name = "raid-party-" + sanitize_channel_name(raid_details)
    raid_channel_overwrites = message.channel.overwrites
    meowth_overwrite = (Clembot.user, discord.PermissionOverwrite(send_messages=True))

    raid_channel = await Clembot.create_channel(message.server, raid_channel_name, *raid_channel_overwrites, meowth_overwrite)
    raidreport = await Clembot.send_message(message.channel, content=_("Beep Beep! A raid party is being organized by {member}! You can coordinate in {raid_channel}").format(member=message.author.mention, raid_channel=raid_channel.mention))
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! A raid-party is happening and {member} will be organizing it here in {raid_channel}! Coordinate here!
** **
`!beep raidparty` lists all the command Clembot has to offer for a raid party!
`!beep raidowner` lists all the command which can be used to manage the raid party!
    """).format(member=message.author.mention, raid_channel=raid_channel.mention)

    raidmessage = await Clembot.send_message(raid_channel, content=raidmsg)

    server_dict[message.server.id]['raidchannel_dict'][raid_channel.id] = {
        'reportcity': message.channel.name,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': None,
        'raidreport': raidreport.id,
        'address': raid_details,
        'type': 'raidparty',
        'pokemon': None,
        'egglevel': '0',
        'suggested_start': False,
        'roster': [],
        'roster_index': None
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


@Clembot.command(pass_context=True, hidden=True)
@checks.citychannel()
@checks.raidset()
async def raidegg(ctx):
    """Report a raid egg.

    Usage: !raidegg <level> <location> [minutes]

    Clembot will give a map link to the entered location and create a channel for organising the coming raid in.
    Clembot will also provide info on the possible bosses that can hatch and their types.

    <level> - Required. Level of the egg. Levels are from 1 to 5.
    <location> - Required. Address/Location of the gym.
    <minutes-remaining> - Not required. Time remaining until the egg hatches into an open raid. 1-60 minutes will be accepted. If not provided, 1 hour is assumed. Whole numbers only."""
    await _raidegg(ctx.message)


async def _raidegg(message):
    raidegg_split = message.clean_content.lower().split()
    del raidegg_split[0]
    if len(raidegg_split) <= 1:
        await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Usage: **!raidegg <level> <location>**"))
        return

    gym_info = None

    if raidegg_split[-1].isalpha():
        gym_code = raidegg_split[-1].upper()
        gym_info = gymutil.get_gym_info(gym_code, city_state=get_city_list(message))
        if gym_info:
            del raidegg_split[-1]
    if raidegg_split[0].isdigit():
        egg_level = int(raidegg_split[0])
        del raidegg_split[0]
    else:
        await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Use at least: **!raidegg <level> <location>**. Type **!help** raidegg for more info."))
        return

    if len(raidegg_split) > 1 and raidegg_split[-1].isdigit():
        raidexp = int(raidegg_split[-1])
        del raidegg_split[-1]
    elif len(raidegg_split) > 1 and ":" in raidegg_split[-1]:
        raidegg_split[-1] = re.sub(r"[a-zA-Z]", "", raidegg_split[-1])
        if raidegg_split[-1].split(":")[0] == "":
            endhours = 0
        else:
            endhours = int(raidegg_split[-1].split(":")[0])
        if raidegg_split[-1].split(":")[1] == "":
            endmins = 0
        else:
            endmins = int(raidegg_split[-1].split(":")[1])
        raidexp = 60 * endhours + endmins
        del raidegg_split[-1]
    else:
        raidexp = False

    if raidexp is not False:
        if _timercheck(raidexp, egg_timer):
            await Clembot.send_message(message.channel, _("Beep Beep...that's too long. Raid Eggs currently last no more than one hour..."))
            return

    raid_details = " ".join(raidegg_split)
    raid_details = raid_details.strip()
    if raid_details == '':
        if gym_info:
            raid_details = gym_info['gym_name']
        else:
            await Clembot.send_message(message.channel, _("Beep Beep! Give more details when reporting! Use at least: **!raidegg <level> <location>**. Type **!help** raidegg for more info."))
            return

    if gym_info is None and 2 <= raid_details.__len__() <= 6:
        raid_details_gym_code = raid_details.upper()
        raid_details_gym_info = gymutil.get_gym_info(raid_details_gym_code, city_state=get_city_list(message))
        if raid_details_gym_info:
            gym_info = raid_details_gym_info
            raid_details = gym_info['gym_name']

    if egg_level > 5 or egg_level == 0:
        await Clembot.send_message(message.channel, _("Beep Beep! Raid egg levels are only from 1-5!"))
        return
    else:
        egg_level = str(egg_level)
        egg_info = raid_info['raid_eggs'][egg_level]
        egg_img = egg_info['egg_img']
        boss_list = []
        mon_in_one_line = 0
        for p in egg_info['pokemon']:
            p_name = get_name(p)
            p_type = get_type(message.server, p)
            boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))
        if gym_info:
            raid_gmaps_link = gym_info['gmap_link']
            raid_channel_name = "level-" + egg_level + "-egg-" + sanitize_channel_name(gym_info['gym_name'])
        else:
            raid_gmaps_link = create_gmaps_query(raid_details, message.channel)
            raid_channel_name = "level-" + egg_level + "-egg-" + sanitize_channel_name(raid_details)
        try:
            raid_channel = await Clembot.create_channel(message.server, raid_channel_name, *message.channel.overwrites)
        except Exception as error:
            print(error)
            await Clembot.send_message(message.channel, content=_("Beep Beep! An error occurred while creating the channel. {error}").format(error=error))
            return

        raid_img_url = get_egg_image_url(egg_level)
        raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.server.me.colour)
        if len(egg_info['pokemon']) > 1:
            raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
            raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
        else:
            raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)

        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
        raid_embed.set_thumbnail(url=raid_img_url)
        try :
            raidreport = await Clembot.send_message(message.channel, content=_("Beep Beep! Level {level} raid egg reported by {member}! Details: {location_details}. Coordinate in {raid_channel}").format(level=egg_level, member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
        except Exception as error:
            print(error)
        await asyncio.sleep(1)  # Wait for the channel to be created.

        raidmsg = _("""Beep Beep! Level {level} raid egg reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
When this egg raid expires, there will be 15 minutes to update it into an open raid before it'll be deleted.
** **
Please type `!beep raid` if you need a refresher of Clembot commands! 
""").format(level=egg_level, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

        #         raidmsg = _("""Beep Beep! Level {level} raid egg reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
        #
        # Message **!interested** if you're interested in attending.
        # If you are interested in bringing more than one trainer/account, add in the number at the end of the commend.
        # Example: `!interested 5`
        #
        # Use **!list interested** to see the list of trainers who are interested.
        #
        # **!location** will show the current raid location.
        # **!location new <address>** will let you correct the raid address.
        # Sending a Google Maps link will also update the raid location.
        #
        # **!timer** will show how long until the egg catches into an open raid.
        # **!timerset** will let you correct the egg countdown time.
        #
        # Message **!raid <pokemon>** to update this channel into an open raid.
        # Message **!raid assume <pokemon>** to have the channel auto-update into an open raid.
        #
        # When this egg raid expires, there will be 15 minutes to update it into an open raid before it'll be deleted.""").format(level=egg_level, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)
        raidmessage = await Clembot.send_message(raid_channel, content=raidmsg, embed=raid_embed)

        server_dict[message.server.id]['raidchannel_dict'][raid_channel.id] = {
		'reportcity': message.channel.name, 
		'trainer_dict': {}, 
		'exp': fetch_current_time(message.channel.server.id) + timedelta(minutes=egg_timer),  # One hour from now
		'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
		'active': True, 
		'raidmessage': raidmessage.id, 
		'raidreport': raidreport.id, 
		'address': raid_details, 
		'type': 'egg', 
		'pokemon': '', 
		'egglevel': egg_level, 
		'suggested_start': False
		}

        if raidexp is not False:
            await _timerset(raid_channel, raidexp)
        else:
            await Clembot.send_message(raid_channel, content=_("Beep Beep! Hey {member}, if you can, set the time left until the egg hatches using **!timerset <minutes>** so others can check it with **!timer**.").format(member=message.author.mention))

        if len(raid_info['raid_eggs'][egg_level]['pokemon']) == 1:
            await _eggassume("assume "+ get_name(raid_info['raid_eggs'][egg_level]['pokemon'][0]), raid_channel)

        event_loop.create_task(expiry_check(raid_channel))


async def _eggassume(args, raid_channel):
    eggdetails = server_dict[raid_channel.server.id]['raidchannel_dict'][raid_channel.id]
    egglevel = eggdetails['egglevel']
    if config['allow_assume'][egglevel] == "False":
        await Clembot.send_message(raid_channel, _("Beep Beep! **!raid assume** is not allowed in this level egg."))
        return
    entered_raid = re.sub("[\@]", "", args.lstrip("assume").lstrip(" ").lower())
    if entered_raid not in pkmn_info['pokemon_list']:
        await Clembot.send_message(raid_channel, spellcheck(entered_raid))
        return
    else:
        if entered_raid not in pkmn_info['raid_list']:
            await Clembot.send_message(raid_channel, _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
            return
        else:
            if get_number(entered_raid) not in raid_info['raid_eggs'][egglevel]['pokemon']:
                await Clembot.send_message(raid_channel, _("Beep Beep! The Pokemon {pokemon} does not hatch from level {level} raid eggs!").format(pokemon=entered_raid.capitalize(), level=egglevel))
                return

    eggdetails['pokemon'] = entered_raid
    raidrole = discord.utils.get(raid_channel.server.roles, name=entered_raid)
    if raidrole is None:
        raidrole = await Clembot.create_role(server=raid_channel.server, name=entered_raid, hoist=False, mentionable=True)
        await asyncio.sleep(0.5)
    await Clembot.send_message(raid_channel, _("Beep Beep! This egg will be assumed to be {pokemon} when it hatches!").format(pokemon=raidrole.mention))
    server_dict[raid_channel.server.id]['raidchannel_dict'][raid_channel.id] = eggdetails
    return


async def _eggtoraid(entered_raid, channel):
    eggdetails = server_dict[channel.server.id]['raidchannel_dict'][channel.id]
    egglevel = eggdetails['egglevel']
    reportcity = eggdetails['reportcity']
    reportcitychannel = discord.utils.get(channel.server.channels, name=reportcity)
    manual_timer = eggdetails['manual_timer']
    trainer_dict = eggdetails['trainer_dict']
    egg_address = eggdetails['address']
    egg_report = await Clembot.get_message(reportcitychannel, eggdetails['raidreport'])
    raid_message = await Clembot.get_message(channel, eggdetails['raidmessage'])
    try:
        raid_messageauthor = raid_message.mentions[0]
    except IndexError:
        raid_messageauthor = "<@" + raid_message.raw_mentions[0] + ">"
        logger.info("Hatching Mention Failed - Trying alternative method: channel: {} (id: {}) - server: {} | Attempted mention: {}...".format(channel.name, channel.id, channel.server.name, raid_message.content[:125]))

    if eggdetails['egglevel'].isdigit():
        suggested_start = eggdetails['suggested_start']
        raidexp = eggdetails['exp'] + timedelta(minutes=raid_timer)
        hatchtype = "raid"
        raidreportcontent = _("Beep Beep! The egg has hatched into a {pokemon} raid! Details: {location_details}. Coordinate in {raid_channel}").format(pokemon=entered_raid.capitalize(), location_details=egg_address, raid_channel=channel.mention)

    if entered_raid not in pkmn_info['pokemon_list']:
        await Clembot.send_message(channel, spellcheck(entered_raid))
        return
    else:
        if entered_raid not in pkmn_info['raid_list']:
            await Clembot.send_message(channel, _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=entered_raid.capitalize()))
            return
        else:
            if get_number(entered_raid) not in raid_info['raid_eggs'][egglevel]['pokemon']:
                await Clembot.send_message(channel, _("Beep Beep! The Pokemon {pokemon} does not hatch from level {level} raid eggs!").format(pokemon=entered_raid.capitalize(), level=egglevel))
                return
    raid_channel_name = entered_raid + "-" + sanitize_channel_name(egg_address)
    oldembed = raid_message.embeds[0]
    raid_gmaps_link = oldembed['url']
    raid = discord.utils.get(channel.server.roles, name=entered_raid)
    if raid is None:
        raid = await Clembot.create_role(server=channel.server, name=entered_raid, hoist=False, mentionable=True)
        await asyncio.sleep(0.5)
    raid_number = pkmn_info['pokemon_list'].index(entered_raid) + 1
    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/pkmn/{0}_.png".format(str(raid_number).zfill(3))
    raid_img_url = get_pokemon_image_url(raid_number)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the raid!"), url=raid_gmaps_link, colour=channel.server.me.colour)
    raid_embed.add_field(name="**Details:**", value=_("{pokemon} ({pokemonnumber}) {type}").format(pokemon=entered_raid.capitalize(), pokemonnumber=str(raid_number), type="".join(get_type(channel.server, raid_number)), inline=True))
    raid_embed.add_field(name="**Weaknesses:**", value=_("{weakness_list}").format(weakness_list=weakness_to_str(channel.server, get_weaknesses(entered_raid))), inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=raid_messageauthor.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=raid_messageauthor, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    await Clembot.edit_channel(channel, name=raid_channel_name)
    raidmsg = _("""
Beep Beep! The egg reported by {member} in {citychannel} hatched into a {pokemon} raid! Details: {location_details}. Coordinate here!
This channel will be deleted five minutes after the timer expires.
** **
Please type `!beep raid` if you need a refresher of Clembot commands! 
""").format(member=raid_messageauthor.mention, citychannel=reportcitychannel.mention, pokemon=entered_raid.capitalize(), location_details=egg_address)

    #     raidmsg = _("""Beep Beep! The egg reported by {member} in {citychannel} hatched into a {pokemon} raid! Details: {location_details}. Coordinate here!
    #
    # To update your status, choose from the following commands:
    # **!interested, !coming, !here, !cancel**
    # If you are bringing more than one trainer/account, add the number of accounts total on your first status update.
    # Example: `!coming 5`
    #
    # To see the list of trainers who have given their status:
    # **!list interested, !list coming, !list here**
    # Alternatively **!list** by itself will show all of the above.
    #
    # **!location** will show the current raid location.
    # **!location new <address>** will let you correct the raid address.
    # Sending a Google Maps link will also update the raid location.
    #
    # **!timer** will show the current raid time.
    # **!timerset** will let you correct the raid countdown time.
    #
    # Message **!starting** when the raid is beginning to clear the raid's 'here' list.
    #
    # This channel will be deleted five minutes after the timer expires.""").format(member=raid_messageauthor.mention,
    #                                                                               citychannel=reportcitychannel.mention,
    #                                                                               pokemon=entered_raid.capitalize(),
    #                                                                               location_details=egg_address)

    try:
        raid_message = await Clembot.edit_message(raid_message, new_content=raidmsg, embed=raid_embed)
    except discord.errors.NotFound:
        pass
    try:
        egg_report = await Clembot.edit_message(egg_report, new_content=raidreportcontent, embed=raid_embed)
    except discord.errors.NotFound:
        pass

    server_dict[channel.server.id]['raidchannel_dict'][channel.id] = {
        'reportcity': reportcity,
        'trainer_dict': trainer_dict,
        'exp': raidexp,
        'manual_timer': manual_timer,
        'active': True,
        'raidmessage' : raid_message.id,
        'raidreport' : egg_report.id,
        'address': egg_address,
        'type': hatchtype,
        'pokemon': entered_raid,
        'egglevel': '0',
        'suggested_start': suggested_start
    }

    trainer_list = []
    trainer_dict = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['trainer_dict']
    for trainer in trainer_dict.keys():
        if trainer_dict[trainer]['status'] == 'maybe' or trainer_dict[trainer]['status'] == 'omw' or trainer_dict[trainer]['status'] == 'waiting':
            user = await Clembot.get_user_info(trainer)
            trainer_list.append(user.mention)

            # or len(raid_info['raid_eggs']['EX']['pokemon']) > 1
    try:
        if eggdetails['egglevel'].isdigit():
            await Clembot.send_message(channel, content=_("Beep Beep! Trainers {trainer_list}: The raid egg has just hatched into a {pokemon} raid!\nIf you couldn't before, you're now able to update your status with **!coming** or **!here**. If you've changed your plans, use **!cancel**.").format(trainer_list=", ".join(trainer_list), pokemon=raid.mention), embed=raid_embed)
    except Exception as error:
        print(error)
    event_loop.create_task(expiry_check(channel))

@Clembot.command(pass_context=True, hidden=True)
async def gymhelp(ctx):
    await Clembot.send_message(ctx.message.channel, _("Beep Beep! We've moved this command to `!beep gym`."))


@Clembot.command(pass_context=True, hidden=True)
async def gymlookup(ctx):
    """looks up gym information based on gym code.

    Usage: !gymlookup <prefix>
    Clembot will search and will list all gyms which start with the provided prefix."""

    args = ctx.message.content
    args_split = args.split(" ")
    del args_split[0]

    gym_code = args_split[0].upper()
    gym_message_output = ""
    try:

        city_state_list = get_city_list(ctx.message)

        for gym_info in gymutil.get_matching_gym_info(gym_code, city_state=city_state_list):
            if len(city_state_list) == 1:
                gym_message_output += ("{gym_code} \t- {gym_name}\n".format(gym_code=gym_info.get('gym_code'), gym_name=gym_info.get('gym_name')))
            else:
                gym_message_output += ("{gym_code} \t- {gym_name} ({city_state})\n".format(gym_code=gym_info.get('gym_code'), gym_name=gym_info.get('gym_name'), city_state=gym_info.get('city_state')))

        if gym_message_output:
            await Clembot.send_message(ctx.message.channel, content=gym_message_output)
        else:
            await Clembot.send_message(ctx.message.channel, content="Beep Beep...Hmmm, no matches found for {gym_code}".format(gym_code=gym_code))
    except Exception as error:
        await Clembot.send_message(ctx.message.channel, content=error)


@Clembot.command(pass_context=True, hidden=True)
async def status(ctx):

    try:

        raid_channel_dict = get_raid_channel_dict(ctx.message)

        if raid_channel_dict is None:
            await Clembot.send_message(ctx.message.channel, content="Beep Beep! This channel is not active anymore, feel free to tag any admin to clean it up!")
            return
        status_map = copy.deepcopy(server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id])
        exp = status_map.pop('exp')
        if exp:
            status_map['exp'] = exp.strftime("%Y-%m-%d %H:%M:%S")

        suggested_start = status_map.pop('suggested_start')
        if suggested_start:
            status_map['suggested_start'] = suggested_start.strftime("%Y-%m-%d %H:%M:%S")
        await Clembot.send_message(ctx.message.channel, content=json.dumps(status_map, indent=4, sort_keys=True))

    except Exception as error:
        await Clembot.send_message(ctx.message.channel, content=error)


@Clembot.command(pass_context=True, hidden=True, aliases=["g"])
async def gym(ctx):
    args = ctx.message.content
    args_split = args.split(" ")
    del args_split[0]

    gym_code = args_split[0].upper()
    gym_info = None

    if gym_code:
        gym_info = gymutil.get_gym_info(gym_code, city_state=get_city_list(ctx.message))

    if gym_info:
        gym_location = gym_info['gmap_link']
        gym_name = gym_info['gym_name']

        embed_title = _("Click here for direction to {gymname}!").format(gymname=gym_name)

        embed_desription = _("Gym Code : {gymcode}\nGym Name: {gymname}").format(gymcode=gym_code, gymname=gym_name)

        raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title), url=gym_location, description=embed_desription)

        embed_map_image_url = fetch_gmap_image_link(gym_info['lat_long'])
        raid_embed.set_image(url=embed_map_image_url)
        roster_message = "here are the gym details! "

        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! {member} {roster_message}").format(member=ctx.message.author.mention, roster_message=roster_message), embed=raid_embed)

        if check_raid_channel(ctx.message.channel):
            gym_location_update = await ask_confirmation(ctx.message, "Do you want to update this raid's location?", "Updating raid's location...", "Thank you", "Too late! try again!")
        elif check_raidparty_channel(ctx.message.channel):
            gym_location_update = True

        if gym_location_update:
            await process_map_link(ctx.message, gym_location)
    else:
        await Clembot.send_message(ctx.message.channel, content="Beep Beep...Hmmm, that's a gym-code I am not aware of! Type `!beep gym` for more details to use it correctly!")


def check_raid_channel(channel_id):
    channel = Clembot.get_channel(channel_id)
    type = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['type']

    if type == 'raid' or type == 'egg':
        return True
    return False


def check_raidparty_channel(channel_id):
    channel = Clembot.get_channel(channel_id)
    type = server_dict[channel.server.id]['raidchannel_dict'][channel.id]['type']

    if type == 'raidparty':
        return True
    return False


# ---------------------------------------------------------------------------------------

beepmsg = _("""
{member} **!beep** can be used with following options:
`!beep report` - to see commands to report raid or raidegg.
`!beep raid` - for raid specific commands.
`!beep gym` - for gym code related commands.
""")

beep_report = _("""
{member} here is how you can report a raid/raidegg ( the <> will be replaced with actual value):
** **
`!raid <pokemon> <location or gym-code>` to report a raid channel.
Example:
`!raid kyogre somewhere-in-my-city` or 
`!raid magikarp ABCD` - where ABCD is the gym code.
** **
`!raidegg <level> <loc or gym-code>` to report an egg.
Example:
`!raidegg 3 right-here`
`!raidegg 2 ABCD` - where ABCD is the gym code.
** **
Also, see `!beep gym` for gym-code commands!
""")

beep_raid = _("""
{member} to update your status, choose from the following commands:
** **
`!interested`, `!coming`, `!here` or `!cancel`
or alternatively use the shortcuts 
`!i`, `!c`, `!h` or `!x`
** **
If you are bringing more than one trainer/account, add the number of accounts total on your first status update.
Example: `!coming 5` or `!c 5`
** **
`!list` or `!l` will show the list of trainers who have given their status.
** **
*Sending a Google Maps link will update the raid location.*
**New**
`!gym gymcode` looks up gym location based upon gymcode, try `!beep gym` for more details!
** **
`!timer` will show the current raid time.
`!timerset <minutes>` will let you correct the raid countdown time.
** **
`!raid <pokemon>` to update egg channel into an open raid.
`!raid assume <pokemon>` to have the egg channel auto-update into an open raid.
** **
`!start HH:MM AM/PM` to suggest a start time.
`!starting` when the raid is beginning to clear the raid's 'here' list.""")

beep_raidparty = ("""
{member} here are the commands to work with raid party. 

`!roster` prints the current roster
`!where <location #>` will tell directions for location #
`!current` will tell you current location of the raid party
`!next` will tell you where the raid party is headed next.
** ** 
to update your status, choose from the following commands:
** **
`!interested`, `!coming`, `!here` or `!cancel`
or alternatively use the shortcuts 
`!i`, `!c`, `!h` or `!x`
** **

Also, see `!beep raidowner` for Raid Party management commands!
""")

beep_raidowner = ("""
{member} here are the commands to organize raid party:

`!raidparty <channel name>` creates a raid party channel
`!add <pokemon or egg> <gym-code or gym name or location>` adds a location into the roster
*Alternatively you can always paste a link and add a location into roster!*

`!move` moves raid party to the next location in roster

`!update <location#> <gym-code>` updates the gym code for location #
`!update <location#> <pokemon>` updates the pokemon for location #
`!update <location#> <link>` updates the link for location #
`!remove <location#>` removes specified location from roster
`!reset` cleans up the roster
** **
Also, see `!beep raidparty` for commands which raid party participants can use!
""")

beep_gym = ("""
{member} you can use following commands for gym lookup. 

`!gym <gym-code>` brings up the google maps location of the gym.

Note : **gym-code** is **first two letters** of **first two words** of gym name with some exceptions

`!gymlookup <code>` looks up all gyms starting with code. 
** **
 Example:
`!gymlookup A` will bring up all gym code and gym names starting with A
`!gymlookup BU` will bring up all gym code and gym names starting with BU
""")


# ---------------------------------------------------------------------------------------

@Clembot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def dump(ctx):

    try:

        raid_channel_dict = copy.deepcopy(server_dict[ctx.message.server.id])

        output = jsonpickle.encode(raid_channel_dict)
        parsed = json.loads(output)

        await Clembot.send_message(ctx.message.channel, content=json.dumps(parsed, indent=4, sort_keys=True))

    except Exception as error:
        await Clembot.send_message(ctx.message.channel, content=error)


@Clembot.command(pass_context=True, hidden=True, aliases=["b","help"])
async def beep(ctx):
    args = ctx.message.clean_content[len("!beep"):]
    args_split = args.split()

    if len(args_split) == 0:
        await Clembot.send_message(ctx.message.channel, content=beepmsg.format(member=ctx.message.author.mention))
    else:
        if args_split[0] == 'report':
            await Clembot.send_message(ctx.message.channel, content=beep_report.format(member=ctx.message.author.mention))
        elif args_split[0] == 'raid':
            await Clembot.send_message(ctx.message.channel, content=beep_raid.format(member=ctx.message.author.mention))
        elif args_split[0] == 'raidparty':
            await Clembot.send_message(ctx.message.channel, content=beep_raidparty.format(member=ctx.message.author.mention))
        elif args_split[0] == 'raidowner':
            await Clembot.send_message(ctx.message.channel, content=beep_raidowner.format(member=ctx.message.author.mention))
        elif args_split[0] == 'gym':
            await Clembot.send_message(ctx.message.channel, content=beep_gym.format(member=ctx.message.author.mention))


@Clembot.command(pass_context=True, hidden=True, aliases=["i", "maybe"])
@checks.activeraidchannel()
async def interested(ctx, *, count: str = None):
    """Indicate you are interested in the raid.

    Usage: !interested [message]
    Works only in raid channels. If message is omitted, assumes you are a group of 1.
    Otherwise, this command expects at least one word in your message to be a number,
    and will assume you are a group with that many people."""
    trainer_dict = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']
    if count:
        if count.isdigit():
            count = int(count)
            if count > 20 or count < 1:
                await Clembot.send_message(ctx.message.channel, _("Beep Beep! Currently the group size is limited between 1 to 20."))
                return
        else:
            await Clembot.send_message(ctx.message.channel, _("Beep Beep! I can't understand how many are in your group. Just say **!interested** if you're by yourself, or **!interested 5** for example if there are 5 in your group."))
            return
    else:
        if ctx.message.author.id in trainer_dict:
            count = trainer_dict[ctx.message.author.id]['count']
        else:
            count = 1

    await _maybe(ctx.message, count)


@Clembot.command(pass_context=True, hidden=True, aliases=["c"])
@checks.activeraidchannel()
async def coming(ctx, *, count: str = None):
    """Indicate you are on the way to a raid.

    Usage: !coming [message]
    Works only in raid channels. If message is omitted, checks for previous !maybe
    command and takes the count from that. If it finds none, assumes you are a group
    of 1.
    Otherwise, this command expects at least one word in your message to be a number,
    and will assume you are a group with that many people."""
    #    try:
    #        if server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['type'] == "egg":
    #           if server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['pokemon'] == "":
    #                await Clembot.send_message(ctx.message.channel, _("Beep Beep! Please wait until the raid egg has hatched before announcing you're coming or present."))
    #                return
    #    except:
    #        pass

    trainer_dict = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']

    if count:
        if count.isdigit():
            count = int(count)
            if count > 20 or count < 1:
                await Clembot.send_message(ctx.message.channel, _("Beep Beep! Currently the group size is limited between 1 to 20."))
                return
        else:
            await Clembot.send_message(ctx.message.channel, _("Beep Beep! I can't understand how many are in your group. Just say **!coming** if you're by yourself, or **!coming 5** for example if there are 5 in your group."))
            return
    else:
        if ctx.message.author.id in trainer_dict:
            count = trainer_dict[ctx.message.author.id]['count']
        else:
            count = 1

    await _coming(ctx.message, count)


@Clembot.command(pass_context=True, hidden=True, aliases=["h"])
@checks.activeraidchannel()
async def here(ctx, *, count: str = None):
    """Indicate you have arrived at the raid.

    Usage: !here [message]
    Works only in raid channels. If message is omitted, and
    you have previously issued !coming, then preserves the count
    from that command. Otherwise, assumes you are a group of 1.
    Otherwise, this command expects at least one word in your message to be a number,
    and will assume you are a group with that many people."""
    # try:
    #     if server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['type'] == "egg":
    #         if server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['pokemon'] == "":
    #             await Clembot.send_message(ctx.message.channel, _("Beep Beep! Please wait until the raid egg has hatched before announcing you're coming or present."))
    #             return
    # except:
    #     pass

    trainer_dict = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']

    if count:
        if count.isdigit():
            count = int(count)
            if count > 20 or count < 1:
                await Clembot.send_message(ctx.message.channel, _("Beep Beep! Currently the group size is limited between 1 to 20."))
                return
        else:
            await Clembot.send_message(ctx.message.channel, _("Beep Beep! I can't understand how many are in your group. Just say **!here** if you're by yourself, or **!coming 5** for example if there are 5 in your group."))
            return
    else:
        if ctx.message.author.id in trainer_dict:
            count = trainer_dict[ctx.message.author.id]['count']
        else:
            count = 1

    await _here(ctx.message, count)


@Clembot.command(pass_context=True, hidden=True, aliases=["x"])
@checks.activeraidchannel()
async def cancel(ctx):
    """Indicate you are no longer interested in a raid.

    Usage: !cancel
    Works only in raid channels. Removes you and your party
    from the list of trainers who are "otw" or "here"."""
    await _cancel(ctx.message)


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def starting(ctx):
    """Signal that a raid is starting.

    Usage: !starting
    Works only in raid channels. Sends a message and clears the waiting list. Users who are waiting
    for a second group must reannounce with the :here: emoji or !here."""

    ctx_startinglist = []
    id_startinglist = []

    trainer_dict = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']

    # Add all waiting trainers to the starting list
    for trainer in trainer_dict:
        if trainer_dict[trainer]['status'] == "waiting":
            user = await Clembot.get_user_info(trainer)
            ctx_startinglist.append(user.mention)
            id_startinglist.append(trainer)

    # Go back and delete the trainers from the waiting list
    for trainer in id_startinglist:
        del trainer_dict[trainer]
    server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'] = trainer_dict

    starting_str = _("Beep Beep! The group that was waiting is starting the raid! Trainers {trainer_list}, please respond with {here_emoji} or **!here** if you are waiting for another group!").format(trainer_list=", ".join(ctx_startinglist), here_emoji=parse_emoji(ctx.message.server, config['here_id']))
    if len(ctx_startinglist) == 0:
        starting_str = _("Beep Beep! How can you start when there's no one waiting at this raid!?")
    await Clembot.send_message(ctx.message.channel, starting_str)


@Clembot.group(pass_context=True, hidden=True, aliases=["lists"])
@checks.cityraidchannel()
@checks.raidset()
async def list(ctx):
    """Lists all raid info for the current channel.

    Usage: !list
    Works only in raid or city channels. Calls the interested, waiting, and here lists. Also prints
    the raid timer. In city channels, lists all active raids."""
    try:
        if ctx.invoked_subcommand is None:
            listmsg = ""
            server = ctx.message.server
            channel = ctx.message.channel
            exp = None
            if checks.check_citychannel(ctx):
                activeraidnum = 0
                cty = channel.name
                rc_d = server_dict[server.id]['raidchannel_dict']

                raid_dict = {}
                egg_dict = {}
                exraid_list = []
                for r in rc_d:
                    if rc_d[r]['reportcity'] == cty and rc_d[r]['active'] and discord.utils.get(server.channels, id=r):
                        exp = rc_d[r]['exp']
                        type = rc_d[r]['type']
                        level = rc_d[r]['egglevel']
                        if type == 'egg' and level.isdigit():
                            egg_dict[r] = exp
                        elif type == 'exraid' or level == "EX":
                            exraid_list.append(r)
                        elif type == 'raidparty':
                            activeraidnum -= 1
                            #ignore raid party
                        else:
                            raid_dict[r] = exp

                        activeraidnum += 1

                def list_output(r):
                    rchan = Clembot.get_channel(r)
                    # now = datetime.datetime.utcnow() + datetime.timedelta(hours=server_dict[server.id]['offset'])
                    # end = now + datetime.timedelta(seconds=rc_d[r]['exp']-time.time())
                    # now = fetch_current_time(rchan.server.id)
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
                    if rc_d[r]['egglevel'].isdigit() and int(rc_d[r]['egglevel']) > 0:
                        expirytext = " - Hatches: {expiry}{is_assumed}".format(expiry=end.strftime("%I:%M %p (%H:%M)"), is_assumed=assumed_str)
                    elif rc_d[r]['egglevel'] == "EX" or rc_d[r]['type'] == "exraid":
                        expirytext = " - Hatches: {expiry}{is_assumed}".format(expiry=end.strftime("%B %d at %I:%M %p (%H:%M)"),is_assumed=assumed_str)
                    else:
                        expirytext = " - Expiry: {expiry}{is_assumed}".format(expiry=end.strftime("%I:%M %p (%H:%M)"), is_assumed=assumed_str)
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
                        await Clembot.send_message(channel, _("Beep Beep! No active raids! Report one with **!raid <name> <location>**."))
                        return
                    else:
                        await Clembot.send_message(channel, listmsg)
                    return
                except Exception as error:
                    print(error)

            if checks.check_raidpartychannel(ctx):
                if checks.check_raidactive(ctx):
                    rc_d = server_dict[server.id]['raidchannel_dict'][channel.id]

                    await _generate_list_embed(ctx.message)

                    return

            if checks.check_raidchannel(ctx):
                if checks.check_raidactive(ctx):
                    rc_d = server_dict[server.id]['raidchannel_dict'][channel.id]
                    embed_msg = ""

                    embed = discord.Embed(description=embed_msg, colour=discord.Colour.gold())

                    raid_time_label = "**Raid Expires At**"
                    if rc_d['type'] == 'egg' and rc_d['egglevel'].isdigit():
                        raid_time_label = "**Egg Hatches At**"
                    raid_time_value = fetch_channel_expire_time(ctx.message.channel.id).strftime("%I:%M %p (%H:%M)")

                    start_time = fetch_channel_start_time(ctx.message.channel.id)
                    start_time_label = "None"
                    if start_time:
                        raid_time_label = raid_time_label + " **/ Suggested Start Time**"
                        raid_time_value = raid_time_value + " / " + start_time.strftime("%I:%M %p (%H:%M)")

                    embed.add_field(name=raid_time_label, value=raid_time_value)

                    embed.add_field(name="**Interested / On the way / At the raid**", value="{maybe} / {omw} / {waiting}".format(waiting=get_count_from_channel(ctx.message, "waiting"), omw=get_count_from_channel(ctx.message, "omw"), maybe=get_count_from_channel(ctx.message, "maybe")), inline=True)

                    maybe = get_names_from_channel(ctx.message, "maybe")
                    if maybe:
                        embed.add_field(name="**Interested**", value=maybe)

                    omw = get_names_from_channel(ctx.message, "omw")
                    if omw:
                        embed.add_field(name="**On the way**", value=omw)

                    waiting = get_names_from_channel(ctx.message, "waiting")
                    if waiting:
                        embed.add_field(name="**At the raid**",value=waiting)

                    await Clembot.send_message(channel, embed=embed)

                    listmsg += await _interest(ctx)
                    listmsg += "\n" + await _otw(ctx)
                    listmsg += "\n" + await _waiting(ctx)
                    if rc_d['type'] != 'exraid':
                        listmsg += "\n" + await print_raid_timer(channel.id)
                    listmsg += "\n" + await print_start_time(channel.id)


    except Exception as error:
        print(error)
    return



async def _generate_list_embed(message):
    embed_msg = ""

    embed = discord.Embed(description=embed_msg, colour=discord.Colour.gold())

    embed.add_field(name="**Interested / On the way / At the raid**", value="{maybe} / {omw} / {waiting}".format(waiting=get_count_from_channel(message, "waiting"), omw=get_count_from_channel(message, "omw"), maybe=get_count_from_channel(message, "maybe")), inline=True)

    maybe = get_names_from_channel(message, "maybe")
    if maybe:
        embed.add_field(name="**Interested**", value=maybe)

    omw = get_names_from_channel(message, "omw")
    if omw:
        embed.add_field(name="**On the way**", value=omw)

    waiting = get_names_from_channel(message, "waiting")
    if waiting:
        embed.add_field(name="**At the raid**", value=waiting)

    await Clembot.send_message(message.channel, embed=embed)


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def omw(ctx):
    await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! Hey {member}, I don't know if you meant **!coming** to say that you are coming or **!list coming** to see the other trainers on their way").format(member=ctx.message.author.mention))


@list.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def interested(ctx):
    """Lists the number and users who are interested in the raid.

    Usage: !list interested
    Works only in raid channels."""
    listmsg = await _interest(ctx)
    await Clembot.send_message(ctx.message.channel, listmsg)


@list.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def coming(ctx):
    """Lists the number and users who are coming to a raid.

    Usage: !list coming
    Works only in raid channels."""
    listmsg = await _otw(ctx)
    await Clembot.send_message(ctx.message.channel, listmsg)


@list.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def here(ctx):
    """List the number and users who are present at a raid.

    Usage: !list here
    Works only in raid channels."""
    listmsg = await _waiting(ctx)
    await Clembot.send_message(ctx.message.channel, listmsg)


@Clembot.command(pass_context=True, hidden=True)
@commands.has_permissions(manage_server=True)
@checks.raidchannel()
async def clearstatus(ctx):
    """Clears raid channel status lists.

    Usage: !clearstatus
    Only usable by admins."""
    try:
        server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'] = {}
        await Clembot.send_message(ctx.message.channel, "Beep Beep! Raid status lists have been cleared!")
    except KeyError:
        pass


async def ask_confirmation(message, rusure_message, yes_message, no_message, timed_out_message):
    author = message.author
    channel = message.channel

    reaction_list = ['✅', '❎']
    # reaction_list = ['❔', '✅', '❎']

    rusure = await Clembot.send_message(channel, _("Beep Beep! {message}".format(message=rusure_message)))
    await Clembot.add_reaction(rusure, "✅")  # checkmark
    await Clembot.add_reaction(rusure, "❎")  # cross

    def check(react, user):
        if user.id != author.id:
            return False
        return True

    res = await Clembot.wait_for_reaction(reaction_list, message=rusure, check=check, timeout=60)

    if res is not None:
        if res.reaction.emoji == "❎":
            await Clembot.delete_message(rusure)
            confirmation = await Clembot.send_message(channel, _("Beep Beep! {message}".format(message=no_message)))
            await asyncio.sleep(3)
            await Clembot.delete_message(confirmation)
            return False
        elif res.reaction.emoji == "✅":
            await Clembot.delete_message(rusure)
            confirmation = await Clembot.send_message(channel, _("Beep Beep! {message}".format(message=yes_message)))
            await asyncio.sleep(3)
            await Clembot.delete_message(confirmation)
            return True
    else:
        await Clembot.delete_message(rusure)
        confirmation = await Clembot.send_message(channel, _("Beep Beep! {message}".format(message=timed_out_message)))
        await asyncio.sleep(3)
        await Clembot.delete_message(confirmation)
        return False


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def duplicate(ctx):
    """A command to report a raid channel as a duplicate.

    Usage: !duplicate
    Works only in raid channels. When three users report a channel as a duplicate,
    Clembot deactivates the channel and marks it for deletion."""
    channel = ctx.message.channel
    author = ctx.message.author
    server = ctx.message.server
    rc_d = server_dict[server.id]['raidchannel_dict'][channel.id]
    t_dict = rc_d['trainer_dict']
    can_manage = channel.permissions_for(author).manage_channels

    if can_manage:
        dupecount = 2
        rc_d['duplicate'] = dupecount
    else:
        if author.id in t_dict:
            try:
                if t_dict[author.id]['dupereporter']:
                    dupeauthmsg = await Clembot.send_message(channel, _("Beep Beep! You've already made a duplicate report for this raid!"))
                    await asyncio.sleep(10)
                    await Clembot.delete_message(dupeauthmsg)
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
        rusure = await Clembot.send_message(channel, _("Beep Beep! Are you sure you wish to remove this raid?"))
        await asyncio.sleep(0.25)
        await Clembot.add_reaction(rusure, "✅")  # checkmark
        await asyncio.sleep(0.25)
        await Clembot.add_reaction(rusure, "❎")  # cross

        def check(react, user):
            if user.id != author.id:
                return False
            return True

        res = await Clembot.wait_for_reaction(['✅', '❎'], message=rusure, check=check, timeout=60)

        if res is not None:
            if res.reaction.emoji == "❎":
                await Clembot.delete_message(rusure)
                confirmation = await Clembot.send_message(channel, _("Duplicate Report cancelled."))
                logger.info("Duplicate Report - Cancelled - " + channel.name + " - Report by " + author.name)
                dupecount = 2
                server_dict[server.id]['raidchannel_dict'][channel.id]['duplicate'] = dupecount
                await asyncio.sleep(10)
                await Clembot.delete_message(confirmation)
                return
            elif res.reaction.emoji == "✅":
                await Clembot.delete_message(rusure)
                await Clembot.send_message(channel, "Duplicate Confirmed")
                logger.info("Duplicate Report - Channel Expired - " + channel.name + " - Last Report by " + author.name)
                await expire_channel(channel)
                return
        else:
            await Clembot.delete_message(rusure)
            confirmation = await Clembot.send_message(channel, _("Duplicate Report Timed Out."))
            logger.info("Duplicate Report - Timeout - " + channel.name + " - Report by " + author.name)
            dupecount = 2
            server_dict[server.id]['raidchannel_dict'][channel.id]['duplicate'] = dupecount
            await asyncio.sleep(10)
            await Clembot.delete_message(confirmation)
    else:
        rc_d['duplicate'] = dupecount
        confirmation = await Clembot.send_message(channel, _("Duplicate report #{duplicate_report_count} received.").format(duplicate_report_count=str(dupecount)))
        logger.info("Duplicate Report - " + channel.name + " - Report #" + str(dupecount) + "- Report by " + author.name)
        return


@Clembot.group(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def location(ctx):
    """Get raid location.

    Usage: !location
    Works only in raid channels. Gives the raid location link."""
    if ctx.invoked_subcommand is None:
        message = ctx.message
        server = message.server
        channel = message.channel
        rc_d = server_dict[server.id]['raidchannel_dict']
        raidmsg = rc_d[channel.id]['raidmessage']
        location = rc_d[channel.id]['address']
        report_city = rc_d[channel.id]['reportcity']
        report_channel = discord.utils.get(server.channels, name=report_city)
        oldembed = raidmsg.embeds[0]
        locurl = oldembed['url']
        newembed = discord.Embed(title=oldembed['title'], url=locurl, description=oldembed['description'], colour=server.me.colour)
        newembed.set_thumbnail(url=oldembed['thumbnail']['url'])
        locationmsg = await Clembot.send_message(channel, content=_("Beep Beep! Here's the current location for the raid!\nDetails:{location}").format(location=location), embed=newembed)
        await asyncio.sleep(60)
        await Clembot.delete_message(locationmsg)


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
        await Clembot.send_message(message.channel, _("Beep Beep! We're missing the new location details! Usage: **!location new <new address>**"))
        return
    else:
        report_city = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['reportcity']
        report_channel = discord.utils.get(message.server.channels, name=report_city)

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

        server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['address'] = details
        oldraidmsg = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidmessage']
        oldreportmsg = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidreport']
        oldembed = oldraidmsg.embeds[0]
        newembed = discord.Embed(title=oldembed['title'], url=newloc, colour=message.server.me.colour)
        newembed.add_field(name=oldembed['fields'][0]['name'], value=oldembed['fields'][0]['value'], inline=True)
        newembed.add_field(name=oldembed['fields'][1]['name'], value=oldembed['fields'][1]['value'], inline=True)
        newembed.set_footer(text=oldembed['footer']['text'], icon_url=oldembed['footer']['icon_url'])
        newembed.set_thumbnail(url=oldembed['thumbnail']['url'])
        newraidmsg = await Clembot.edit_message(oldraidmsg, new_content=oldraidmsg.content, embed=newembed)
        newreportmsg = await Clembot.edit_message(oldreportmsg, new_content=oldreportmsg.content, embed=newembed)
        server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidmessage'] = newraidmsg
        server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['raidreport'] = newreportmsg
        otw_list = []
        trainer_dict = server_dict[message.server.id]['raidchannel_dict'][message.channel.id]['trainer_dict']
        for trainer in trainer_dict.keys():
            user = await Clembot.get_user_info(trainer)
            if trainer_dict[user.id]['status'] == 'omw':
                otw_list.append(user.mention)
        await Clembot.send_message(message.channel, content=_("Beep Beep! Someone has suggested a different location for the raid! Trainers {trainer_list}: make sure you are headed to the right place!").format(trainer_list=", ".join(otw_list)), embed=newembed)
        return


async def _interest(ctx):
    ctx_maybecount = 0

    now = fetch_current_time(ctx.message.channel.server.id)
    # Grab all trainers who are maybe and sum
    # up their counts
    trainer_dict = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']
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
        if now.time() >= datetime.time(5,0) and now.time() <= datetime.time(21,0):
            maybe_exstr = _(" including {trainer_list} and the people with them! Let them know if there is a group forming").format(trainer_list=", ".join(maybe_list))
        else:
            maybe_exstr = _(" including {trainer_list} and the people with them! Let them know if there is a group forming").format(trainer_list=", ".join(maybe_list))
    listmsg = (_("Beep Beep! {trainer_count} interested{including_string}!").format(trainer_count=str(ctx_maybecount), including_string=maybe_exstr))

    return listmsg


async def _otw(ctx):
    ctx_omwcount = 0
    now = fetch_current_time(ctx.message.channel.server.id)

    # Grab all trainers who are :omw: and sum
    # up their counts
    trainer_dict = copy.deepcopy(server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict'])
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
    now = fetch_current_time(ctx.message.channel.server.id)

    # Grab all trainers who are :here: and sum
    # up their counts
    trainer_dict = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['trainer_dict']
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
            if now.time() >= datetime.time(5,0) and now.time() <= datetime.time(21,0):
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
    await Clembot.send_message(ctx.message.channel, _("Beep Beep! We've moved this command to **!list interested**."))


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def otw(ctx):
    await Clembot.send_message(ctx.message.channel, _("Beep Beep! We've moved this command to **!list coming**."))


@Clembot.command(pass_context=True, hidden=True)
@checks.activeraidchannel()
async def waiting(ctx):
    await Clembot.send_message(ctx.message.channel, _("Beep Beep! We've moved this command to **!list here**."))


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def update(ctx):
    try:
        roster = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
        if len(roster) <= 0:
            await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
            return

        args = ctx.message.clean_content[len("!update"):]
        args_split = args.split()

        location_number = 0
        if len(args_split) > 0:
            if args_split[0].isdigit():
                location_number = int(args_split[0])

        if location_number == 0:
            await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! I couldn't understand the location #."))
            return

        del args_split[0]

        roster_loc = None
        for roster_loc_at in roster:
            if roster_loc_at['index'] == location_number:
                roster_loc = roster_loc_at
                break

        if roster_loc is None:
            await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! Location {location} doesn't exist on the roster!".format(location=emojify_numbers(location_number))))
            return

        # if len(args_split) > 1:
        #     await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! That's too much to update... use `!update <location#> <pokemon-name or gym-code or google map link>`"))
        #     return

        arg = args_split[0]
        gym_info = gymutil.get_gym_info(arg, city_state=get_city_list(ctx.message))

        if gym_info:
            roster_loc['gym_name'] = gym_info['gym_name']
            roster_loc['gym_code'] = gym_info['gym_code']
            roster_loc['lat_long'] = gym_info['lat_long']
            roster_loc['gmap_link'] = gym_info['gmap_link']
            roster_loc['eta'] = None
            args_split.remove(arg)

        elif arg in pkmn_info['pokemon_list']:
            roster_loc['pokemon'] = arg
            args_split.remove(arg)
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
                    await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! I am not sure what to update;... use `!update <location#> <pokemon-name | gym-code | google map link | eta>` "))
                    return

        await print_roster_with_highlight(ctx.message, location_number, "Beep Beep! Location {location} has been updated.".format(location=emojify_numbers(location_number)))
        return

    except Exception as error:
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))


@Clembot.command(pass_context=True, hidden=True)
async def check(ctx):
    try :
        message = ctx.message
        await Clembot.send_message(message.channel,"<:water:394992044562448394>")
    except Exception as error:
        print(error)

@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def add(ctx):
    try:
        roster = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
        first_index = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster_index']
        if first_index is None:
            first_index = 0

        args = ctx.message.clean_content[4:]
        args_split = args.split(" ")
        del args_split[0]



        roster_loc_mon = args_split[0].lower()
        if roster_loc_mon != "egg":
            if roster_loc_mon not in pkmn_info['pokemon_list']:
                await Clembot.send_message(ctx.message.channel, spellcheck(roster_loc_mon))
                return
            if roster_loc_mon not in pkmn_info['raid_list'] and roster_loc_mon in pkmn_info['pokemon_list']:
                await Clembot.send_message(ctx.message.channel, _("Beep Beep! The Pokemon {pokemon} does not appear in raids!").format(pokemon=roster_loc_mon.capitalize()))
                return
        del args_split[0]

        roster_loc_gym_code = args_split[0]
        gym_info = gymutil.get_gym_info(roster_loc_gym_code, city_state=get_city_list(ctx.message))

        if gym_info:
            del args_split[0]

        eta = None
        if len(args_split) > 0 :
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
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))


async def _add(message, gmap_link):
    author = message.author
    server = message.server
    channel = message.channel

    if author.id == "364905300244824065":
        return

    add_location = await ask_confirmation(message, "Do you want to add this location to roster?", "Location will be added to roster", "Clembot will ignore the location", "request timed out")

    if add_location == False:
        return

    try:
        roster = server_dict[server.id]['raidchannel_dict'][channel.id]['roster']
        first_index = server_dict[server.id]['raidchannel_dict'][channel.id]['roster_index']
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
        await Clembot.send_message(message.channel, content=_("Beep Beep! Error : {error} {error_details}").format(error=error, error_details=str(error)))
    return


async def reindex_roster(roster):
    if len(roster) > 0:
        current_index = roster[0]['index']

        for roster_loc in roster:
            roster_loc['index'] = current_index
            current_index = current_index + 1
    return roster


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def remove(ctx):
    roster = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

    if len(roster) < 1:
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
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
            # server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster_index'] = first_roster_index
            await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! {member}, {roster_message}").format(member=ctx.message.author.mention, roster_message=roster_message))
        else:
            await reindex_roster(roster)
            await print_roster(ctx.message, roster_message)
    else:
        roster_message = _("Location {location_number} does not exist on roster!").format(location_number=emojify_numbers(location_number))
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! {member}, {roster_message}").format(member=ctx.message.author.mention, roster_message=roster_message))

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def move(ctx):
    roster = server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']
    if len(roster) < 1:
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return

    # if all roster items are visited already, keep the number for later usage!
    first_roster_index = roster[0]['index']

    del roster[0]

    if len(roster) == 0:
        server_dict[ctx.message.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster_index'] = first_roster_index
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! {member}, all the locations on this roster are done!").format(member=ctx.message.author.mention))
    else:
        await print_roster(ctx.message, _("raid party is moving to the next location in the roster!"))

    return


def get_roster_with_highlight(roster, highlight_roster_loc):
    roster_msg = ""

    try:
        for roster_loc in roster:
            if highlight_roster_loc == roster_loc['index']:
                marker = "**"
            else:
                marker = ""
            eta = roster_loc.get('eta',"")
            if eta:
                eta = " [{eta}]".format(eta=eta)
            else:
                eta = ""
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
    await Clembot.send_message(ctx.message.channel, _("Beep Beep! We've moved this command to `!beep raidparty`."))
    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def current(ctx):
    roster = server_dict[ctx.message.channel.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

    if len(roster) < 1:
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return
    roster_index = roster[0]['index']
    roster_message = _("Raid Party is at location {location_number} on the roster!").format(location_number=emojify_numbers(roster_index))

    await print_roster_with_highlight(ctx.message, roster_index, roster_message)
    return


@Clembot.command(pass_context=True, hidden=True)
async def makeitraidparty(ctx):
    message = ctx.message

    server_dict[message.server.id]['raidchannel_dict'][message.channel.id] = {
        'reportcity': message.channel.name,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': None,
        'type': 'raidparty',
        'pokemon': None,
        'egglevel': '0',
        'suggested_start': False,
        'roster': [],
        'roster_index': None
    }

    await Clembot.send_message(message.channel, content=_("Beep Beep! It's a raid party channel now!"))

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def reset(ctx):
    message = ctx.message

    server_dict[message.server.id]['raidchannel_dict'][message.channel.id] = {
        'reportcity': message.channel.name,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': None,
        'type': 'raidparty',
        'pokemon': None,
        'egglevel': '0',
        'suggested_start': False,
        'roster': [],
        'roster_index': None
    }

    await Clembot.send_message(message.channel, content=_("Beep Beep! The roster has been cleared!"))

    return


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def where(ctx):
    try:
        roster = server_dict[ctx.message.channel.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

        if len(roster) < 1:
            await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
            return

        args = ctx.message.clean_content[len("!remove"):]
        args_split = args.split()

        location_number = 0
        if len(args_split) > 0:
            if args_split[0].isdigit():
                location_number = int(args_split[0])
        else:
            await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! Give more details! Usage: `!where <location #>`"))
            return

        for roster_loc_at in roster:
            if roster_loc_at['index'] == location_number:
                roster_loc = roster_loc_at

                await print_roster_with_highlight(ctx.message, roster_loc['index'], "Location {location} - {gym} - {pokemon}".format(location=emojify_numbers(roster_loc['index']), pokemon=roster_loc['pokemon'].capitalize(), gym=roster_loc['gym_name']))
                return
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have location {location_number}.".format(location_number=emojify_numbers(location_number))))
        return

    except Exception as error:
        print(error)


@Clembot.command(pass_context=True, hidden=True)
@checks.raidpartychannel()
async def next(ctx):
    roster = server_dict[ctx.message.channel.server.id]['raidchannel_dict'][ctx.message.channel.id]['roster']

    if len(roster) < 1:
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return
    roster_index = roster[0]['index']

    if len(roster) < 2:
        status_message = _("Raid party is at **{current}/{total}** location. Next location doesn't exist on roster!").format(current=roster_index, total=roster_index)
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! {status_message}").format(status_message=status_message))
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
        roster = server_dict[message.channel.server.id]['raidchannel_dict'][message.channel.id]['roster']

        if highlight_roster_loc:
            roster_index = highlight_roster_loc
        else:
            if len(roster) < 1:
                await Clembot.send_message(message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
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
        raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.name), icon_url=message.author.avatar_url)
        if lat_long:
            embed_map_image_url = fetch_gmap_image_link(lat_long)
            raid_embed.set_image(url=embed_map_image_url)

        await Clembot.send_message(message.channel, content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention, roster_message=roster_message), embed=raid_embed)

    except Exception as error:
        print(error)
    return


async def print_roster(message, roster_message=None):
    roster = server_dict[message.channel.server.id]['raidchannel_dict'][message.channel.id]['roster']

    if len(roster) < 1:
        await Clembot.send_message(message.channel, content=_("Beep Beep! The roster doesn't have any location(s)! Type `!beep raidparty` to see how you can manage raid party!"))
        return

    roster_index = roster[0]['index']

    roster_msg = get_roster_with_highlight(roster, roster_index)

    raid_party_image_url = "https://cdn.discordapp.com/attachments/354694475089707039/371000826522632192/15085243648140.png"

    raid_img_url = raid_party_image_url
    # "http://floatzel.net/pokemon/black-white/sprites/images/{0}.png".format(str(raid_number))

    if roster_index:
        current_roster = roster[0]
        embed_title = _("Raid Party is at Location#{index}. Click here for directions!").format(index=emojify_numbers(roster_index))
        raid_party_image_url = current_roster['gmap_link']
    else:
        embed_title = "Raid Party has not started yet!!"
        raid_party_image_url = ""

    raid_embed = discord.Embed(title=_("Beep Beep! {embed_title}").format(embed_title=embed_title), url=raid_party_image_url, description=roster_msg)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.name), icon_url=message.author.avatar_url)
    raid_embed.set_thumbnail(url=raid_img_url)

    if roster_message:
        await Clembot.send_message(message.channel, content=_("Beep Beep! {member} {roster_message}").format(member=message.author.mention, roster_message=roster_message), embed=raid_embed)
    else:
        await Clembot.send_message(message.channel, content=_("Beep Beep! {member} here is the raid party roster: ").format(member=message.author.mention), embed=raid_embed)

    return


@Clembot.command(pass_context=True, hidden=True)
async def reloadconfig(ctx):
    try:
        load_config()
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! configuration reloaded!"))
    except Exception as error:
        await Clembot.send_message(ctx.message.channel, content=_("Beep Beep! Error : {error}").format(error=str(error)))
    return


@Clembot.command(pass_context=True, hidden=True)
@checks.citychannel()
async def invite(ctx):
    """Join an EXraid by showing your invite.

    Usage: !invite [image attachment]
    If the image isn't added at the same time as the command, Clembot will wait 30 seconds for a followup message containing the image."""
    if ctx.message.attachments:
        await _invite(ctx)
    else:
        wait_msg = await Clembot.send_message(ctx.message.channel, _("Beep Beep! I'll wait for you to send your pass!"))

        def check(msg):
            if msg.channel == ctx.message.channel and ctx.message.author.id == msg.author.id:
                if msg.attachments:
                    return True

        invitemsg = await Clembot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
        if invitemsg is not None:
            ctx.message = invitemsg
            await _invite(ctx)
            return
        else:
            await Clembot.delete_message(wait_msg)
            await Clembot.send_message(ctx.message.channel, "Beep Beep! You took too long to show me a screenshot of your invite! Retry when you're ready.")
            return


async def _invite(ctx):
    if 'https://cdn.discordapp.com' in ctx.message.attachments[0]['url']:
        if 'png' in ctx.message.attachments[0]['url'].lower() or 'jpg' in ctx.message.attachments[0]['url'].lower():
            fd = requests.get(ctx.message.attachments[0]['url'])
            img = Image.open(BytesIO(fd.content))
            width, height = img.size
            new_height = 3500
            new_width = int(new_height * width / height)
            img = img.resize((new_width, new_height), Image.BICUBIC)
            img = img.filter(ImageFilter.EDGE_ENHANCE)
            enh = ImageEnhance.Brightness(img)
            img = enh.enhance(0.4)
            enh = ImageEnhance.Contrast(img)
            img = enh.enhance(4)
            txt = pytesseract.image_to_string(img, config=tesseract_config)
            if 'EX Raid Battle' in txt or "This is a reward" in txt or "Please visit the Gym" in txt:
                exraidlist = ''
                exraid_dict = {}
                exraidcount = 0
                for channel in server_dict[ctx.message.server.id]['raidchannel_dict']:
                    if not discord.utils.get(ctx.message.server.channels, id=channel.id):
                        continue
                    if server_dict[ctx.message.server.id]['raidchannel_dict'][channel.id]['egglevel'] == 'EX' or server_dict[ctx.message.server.id]['raidchannel_dict'][channel.id]['type'] == 'exraid':
                        if channel.mention != '#deleted-channel':
                            exraidcount += 1
                            exraidlist += '\n' + str(exraidcount) + '.   ' + channel.mention
                            exraid_dict[str(exraidcount)] = channel
                if exraidcount > 0:
                    await Clembot.send_message(ctx.message.channel, "Beep Beep! {0}, it looks like you've got an EX Raid invitation! The following {1} EX Raids have been reported: \n {2} \n Reply with the number of the EX Raid you have been invited to. If none of them match your invite, type 'N' and report it with **!exraid**".format(ctx.message.author.mention, str(exraidcount), exraidlist))
                    reply = await Clembot.wait_for_message(author=ctx.message.author)
                    if reply.content.lower() == 'n':
                        await Clembot.send_message(ctx.message.channel, "Beep Beep! Be sure to report your EX Raid with **!exraid**!")
                    elif not reply.content.isdigit() or int(reply.content) > exraidcount:
                        await Clembot.send_message(ctx.message.channel, "Beep Beep! I couldn't tell which EX Raid you meant! Try the **!invite** command again, and make sure you respond with the number of the channel that matches!")
                    elif int(reply.content) <= exraidcount and int(reply.content) > 0:
                        overwrite = discord.PermissionOverwrite()
                        overwrite.send_messages = True
                        overwrite.read_messages = True
                        exraid_channel = exraid_dict[str(int(reply.content))]
                        await Clembot.edit_channel_permissions(exraid_channel, ctx.message.author, overwrite)
                        await Clembot.send_message(ctx.message.channel, "Beep Beep! Alright {0}, you can now send messages in {1}! Make sure you let the trainers in there know if you can make it to the EX Raid!".format(ctx.message.author.mention, exraid_channel.mention))
                    else:
                        await Clembot.send_message(ctx.message.channel, "Beep Beep! I couldn't understand your reply! Try the **!invite** command again!")
                else:
                    await Clembot.send_message(ctx.message.channel, "Beep Beep! No EX Raids have been reported in this server! Use **!exraid** to report one!")
            else:
                await Clembot.send_message(ctx.message.channel, "Beep Beep! That doesn't look like an EX Raid invitation to me! If it is, please message an admin to get added to the EX Raid channel manually!")
        else:
            await Clembot.send_message(ctx.message.channel, "Beep Beep! Your attachment was not a supported image format!")
    else:
        await Clembot.send_message(ctx.message.channel, "Beep Beep! Please upload your screenshot directly to Discord!")

@Clembot.command(pass_context=True)
@commands.has_permissions(manage_server=True)
async def recover(ctx):
    if checks.check_wantchannel(ctx) or checks.check_citychannel(ctx) or checks.check_raidchannel(ctx) or checks.check_eggchannel(ctx) or checks.check_exraidchannel(ctx):
        await Clembot.send_message(ctx.message.channel, "Beep Beep!I can't recover this channel because I know about it already!")
    else:
        channel = ctx.message.channel
        server = channel.server
        name = channel.name
        topic = channel.topic
        egg = re.match('level-[1-5]-egg', name)
        if egg:
            raidtype = 'egg'
            chsplit = egg.string.split('-')
            del chsplit[0]
            egglevel = chsplit[0]
            del chsplit[0]
            del chsplit[0]
            raid_details = " ".join(chsplit)
            raid_details = raid_details.strip()
            if not topic:
                exp = time.time() + 60 * raid_info['raid_eggs'][egglevel]['hatchtime']
                manual_timer = False
            else:
                topicsplit = topic.split('|')
                localhatch = datetime.datetime.strptime(topicsplit[0][:-9], "Hatches on %B %d at %I:%M %p")
                utchatch = localhatch - datetime.timedelta(hours=server_dict[server.id]['offset'])
                exp = utchatch.replace(tzinfo=datetime.timezone.utc).timestamp()
                manual_timer = True
            pokemon = ''
            if len(raid_info['raid_eggs'][egglevel]['pokemon']) == 1:
                pokemon = raid_info['raid_eggs'][egglevel]['pokemon'][0]
        elif name.split('-')[0] in get_raidlist():
            raidtype = 'raid'
            chsplit = name.split('-')
            pokemon = chsplit[0]
            del chsplit[0]
            raid_details = " ".join(chsplit)
            raid_details = raid_details.strip()
            if not topic:
                exp = time.time() + 60 * 45
                manual_timer = False
            else:
                localend = datetime.datetime.strptime(topic[:-8], "Ends on %B %d at %I:%M %p")
                utcend = localend - datetime.timedelta(hours=server_dict[server.id]['offset'])
                exp = utcend.replace(tzinfo=datetime.timezone.utc).timestamp()
                manual_timer = True
        elif name.split('-')[0] == 'ex':
            raidtype = 'egg'
            egglevel = 'EX'
            chsplit = name.split('-')
            del chsplit[0]
            del chsplit[0]
            del chsplit[0]
            raid_details = " ".join(chsplit)
            raid_details = raid_details.strip()
            if not topic:
                exp = time.time() + 60*60*24*14
                manual_timer = False
            else:
                topicsplit = topic.split('|')
                localhatch = datetime.datetime.strptime(topicsplit[0][:-9], "Hatches on %B %d at %I:%M %p")
                utchatch = localhatch - datetime.timedelta(hours=server_dict[server.id]['offset'])
                exp = utchatch.replace(tzinfo=datetime.timezone.utc).timestamp()
                manual_timer = True
            pokemon = ''
            if len(raid_info['raid_eggs']['EX']['pokemon']) == 1:
                pokemon = raid_info['raid_eggs']['EX']['pokemon'][0]
        else:
            await Clembot.send_message(channel, "Beep Beep!I couldn't recognize this as a raid channel!")
            return
        server_dict[channel.server.id]['raidchannel_dict'][channel.id] = {
            'reportcity' : None,
            'trainer_dict' : {},
            'exp': exp,
            'manual_timer': manual_timer,
            'active': True,
            'raidmessage': None,
            'raidreport': None,
            'address': raid_details,
            'type': raidtype,
            'pokemon' : pokemon,
            'egglevel': egglevel
            }
        await Clembot.send_message(channel, "Beep Beep!This channel has been recovered! However, I can't remember if anyone RSVPed to this raid.")

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
