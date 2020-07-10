import textwrap

from clembot.config.constants import Icons
from clembot.core.bot import group, command
from clembot.core.commands import Cog
from clembot.core.error_handler import InvalidInputError
from clembot.core.logs import Logger
from clembot.exts.draft.draft import CUIDGenerator
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
        to_midnight = (24 * 60 * 60) - int((self.reported_time - TH.convert_to_timestamp("12:00 AM", self.timezone)))
        self.reset_time = ( self.reported_time + to_midnight ) if reset_time is None else reset_time



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

    @group(pass_context=True, hidden=True, aliases=["research", "re"])
    async def cmd_research(self, ctx, *, args):
        if args:
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

                await research.insert()
                Logger.info(research)
                return await ctx.send(embed=await research.embed(ctx))

        raise InvalidInputError(f"`{ctx.prefix}research pokestop or location, quest information, reward information`")



    @cmd_research.command(pass_context=True, hidden=True, aliases=["remove"])
    async def cmd_research_remove(self, ctx, research_cuid):

        print("cmd_research_remove")

        pass

    @command(pass_context=True, hidden=True, aliases=["relist"])
    async def cmd_list_research(self, ctx, filter_text=None):
        research_list = await Research.find_by_filter_text(self.bot, ctx.guild.id, ctx.channel.id, filter_text.lower())

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

