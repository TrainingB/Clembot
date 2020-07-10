import asyncio

from discord.ext import commands

from clembot.core.bot import group
from clembot.utilities.utils.argparser import ArgParser
from clembot.utilities.utils.utilities import Utilities

CACHE_VERSION = 15


class SpawnManagerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities
        self.argParser = ArgParser(bot.dbi)

    spawn_SYNTAX_ATTRIBUTE = ['command', 'pokemon', 'latlong', 'cp', 'iv', 'lvl']

    def is_pokemon_valid(self, entered_raid):
        if entered_raid.lower() in self.bot.pkmn_info['pokemon_list']:
            return True
        return False

    def get_number(self, pkm_name):
        try:
            number = self.bot.pkmn_info['pokemon_list'].index(pkm_name) + 1
        except ValueError:
            number = None
        return number

    @group(pass_context=True, hidden=True, aliases=["spawn", "sp"])
    async def _spawn(self, ctx):
        try:
            argument_text = ctx.message.clean_content.lower()
            parameters = await self.argParser.parse_arguments(argument_text, self.spawn_SYNTAX_ATTRIBUTE, {'pokemon' : self.is_pokemon_valid }, {'message': ctx.message})

            print(parameters)

            if not (parameters.__contains__('pokemon') and parameters.__contains__('lat') and parameters.__contains__('long')):
                raise Exception("Please provide syntax.")

            pokedex = self.get_number(parameters['pokemon'][0])
            pokemon = parameters['pokemon'][0]
            cp_emoji = "<:cp:605158949389598723>"
            iv_emoji = "<:iv:605180970945085485>"
            loc_emoji = "<:loc:605183595073634306>"
            level_emoji = "<:level:605293692735062027>"
            cp = parameters.get('cp', None)
            iv = parameters.get('iv', None)
            level = parameters.get('lvl', None)
            loc = f"{parameters['lat']},{parameters['long']}"

            apple_maps = f"http://maps.apple.com/?sll={loc}&z=10&t=s"
            google_maps = f"http://maps.apple.com/?sll={loc}&z=10&t=s"
            waze_maps = f"https://www.waze.com/ul?ll={loc}&navigate=yes&zoom=17"

            if ctx.invoked_subcommand is None:
                description = f"{cp_emoji} **{cp}** / {level_emoji} **{level}** / {iv_emoji} **{iv}**\n{loc_emoji} **{loc}**"
                    # f"[[Google Maps]]({google_maps}) [[Apple Maps]]({apple_maps}) [[Waze Maps]]({waze_maps})"

                await ctx.embed(f"A wild {pokemon} ({pokedex}) has appeared.",
                                f"{description}",
                                plain_msg=f"{loc}",
                                icon=self.get_pokemon_image_url(pokedex), thumbnail=self.get_pokemon_image_url(pokedex),
                                footer=f"Reported by {ctx.message.author.display_name}",
                                footer_icon=f"https://cdn.discordapp.com/avatars/{ctx.message.author.id}/{ctx.message.author.avatar}.png?size=32"
                                #image=self.get_pokemon_image_url(pokedex)
                                )

        except Exception as error:
            print(error)
            error_message = await self.utilities._send_error_message(ctx.channel, f"The correct usage is `!spawn pokemon 0.0000,0.0000 0000CP 100IV`")
            await asyncio.sleep(30)
            await error_message.delete()

        await asyncio.sleep(45)
        await ctx.message.delete()

    def get_name(self, pkmn_number):
        pkmn_number = int(pkmn_number) - 1
        name = self.bot.pkmn_info['pokemon_list'][pkmn_number].capitalize()
        return name

    def get_pokemon_image_url(self, pokedex_number):
        # url = icon_list.get(str(pokedex_number))
        url = "https://raw.githubusercontent.com/TrainingB/PokemonGoImages/master/images/pkmn/{0}_.png?cache={1}".format(str(pokedex_number).zfill(3), CACHE_VERSION)
        if url:
            return url
        else:
            return "http://floatzel.net/pokemon/black-white/sprites/images/{pokedex}.png".format(pokedex=pokedex_number)


class Spawn:

    def __init(self, guild_id, pkmn, lat=None, long=None, level=None, cp=None, iv=None):

        self.guild_id = guild_id
        self.pkmn = pkmn

class SpawnEmbed:

    def __init(self):
        self.counter = 1


