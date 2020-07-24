import asyncio
import json
import math
import os
import pydash as _

from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config import config_template
from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.core.logs import Logger
from clembot.exts.pkmn.cpcalculator import CPCalculator
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.exts.pkmn.spelling import SpellHelper
from clembot.utilities.utils.utilities import Utilities


class RaidMaster:

    TABLE_NAME = 'raid_master'

    by_level = dict()

    def __init__(self, bot, db_dict=dict()):
        self.bot = bot
        self.db_dict = {
            'raid_level' : None,
            'raid_boss': [],
            'next_raid_boss': [],
            'egg_key': None,
            'egg_image': None,
            'egg_timer': None,
            'raid_timer': None
        }
        self.db_dict.update(db_dict)


    @property
    def level(self):
        return self['raid_level']

    @property
    def egg_timer(self):
        return self['egg_timer']

    @property
    def raid_timer(self):
        return self['raid_timer']

    @property
    def egg_image(self):
        return self['egg_image']

    @property
    def raid_boss_list(self):
        return self['raid_boss']


    def update_dict(self, db_dict):
        self.db_dict.update(db_dict)

    async def insert(self):
        table = self.bot.dbi.table(RaidMaster.TABLE_NAME)
        insert_query = table.insert(**self.db_dict)
        await insert_query.commit()
        RaidMaster.cache(self)

    async def update(self):
        table = self.bot.dbi.table(RaidMaster.TABLE_NAME)
        update_query = table.update(**self.db_dict).where(raid_level=self.level)
        await update_query.commit()
        RaidMaster.cache(self)

    @staticmethod
    async def find_all(bot):
        table = bot.dbi.table(RaidMaster.TABLE_NAME)
        query = table.query().select()
        record_list = await query.getjson()
        return record_list

    @classmethod
    async def find_by(cls, bot, raid_level):
        table = bot.dbi.table(RaidMaster.TABLE_NAME)
        query = table.query().select().where(raid_level=raid_level)
        try:
            record_list = await query.getjson()
            if record_list:
                return cls(bot, record_list[0])
        except Exception as error:
            Logger.info(f"{error}")

        return None

    @classmethod
    async def load(cls, bot, force=False):
        Logger.info("load()")
        if len(cls.by_level) == 0 or force:
            table = bot.dbi.table(RaidMaster.TABLE_NAME)
            records = await table.query().select().getjson()

            for record in records:
                raid_master = RaidMaster(bot, record)
                RaidMaster.cache(raid_master)


    @classmethod
    def cache(cls, raid_master):
        cls.by_level[raid_master.level] = raid_master
        pass


    @classmethod
    def from_cache(cls, level):
        if len(cls.by_level) < 1:
            raise Exception("Error : Raid bosses are not loaded.")

        if level:
            raid_master = cls.by_level.get(str(level), None)
            return raid_master

        raise Exception(f"Error : Raid bosses (level - {level}) are not loaded.")

    def __getitem__(self, item):
        """use [] operator to access members, simpler to create entity objects"""
        return self.db_dict.get(item)


    def __setitem__(self, key, value):
        """use [] operator to access members, simpler to create entity objects. Handles array kind of values."""
        self.db_dict[key] = value


    @classmethod
    def get_level(cls, pokeform):
        """get_level(pokemon) - return None if the boss is listed."""
        for raid_master in RaidMaster.by_level.values():
            if pokeform.id in raid_master.raid_boss_list:
                return int(raid_master.level)

        return None

    @classmethod
    def get_boss_list(cls, level):
        """get_boss_list(level) - returns a list of raid bosses for that level"""
        raid_master = RaidMaster.by_level.get(str(level), None)
        if raid_master:
            return raid_master.raid_boss_list

        return []

    @classmethod
    def is_current_raid_boss(cls, pokeform):
        return RaidMaster.get_level(pokeform) is not None
