import asyncio
import traceback

from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.core.logs import Logger

test_dbi = None

async def initialize():
    Logger.info("initialize()")
    global test_dbi
    test_dbi = DatabaseInterface.get_instance() # DatabaseInterface(**config_template.db_config_details)
    await test_dbi.start()
    Logger.info(f"{test_dbi.cxn}")

async def cleanup():
    Logger.info("cleanup()")
    global test_dbi
    await test_dbi.stop()


def async_db_wrapper(function_to_run):
    """
    Passes dbi as a parameter to the async function which needs to be executed
    """
    Logger.info("async_db_wrapper()")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize())
        loop.run_until_complete(function_to_run(test_dbi))
        loop.run_until_complete(cleanup())
    except Exception as error:
        Logger.error(f"{traceback.format_exc()}")
