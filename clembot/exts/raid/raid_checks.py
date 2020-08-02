from discord.ext import commands

from clembot.exts.raid.errors import RSVPNotEnabled, NotARaidChannel
from clembot.exts.raid.raid import Raid, RaidParty


def _is_raid_channel(ctx):
    raid = Raid.by_channel.get(ctx.channel.id, None)
    if raid is not None:
        return True

    raise NotARaidChannel


def _is_raid_party_channel(ctx):
    raid = RaidParty.by_channel.get(ctx.channel.id, None)
    if raid is not None:
        return True

    raise NotARaidChannel

def _is_rsvp_enabled(ctx):

    is_raid = Raid.by_channel.get(ctx.channel.id, None)
    is_raid_party = RaidParty.by_channel.get(ctx.channel.id, None)

    if is_raid is None and is_raid_party is None:
        raise RSVPNotEnabled
    return True


def raid_channel():
    return commands.check(_is_raid_channel)

def raid_party_channel():
    return commands.check(_is_raid_party_channel)

def rsvp_enabled():
    return commands.check(_is_rsvp_enabled)
