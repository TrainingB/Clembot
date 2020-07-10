from enum import Enum

import discord


class Icons:

    raid_report = "https://i.imgur.com/uRhgISs.png"
    configure = "https://i.imgur.com/nPyXbkD.png"
    configure_success = "https://i.imgur.com/OBlddqw.png"
    configure_failure = "https://i.imgur.com/30rAjXD.png"
    uptime = "https://i.imgur.com/82Cqf1x.png"
    wild_report = "https://i.imgur.com/eW8sCSo.png"
    field_research = "https://raw.githubusercontent.com/TrainingB/Clembot/v1-rewrite/images/field-research.png?cache=13"
    research_report = "https://i.imgur.com/O1XNv5z.png"
    bot_error="https://i.imgur.com/C3qZaeo.png"
    trash = "https://i.imgur.com/K6iLiPP.png"


    invalid_input = "https://i.imgur.com/Sl9Nr3g.png"
    bot_error_2 = "https://i.imgur.com/P8UEhkD.png"
    configuration = "https://i.imgur.com/Brzu64u.png"
    invalid_access = "https://i.imgur.com/4AX0bZ0.png"





    @staticmethod
    def avatar(user: discord.Member):
        icon_url = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.jpg?size=32"
        return icon_url


class ClembotReactions(Enum):

    DESPAWNED = '💨'
    ON_MY_WAY = '🏎️'
    TRASH = '🗑️'


