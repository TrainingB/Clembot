
import discord

from clembot.core.bot import Bot
from clembot.core.data_manager.dbi import DatabaseInterface


class UsesBotInterface:

    def __init__(self, bot: Bot):
        self.bot = bot

    def __str__(self):
        return f"bot: {self.bot.command_prefix}"


class MetaDataInterface:

    def __init__(self, dbi: DatabaseInterface):
        self.dbi = dbi



class RaidInterface(MetaDataInterface):

    def __init__(self, dbi):
        super().__init__(dbi)


    def __str__(self):
        return f"DBI: {self.dbi.dsn}"


my_client = Bot(command_prefix="!", case_insensitive=True, activity=discord.Game(name="Pokemon Go"), debug=False)
dbi = DatabaseInterface.get_instance() # DatabaseInterface(**config_template.db_config_details)



def test_bot():
    global my_client


    my_bot = UsesBotInterface(my_client)

    my_interface = RaidInterface(dbi)


    print(my_bot)

    print(my_interface)

def main():

    test_bot()
    print("Test finished")


main()


