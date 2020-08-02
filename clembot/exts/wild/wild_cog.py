from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config.constants import MyEmojis
from clembot.core.bot import group
from clembot.core.commands import Cog
from clembot.core.logs import Logger
from clembot.exts.config import channel_checks
from clembot.exts.gymmanager.gym import POILocationConverter
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.exts.wild.wild import Wild
from clembot.utilities.utils import snowflake


class WildCog(commands.Cog):


    wild_SYNTAX_ATTRIBUTE = ['gym', 'others']

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.load_wild_reports())


    async def load_wild_reports(self):
        await Pokemon.load(self.bot)
        for rcrd in await Wild.find_all(self.bot):
            self.bot.loop.create_task(self.load_wild_report(rcrd))


    async def load_wild_report(self, rcrd):
        Logger.info(f"load_wild_report({rcrd.get('wild_id', None)})")
        wild = await Wild.from_db_dict(self.bot, rcrd)
        wild.monitor_task = wild.create_task_tuple(wild.monitor_status())


    @group(pass_context=True, hidden=True, aliases=["wild"])
    @channel_checks.wild_report_enabled()
    async def cmd_wild(self, ctx, pokemon: Pokemon, *loc):
        """Reports a wild spawn
        **Arguments**
        *pokemon* The name of the wild pokemon
        *location* The location of the spawn

        If the location is a gym, directions will be accruate otherwise I will
        just provide a link for **location** + city of the channel.
        """

        timezone = await ctx.timezone()
        wild_id = next(snowflake.create())
        if len(loc) == 0:
            raise BadArgument("Ohh, that's awesome, but where? I can't create a report without location.")
        location = await POILocationConverter.convert(ctx, ' '.join(loc))

        wild = Wild(self.bot, wild_id=wild_id, guild_id=ctx.guild.id, reporter_id=ctx.message.author.id,
                    pkmn=pokemon, location=location, timezone=timezone)

        wild_report = await ctx.send(embed=wild.wild_embed(ctx))
        await wild_report.add_reaction(MyEmojis.DESPAWNED)
        wild.set_message(wild_report)
        await wild.insert()


        # TODO: record wild report for leader-board
        user_guild_profile = await UserGuildProfile.find(self.bot, user_id=ctx.message.author.id, guild_id=ctx.guild.id)
        user_guild_profile.record_report('wilds')
        await user_guild_profile.update()

        self.bot.loop.create_task(wild.monitor_status())

    @group(pass_context=True, hidden=True, aliases=["wilds"])
    async def cmd_wilds(self, ctx ):
        pass

    @cmd_wilds.command(pass_context=True, hidden=True, aliases=["report"])
    async def cmd_wild_report(self, ctx, some1, some2):
        pass


    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        wild = Wild.by_message.get(payload.message_id, None)
        if wild:
            emoji = str(payload.emoji)
            if MyEmojis.DESPAWNED == emoji:
                await wild.despawn()

