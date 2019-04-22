from . import raid_info


class RaidCog(Cog):

    def __init__(self, bot):
        bot.raid_info = raid_info
        self.bot = bot

class Raid:

    def __init__(self, bot, guild_id, gym=None, level=None, pkmn=None, hatch=None, end=None, tz=None):
        self.bot = bot
        self.guild_id = guild_id
        self.gym = gym
        self.level = level
        self.pkmn = pkmn
        self.hatch = hatch
        self.end = end
        self.tz = tz


    @property
    def status(self):

        if self.hatch and time.time() < self.hatch:
            return "egg"
        elif not self.pkmn:
            return "hatched"
        elif time.time() < self.end:
            return "active"
        else:
            return "expired"

    @property
    def max_hatch(self):
        level = self.level
        max_times = self.bot.raid_info.raid_times[level]
        return max_times[0]

    @property
    def max_active(self):
        level = self.level
        max_times = self.bot.raid_info.raid_times[level]
        return max_times[1]

    gym_format = {
        'name' : 'name',
        'url' : 'url'
    }

    async def channel_name(self):
        if isinstance(self.gym, dict):
            gym_name = await self.gym['name']
        else:
            gym_name = self.gym

        if self.pkmn:
            boss_name = await self.pkmn
            return f"{boss_name}-{gym_name}"
        else:
            if self.status == 'hatched':
                return f"hatched-{self.level}-{gym_name}"
            else:
                return f"egg-{self.level}-{gym_name}"



class RaidEmbed:

    def __init__(self, embed):
        self.embed = embed

    where_index = 1
    details_index = 2
    weakness_index = 3

    def set_boss(self, boss_dict):

        name = boss_dict['name']
        cp_range = boss_dict['cp_range']
        weakness = boss_dict['weakness']

        self.embed.set_field_at(RaidEmbed.details_index, name="Details", value=name)
        self.embed.set_field_at(RaidEmbed.details_index, name="Weakness", value=weakness)

        return self

