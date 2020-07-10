from .leaderboard_cog import LeaderboardCog


def setup(bot):
    bot.add_cog(LeaderboardCog(bot))
