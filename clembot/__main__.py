import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import argparse

import discord

from clembot.config import config_template
from clembot.core.logs import Logger
from clembot.core.bot import Bot, ExitCodes
from clembot.core.errors import custom_error_handling


################################################################################################################################################


def run_bot(debug=False, launcher=None, from_restart=False):
    """Sets up the bot, runs it and handles exit codes."""

    #create async loop and setup contextvar
    loop = asyncio.get_event_loop()

    # TODO: Figure out if I really need it?
    # context.ctx_setup(loop)

    bot = Bot(case_insensitive=True, activity=discord.Game(name="Pokemon Go"), debug=False, from_restart=False)

    bot.load_extension('clembot.core.commands')
    bot.load_extension('clembot.core.cog_manager')
    custom_error_handling(bot, Logger)
    try:
        loop.run_until_complete(bot.start(config_template.bot_token))
        Logger.info("started!")
    except discord.LoginFailure:
        Logger.critical("Invalid token")
        loop.run_until_complete(bot.logout())
        bot.shutdown_mode = ExitCodes.SHUTDOWN
    except KeyboardInterrupt:
        Logger.info("Keyboard interrupt detected. Quitting...")
        loop.run_until_complete(bot.logout())
        bot.shutdown_mode = ExitCodes.SHUTDOWN
    except Exception as e:
        Logger.critical("Fatal exception", exc_info=e)
        loop.run_until_complete(bot.logout())
    finally:
        code = bot.shutdown_mode
        sys.exit(code.value)


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Clembot - Discord Bot for Pokemon Go Communities")
    parser.add_argument(
        "--debug", "-d", help="Enabled debug mode.", action="store_true")
    parser.add_argument(
        "--launcher", "-l", help=argparse.SUPPRESS, action="store_true")
    parser.add_argument(
        "--fromrestart", help=argparse.SUPPRESS, action="store_true")
    return parser.parse_args()


def main():
    args = parse_cli_args()
    run_bot(debug=args.debug, launcher=args.launcher,
        from_restart=args.fromrestart)


if __name__ == '__main__':
    main()



