from discord.ext import commands

from clembot.core.logs import Logger


class RaidLevelConverter(commands.Converter):
    level_alias_map = {
        'MEGA': 'M',
        'EX': 'E'
    }

    label_map = {
        'M' : 'mega',
        'E' : 'ex'
    }

    @classmethod
    def to_level(cls, argument) -> str:
        case_corrected_level = argument.upper()

        if case_corrected_level in RaidLevelMaster.get_all_levels():
            return case_corrected_level

        if case_corrected_level in RaidLevelConverter.level_alias_map.keys():
            return RaidLevelConverter.level_alias_map.get(case_corrected_level)

        return None

    async def convert(self, ctx, argument) -> str:
        return RaidLevelConverter.to_level(argument)

    @classmethod
    def label(cls, level):
        if level in RaidLevelConverter.label_map.keys():
            return RaidLevelConverter.label_map.get(level)

        return level


class RaidLevelMaster:

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
        table = self.bot.dbi.table(RaidLevelMaster.TABLE_NAME)
        insert_query = table.insert(**self.db_dict)
        await insert_query.commit()
        RaidLevelMaster.cache(self)

    async def update(self):
        table = self.bot.dbi.table(RaidLevelMaster.TABLE_NAME)
        update_query = table.update(**self.db_dict).where(raid_level=self.level)
        await update_query.commit()
        RaidLevelMaster.cache(self)

    @staticmethod
    async def find_all(bot):
        table = bot.dbi.table(RaidLevelMaster.TABLE_NAME)
        query = table.query().select()
        record_list = await query.getjson()
        return record_list

    @classmethod
    async def find_by(cls, bot, raid_level):
        table = bot.dbi.table(RaidLevelMaster.TABLE_NAME)
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
            table = bot.dbi.table(RaidLevelMaster.TABLE_NAME)
            records = await table.query().select().getjson()

            for record in records:
                raid_master = RaidLevelMaster(bot, record)
                RaidLevelMaster.cache(raid_master)


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


        if 'MEGA' in pokeform.id:
            return 'M'

        for raid_master_level in RaidLevelMaster.by_level.values():
            if pokeform.id in raid_master_level.raid_boss_list:
                return raid_master_level.level

        return None

    @classmethod
    def get_all_levels(cls):
        """get_all_levels(pokemon) - return pokemon raid levels"""
        return RaidLevelMaster.by_level.keys()

    @classmethod
    def get_boss_list(cls, level):
        """get_boss_list(level) - returns a list of raid bosses for that level"""
        raid_master = RaidLevelMaster.by_level.get(str(level), None)
        if raid_master:
            return raid_master.raid_boss_list

        return []

    @classmethod
    def is_current_raid_boss(cls, pokeform):
        return RaidLevelMaster.get_level(pokeform) is not None
