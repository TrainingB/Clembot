import asyncio
import json
import re
import time

import discord
from discord.ext.commands import command

from clembot.core import checks
from clembot.core.logs import Logger
from clembot.utilities.utils import parse_emoji


def do_template(message, author, guild):
    not_found = []

    def template_replace(match):
        if match.group(3):
            if match.group(3) == 'user':
                return '{user}'
            elif match.group(3) == 'server':
                return guild.name
            else:
                return match.group(0)
        if match.group(4):
            emoji = (':' + match.group(4)) + ':'
            return parse_emoji(guild, emoji)
        match_type = match.group(1)
        full_match = match.group(0)
        match = match.group(2)
        if match_type == '<':
            mention_match = re.search('(#|@!?|&)([0-9]+)', match)
            match_type = mention_match.group(1)[0]
            match = mention_match.group(2)
        if match_type == '@':
            member = guild.get_member_named(match)
            if match.isdigit() and (not member):
                member = guild.get_member(match)
            if (not member):
                not_found.append(full_match)
            return member.mention if member else full_match
        elif match_type == '#':
            channel = discord.utils.get(guild.channels, name=match)
            if match.isdigit() and (not channel):
                channel = guild.get_channel(match)
            if (not channel):
                not_found.append(full_match)
            return channel.mention if channel else full_match
        elif match_type == '&':
            role = discord.utils.get(guild.roles, name=match)
            if match.isdigit() and (not role):
                role = discord.utils.get(guild.roles, id=match)
            if (not role):
                not_found.append(full_match)
            return role.mention if role else full_match
    template_pattern = '{(@|#|&|<)([^{}]+)}|{(user|server)}|<*:([a-zA-Z0-9]+):[0-9]*>*'
    msg = re.sub(template_pattern, template_replace, message)
    return (msg, not_found)


@command(hidden=True)
async def template(ctx, *, sample_message):
    """Sample template messages to see how they would appear."""
    embed = None
    (msg, errors) = do_template(sample_message, ctx.author, ctx.guild)
    if errors:
        if msg.startswith('[') and msg.endswith(']'):
            embed = discord.Embed(
                colour=ctx.guild.me.colour, description=msg[1:(- 1)])
            embed.add_field(name='Warning', value='The following could not be found:\n{}'.format(
                '\n'.join(errors)))
            await ctx.channel.send(embed=embed)
        else:
            msg = '{}\n\n**Warning:**\nThe following could not be found: {}'.format(
                msg, ', '.join(errors))
            await ctx.channel.send(msg)
    elif msg.startswith('[') and msg.endswith(']'):
        await ctx.channel.send(embed=discord.Embed(colour=ctx.guild.me.colour, description=msg[1:(- 1)].format(user=ctx.author.mention)))
    else:
        await ctx.channel.send(msg.format(user=ctx.author.mention))


@command.command(pass_context=True, hidden=True)
async def timestamp(ctx):
    await ctx.channel.send(ctx.channel, str(time.time()))


