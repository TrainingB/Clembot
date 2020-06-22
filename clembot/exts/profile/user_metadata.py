import json

import pydash as _

from clembot.utilities.utils.embeds import Embeds


class Serializable:

    @staticmethod
    def serialize(data_dict):
        return _.map_values(data_dict, lambda val: json.dumps(val) if isinstance(val, dict) else val)

    @staticmethod
    def deserialize(data_dict, dict_fields = ['config']):
        return { k : json.loads(v) if k in dict_fields and v is not None else v for (k, v) in data_dict.items()}


class UserMetadata:

    dict_fields = ['reports_dict', 'info']

    def __init__(self, bot, user_id, guild_id, trainer_code = [], ign = [], silph_id = None, pokebattler_id = None, reports_dict = dict(), info = dict()):
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.trainer_code = trainer_code
        self.ign = ign
        self.silph_id = silph_id
        self.pokebattler_id = pokebattler_id
        self.reports_dict = reports_dict
        self.info = info

    @classmethod
    def from_db_dict(cls, bot, user_dict = dict()):
        user_id, guild_id, trainer_code, ign, silph_id, pokebattler_id = (user_dict.get(name) for name in ['user_id', 'guild_id', 'trainer_code', 'ign', 'silph_id', 'pokebattler_id'])
        reports_dict, info = (json.loads(user_dict.get(name)) for name in ['reports_dict', 'info'])

        return cls(bot, user_id, guild_id, trainer_code, ign, silph_id, pokebattler_id, reports_dict, info)

    def to_db_dict(self):
        d = {
            'user_id' : self.user_id,
            'guild_id' : self.guild_id,
            'trainer_code' : self.trainer_code,
            'ign' : self.ign,
            'silph_id' : self.silph_id,
            'pokebattler_id' : self.pokebattler_id,
            'reports_dict' : self.reports_dict,
            'info' : self.info

        }
        return d

    @classmethod
    async def data(cls, bot, user_id, guild_id) -> dict():
        report_user_query = bot.dbi.table('user_metadata').query()
        _data = report_user_query.where(user_id=user_id, guild_id=guild_id)
        db_record = await _data.get()

        if db_record:
            user_metadata = UserMetadata.from_db_dict(bot, dict(db_record[0]))
        else:

            user_metadata = UserMetadata(bot, user_id, guild_id)
            await user_metadata.insert()

        return user_metadata

    async def update(self):
        user_metadata_table = self.bot.dbi.table('user_metadata')
        update_dict=Serializable.serialize(Serializable.deserialize(self.to_db_dict()))
        channel_metadata_table_update = user_metadata_table.update(**update_dict).where(user_id=self.user_id, guild_id=self.guild_id)
        await channel_metadata_table_update.commit()

    async def insert(self):
        user_metadata_table = self.bot.dbi.table('user_metadata')
        update_dict=Serializable.serialize(Serializable.deserialize(self.to_db_dict()))
        channel_metadata_table_insert = user_metadata_table.insert(**update_dict)
        await channel_metadata_table_insert.commit()


    def embed(self, ctx):
        return (ProfileEmbed.from_user_metadata(ctx, self)).embed


class ProfileEmbed:

    def __init__(self, embed):
        self.embed = embed

    @classmethod
    def from_user_metadata(cls, ctx, user_metadata: UserMetadata):

        user = ctx.message.author if user_metadata.user_id == ctx.message.author.id else ctx.get.member(user_metadata.user_id)

        silph, trainer_code, ign, pokebattler_id = (user_metadata.silph_id, user_metadata.trainer_code, user_metadata.ign, user_metadata.pokebattler_id)
        if silph:
            silph = f"[Traveler Card](https://sil.ph/{silph.lower()})"

        embed = Embeds.make_embed(header=f"Trainer Profile for {user.display_name}", msg_color=user.colour, header_icon=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)

        if trainer_code:
            embed.add_field(name="**Trainer Code**", value=f"**{', '.join(trainer_code)}**", inline=True)
        else:
            embed.add_field(name="**Trainer Code**", value="set using `!profile trainer-code`", inline=True)

        if ign:
            embed.add_field(name="**IGN**", value=f"**{', '.join(ign)}**", inline=True)
        else:
            embed.add_field(name="**IGN**", value="set using `!profile ign`", inline=True)

        embed.add_field(name="**Silph Road**", value=f"{silph or 'set using `!profile silph`'}", inline=True)
        embed.add_field(name="**Pokebattler Id**", value=f"{pokebattler_id or 'set using `!profile pokebattler`'}", inline=True)

        leaderboard_list = ['lifetime']

        trainer_profile = user_metadata.reports_dict

        for leaderboard in leaderboard_list:
            reports_text = "**Raids : {} | Eggs : {} | Wilds : {} | Research : {}**".format(
                trainer_profile.setdefault(leaderboard, {}).get('raids', 0),
                trainer_profile.setdefault(leaderboard, {}).get('eggs', 0),
                trainer_profile.setdefault(leaderboard, {}).get('wilds', 0),
                trainer_profile.setdefault(leaderboard, {}).get('quests', 0))

            embed.add_field(name="**Leaderboard ({}) :**".format(leaderboard.capitalize()), value=f"{reports_text}", inline=False)

        return cls(embed)