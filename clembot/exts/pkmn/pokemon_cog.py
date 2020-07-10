import os

from discord.ext import commands


class PokemonCog(commands.Cog):
    """
    Pokemon Manager Code
    """

    active_raids = {}

    def __init__(self, bot):
        self.bot = bot
        # self.bot.loop.create_task(PokemonCache.load_cache_from_dbi(bot.dbi))


def main():
    pass


if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")

