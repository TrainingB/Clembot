import asyncio
import textwrap

from clembot.config import config_template
from clembot.config.constants import Icons
from clembot.core.bot import group
from clembot.core.commands import Cog
from clembot.core.error_handler import InvalidInputError
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.exts.draft.draft import CUIDGenerator
from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.utilities.timezone import timehandler as TH
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.snowflake import Snowflake
from clembot.utilities.utils.utilities import Utilities

guild_dict = {}

class Research:

    by_id = dict()
    by_message = dict()
    by_cuid = dict()


    def __init__(self, bot, research_id=None, research_cuid=None, guild_id=None, channel_id=None, message_id=None, reporter_id=None,
                 location=None, quest_info=None, reward=None, reported_time=None, reset_time=None, timezone=None):
        self.bot = bot
        self.research_id = research_id
        self.research_cuid = research_cuid
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.reporter_id = reporter_id
        self.location = location
        self.quest_info = quest_info
        self.reward = reward
        self.timezone = timezone
        self.reported_time = TH.current_epoch(second_precision=False) if reported_time is None else reported_time
        to_midnight = 300 # (24 * 60 * 60) - int((self.reported_time - TH.convert_to_timestamp("12:00 AM", self.timezone)))
        self.reset_time = ( self.reported_time + to_midnight ) if reset_time is None else reset_time

        Research.cache(self)


    def to_db_dict(self):
        state = {
            'research_id': self.research_id,
            'research_cuid': self.research_cuid,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'message_id': self.message_id,
            'reporter_id': self.reporter_id,
            'location': self.location,
            'quest_info': self.quest_info,
            'reward': self.reward,
            'reported_time': self.reported_time,
            'reset_time': self.reset_time,
            'timezone': self.timezone,
        }
        return state

    @classmethod
    def from_db_dict(cls, bot, db_dict):
        research_id, research_cuid, guild_id, channel_id, message_id, reporter_id, location, quest_info, reward, reported_time, reset_time, timezone = [
            db_dict.get(attr, None) for attr in ['research_id', 'research_cuid', 'guild_id', 'channel_id', 'message_id',
                                                 'reporter_id', 'location', 'quest_info', 'reward', 'reported_time',
                                                 'reset_time', 'timezone']]
        research = cls(bot, research_id=research_id, research_cuid=research_cuid, guild_id=guild_id, channel_id=channel_id,
                    message_id=message_id,reporter_id=reporter_id, location=location, quest_info=quest_info,
                    reward=reward, reported_time=reported_time, reset_time=reset_time, timezone=timezone)

        return research

    @classmethod
    def cache(cls, research):
        cls.by_message[research.message_id] = research
        cls.by_id[research.research_id] = research
        cls.by_cuid[research.research_cuid] = research


    @classmethod
    def evict(cls, research):
        cls.by_message.pop(research.message_id, None)
        cls.by_id.pop(research.research_id, None)
        cls.by_cuid.pop(research.research_cuid, None)

    @staticmethod
    async def find_all(bot):
        research_table = bot.dbi.table('research_report')
        research_table_query = research_table.query().select()
        record_list = await research_table_query.getjson()
        return record_list


    @staticmethod
    async def find_by_cuid(bot, cuid):
        research_table = bot.dbi.table('research_report')
        select_research = await research_table.query().select().where(research_cuid=cuid).getjson()
        if len(select_research) > 0:
            research = Research.from_db_dict(bot, select_research[0])
            return research
        return None

    async def monitor_status(self):
        expires_at = self.reset_time
        sleep_time = expires_at - TH.current_epoch()
        await asyncio.sleep(sleep_time)
        await self.expire_research()


    async def expire_research(self):
        channel = self.bot.get_channel(self.channel_id)
        if channel is not None:
            message = await channel.fetch_message(self.message_id)
            if message is not None:
                await message.edit(embed=Embeds.make_embed(content="This research task has expired!"))

        await self.delete()


    @classmethod
    async def find_by_filter_text(cls, bot, guild_id, channel_id, filter_text):
        query = list_research_sql
        query_args = [guild_id, channel_id]
        if filter_text:
            query = list_research_filter_sql
            query_args.append(f'%{filter_text.lower()}%')

        research_record_list = await bot.dbi.execute_query_json(query, *query_args)
        research_list = [cls.from_db_dict(bot, research_record) for research_record in research_record_list]
        return research_list


    def __str__(self):
        return f"{self.research_cuid} Reported: {TH.as_local_readable_time(self.reported_time, self.timezone)} Reset : {TH.as_local_readable_time(self.reset_time, self.timezone)} "

    async def insert(self):
        research_table = self.bot.dbi.table('research_report')
        research_table_insert = research_table.insert(**self.to_db_dict())
        await research_table_insert.commit()
        Research.cache(self)


    async def delete(self):
        research_table = self.bot.dbi.table('research_report')
        research_table_delete = research_table.query().where(research_id=self.research_id)
        await research_table_delete.delete()
        Research.evict(self)


    async def embed(self, ctx):
        return (await ResearchEmbed.from_research(self, ctx)).embed