# @command(aliases=["re"])
# # @checks.nonraidchannel()
# async def research(ctx, *, args = None):
#     """Report Field research
#     Guided report method with just !research. If you supply arguments in one
#     line, avoid commas in anything but your separations between pokestop,
#     quest, reward. Order matters if you supply arguments. If a pokemon name
#     is included in reward, a @mention will be used if role exists.
#
#     Usage: !research [pokestop, quest, reward]"""
#     try:
#         message = ctx.message
#         channel = message.channel
#         author = message.author
#
#         guild = message.guild
#         timestamp = (message.created_at + datetime.timedelta(hours=guild_dict[message.channel.guild.id]['offset']))
#         Logger.info(message.created_at)
#         Logger.info(timestamp)
#
#         error = False
#         research_id = '%04x' % randrange(16 ** 4)
#         research_embed = discord.Embed(colour=discord.Colour.gold()).set_thumbnail(url='https://raw.githubusercontent.com/TrainingB/Clembot/v1-rewrite/images/field-research.png?cache={0}'.format(CACHE_VERSION))
#         research_embed.set_footer(text=_('Reported by @{author} - {timestamp} | {research_id}').format(author=author.display_name, timestamp=timestamp.strftime(_('%I:%M %p (%H:%M)')), research_id=research_id), icon_url=author.avatar_url_as(format=None, static_format='jpg', size=32))
#
#         reward_role = None
#
#         while True:
#             if args:
#                 research_split = message.clean_content.replace("!research ","").split(", ")
#                 if len(research_split) != 3:
#                     error = _("entered an incorrect amount of arguments.\n\nUsage: **!research** or **!research <pokestop>, <quest>, <reward>**")
#                     break
#                 location, quest, reward = research_split
#                 research_embed.add_field(name=_("**Location:**"),value='\n'.join(textwrap.wrap(location.title(), width=30)),inline=True)
#                 research_embed.add_field(name=_("**Quest:**"),value='\n'.join(textwrap.wrap(quest.title(), width=30)),inline=True)
#                 research_embed.add_field(name=_("**Reward:**"),value='\n'.join(textwrap.wrap(reward.title(), width=30)),inline=True)
#
#                 reward_role = discord.utils.get(ctx.message.guild.roles, name=reward)
#
#                 break
#             else:
#                 research_embed.add_field(name=_('**New Research Report**'), value=_("Beep Beep! I'll help you report a research quest!\n\nFirst, I'll need to know what **pokestop** you received the quest from. Reply with the name of the **pokestop**. You can reply with **cancel** to stop anytime."), inline=False)
#                 pokestopwait = await channel.send(embed=research_embed)
#                 try:
#                     pokestopmsg = await Clembot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
#                 except asyncio.TimeoutError:
#                     pokestopmsg = None
#                 await pokestopwait.delete()
#                 if not pokestopmsg:
#                     error = _("took too long to respond")
#                     break
#                 elif pokestopmsg.clean_content.lower().strip()  == 'cancel':
#                     error = _("cancelled the report")
#                     break
#                 elif pokestopmsg:
#                     location = pokestopmsg.clean_content
#                 await pokestopmsg.delete()
#                 research_embed.add_field(name=_("**Location:**"),value='\n'.join(textwrap.wrap(location.title(), width=30)),inline=True)
#                 research_embed.set_field_at(0, name=research_embed.fields[0].name, value=_("Great! Now, reply with the **quest** that you received from **{location}**. You can reply with **cancel** to stop anytime.\n\nHere's what I have so far:").format(location=location), inline=False)
#                 questwait = await channel.send(embed=research_embed)
#                 try:
#                     questmsg = await bot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
#                 except asyncio.TimeoutError:
#                     questmsg = None
#                 await questwait.delete()
#                 if not questmsg:
#                     error = _("took too long to respond")
#                     break
#                 elif questmsg.clean_content.lower().strip() == 'cancel':
#                     error = _("cancelled the report")
#                     break
#                 elif questmsg:
#                     quest = questmsg.clean_content
#                 await questmsg.delete()
#                 research_embed.add_field(name=_("**Quest:**"),value='\n'.join(textwrap.wrap(quest.title(), width=30)),inline=True)
#                 research_embed.set_field_at(0, name=research_embed.fields[0].name, value=_("Fantastic! Now, reply with the **reward** for the **{quest}** quest that you received from **{location}**. You can reply with **cancel** to stop anytime.\n\nHere's what I have so far:").format(quest=quest, location=location), inline=False)
#                 rewardwait = await channel.send(embed=research_embed)
#                 try:
#                     rewardmsg = await bot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
#                 except asyncio.TimeoutError:
#                     rewardmsg = None
#                 await rewardwait.delete()
#                 if not rewardmsg:
#                     error = _("took too long to respond")
#                     break
#                 elif rewardmsg.clean_content.lower().strip() == 'cancel':
#                     error = _("cancelled the report")
#                     break
#                 elif rewardmsg:
# 	                reward = rewardmsg.clean_content
#                 await rewardmsg.delete()
#                 research_embed.add_field(name=_("**Reward:**"),value='\n'.join(textwrap.wrap(reward.title(), width=30)),inline=True)
#                 research_embed.remove_field(0)
#                 break
#         if not error:
#             roletest = ""
#             pkmn_match = next((p for p in pkmn_info['pokemon_list'] if re.sub('[^a-zA-Z0-9]', '', p) == re.sub('[^a-zA-Z0-9]', '', reward.lower())), None)
#             if pkmn_match:
#                 reward_role = discord.utils.get(guild.roles, name=pkmn_match)
#
#             if reward_role:
#                 pokemon_reward = f" for {reward_role.mention}"
#             else:
#                 pokemon_reward = ""
#             research_msg = f"Beep Beep! A field research{pokemon_reward} has been reported by {ctx.message.author.mention}!"
#             await ctx.message.channel.send(content=research_msg)
#
#             research_embed.__setattr__('title', f"A field research has been reported.")
#             confirmation = await channel.send(embed=research_embed)
#             research_dict = copy.deepcopy(guild_dict[guild.id].get('questreport_dict',{}))
#             research_dict[confirmation.id] = {
#                 'research_id' : research_id,
#                 'exp':time.time() + to_midnight,
#                 'expedit':"delete",
#                 'reportmessage':message.id,
#                 'reportchannel':channel.id,
#                 'reportauthor':author.id,
#                 'reportauthorname':author.name,
#                 'location':location,
#                 'quest':quest,
#                 'reward':reward
#             }
#             guild_dict[guild.id]['questreport_dict'] = research_dict
#             try:
#                 await message.delete()
#             except Exception:
#                 pass
#             await record_reported_by(message.guild.id, message.channel.name, message.author.id, 'quests')
#         else:
#             research_embed.clear_fields()
#             research_embed.add_field(name='**Research Report Cancelled**', value=_("Beep Beep! Your report has been cancelled because you {error}! Retry when you're ready.").format(error=error), inline=False)
#             confirmation = await channel.send(embed=research_embed)
#             await asyncio.sleep(10)
#             await confirmation.delete()
#             await message.delete()
#
#
#
#
#     except Exception as error:
#         Logger.info(error)
#         Logger.info(error)
#         Logger.info(traceback.print_exc())
#
#
#
# @unused_list.command(pass_context=True, hidden=True)
# @checks.nonraidchannel()
# async def research(ctx):
#     """List the quests for the channel
#
#     Usage: !list research"""
#
#     print(f"list research called {ctx.message.author}")
#     listmsg = _('**Beep Beep!**')
#     listmsg += await _researchlist(ctx)
#     await _send_message(ctx.channel, description=listmsg)
#
# async def _researchlist(ctx):
#     try:
#         args = ctx.message.clean_content.lower().split()
#         filter_text = None if len(args) < 3 else args[2]
#
#         research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict',{}))
#         questmsg = ""
#         for questid in research_dict:
#             if research_dict[questid]['reportchannel'] == ctx.message.channel.id:
#                 if not filter_text or filter_text in research_dict[questid]['quest'].title().lower() or filter_text in research_dict[questid]['reward'].title().lower():
#                     try:
#                         questreportmsg = await ctx.message.channel.fetch_message(questid)
#                         questauthor = ctx.channel.guild.get_member(research_dict[questid]['reportauthor'])
#                         if questauthor :
#                             author_display_name = questauthor.display_name
#                         else:
#                             author_display_name = research_dict[questid]['reportauthorname']
#                         research_id = research_dict[questid]['research_id']
#                         questmsg += _('\n🔰')
#                         if ctx.message.author.bot or filter_text :
#                             questmsg += _("**[{research_id}]** - {location} / {quest} / {reward} / {author}".format(research_id=research_id,location=research_dict[questid]['location'].title(),quest=research_dict[questid]['quest'].title(),reward=research_dict[questid]['reward'].title(), author=author_display_name))
#                         else:
#                             questmsg += _("**[{research_id}]** - **Location**: {location}, **Quest**: {quest}, **Reward**: {reward}, **Reported By**: {author}".format(research_id=research_id, location=research_dict[questid]['location'].title(), quest=research_dict[questid]['quest'].title(), reward=research_dict[questid]['reward'].title(), author=author_display_name))
#                     except discord.errors.NotFound:
#                         pass
#         if questmsg:
#             listmsg = _(' **Here\'s the current research reports for {channel}**\n{questmsg}').format(channel=ctx.message.channel.name.capitalize(), questmsg=utilities.trim_to(questmsg, 1900, '\n🔰') )
#         else:
#             if len(args) < 3 :
#                 listmsg = _(" There are no research reports. Report one with **!research**")
#             else:
#                 listmsg = _(" There are no research reports with **{quest}**. Report one with **!research**".format(quest=filter_text))
#         return listmsg
#     except Exception as error:
#         Logger.error(error)
#         print(error)
#
# @Clembot.command(pass_context=True, hidden=True, aliases=["remove-research"])
# async def _remove_research(ctx, research_id=None):
#     if research_id is None:
#         return await _send_error_message(ctx.channel, "Please provide the 4 char code for the research quest!")
#
#     if research_id == 'all':
#         guild_dict[ctx.guild.id]['questreport_dict'] = {}
#         return await _send_message(ctx.channel, "**{0}** Research list has been cleared.".format(ctx.message.author.display_name, research_id))
#
#     research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict', {}))
#     questmsg = ""
#     delete_quest_id = None
#     for questid in research_dict:
#         if research_dict[questid]['reportchannel'] == ctx.message.channel.id:
#             try:
#                 quest_research_id = research_dict[questid]['research_id']
#                 quest_reported_by = research_dict[questid]['reportauthor']
#                 if quest_research_id == research_id:
#                     await record_error_reported_by(ctx.message.guild.id, ctx.message.channel.name, quest_reported_by,
#                                              'quests')
#                     del research_dict[questid]
#                     guild_dict[ctx.guild.id]['questreport_dict'] = research_dict
#                     research_report = await ctx.channel.fetch_message(questid)
#                     if research_report:
#                         await research_report.delete()
#                     return await _send_message(ctx.channel, "**{0}** Research # **{1}** has been removed.".format(ctx.message.author.display_name,research_id))
#                     break
#             except discord.errors.NotFound:
#                 pass
#     return await _send_error_message(ctx.channel, "**{0}** No Research found with **{1}** .".format(ctx.message.author.display_name, research_id))
#
# @Clembot.command(pass_context=True, hidden=True, aliases=["research-status"])
# async def _research_status(ctx, research_id=None):
#
#     questmsg = ""
#     delete_quest_id = None
#     research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict', {}))
#
#     Logger.info(json.dumps(research_dict, indent=2))
#
#     if research_id is None:
#         return await _send_error_message(ctx.channel, "Please provide the 4 char code for the research quest!")
#
#     for questid in research_dict:
#         if research_dict[questid]['reportchannel'] == ctx.message.channel.id:
#             try:
#                 quest_research_id = research_dict[questid]['research_id']
#                 quest_reported_by = research_dict[questid]['reportauthor']
#                 if quest_research_id == research_id:
#                     quest_research_dict = copy.deepcopy(guild_dict[ctx.guild.id].get('questreport_dict', {})).get(questid,{})
#                     return await _send_message(ctx.channel, json.dumps(quest_research_dict, indent=2))
#
#             except discord.errors.NotFound:
#                 pass
#     return await _send_error_message(ctx.channel, "**{0}** No Research found with **{1}** .".format(ctx.message.author.display_name, research_id))
#
#
