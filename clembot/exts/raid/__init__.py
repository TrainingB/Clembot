from .raid_cog import RaidCog
from .raid_party_cog import RaidPartyCog
from .rsvp_cog import RSVPCog

def setup(bot):
    bot.add_cog(RSVPCog(bot))
    bot.add_cog(RaidCog(bot))
    bot.add_cog(RaidPartyCog(bot))