@command(pass_context=True, hidden=True)
# @commands.has_permissions(manage_guild=True)
async def announce(ctx, *, announce=None):
    """Repeats your message in an embed from Clembot.

    Usage: !announce [announcement]
    If the announcement isn't added at the same time as the command, Clembot will wait 3 minutes for a followup message containing the announcement."""
    message = ctx.message
    channel = message.channel
    guild = message.guild
    author = message.author
    if announce == None:
        announcewait = await channel.send( "I'll wait for your announcement!")
        announcemsg = await ctx.bot.wait_for('message', timeout=180, check=(lambda reply: reply.author == message.author))
        await announcewait.delete()
        if announcemsg != None:
            announce = announcemsg.content
            await announcemsg.delete()
        else:
            confirmation = await channel.send( "Beep Beep! You took too long to send me your announcement! Retry when you're ready.")
    embeddraft = discord.Embed(colour=guild.me.colour, description=announce)
    title = 'Announcement'
    if ctx.bot.user.avatar_url:
        embeddraft.set_author(name=title, icon_url=ctx.bot.user.avatar_url)
    else:
        embeddraft.set_author(name=title)
    draft = await channel.send( embed=embeddraft)

    reaction_list = ['❔', '✅', '❎']
    owner_msg_add = ''
    if checks.is_owner_check(ctx):
        owner_msg_add = "🌎 to send it to all guilds, "
        reaction_list.insert(0, '🌎')

    def check(reaction, user):
        if user.id == author.id:
            if (str(reaction.emoji) in reaction_list) and (reaction.message.id == rusure.id):
                return True
        return False

    rusure = await channel.send( _("That's what you sent, does it look good? React with {}❔ to send to another channel, ✅ to send it to this channel, or ❎ to cancel").format(owner_msg_add))
    res = await ask(rusure, channel, author.id, react_list=reaction_list)
    if res:
        await rusure .delete()
        if res[0].emoji == "❎":
            confirmation = await channel.send( _("Announcement Cancelled."))
            await draft .delete()
        elif res[0].emoji == "✅":
            confirmation = await channel.send( _("Announcement Sent."))
        elif res[0].emoji == "❔":
            channelwait = await channel.send( 'What channel would you like me to send it to?')
            channelmsg = await ctx.bot.wait_for('message', timeout=60, check=(lambda reply: reply.author == message.author))
            if channelmsg.content.isdigit():
                sendchannel = ctx.bot.get_channel(int(channelmsg.content))
            elif channelmsg.raw_channel_mentions:
                sendchannel = ctx.bot.get_channel(channelmsg.raw_channel_mentions[0])
            else:
                sendchannel = discord.utils.get(guild.text_channels, name=channelmsg.content)
            if (channelmsg != None) and (sendchannel != None):
                announcement = await sendchannel.send( embed=embeddraft)
                confirmation = await channel.send( _('Announcement Sent.'))
            elif sendchannel == None:
                confirmation = await channel.send( "Beep Beep! That channel doesn't exist! Retry when you're ready.")
            else:
                confirmation = await channel.send( "Beep Beep! You took too long to send me your announcement! Retry when you're ready.")
            await channelwait .delete()
            await channelmsg .delete()
            await draft .delete()
        elif (res[0].emoji == '🌎') and checks.is_owner_check(ctx):
            failed = 0
            sent = 0
            count = 0
            recipients = {

            }

            embeddraft.set_footer(text="For support, contact us on our Discord guild. https://discord.gg/AUzEXRU")
            embeddraft.colour = discord.Colour.lighter_grey()
            for guild in ctx.bot.guilds:
                recipients[guild.name] = guild.owner
            for (guild, destination) in recipients.items():

                try:
                    await destination.send(embed=embeddraft)
                except discord.HTTPException:
                    failed += 1
                    Logger.info('Announcement Delivery Failure: {} - {}'.format(destination.name, guild))
                else:
                    sent += 1
                count += 1
            Logger.info('Announcement sent to {} server owners: {} successful, {} failed.'.format(count, sent, failed))
            confirmation = await channel.send('Announcement sent to {} server owners: {} successful, {} failed.'.format(count, sent, failed))
        await asyncio.sleep(10)
        await confirmation.delete()
    else:
        await rusure.delete()
        confirmation = await channel.send( _('Announcement Timed Out.'))
        await asyncio.sleep(10)
        await confirmation.delete()
    await asyncio.sleep(30)
    await message.delete()


@command(pass_context=True, hidden=True)
async def analyze(ctx, *, count: str = None):
    limit = 200

    try:
        if count:
            if count.isdigit():
                count = int(count)
                limit = count

        channel = ctx.message.channel
        await ctx.message .delete()

        map_users = {}
        counter = 1
        async for message in channel.history(limit=None):
            if len(message.attachments) > 0:
                map_users.update({message.author.mention: map_users.get(message.author.mention, 0) + 1})
                counter = counter + 1
                if counter > limit:
                    break

        sorted_map = dict(sorted(map_users.items(), key=lambda x: x[1], reverse=True))

        text = json.dumps(sorted_map, indent=4)

        parts = [text[i:i + 1800] for i in range(0, len(text), 1800)]

        await ctx.message.author.send(content=f"Results from {ctx.message.guild.name}.{ctx.message.channel.name} requested by {ctx.message.author.display_name}")
        for message_text in parts:
            await ctx.message.author.send( content=message_text)

    except Exception as error:
        await ctx.message.author.send(content=error)
        Logger.info(error)