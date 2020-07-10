import json

import pydash as _


class Serializer:

    @staticmethod
    def serialize(data_dict):
        return _.map_values(data_dict, lambda val: json.dumps(val) if isinstance(val, dict) else val)

    @staticmethod
    def deserialize(data_dict, dict_fields = ['config']):
        return { k : json.loads(v) if k in dict_fields and v is not None else v for (k, v) in data_dict.items()}


class UserGuildProfile:

    TABLE_NAME = 'user_guild_profile'

    dict_fields = ['leaderboard_status']
    list_fields = ['badge_id']

    LEADERBOARD_STATS = ['wilds', 'raids', 'quests', 'eggs', 'nest', 'rocket']

    def __init__(self, bot, db_dict = dict()):
        self.bot = bot
        self.db_dict = {
            'user_id' : None,
            'guild_id' : None,
            'badge_id' :  [],
            'leaderboard_status' : {},
            'status' : None
        }
        self.db_dict.update(Serializer.deserialize(db_dict, dict_fields=UserGuildProfile.dict_fields))


    def __getitem__(self, item):
        return self.db_dict.get(item) or ([] if item in UserGuildProfile.list_fields else None) or ({} if item in UserGuildProfile.dict_fields else None)


    def __setitem__(self, key, value):
        """use [] operator to access members, simpler to create entity objects. Handles array kind of values."""
        if key in UserGuildProfile.list_fields:
            if self.db_dict[key] is None or value is None:
                self.db_dict[key] = []
            if value:
                self.db_dict[key].append(value)
        else:
            self.db_dict[key] = value


    @classmethod
    async def data(cls, bot, user_id, guild_id) -> dict():
        report_user_query = bot.dbi.table('user_metadata').query()
        _data = report_user_query.where(user_id=user_id, guild_id=guild_id)
        db_record = await _data.get()

        if db_record:
            user_metadata = UserGuildProfile.from_db_dict(bot, dict(db_record[0]))
        else:

            user_metadata = UserGuildProfile(bot, user_id, guild_id)
            await user_metadata.insert()

        return user_metadata


    @classmethod
    async def find(cls, bot, user_id, guild_id):
        table = bot.dbi.table(UserGuildProfile.TABLE_NAME)
        query = table.query().select().where(user_id=user_id, guild_id=guild_id)
        user_list = await query.getjson()
        if user_list:
            return cls(bot, user_list[0])
        else:
            await UserGuildProfile.create(bot, user_id, guild_id)
            query = table.query().select().where(user_id=user_id, guild_id=guild_id)
            user_list = await query.getjson()
            if user_list:
                return cls(bot, user_list[0])
        return None


    @classmethod
    async def create(cls, bot, user_id, guild_id):
        user_guild_profile = UserGuildProfile(bot, {'user_id': user_id, 'guild_id': guild_id})
        await user_guild_profile.insert()
        return user_guild_profile


    async def update(self):
        table = self.bot.dbi.table(UserGuildProfile.TABLE_NAME)
        update_dict=Serializer.serialize(self.db_dict)
        update_query = table.update(**update_dict).where(user_id=self['user_id'], guild_id=self['guild_id'])
        await update_query.commit()


    async def insert(self):
        table = self.bot.dbi.table(UserGuildProfile.TABLE_NAME)
        insert_dict=Serializer.serialize(self.db_dict)
        insert_query = table.insert(**insert_dict)
        await insert_query.commit()


    def record_report(self, stat_type, board_type='lifetime', increase_by=1, initialize=False):
        """
            record_report('eggs','lifetime') => increases by 1
            record_report('raids','lifetime', initialize=True) => set to 1
            record_report('wilds','lifetime', increase_by=0, initialize=True) => set to 0
            record_report('quests','lifetime', increase_by=12, initialize=True) => set to 12
        """
        if stat_type in UserGuildProfile.LEADERBOARD_STATS:
            current_stat = 0 if initialize else _.get(self.db_dict,f'leaderboard_status.{board_type}.{stat_type}', 0)
            self.db_dict.setdefault('leaderboard_status',{}).setdefault(board_type, {})[stat_type] = current_stat + increase_by


    def leaderboard_stats_dict(self, board_type):
        return _.get(self.db_dict, f'leaderboard_status.{board_type}')



    def leaderboard_status(self, board_type):
        status_dict = _.get(self.db_dict, f'leaderboard_status.{board_type}')

        wilds, raids, quests, eggs, nest, rocket = ([status_dict.get(stat, 0) for stat in UserGuildProfile.LEADERBOARD_STATS])

        status_text = f"Raids: **{raids}** | Eggs: **{eggs}** | Wilds: **{wilds}** | Research: **{quests}** | Nest: **{nest}** | Grunts: **{rocket}**"

        return status_text

    @property
    def user_id(self):
        return self['user_id']

    @classmethod
    async def find_top10_reporters(cls, bot, guild_id, leaderboard_type, stat_type):

        query = top_10_leaderboard_query
        query_args = [guild_id, f'{leaderboard_type}', f'{leaderboard_type}', None if stat_type == 'total' else stat_type , 10]
        user_rcrd_list = await bot.dbi.execute_query_json(query, *query_args)

        return user_rcrd_list


top_10_leaderboard_query="""
with leaderboard as (
    select user_id, guild_id, leaderboard_status, board_type.key board, raid_stat.key stat_type, raid_stat.value reports
    from user_guild_profile as ugp
             join json_each_text(ugp.leaderboard_status::json) as board_type on true
             join json_each_text(board_type.value::json) as raid_stat on true
    where   guild_id = $1 and
            leaderboard_status::jsonb?$2 and
            board_type.key = $3 and
            raid_stat.key = coalesce($4, raid_stat.key)
)
select guild_id, user_id, leaderboard_status, board, sum(reports::int) total_reports
from leaderboard
group by guild_id, user_id, leaderboard_status, board
order by total_reports desc
limit $5
;
"""