class ResearchEmbed:

    def __init__(self, embed):
        self.embed = embed

    @classmethod
    async def from_research(cls, research, ctx):

        reporter = await ctx.get.user(research.reporter_id)
        embed = Embeds.make_embed()
        fields = {
            'Location': [True, '\n'.join(textwrap.wrap(research.location.title(), width=30))],
            'Quest': [True, '\n'.join(textwrap.wrap(research.quest_info.title(), width=30))],
            'Reward': [True, '\n'.join(textwrap.wrap(research.reward.title(), width=30))]
        }

        embed = Embeds.make_embed(fields=fields,
                                  footer=f"Reported by {reporter.display_name} | {research.research_cuid}",
                                  footer_icon=Icons.avatar(reporter), thumbnail=Icons.field_research,
                                  header="Research Report")
        return cls(embed)





class ResearchCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.snowflake = Snowflake()
        self.bot.loop.create_task(self.load_researches())


    async def load_researches(self):
        Logger.info("load_researches()")
        for rcrd in await Research.find_all(self.bot):
            self.bot.loop.create_task(self.load_research(rcrd))
        pass

    async def load_research(self, rcrd):
        research = Research.from_db_dict(self.bot, rcrd)
        self.bot.loop.create_task(research.monitor_status())


    @group(pass_context=True, category='Bot Info', aliases=["research", "re"])
    async def cmd_research(self, ctx):
        """Report Field research
        **Usage:**
        **!research pokestop, quest, reward** - reports a research quest at pokestop for reward. Poke-stop, quest and reward should be separated with a comma (,).

        **!research list** - shows the list of research quests reported in the channel.
        **!research list filter-text** - filters the quests list using the filter-text.

        """

        await ctx.send(
            content=f"invoked_subcommand : {ctx.invoked_subcommand} | subcommand_passed: {ctx.subcommand_passed} ")

        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                await Embeds.message(ctx.channel, f"Use **help research** to see the usage.")
            else:
                prefix = ctx.bot.prefixes.get(ctx.message.guild.id, config_template.default_prefix)
                content_without_prefix = ctx.message.content.replace(prefix, '')
                only_content = content_without_prefix.replace(ctx.invoked_with, '')
                await self.report_research(ctx, only_content)



    async def report_research(self, ctx, args):
        """Report Field research
        
        **Usage:**
        **!research pokestop, quest, reward** - reports a research quest at pokestop for reward. Poke-stop, quest and reward should be separated with a comma (,).

        **!research list** - shows the list of research quests reported in the channel.
        **!research list filter-text** - filters the quests list using the filter-text.

        """
        args_split = args.split(", ")
        if len(args_split) == 3:
            timezone = await ctx.guild_timezone(ctx)
            research_id = self.snowflake.next()
            research_cuid = CUIDGenerator.cuid(research_id)
            location, quest, reward = args_split

            research = Research(self.bot, research_id=research_id, research_cuid=research_cuid,
                                guild_id=ctx.guild.id, channel_id=ctx.channel.id,
                                message_id=ctx.message.id, reporter_id=ctx.message.author.id, location=location,
                                quest_info=quest, reward=reward, timezone=timezone)

            research_response = await ctx.send(embed=await research.embed(ctx))
            research.message_id = research_response.id
            await research.insert()
            self.bot.loop.create_task(research.monitor_status())
            Logger.info(research)

            # TODO: record research report for leader-board
            user_guild_profile = await UserGuildProfile.find(self.bot, user_id=ctx.message.author.id, guild_id=ctx.guild.id)
            user_guild_profile.record_report('quests')
            await user_guild_profile.update()

            return

        raise InvalidInputError(f"`{ctx.prefix}research pokestop or location, quest information, reward information`")



    @cmd_research.command(pass_context=True, category='Bot Info', aliases=["remove"])
    @wrap_error
    async def cmd_research_remove(self, ctx, cuid):

        research = await Research.find_by_cuid(self.bot, cuid)
        if research:
            research.reset_time = TH.current_epoch()
            await research.expire_research()
            await ctx.send(content=f"Research with CUID : {cuid} has been removed.")
        else:
            await Embeds.error(ctx.channel, f"No research found with CUID : {cuid}.")


    @cmd_research.command(pass_context=True, category='Bot Info', aliases=["list"])
    async def cmd_research_list(self, ctx, filter_text=None):
        research_list = await Research.find_by_filter_text(self.bot, ctx.guild.id, ctx.channel.id, filter_text)

        if research_list:
            research_text = []

            for r in research_list:

                reporter = await ctx.get.user(r.reporter_id)
                research_text.append(f':beginner:[{r.research_cuid}] - **Location:** {r.location}, **Quest:** {r.quest_info}, **Reward:** {r.reward}, **Reported by:** {reporter.display_name}')

            return await ctx.send(embed=Embeds.make_embed(header="Research List", header_icon=Icons.research_report,
                                                          content=Utilities.trim_to('\n'.join(research_text), 1900, '\n🔰')))
        else:
            filter_text_clause = f' with **{filter_text}**' if filter_text else ''
            return await ctx.send(embed=Embeds.make_embed(header="Research List", header_icon=Icons.research_report,
                                                          content=f"No research reports are found{filter_text_clause}. Report one using `!research`"))


list_research_sql = """
select * from research_report
    where guild_id = $1
    and channel_id = $2;
"""

list_research_filter_sql = """
select * from research_report
    where guild_id = $1
    and channel_id = $2 
    and (lower(location) like $3 or lower(quest_info) like $3 or lower(reward) like $3);
"""

list_research_by_cuid = """
select * from research_report
    where research_cuid = $1;
"""