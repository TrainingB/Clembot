from discord.ext import commands

from clembot.core.bot import group
from clembot.core.logs import Logger
from clembot.exts.profile.user_guild_profile import UserGuildProfile
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class LeaderboardCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

    @group(pass_context=True, hidden=True, aliases=["leaderboard"])
    async def cmd_leaderboard(self, ctx, stat="total", board_type = "lifetime"):
        """
        Usage:
        !leaderboard
        !leaderboard raids
        !leaderboard eggs burbank
        """
        # TODO: implement custom leaderboards
        try:



            record_list = await UserGuildProfile.find_top10_reporters(self.bot, ctx.guild.id, board_type, stat)
            field_list = {}
            rank = 1
            for record in record_list:
                user_guild_profile = UserGuildProfile(self.bot, record)
                stats = user_guild_profile.leaderboard_status(board_type)
                user = ctx.guild.get_member(user_guild_profile.user_id)
                field_list[f"{rank}. {user.display_name} - {stat} - {user_guild_profile['total_reports']}"] = [False, stats]
                rank += 1

            embed = Embeds.make_embed(header=f"Leaderboard Type: {board_type} ({stat})",
                                      header_icon=ctx.message.guild.me.avatar_url, thumbnail=ctx.guild.icon_url,
                                      fields=field_list)
            await ctx.send(embed=embed)

        except Exception as error:
            Logger.error(error)


