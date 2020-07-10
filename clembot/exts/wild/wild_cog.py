from discord.ext import commands

from clembot.config.constants import ClembotReactions
from clembot.core.bot import group
from clembot.core.commands import Cog
from clembot.core.error_handler import wrap_error
from clembot.core.logs import Logger
from clembot.exts.gymmanager.gym import POILocationConverter
from clembot.exts.pkmn.pokemon import PokemonConverter, PokemonCache
from clembot.exts.wild.wild import Wild
from clembot.utilities.utils import snowflake


class WildCog(commands.Cog):


    wild_SYNTAX_ATTRIBUTE = ['gym', 'others']

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.pickup_wilddata())


    async def pickup_wilddata(self):
        await PokemonCache.load_cache_from_dbi(self.bot.dbi)
        for rcrd in await Wild.find_all(self.bot):
            self.bot.loop.create_task(self.pickup_wild(rcrd))


    async def pickup_wild(self, rcrd):
        Logger.info(f"pickup_wild({rcrd.get('wild_id', None)})")
        wild = await Wild.from_db_dict(self.bot, rcrd)
        wild.monitor_task = wild.create_task_tuple(wild.monitor_status())


    @group(pass_context=True, hidden=True, aliases=["wild"])
    async def cmd_wild(self, ctx, pokemon: PokemonConverter, *loc):
        """Reports a wild spawn
        **Arguments**
        *pokemon* The name of the wild pokemon
        *location* The location of the spawn

        If the location is a gym, directions will be accruate otherwise I will
        just provide a link for **location** + city of the channel.
        """

        timezone = await ctx.guild_metadata(key='timezone')
        wild_id = next(snowflake.create())
        location = await POILocationConverter.convert(ctx, ' '.join(loc))

        wild = Wild(self.bot, wild_id=wild_id, guild_id=ctx.guild.id, reporter_id=ctx.message.author.id,
                    pkmn=pokemon, location=location, timezone=timezone)

        wild_report = await ctx.send(embed=wild.wild_embed(ctx))
        wild.set_message(wild_report)
        await wild.insert()
        self.bot.loop.create_task(wild.monitor_status())

    @group(pass_context=True, hidden=True, aliases=["wilds"])
    async def cmd_wilds(self, ctx ):
        pass

    @cmd_wilds.command(pass_context=True, hidden=True, aliases=["report"])
    async def cmd_wild_report(self, ctx, some1, some2):
        pass


    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        wild = Wild.by_message.get(payload.message_id, None)
        if wild:
            emoji = str(payload.emoji)

            if ClembotReactions.DESPAWNED == emoji:
                await wild.despawn()
            elif ClembotReactions.ON_MY_WAY == emoji:
                pass
