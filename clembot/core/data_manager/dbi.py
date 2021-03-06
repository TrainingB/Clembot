import asyncio
import json
import os
import traceback

import asyncpg
from discord.ext.commands import when_mentioned_or

from clembot.config import config_template
from clembot.core.data_manager.schema import Table, Query, Insert, Update, Schema
from clembot.core.data_manager.tables import core_table_sqls
from clembot.core.logs import Logger


async def init_conn(conn):
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog", format='binary')
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog", format='binary')





class DatabaseInterface:
    """Get, Create and Edit data in the connected database."""

    _instance = None

    # def __init__(self,
    #              password=config_template.db_config_details.get('password'),
    #              hostname=config_template.db_config_details.get('hostname'),
    #              username=config_template.db_config_details.get('username'),
    #              database=config_template.db_config_details.get('database'),
    #              port=config_template.db_config_details['port'],
    #              debug=config_template.db_config_details['debug']):
    #     self.loop = None
    #     self.dsn = "postgres://{}:{}@{}:{}/{}".format(
    #         username, password, hostname, port, database)
    #     self.cxn = f"postgres://{username}@{hostname}:{port}/{database}"
    #     Logger.info(f"[dbi.py] Connecting to : {self.cxn}")
    #     self.pool = None
    #     self.prefix_conn = None
    #     self.prefix_stmt = None
    #     self.settings_conn = None
    #     self.settings_stmt = None
    #     self.channel_settings_stmt = None
    #
    #     # self.types = sqltypes
    #     self.listeners = []
    #     self.debug = debug

    @classmethod
    def get_instance(cls):
        """ Class access method. """
        if cls._instance is None:
            return DatabaseInterface()
        return cls._instance

    def __init__(self):
        """ Virtually private constructor. """
        if DatabaseInterface._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            DatabaseInterface._instance = self
            password = config_template.db_config_details.get('password')
            hostname = config_template.db_config_details.get('hostname')
            username = config_template.db_config_details.get('username')
            database = config_template.db_config_details.get('database')
            port = config_template.db_config_details['port']
            debug = config_template.db_config_details['debug']
            self.loop = None
            self.dsn = f'postgres://{username}:{password}@{hostname}:{port}/{database}'
            self.cxn = f"postgres://{username}@{hostname}:{port}/{database}"
            Logger.info(f"[dbi.py] Connecting to : {self.cxn}")
            self.pool = None

            self.guild_prefix_conn = None
            self.guild_prefix_stmt = None

            self.guild_metadata_conn = None
            self.guild_metadata_stmt = None
            self.guild_config_stmt = None
            self.channel_profile_select_stmt = None

            # self.types = sqltypes
            self.listeners = []
            self.debug = debug



    async def start(self, loop=None):
        try:
            Logger.info(f"start()")
            if loop:
                self.loop = loop
            self.pool = await asyncpg.create_pool(
                self.dsn, loop=loop, init=init_conn)
            await self.prepare()
        except Exception as error:
            Logger.error(error)

    async def recreate_pool(self):
        Logger.warning(f'Re-creating closed database pool.')
        self.pool = await asyncpg.create_pool(
            self.dsn, loop=self.loop, init=init_conn)

    async def prepare(self):

        # guild prefix callable statement
        self.guild_prefix_conn = await self.pool.acquire()
        prefix_sql = 'SELECT prefix FROM guild_config WHERE guild_id=$1;'
        self.guild_prefix_stmt = await self.guild_prefix_conn.prepare(prefix_sql)

        # guild settings statement
        self.guild_metadata_conn = await self.pool.acquire()
        guild_metadata_sql = 'SELECT config_value FROM guild_metadata WHERE guild_id=$1 AND config_name=$2;'
        self.guild_metadata_stmt = await self.guild_metadata_conn.prepare(guild_metadata_sql)

        guild_config_sql = 'SELECT * from guild_config where guild_id=$1;'
        self.guild_config_stmt = await self.guild_metadata_conn.prepare(guild_config_sql)

        channel_profile_select_sql = 'SELECT * FROM channel_metadata WHERE guild_id=$1 AND channel_id=$2;'
        self.channel_profile_select_stmt = await self.guild_metadata_conn.prepare(channel_profile_select_sql)




    async def acquire_connection_from_pool(self):
        if not self.pool:
            await self.start()
        return await self.pool.acquire()

    async def core_tables_exist(self):
        core_sql = core_table_sqls()
        for k, v in core_sql.items():
            table_exists = await self.table(k).exists()
            if not table_exists:
                Logger.warning(f'Core table {k} not found. Creating...')
                await self.execute_transaction(v)
                Logger.warning(f'Core table {k} created.')

    async def stop(self):
        conns = (self.guild_prefix_conn, self.guild_metadata_conn)
        for c in conns:
            if c:
                await self.pool.release(c)
        if self.pool:
            await self.pool.close()
            self.pool.terminate()

    async def prefix_manager(self, bot, message):
        """Returns the bot prefixes by context.

        Returns a guild-specific prefix if it has been set. If not,
        returns the default prefix.

        Uses a prepared statement to ensure caching.
        """
        default_prefix = bot.default_prefix
        if message.guild:
            g_prefix = await self.guild_prefix_stmt.fetchval(message.guild.id)
            prefix = g_prefix if g_prefix else default_prefix
        else:
            prefix = default_prefix

        return when_mentioned_or(prefix)(bot, message)

    async def execute_query_json(self, query, *query_args):
        result = []
        if self.debug:
            Logger.info(f"{query} Parameters: {query_args}")
        rcrds_dict = []
        try:
            if not self.pool:
                await self.start()
            async with self.pool.acquire() as conn:
                try:
                    rcrds = await conn.fetch(query, *query_args)
                    for rcrd in rcrds:
                        rcrds_dict.append(dict(rcrd))
                    return rcrds_dict
                except Exception as e:
                    print(e)
                # stmt = await conn.prepare(query)
                # rcrds = await dict(stmt.fetchrow(query, *query_args))
            return rcrds
            #     for rcrd in rcrds:
            #         result.append(rcrd)
            # return result
        # except asyncpg.exceptions.InterfaceError as e:
            # logger.error(f'Exception {type(e)}: {e}')
            # await self.recreate_pool()
            # return await self.execute_query(query, *query_args)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

    async def execute_query(self, query, *query_args):
        result = []
        if self.debug:
            Logger.info(f"{query} Parameters: {query_args}")
        try:
            if not self.pool:
                await self.start()
            async with self.pool.acquire() as conn:
                stmt = await conn.prepare(query)
                rcrds = await stmt.fetch(*query_args)
                for rcrd in rcrds:
                    result.append(dict(rcrd))
            return result
        except asyncpg.exceptions.InterfaceError as e:
            Logger.error(f'Exception {type(e)}: {e}')
            await self.recreate_pool()
            return await self.execute_query(query, *query_args)
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")

    async def execute_transaction(self, query, *query_args):
        result = []
        try:
            if self.debug:
                Logger.info(f"{query} {query_args}")

            if not self.pool:
                await self.start()
            async with self.pool.acquire() as conn:
                stmt = await conn.prepare(query)

                if any(isinstance(x, (set, tuple)) for x in query_args):
                    async with conn.transaction():
                        for query_arg in query_args:
                            async for rcrd in stmt.cursor(*query_arg):
                                result.append(rcrd)
                else:
                    async with conn.transaction():
                        async for rcrd in stmt.cursor(*query_args):
                            result.append(rcrd)
                return result
        except asyncpg.exceptions.InterfaceError as e:
            print(f'Exception {type(e)}: {e}')
            await self.recreate_pool()
            return await self.execute_transaction(query, *query_args)

    async def add_listener(self, channel, callback):
        con = await self.pool.acquire()
        if (channel, callback) in self.listeners:
            return
        self.listeners.append((channel, callback))
        return await con.add_listener(channel, callback)

    async def create_table(self, name, columns: list, *, primaries=None):
        """Create table."""
        return await Table(self, name).create(columns, primaries=primaries)

    def table(self, name):
        return Table(name, self)

    def query(self, *tables):
        print("query() called")
        tables = [Table(self, name) for name in tables]
        return Query(self, tables)

    def insert(self, table):
        return Insert(self, table)

    def update(self, table):
        return Update(self, table)

    async def tables(self):
        table = self.table('information_schema.tables')
        table.query('table_name')
        table.query.where(table_schema='public')
        table.query.order_by('table_name')
        return await table.query.get()

    def schema(self, name):
        return Schema(self, name)



