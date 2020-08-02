import time

from discord.ext import commands
from discord.ext.commands import CommandError


class AccessDenied(CommandError):
    pass


async def _check_is_owner(ctx):
    has_access = await ctx.bot.is_owner(ctx.author)
    if has_access:
        return True
    return False

async def check_is_owner(ctx):
    if await _check_is_owner(ctx):
        return True
    raise AccessDenied("Access restricted for bot admin.")


async def _check_is_trusted(ctx):
    if await _check_is_owner(ctx):
        return True
    if ctx.author.id in ctx.bot.trusted_users:
        return True
    return False

async def check_is_trusted(ctx):
    if await _check_is_trusted(ctx):
        return True
    raise AccessDenied("Access restricted for bot managers only.")


async def _check_is_guild_owner(ctx):
    if await _check_is_owner(ctx):
        return True
    if ctx.author.id == ctx.guild.owner.id:
        return True
    return False

async def check_is_guild_owner(ctx):
    if await _check_is_guild_owner(ctx):
        return True
    raise AccessDenied("Access restricted for Guild owners only.")

async def _check_is_guild_admin(ctx):
    if await check_is_guild_owner(ctx):
        return True
    if ctx.author.guild_permissions.manage_guild:
        return True
    return False

async def check_is_guild_admin(ctx):
    if await _check_is_guild_admin(ctx):
        return True
    raise AccessDenied("Access restricted for Guild admins (with manage_guild permission) only.")


async def _check_is_moderator(ctx):
    if await check_is_guild_admin(ctx):
        return True
    if ctx.author.permissions_in(ctx.channel).manage_messages:
        return True
    return False

async def check_is_moderator(ctx):
    if await _check_is_moderator(ctx):
        return True
    raise AccessDenied("Access restricted for Moderators (with manage_messages permission) only.")


def go_thru_sometimes():
    random = int(time.time()) % 10
    return random > 5





"""Decorators to perform a check"""

def is_bot_owner():
    return commands.check(check_is_owner)


def is_trusted():
    return commands.check(check_is_trusted)


def is_guild_owner():
    return commands.check(check_is_guild_owner)


def is_guild_admin():
    return commands.check(check_is_guild_admin)


def is_guild_mod():
    return commands.check(check_is_moderator)
