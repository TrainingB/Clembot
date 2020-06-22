
@unused_list.command()
@checks.citychannel()
async def wild(ctx):
    """List the wilds for the channel

    Usage: !list wilds"""
    listmsg = _('**Beep Beep!**')
    listmsg += await _wildlist(ctx)
    await _send_message(ctx.channel, listmsg)

async def _wildlist(ctx):
    wild_dict = copy.deepcopy(guild_dict[ctx.guild.id]['wildreport_dict'])
    wildmsg = ""
    for wildid in wild_dict:
        if wild_dict[wildid]['reportchannel'] == ctx.message.channel.id:
            wildmsg += ('\n🔰')
            wildmsg += _("**Pokemon**: {pokemon}, **Location**: {location}".format(pokemon=wild_dict[wildid]['pokemon'].title(),location=wild_dict[wildid]['location'].title()))
    if wildmsg:
        listmsg = _(' **Here\'s the current wild reports for {channel}**\n{wildmsg}').format(channel=ctx.message.channel.name.capitalize(),wildmsg=wildmsg)
    else:
        listmsg = _(" There are no reported wild pokemon. Report one with **!wild <pokemon> <location>**")
    return listmsg


