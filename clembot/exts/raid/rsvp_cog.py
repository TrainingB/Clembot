from discord.ext import commands

from clembot.core.commands import Cog
from clembot.exts.raid import raid_checks
from clembot.exts.raid.errors import RSVPNotEnabled
from clembot.exts.raid.raid import RSVPEnabled, Raid, RaidParty
from clembot.utilities.utils.embeds import Embeds


class RSVPCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._dbi = bot.dbi

    @staticmethod
    def get_rsvp_source(ctx) -> RSVPEnabled:

        raid = Raid.by_channel.get(ctx.channel.id)
        if raid:
            return raid

        raid_party = RaidParty.by_channel.get(ctx.channel.id)
        if raid_party:
            return raid_party

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        """Method to handle Cog specific errors"""
        if isinstance(error, RSVPNotEnabled):
            await Embeds.error(ctx.channel, 'RSVP commands are not enabled for this channel.', ctx.message.author)

    @commands.group(pass_context=True, hidden=True, aliases=["c"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_coming(self, ctx):
        try:
            rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
            await rsvp_enabled.handle_rsvp(ctx.message, "omw")

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["h"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_here(self, ctx):
        try:
            rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
            await rsvp_enabled.handle_rsvp(ctx.message, "waiting")

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["i"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_interested(self, ctx):
        try:
            rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
            await rsvp_enabled.handle_rsvp(ctx.message, "maybe")

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)

    @commands.group(pass_context=True, hidden=True, aliases=["x"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_cancel(self, ctx):
        try:
            rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
            await rsvp_enabled.handle_rsvp(ctx.message, "cancel")

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    @commands.group(pass_context=True, hidden=True, aliases=["s"])
    @raid_checks.rsvp_enabled()
    async def cmd_rsvp_started(self, ctx):
        """Signal that a raid is starting.

        Usage: !starting
        Works only in raid channels. Sends a message and clears the waiting list. Users who are waiting
        for a second group must re-announce with the :here: emoji or !here."""

        try:
            rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
            await rsvp_enabled.handle_group_start()

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


    def convert_command_to_status(self, text):
        coming_list = ["c", "coming", "o", "omw"]
        cancel_list = ["x", "cancel"]
        maybe_list = ["i", "interested", "maybe"]
        here_list = ["h", "here"]
        status = None
        command_text = text.replace('!', '')

        if command_text in coming_list:
            status = "omw"
        elif command_text in cancel_list:
            status = "cancel"
        elif command_text in maybe_list:
            status = "maybe"
        elif command_text in here_list:
            status = "waiting"

        return status

    @commands.group(pass_context=True, hidden=True, aliases=["mention"])
    @raid_checks.rsvp_enabled()
    async def cmd_mention(self, ctx, *, status_with_message=None):
        try:

            allowed_status = ["c", "h", "i"]
            args = status_with_message.split()

            # if first word specifies the status, convert to rsvp status
            status, message = (self.convert_command_to_status(args[0]), args[1:]) if args[0] in allowed_status else ("all", args[0:])
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

        except Exception as error:
            await Embeds.error(ctx.channel, error)

    @commands.group(pass_context=True, hidden=True, aliases=["list"])
    async def cmd_list(self, ctx):
        try:
            rsvp_enabled = RSVPCog.get_rsvp_source(ctx)
            await rsvp_enabled.send_rsvp_embed(ctx.message, "")

        except Exception as error:
            await Embeds.error(ctx.channel, f"{error}", user=ctx.message.author)


