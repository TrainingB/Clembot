import discord

from clembot.config import config_template
from clembot.core.logs import Logger

class Emojis:

    info = "<:icon_info:715354001796890687>"
    error = "<:icon_error:715354002316853268>"


def color(*args):
    """Returns discord.Color object"""

    arg = args[0] if args else None

    if isinstance(arg, int):
        return discord.Color(arg)

    if isinstance(arg, str):
        try:
            return getattr(discord.Color, arg)()
        except AttributeError:
            return discord.Color.lighter_grey()

    if isinstance(arg, discord.Guild):
        return arg.me.color
    else:
        return discord.Color.lighter_grey()






class Embeds:

    def __init__(self):
        return

    @staticmethod
    def google_location_preview_url(lat_long):
        key = config_template.api_keys["google-api-key"]
        gmap_base_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat_long}&markers=color:blue%7C{lat_long}&maptype=roadmap&size=250x125&zoom=15&key={key}"

        return gmap_base_url

    @staticmethod
    async def message(channel, description, title=None, footer=None, user=None):
        try:
            error_message = "The output contains more than 2000 characters."

            user_mention = "<:icon_info:715354001796890687> "
            if user:
                user_mention = f"<:icon_info:715354001796890687> **{user.display_name}** "

            if len(description) >= 2000:
                discord.Embed(description="{0}".format(error_message), colour=discord.Color.red())

            message_embed = discord.Embed(description=f"{user_mention}{description}", colour=discord.Colour.green(), title=title)
            if footer:
                message_embed.set_footer(text=footer)
            return await channel.send(embed=message_embed)
        except Exception as error:
            Logger.error(error)


    @staticmethod
    async def error(channel, description, user=None):

        color = discord.Colour.red()
        user_mention = ""
        if user:
            user_mention = f"**{user.display_name}** "
        error_embed = discord.Embed(description=f"{Emojis.error} {user_mention}{description}", colour=color)
        return await channel.send(embed=error_embed)

    @staticmethod
    def make_embed(msg_type='', header=None, header_icon=None, title=None, title_url=None, content=None, thumbnail='',
                   image='', fields=None, footer=None, footer_icon=None, inline=True, guild=None, msg_color=None):
        """Returns a formatted discord embed object.

        Define either a type or a colour.
        Types are:
        error, warning, info, success, help.
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
            msg_color = embed_types[msg_type]['colour']
            header_icon = embed_types[msg_type]['icon']
        if guild and not msg_color:
            msg_color = color(guild)
        else:
            if not isinstance(msg_color, discord.Colour):
                msg_color = color(msg_color)

        embed = discord.Embed(title=title or discord.Embed.Empty, title_url=title_url or discord.Embed.Empty,
            description=content, colour=msg_color)

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


