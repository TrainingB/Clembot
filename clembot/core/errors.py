import asyncio
import traceback
from functools import wraps
from inspect import signature, getfullargspec

import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandError, BadArgument

from clembot.config.constants import Icons
from clembot.core.checks import AccessDenied

from clembot.core.context import Context
from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.timezone import timehandler as TH
from clembot.utilities.utils.snowflake import CUIDGenerator


class TeamSetCheckFail(CommandError):
    'Exception raised checks.teamset fails'
    pass

class WantSetCheckFail(CommandError):
    'Exception raised checks.wantset fails'
    pass

class WildSetCheckFail(CommandError):
    'Exception raised checks.wildset fails'
    pass

class RaidSetCheckFail(CommandError):
    'Exception raised checks.raidset fails'
    pass

class CityChannelCheckFail(CommandError):
    'Exception raised checks.citychannel fails'
    pass

class WantChannelCheckFail(CommandError):
    'Exception raised checks.wantchannel fails'
    pass

class RaidChannelCheckFail(CommandError):
    'Exception raised checks.raidchannel fails'
    pass

class EggChannelCheckFail(CommandError):
    'Exception raised checks.raidchannel fails'
    pass

class NonRaidChannelCheckFail(CommandError):
    'Exception raised checks.nonraidchannel fails'
    pass

class ActiveRaidChannelCheckFail(CommandError):
    'Exception raised checks.activeraidchannel fails'
    pass

class CityRaidChannelCheckFail(CommandError):
    'Exception raised checks.cityraidchannel fails'
    pass

class RegionEggChannelCheckFail(CommandError):
    'Exception raised checks.cityeggchannel fails'
    pass

class RegionExRaidChannelCheckFail(CommandError):
    'Exception raised checks.cityeggchannel fails'
    pass

class ExRaidChannelCheckFail(CommandError):
    'Exception raised checks.cityeggchannel fails'
    pass

def missing_arg_msg(ctx):
    prefix = ctx.prefix.replace(ctx.bot.user.mention, '@' + ctx.bot.user.name)
    command = ctx.invoked_with
    parent = f"{next(iter(ctx.command.parent.aliases))} " if ctx.command.parent else ""
    callback = ctx.command.callback
    sig = list(signature(callback).parameters.keys())
    (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations) = getfullargspec(callback)
    if defaults:
        rqargs = args[:(- len(defaults))]
    else:
        rqargs = args
    if varargs:
        if varargs != 'args':
            rqargs.append(varargs)
    arg_num = len(ctx.args) - 1
    sig.remove('ctx')
    args_missing = sig[arg_num:]
    sig.remove('self')

    return prefix, parent, command, args_missing, sig


