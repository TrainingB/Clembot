from .draft_manager import DraftManagerCog


def setup(bot):
    bot.add_cog(DraftManagerCog(bot))
