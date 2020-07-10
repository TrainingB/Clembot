
import discord



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