def custom_error_handling(bot, logger):

    @bot.event
    async def on_command_error(ctx, error):
        channel = ctx.channel


        if isinstance(error, commands.MissingRequiredArgument):

            prefix, parent, command, missing_args, sig = missing_arg_msg(ctx)

            header = missing_arguments_header[int(str(TH.current_epoch()).split(".")[-1]) % len(missing_arguments_header)]

            error_message = await ctx.send(embed=Embeds.make_embed(
                header_icon=Icons.BOT_ERROR, msg_color=discord.Color.dark_red(),
                header=f"{header}",
                content=f'I\'m missing some details such as `{" ".join(missing_args)}`\n\n**Correct Usage:** `{prefix}{parent}{command} {" ".join(sig)}`\n\n||You can tap 🗑️ to delete this message.||'))

            await error_message.add_reaction('🗑️')

        elif isinstance(error, commands.BadArgument):

            header = bad_arguments_header[int(str(TH.current_epoch()).split(".")[-1]) % len(bad_arguments_header)]

            error_message = await ctx.send(embed=Embeds.make_embed(
                header_icon=Icons.error, msg_color=discord.Color.dark_red(),
                header=f"{header}",
                content=f'**Error details:** {error}\n\n ||You can tap 🗑️ to delete this message.||'))

            await error_message.add_reaction('🗑️')

        elif isinstance(error, AccessDenied):

            header = check_failure_header[int(str(TH.current_epoch()).split(".")[-1]) % len(check_failure_header)]

            error_message = await ctx.send(embed=Embeds.make_embed(
                header_icon=Icons.INVALID_ACCESS, msg_color=discord.Color.dark_red(),
                header=f"{header}",
                content=f'**Error details:** {error}\n\n ||You can tap 🗑️ to delete this message.||'))

            await error_message.add_reaction('🗑️')

            pass
            #
            # await ctx.bot.send_cmd_help(
            #     ctx, title=f'Bad Argument - {error}', msg_type='error')

            # try:
            #     pages = await bot.formatter.format_help_for(ctx, ctx.command)
            #     for page in pages:
            #         await ctx.channel.send(page)
            # except Exception as error:
            #     Logger.error(f"{traceback.format_exc()}")
            pass
        elif isinstance(error, commands.CommandError):
            pass
        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, TeamSetCheckFail):
            msg = 'Beep Beep! Team Management is not enabled on this server. **!{cmd_name}** is unable to be used.'.format(cmd_name=ctx.command.name)
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, WantSetCheckFail):
            msg = 'Beep Beep! Pokemon Management is not enabled on this server. **!{cmd_name}** is unable to be used.'.format(cmd_name=ctx.command.name)
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, WildSetCheckFail):
            msg = 'Beep Beep! Wild Reporting is not enabled on this server. **!{cmd_name}** is unable to be used.'.format(cmd_name=ctx.command.name)
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, RaidSetCheckFail):
            msg = 'Beep Beep! Raid Management is not enabled on this server. **!{cmd_name}** is unable to be used.'.format(cmd_name=ctx.command.name)
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, CityChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in '.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id]['city_channels']
            if len(city_channels) > 10:
                msg += 'a Region report channel.'
            else:
                msg += 'one of the following region channels:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, WantChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in '.format(cmd_name=ctx.command.name)
            want_channels = bot.guild_dict[guild.id]['want_channel_list']
            if len(want_channels) > 5:
                msg += 'a Region report channel.'
            else:
                msg += 'one of the following region channels:'
                for c in want_channels:
                    channel = discord.utils.get(guild.channels, id=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, RaidChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in a Raid channel. Use **!list** in any '.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id]['city_channels']
            if len(city_channels) > 10:
                msg += 'Region report channel to see active raids.'
            else:
                msg += 'of the following Region channels to see active raids:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, RaidChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in an Egg channel. Use **!list** in any '.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id]['city_channels']
            if len(city_channels) > 10:
                msg += 'Region report channel to see active raids.'
            else:
                msg += 'of the following Region channels to see active raids:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, NonRaidChannelCheckFail):
            msg = "Beep Beep! **!{cmd_name}** can't be used in a Raid channel.".format(cmd_name=ctx.command.name)
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, ActiveRaidChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in an Active Raid channel. Use **!list** in any '.format(cmd_name=ctx.command.name)
            msg += 'Region report channel to see active raids.'
            # city_channels = bot.guild_dict[guild.id]['city_channels']
            # if len(city_channels) > 10:
            #     msg += 'of the following Region channels to see active raids:'
            #
            # for c in city_channels:
            #     channel = discord.utils.get(guild.channels, name=c)
            #     msg += '\n' + channel.mention
            errormsg = await ctx.channel.send(msg)
            await asyncio.sleep(10)
            await errormsg.delete()
            pass
        elif isinstance(error, CityRaidChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in either a Raid channel or '.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id]['city_channels']
            if len(city_channels) > 10:
                msg += 'a Region report channel.'
            else:
                msg += 'one of the following region channels:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, RegionEggChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in either a Raid Egg channel or '.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id].get('city_channels',[])
            if len(city_channels) > 10:
                msg += 'a Region report channel.'
            else:
                msg += 'one of the following region channels:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, RegionExRaidChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in either a EX Raid channel or one of the following region channels:'.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id].get('city_channels', [])
            if len(city_channels) > 10:
                msg += 'a Region report channel.'
            else:
                msg += 'one of the following region channels:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        elif isinstance(error, ExRaidChannelCheckFail):
            guild = ctx.guild
            msg = 'Beep Beep! Please use **!{cmd_name}** in a EX Raid channel. Use **!list** in any of the following region channels to see active raids:'.format(cmd_name=ctx.command.name)
            city_channels = bot.guild_dict[guild.id]['city_channels']
            if len(city_channels) > 10:
                msg += 'a Region report channel.'
            else:
                msg += 'one of the following region channels:'
                for c in city_channels:
                    channel = discord.utils.get(guild.channels, name=c)
                    msg += '\n' + channel.mention
            await ctx.channel.send(msg)
            pass
        else:
            logger.exception(type(error).__name__, exc_info=error)


