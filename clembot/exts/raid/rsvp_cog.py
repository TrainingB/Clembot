from discord.ext import commands

from clembot.config.constants import Icons
from clembot.core.bot import command
from clembot.core.commands import Cog
from clembot.exts.raid import raid_checks

from clembot.exts.raid.errors import RSVPNotEnabled
from clembot.exts.raid.raid import RSVPEnabled, Raid, RaidParty
from clembot.utilities.utils.embeds import Embeds


class RSVPCog(commands.Cog):
    """
    !i - interested
    !ir - interested remotely
    !ii - interested in remote invite
    !h - here at raid
    !hr - here remotely
    !c - coming
    """


    def __init__(self, bot):
        self.bot = bot
        self._dbi = bot.dbi

    @staticmethod
    def get_rsvp_source(ctx) -> RSVPEnabled:

        raid = Raid.by_channel.get(ctx.channel.id)
        if raid is not None:
            return raid

        raid_party = RaidParty.by_channel.get(ctx.channel.id)
        if raid_party is not None:
            print(raid_party)
            return raid_party

        return None

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        """Method to handle Cog specific errors"""
        if isinstance(error, RSVPNotEnabled):
            await Embeds.error(ctx.channel, 'RSVP commands are not enabled for this channel.', ctx.message.author)

    @command(pass_context=True, aliases=["rsvp"])
    async def cmd_rsvp(self, ctx):

        status = {
            'Indicate your status using:' : [False, f'!i  - interested\n!c  - coming (on the way)\n!h  - here at raid'],
            ':new: status commands' : [False, "!ir - interested *remotely*\n!cr - coming or on the way *remotely*\n!hr - here at raid *remotely*\n!ii - interested in raid *invite*. ***!list** will show your IGN, if set using **!profile**.*"]
        }

        await ctx.send(embed=Embeds.make_embed(header_icon=Icons.CONFIGURATION, header="RSVP Commands", fields=status))

        pass

    @command(pass_context=True, aliases=["changes"])
    async def cmd_changes(self, ctx):

        status = {
            "Set raid boss (post-hatch)": [False, f"~~!raid pokemon~~ is now \n**!boss pokemon**"],
            "Set raid boss (pre-hatch)" : [False, "~~!r assume pokemon~~ is now \n**!assume pokemon**"],
            "Report an egg" : [False, "\n~~!raidegg 4 somewhere~~ is now \n**!raid 4 somewhere**"],
            "Change location of a raid": [False, "\n**!set-gym gym-code**"],
            ":new: RSVP Status" : [False, "**!ir** - interested *remotely*\n**!cr** - coming or on the way *remotely*\n**!hr** - here at raid *remotely*\n**!ii** - interested in raid *invite*. ***!list** will show your IGN, if set using **!profile**.*"]
        }

        await ctx.send(embed=Embeds.make_embed(header_icon=Icons.CONFIGURATION, header="What changed?", fields=status))

        pass


    @command(pass_context=True, aliases=["c"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_coming(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "c")


    @command(pass_context=True, aliases=["h"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_here(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "h")


    @command(pass_context=True, aliases=["i"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_interested(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "i")


    @command(pass_context=True, aliases=["ir"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_interested_remote(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "ir")


    @command(pass_context=True, aliases=["hr"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_here_remote(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "hr")


    @command(pass_context=True, aliases=["ii"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_interested_invite(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "ii")

    @command(pass_context=True, aliases=["cr"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_coming_remote(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "cr")


    @command(pass_context=True, aliases=["x"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_cancel(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_rsvp(ctx.message, "x")


    @command(pass_context=True, aliases=["s"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_started(self, ctx):
        """Signal that a raid is starting.

        Usage: !starting
        Works only in raid channels. Sends a message and clears the waiting list. Users who are waiting
        for a second group must re-announce with the :here: emoji or !here."""

        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        await rsvp_enabled.handle_group_start()


    @command(pass_context=True, aliases=["mention"])
    @raid_checks.rsvp_enabled()
    async def cmd_mention(self, ctx, *, status_with_message=None):

        allowed_status = ["c", "h", "i", "ir", "ii", "cr", "hr"]
        args = status_with_message.split()

        # if first word specifies the status, convert to rsvp status
        status, message = (args[0], args[1:]) if args[0] in RSVPEnabled.status_map.keys() else ("all", args[0:])
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)

        if not message:
            raise ValueError("Beep Beep! **{}**, please use **!mention [status] <message>**.".format(
                ctx.message.author.display_name))

        mention_list = []

        for trainer_id in rsvp_enabled.trainer_dict:
            if status == "all" or rsvp_enabled.trainer_dict[trainer_id].get('status', None) ==  status:
                user = self.bot.get_user(int(trainer_id))
                mention_list.append(user.mention)


        if len(mention_list) == 0:
            raise ValueError(f"Beep Beep! **{ctx.message.author.display_name}**, No trainers found to mention.".format())

        mention_message = f"**{ctx.message.author.display_name}**: {' '.join(message)} {', '.join(mention_list)}"

        await ctx.channel.send(mention_message)


    @command(pass_context=True, aliases=["list"])
    @raid_checks.rsvp_enabled()
    async def cmd_list(self, ctx):
        rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
        if rsvp_enabled is not None:
            return await rsvp_enabled.send_rsvp_embed(ctx.message, "")


