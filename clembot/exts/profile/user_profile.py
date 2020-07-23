from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.utilities.utils.embeds import Embeds


class UserProfile:

    TABLE_NAME = 'user_profile'

    list_fields = ['ign', 'trainer_code', 'trade_requests', 'trade_offers', 'badge_id']

    def __init__(self, bot, db_dict):
        self.bot = bot
        self.db_dict = {
            'user_id' : None,
            'trainer_code' : [],
            'ign' :  [],
            'silph_id' : None,
            'pokebattler_id' : None,
            'trade_requests' : [],
            'trade_offers': [],
            'badge_id': [],
            'status': None
        }
        self.db_dict.update(db_dict)


    def __getitem__(self, item):
        """use [] operator to access members, simpler to create entity objects"""
        return self.db_dict.get(item) or ([] if item in UserProfile.list_fields else None)



    def __setitem__(self, key, value):
        """use [] operator to access members, simpler to create entity objects. Handles array kind of values."""
        if key in UserProfile.list_fields:
            if self.db_dict[key] is None:
                self.db_dict[key] = []
            if value:
                if isinstance(value, list):
                    self.db_dict[key].extend(value)
                else:
                    self.db_dict[key].append(value)
            else:
                self.db_dict[key] = []
        else:
            self.db_dict[key] = value

    def __delitem__(self, key):
        self.db_dict[key] = []


    def reduce(self):
        a = 10
        reduced_db_dict = {
            'trade_requests' : list(set(self['trade_requests'])),
            'trade_offers': list(set(self['trade_offers'])),
            'badge_id': list(set(self['badge_id'])),
            'ign': list(set(self['ign'])),
            'trainer_code': list(set(self['trainer_code']))
        }
        self.db_dict.update(reduced_db_dict)



    async def insert(self):
        table = self.bot.dbi.table(UserProfile.TABLE_NAME)
        insert_query = table.insert(**self.db_dict)
        await insert_query.commit()


    async def update(self):
        table = self.bot.dbi.table(UserProfile.TABLE_NAME)
        self.reduce()
        update_query = table.update(**self.db_dict).where(user_id=self.user_id)
        await update_query.commit()


    async def delete(self):
        """Deletes the raid record from DB and evicts from cache."""
        table = self.bot.dbi.table(UserProfile.TABLE_NAME)
        delete_query = table.query().where(user_id=self.user_id)
        await delete_query.delete()


    @staticmethod
    async def find_all(bot):
        table = bot.dbi.table(UserProfile.TABLE_NAME)
        query = table.query().select()
        user_list = await query.getjson()
        return user_list

    @classmethod
    async def find(cls, bot, user_id):
        table = bot.dbi.table(UserProfile.TABLE_NAME)
        query = table.query().select().where(user_id=user_id)
        user_list = await query.getjson()
        if user_list:
            return cls(bot, user_list[0])
        else:
            await UserProfile.create(bot, user_id)
            query = table.query().select().where(user_id=user_id)
            user_list = await query.getjson()
            if user_list:
                return cls(bot, user_list[0])
        return None


    @classmethod
    async def create(cls, bot, user_id):
        user_profile = UserProfile(bot, {'user_id': user_id})
        await user_profile.insert()
        return user_profile


    @classmethod
    async def find_by_ign(cls, bot, ign):
        user_table = bot.dbi.table(UserProfile.TABLE_NAME)
        report_user_query = user_table.query().where(user_table['ign'].icontains_(ign))
        user_list = await report_user_query.getjson()

        if user_list:
            return cls(bot, user_list[0])

    @classmethod
    async def find_all_by_trade_preferences(cls, bot, search_for, in_field):

        query = f"select * from user_profile where exists (SELECT 1 FROM unnest(user_profile.{in_field}) AS pkmn WHERE pkmn like $1 );"
        query_args = [f'%{search_for}%']
        user_rcrd_list = await bot.dbi.execute_query_json(query, *query_args)
        user_list = [cls(bot, user_record) for user_record in user_rcrd_list]
        return user_list


    @classmethod
    async def find_ign(cls, bot, user_id):
        user_profile = await cls.find(bot, user_id)
        if user_profile:
            return f"{' '.join(user_profile['ign'])}"

        return None


    @property
    def user_id(self):
        return self['user_id']

    async def get_guild_profile(self, guild_id):
        return await UserGuildProfile.find(self.bot, self.user_id, guild_id)

    def embed(self, ctx, show_help=None):
        return (ProfileEmbed.from_user_profile(ctx, self, show_help)).embed