error_header = ["Alright, something happened.",
                "Hmmm, that didn't go as planned.",
                "Wow, That was unexpected.",
                "Are you sure this worked before?",
                "Enough, I need a break.",
                "Surprise, surprise!",
                "You broke me!",
                "I am having a hard time"
                ]

error_message_description = ["I would love to say \"Hey, It's not you, its me!\" but that wouldn't change anything.",
    'You can try again or get on of the admins involved.',
    "Someone will spot the problem in due time.",
    "Don't read too much into this message and ask for help!",
    "You can try again but probably it wouldn't work unless someone takes a look at it.",
    "What else do you expect from a free bot!"
]

bad_arguments_header = ["Uh-huh, bad arguments!",
    "Hey there, that's not good enough!",
    "Whoa, you thought that will work!",
    "Hold on, lets do this right!",
    "What?!?",
    "There is always next time!"
]


missing_arguments_header = [
    "Wait, that's not enough!",
    "I need some more information",
    "Are you sure you are missing something?"
]

check_failure_header = ["Can I see your ID please.",
    "Well, this is it!",
    "Papers, please!",
    "Hmmm, impressive. Nice Try.",
    "Can't let you do this!",
    "Caught ya!"
]



def wrap_error(func):
    """
    Decorator to handle logging of exception and sending an error message to the user.
    Need ctx object to send an error message to user. if ctx is not the second argument, specify which argument is ctx.
    """
    @wraps(func)
    async def decorator(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except BadArgument as bErr:
            ctx = next(filter(lambda arg: isinstance(arg, Context), args))

            header = bad_arguments_header[int(str(TH.current_epoch()).split(".")[-1]) % len(bad_arguments_header)]

            error_message = await ctx.send(embed=Embeds.make_embed(
                header_icon=Icons.error, msg_color=discord.Color.dark_red(),
                header=f"{header}",
                content=f'**Error details:** {bErr}\n\n ||You can tap 🗑️ to delete this message.||'))

            await error_message.add_reaction('🗑️')
            return

        except Exception as error:
            print("--------------------")
            import traceback
            ref_id = f"E-{CUIDGenerator.cuid(int(TH.current_epoch()))}"
            Logger.error(f"{ref_id} - {traceback.format_exc()}")

            ctx = next(filter(lambda arg: isinstance(arg, Context), args))

            if ctx:
                await ctx.send(embed=Embeds.make_embed(
                    header_icon=Icons.BOT_ERROR, msg_color=discord.Color.dark_red(),
                    header=error_header[int(str(TH.current_epoch()).split(".")[-1]) % len(error_header)],
                    content=f'{error_message_description[int(str(TH.current_epoch()).split(".")[-1]) % len(error_message_description)]}\n\n||**Command:** `{ctx.message.content}`\n**Error:** `{error}`\n**Where:** `{func.__name__}()`||',
                    footer=f"Reference Id: {ref_id}"))
            return None

    return decorator