from .subscription_cog import SubscriptionCog

def setup(bot):
    bot.add_cog(SubscriptionCog(bot))