lifetime = {
    'raids': 0,
    'eggs': 0,
    'wilds': 0,
    'quests': 0,

}

leaderboard_stats: {
                    "lifetime": {
                        "wilds": 4,
                        "raids": 45,
                        "quests": 1,
                        "eggs": 135
                    },
                    "burbank": {
                        "raids": 6
                    },
                    "biweekly": {
                        "wilds": 4,
                        "raids": 34,
                        "quests": 1,
                        "eggs": 113
                    },
                    "glendale": {},
                    "noho": {},
                    "north-hills": {},
                    "woodland-hills": {}
                }


class ProfileEmbed:

    def __init__(self, embed):
        self.embed = embed

    @classmethod
    def from_user_profile(cls, ctx, user_profile: UserProfile, show_help=False):

        user = ctx.message.author if user_profile.user_id == ctx.message.author.id else ctx.get.member(user_profile.user_id)

        if not user:
            footer="Note: Discord User might appear a numerical value if I don't share a server with the user anymore."

            ign = f"{', '.join(user_profile['ign'])}" if user_profile['ign'] else None

            embed = Embeds.make_embed(header=f"Member Found - {ign}", footer=footer)
            embed.add_field(name="Discord user", value=f"<@{user_profile.user_id}>", inline=True)
            if ign:
                embed.add_field(name="**IGN**", value=f"**{ign}**", inline=True)

            return cls(embed)


        show_help = show_help if show_help is not None else user.id == ctx.message.author.id


        silph, trainer_code, ign, pokebattler_id = (user_profile['silph_id'], user_profile['trainer_code'], user_profile['ign'], user_profile['pokebattler_id'])
        if silph:
            silph = f"[Traveler Card](https://sil.ph/{silph.lower()})"

        embed = Embeds.make_embed(header=f"Trainer Profile for {user.display_name}", msg_color=user.colour, header_icon=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)

        if not show_help:
            embed.add_field(name="Discord user", value=f"<@{user.id}>", inline=True)

        ign = f"**{', '.join(ign)}**" if ign else "set using \n`!profile ign`" if show_help else None
        if ign:
            embed.add_field(name="**IGN**", value=f"{ign}", inline=True)

        trainer_code = f"**{', '.join(trainer_code)}**" if trainer_code else "set using \n`!profile trainer-code`" if show_help else None
        if trainer_code:
            embed.add_field(name="**Trainer Code**", value=f"{trainer_code}", inline=True)

        silph = silph if silph else "set using \n`!profile silph`" if show_help else None
        if silph:
            embed.add_field(name="**Silph Road**", value=f"{silph}", inline=True)


        pokebattler_id = pokebattler_id if pokebattler_id else 'set using \n`!profile pokebattler`' if show_help else None
        if pokebattler_id:
            embed.add_field(name="**Pokebattler Id**", value=f"{pokebattler_id}", inline=True)

        # leaderboard_list = ['lifetime']
        #
        # trainer_profile = user_profile.reports_dict
        #
        # for leaderboard in leaderboard_list:
        #     reports_text = "**Raids : {} | Eggs : {} | Wilds : {} | Research : {}**".format(
        #         trainer_profile.setdefault(leaderboard, {}).get('raids', 0),
        #         trainer_profile.setdefault(leaderboard, {}).get('eggs', 0),
        #         trainer_profile.setdefault(leaderboard, {}).get('wilds', 0),
        #         trainer_profile.setdefault(leaderboard, {}).get('quests', 0))
        #
        #     embed.add_field(name="**Leaderboard ({}) :**".format(leaderboard.capitalize()), value=f"{reports_text}", inline=False)

        return cls(embed)


