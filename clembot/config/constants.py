from enum import Enum

import discord

from clembot.config import config_template

GLOBAL_CONFIG_KEY = ["bingo-event-title", "cache-version", "timezone", "bingo-event-pokemon", "next-badge-id", "game-master-version"]

GUILD_METADATA_KEY = ["hide-nest-preview", "bingo-card-repo", "bingo-event-title", "bingo-event-pokemon"]

GUILD_CONFIG_KEY = ['prefix', 'city', 'timezone', 'welcome', 'teams', 'config']

CHANNEL_METADATA_KEY = ["city"]

def parse_emoji(guild, emoji_string):
    """Given a string, if it fits the pattern :emoji name:,
       and <emoji_name> is in the guild's emoji list, then
       return the string <:emoji name:emoji id>. Otherwise,
       just return the string unmodified."""

    if len(emoji_string) == 0:
        return ""
    if emoji_string[0] == ':' and emoji_string[-1] == ':':
        emoji = discord.utils.get(guild.emojis, name=emoji_string.strip(':'))
        if emoji:
            emoji_string = "<:{0}:{1}>".format(emoji.name, emoji.id)
        else:
            emoji_string = "{0}".format(emoji_string.strip(':').capitalize())

    return emoji_string


class Icons:

    raid_report = "https://i.imgur.com/uRhgISs.png"
    configure = "https://i.imgur.com/nPyXbkD.png"
    configure_success = "https://i.imgur.com/OBlddqw.png"
    configure_failure = "https://i.imgur.com/30rAjXD.png"
    uptime = "https://i.imgur.com/82Cqf1x.png"
    wild_report = "https://i.imgur.com/eW8sCSo.png"
    field_research = "https://raw.githubusercontent.com/TrainingB/Clembot/v1-rewrite/images/field-research.png?cache=13"
    research_report = "https://i.imgur.com/O1XNv5z.png"
    BOT_ERROR= "https://i.imgur.com/C3qZaeo.png"
    trash = "https://i.imgur.com/K6iLiPP.png"
    error = "https://i.imgur.com/dfyevnZ.png"

    INVALID_INPUT = "https://i.imgur.com/Sl9Nr3g.png"
    bot_error_2 = "https://i.imgur.com/P8UEhkD.png"
    CONFIGURATION = "https://i.imgur.com/Brzu64u.png"
    INVALID_ACCESS = "https://i.imgur.com/8LOsBQS.png"
    TIMEZONE="https://i.imgur.com/j5L85oY.png"


    @staticmethod
    def avatar(user: discord.Member):
        icon_url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.jpg?size=32"
        return icon_url


class MyEmojis:

    DESPAWNED = '💨'
    ON_MY_WAY = '🏎️'
    TRASH = '🗑️'

    REMOTE = f"{parse_emoji(None, config_template.misc_emoji.get('remote_raid'))}"
    INVITE = f"{parse_emoji(None, config_template.misc_emoji.get('add_friend'))}"
    HERE = f"{parse_emoji(None, config_template.misc_emoji.get('here'))}"
    COMING = f"{parse_emoji(None, config_template.misc_emoji.get('coming'))}"
    INTERESTED = f"{parse_emoji(None, config_template.misc_emoji.get('interested'))}"
    INFO = f"{parse_emoji(None, config_template.misc_emoji.get('info'))}"
    ERROR = f"{parse_emoji(None, config_template.misc_emoji.get('error'))}"
