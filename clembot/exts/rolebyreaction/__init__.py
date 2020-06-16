from .reactionrolemanager import ReactionRoleManager
from .reactrolemanager import ReactRoleManager


def setup(bot):
    bot.add_cog(ReactRoleManager(bot))
    bot.add_cog(ReactionRoleManager(bot))