dbi = None

async def initialize():
    global dbi
    dbi = DatabaseInterface()
    await dbi.start()

async def cleanup():
    global dbi
    await dbi.stop()

async def _data(table_name = 'clembot_config'):
    # print("calling _data()")
    table = dbi.table(table_name)
    channel_query = dbi.table(table_name).query().select().where(table['gym_code_key'].like('%GL%'))
    _data = channel_query
    return_data = await _data.get()
    # print(f"{len(return_data)} record(s) found!")
    # print(return_data[0]['gmap_url'])
    # print(return_data[0]['json'])
    return return_data


async def select_from(table_name = 'sample_test'):
    # print("called select_from()")

    sample_test = dbi.table('sample_test')
    query = sample_test.query().select()
    return_data = await query.get()

    print(f"{len(return_data)} record(s) found!")
    if len(return_data) > 0:
        print(return_data[0])
    return return_data

async def test_condition():
    try:
        # guild_channel_city_tbl = dbi.table('guild_channel_city')
        # guild_channel_city_tbl['city_state']
        # city = await dbi.table('clembot_config').query().select().where(dbi.table('guild_channel_city')['channel_id'].is_null_(),guild_id=393545294337277970).get()
        #
        # update_query = dbi.table('guild_channel_config').update(config_value='test123').where(channel_id=None, config_name='city', guild_id=1)
        # result = await update_query.commit() # dbi.table('guild_channel_config')['channel_id'].is_null_()
        #


        config_table = dbi.table('clembot_config').query().select()
        result = await config_table.get()
        #results = json.load(result)
        print(result)

        mydict = {}
        for row in result:
            mydict[row['config_name']] = row['config_value']

        print(mydict)
    except Exception as error:
        Logger.error(f"{traceback.format_exc()}")

async def insert_into(table_name = 'sample_test'):
    print("called select_from()")

    sample_test_record = {
        "key" : "mykey",
        "value" : "my value",
        "notes" : "my notes"
    }

    sample_test = dbi.table('sample_test')
    insert = sample_test.insert()
    insert.row(**sample_test_record)
    await insert.commit()

    return sample_test_record


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize())
        # result = loop.run_until_complete(_data('gym_master'))
        # result = loop.run_until_complete(select_from())
        # result = loop.run_until_complete(insert_into())
        # result = loop.run_until_complete(select_from())
        loop.run_until_complete(test_condition())
        loop.run_until_complete(cleanup())

    except Exception as error:
        Logger.error(f"{traceback.format_exc()}")


if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")
