from enum import Enum

from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds


#
# badge_master
#     badge_id serial,
#     name text,
#     description text,
#     guild_id bigint,
#     emoji_id bigint,
#     emoji text,
#     image_url text,
#     trainers_earned int,
#     last_awarded_on timestamp,
#     active boolean


class Badge:

    TABLE_NAME = 'badge_master'

    class BadgeType(Enum):
        ADMIN_ONLY = 'admin-only'
        GLOBAL = 'global'



    def __init__(self, bot, db_dict=dict()):
        self.bot = bot
        self.db_dict = {
            'name' : None,
            'description': None,
            'guild_id': None,
            'emoji_id': None,
            'emoji': None,
            'image_url': None,
            'trainers_earned': None,
            'last_awarded_on': None,
            'active' : None,
            'badge_type' : None
        }
        self.db_dict.update(db_dict)


    @property
    def badge_id(self):
        return self['badge_id']

    @property
    def is_admin_only(self):
        return self['badge_type'] == Badge.BadgeType.ADMIN_ONLY.value

    @property
    def is_global(self):
        return self['badge_type'] == Badge.BadgeType.GLOBAL.value

    def is_allowed_for_guild(self, guild_id):
        return self.is_global or self['guild_id'] == guild_id


    def update_dict(self, db_dict):
        self.db_dict.update(db_dict)

    async def insert(self):
        table = self.bot.dbi.table(Badge.TABLE_NAME)
        insert_query = table.insert(**self.db_dict)
        await insert_query.commit()


    async def update(self):
        table = self.bot.dbi.table(Badge.TABLE_NAME)
        update_query = table.update(**self.db_dict).where(badge_id=self.badge_id)
        await update_query.commit()


    async def delete(self):
        """Deletes the raid record from DB and evicts from cache."""
        table = self.bot.dbi.table(Badge.TABLE_NAME)
        delete_query = table.query().where(badge_id=self.badge_id)
        await delete_query.delete()

    @staticmethod
    async def find_all(bot):
        table = bot.dbi.table(Badge.TABLE_NAME)
        query = table.query().select()
        auto_response_list = await query.getjson()
        return auto_response_list

    @classmethod
    async def find_first(cls, bot, badge_id):
        table = bot.dbi.table(Badge.TABLE_NAME)
        query = table.query().select().where(badge_id=badge_id)
        auto_response_list = await query.getjson()
        if auto_response_list:
            return cls(bot, auto_response_list[0])
        return None

    @classmethod
    async def find_first_by(cls, bot, **kwargs):
        table = bot.dbi.table(Badge.TABLE_NAME)
        query = table.query().select().where(**kwargs)
        try:
            auto_response_list = await query.getjson()
            if auto_response_list:
                return cls(bot, auto_response_list[0])
        except Exception as error:
            Logger.info(f"{error}")

        return None

    @classmethod
    async def find_by(cls, bot, **kwargs):
        table = bot.dbi.table(Badge.TABLE_NAME)
        query = table.query().select().where(**kwargs)
        try:
            auto_response_list = await query.getjson()
            if auto_response_list:
                badge_list = [cls(bot, badge_record) for badge_record in auto_response_list]
            else:
                badge_list = []

        except Exception as error:
            Logger.info(f"{error}")

        return badge_list or []


    def __getitem__(self, item):
        """use [] operator to access members, simpler to create entity objects"""
        return self.db_dict.get(item)


    def __setitem__(self, key, value):
        """use [] operator to access members, simpler to create entity objects. Handles array kind of values."""
        self.db_dict[key] = value


    def embed(self, ctx):
        return (BadgeEmbed.from_badge_dict(ctx, self.db_dict)).embed


class BadgeEmbed:

    def __init__(self, embed):
        self.embed = embed

    @classmethod
    def from_badge_dict(cls, ctx, current_badge: int):


        badge_fields = { "Distributed By": ctx.get.guild(current_badge['guild_id']).name, "Trainer(s) Earned":  f"{current_badge['trainers_earned']}"}

        footer = "Badge Status : Inactive"
        if current_badge['active']:
            footer = "Badge Status : Active"

        if current_badge['last_awarded_on']:
            footer = f"{footer} | Last awarded on: {current_badge['last_awarded_on']}"


        embed=Embeds.make_embed(header=f"#{current_badge['badge_id']} - {current_badge['name']}", content=f"*{current_badge['description']}*",
                        thumbnail=current_badge['image_url'], fields = badge_fields, footer=footer,
                        footer_icon=ctx.get.guild(current_badge['guild_id']).icon_url, inline=True)

        return cls(embed)