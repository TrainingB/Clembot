


async def __exraid(ctx):
    message = ctx.message
    argument_text = ctx.message.clean_content.lower()
    parameters = await Parser.parse_arguments(argument_text, exraid_SYNTAX_ATTRIBUTE, {'gym' : get_gym_by_code_message}, {'message' : ctx.message})
    Logger.info(parameters)

    if parameters['length'] <= 1:
        await message.channel.send(_("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return

    raidexp = None
    channel_role = None
    gym = None
    if parameters.get('gym', None):
        gym = parameters['gym']
        raid_details = gym.gym_display_name
        # channel_role_id = _get_role_for_notification(message.channel.guild.id, gym_info['gym_code_key'])
        # channel_role = discord.utils.get(message.channel.guild.roles, id=channel_role_id)
        location_prefix = " ".join(parameters.get('others',[]))

        if len(location_prefix) >= 1:
            location_prefix = "-" + location_prefix + "-"

    else:
        location_prefix = ""
        raid_details = " ".join(parameters.get('others'))

    egg_level = 'EX'
    egg_info = raid_info['raid_eggs'][egg_level]
    egg_img = egg_info['egg_img']
    boss_list = []
    mon_in_one_line = 0
    for p in egg_info['pokemon']:
        p_name = get_name(p)
        p_type = get_type(message.guild, p)
        boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))

    region_prefix = await get_region_prefix(message)
    if region_prefix:
        prefix = region_prefix + "-"
    else:
        prefix = ""

    if gym:
        raid_gmaps_link = gym.gym_url
    else:
        raid_gmaps_link = create_gmaps_query(raid_details, message.channel)

    raid_details = sanitize_channel_name(location_prefix) + sanitize_channel_name(raid_details)
    raid_channel_name = prefix + egg_level + "-" + raid_details

    try:
        raid_channel_category = get_category(message.channel, egg_level)
        raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=dict(message.channel.overwrites), category=raid_channel_category)
    except Exception as error:
        Logger.info(error)
        await message.channel.send(content=_("Beep Beep! An error occurred while creating the channel. {error}").format(error=error))
        return

    raid_img_url = get_egg_image_url(egg_level)
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
    if len(egg_info['pokemon']) > 1:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
        raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
    else:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)

    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    try:
        raidreport = await message.channel.send(content=_(f"Beep Beep! Level {egg_level} raid egg reported by {message.author.mention}! Details: {raid_details}. Coordinate in {raid_channel.mention}"), embed=raid_embed)
    except Exception as error:
        Logger.info(error)
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _(
"""
Beep Beep! Level {level} raid egg reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!
** **
Please type `!beep status` if you need a refresher of Clembot commands! 
""").format(level=egg_level, member=message.author.mention, citychannel=message.channel.mention, location_details=raid_details)

    raidmessage = await raid_channel.send(content=raidmsg, embed=raid_embed)

    egg_timer = get_egg_timer('EX')

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel.id] = {
        'reportcity': message.channel.id,
        'trainer_dict': {},
        'exp': fetch_current_time(message.channel.guild.id) + timedelta(days=14),  # One hour from now
        'manual_timer': False,  # No one has explicitly set the timer, Clembot is just assuming 2 hours
        'active': True,
        'raidmessage': raidmessage.id,
        'raidreport': raidreport.id,
        'address': raid_details,
        'type': 'egg',
        'pokemon': '',
        'egglevel': 'EX',
        'suggested_start': False}

    await raid_channel.send(content=_('Beep Beep! Hey {member}, if you can, set the time left until the egg hatches using **!timerset <date and time>** so others can check it with **!timer**. **<date and time>** can just be written exactly how it appears on your EX Raid Pass.').format(member=message.author.mention))

    # if channel_role_list:
    #     await raid_channel.send(content=_("Beep Beep! A raid has been reported for {channel_role}.").format(channel_role=channel_role.mention))

    if len(raid_info['raid_eggs'][egg_level]['pokemon']) == 1:
        await _eggassume("assume " + get_name(raid_info['raid_eggs'][egg_level]['pokemon'][0]), raid_channel)

    await record_reported_by(message.guild.id, message.channel.name, message.author.id, 'eggs')

    event_loop.create_task(expiry_check(raid_channel))
    return


async def _exraid(ctx):
    message = ctx.message
    channel = message.channel
    fromegg = False
    exraid_split = message.clean_content.lower().split()
    del exraid_split[0]
    if len(exraid_split) <= 0:
        await channel.send( _("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return
    raid_details = " ".join(exraid_split)
    raid_details = raid_details.strip()
    if raid_details == '':
        await channel.send( _("Beep Beep! Give more details when reporting! Usage: **!exraid <location>**"))
        return

    raid_gmaps_link = create_gmaps_query(raid_details, message.channel)

    egg_info = raid_info['raid_eggs']['EX']
    egg_img = egg_info['egg_img']
    boss_list = []
    for p in egg_info['pokemon']:
        p_name = get_name(p)
        p_type = get_type(message.guild, p)
        boss_list.append(p_name + " (" + str(p) + ") " + ''.join(p_type))

    region_prefix = await get_region_prefix(message)
    if region_prefix:
        prefix = region_prefix + "-"
    else:
        prefix = ""

    raid_channel_name = prefix + "ex-raid-egg-" + sanitize_channel_name(raid_details)
    raid_channel_overwrite_list = channel.overwrites
    clembot_overwrite = (Clembot.user, discord.PermissionOverwrite(send_messages=True))
    everyone_overwrite = (channel.guild.default_role, discord.PermissionOverwrite(send_messages=False))
    for overwrite in raid_channel_overwrite_list:
        if isinstance(overwrite[0], discord.Role):
            if overwrite[0].permissions.manage_guild:
                continue
        overwrite[1].send_messages = False
    raid_channel_overwrite_list.append(clembot_overwrite )
    raid_channel_overwrite_list.append(everyone_overwrite)
    raid_channel_overwrites = dict(raid_channel_overwrite_list)
    raid_channel_category = get_category(message.channel,"EX")
    raid_channel = await message.guild.create_text_channel(raid_channel_name, overwrites=raid_channel_overwrites,category=raid_channel_category)

    raid_img_url = "https://raw.githubusercontent.com/FoglyOgly/Clembot/master/images/eggs/{}".format(str(egg_img))
    raid_img_url = get_pokemon_image_url(5)  # This part embeds the sprite
    raid_embed = discord.Embed(title=_("Beep Beep! Click here for directions to the coming raid!"), url=raid_gmaps_link, colour=message.guild.me.colour)
    if len(egg_info['pokemon']) > 1:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist1}").format(bosslist1="\n".join(boss_list[::2])), inline=True)
        raid_embed.add_field(name="\u200b", value=_("{bosslist2}").format(bosslist2="\n".join(boss_list[1::2])), inline=True)
    else:
        raid_embed.add_field(name="**Possible Bosses:**", value=_("{bosslist}").format(bosslist="".join(boss_list)), inline=True)
        raid_embed.add_field(name="\u200b", value="\u200b", inline=True)
    raid_embed.set_footer(text=_("Reported by @{author}").format(author=message.author.display_name), icon_url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}?size={size}".format(user=message.author, format="jpg", size=32)))
    raid_embed.set_thumbnail(url=raid_img_url)
    raidreport = await channel.send( content=_("Beep Beep! EX raid egg reported by {member}! Details: {location_details}. Use the **!invite** command to gain access and coordinate in {raid_channel}").format(member=message.author.mention, location_details=raid_details, raid_channel=raid_channel.mention), embed=raid_embed)
    await asyncio.sleep(1)  # Wait for the channel to be created.

    raidmsg = _("""Beep Beep! EX raid reported by {member} in {citychannel}! Details: {location_details}. Coordinate here!

To update your status, choose from the following commands:
**!interested, !coming, !here, !cancel**
If you are bringing more than one trainer/account, add the number of accounts total on your first status update.
Example: `!coming 5`

To see the list of trainers who have given their status:
**!list interested, !list coming, !list here**
Alternatively **!list** by itself will show all of the above.

**!location** will show the current raid location.
**!location new <address>** will let you correct the raid address.
Sending a Google Maps link will also update the raid location.

Message **!starting** when the raid is beginning to clear the raid's 'here' list.""").format(member=message.author.mention, citychannel=channel.mention, location_details=raid_details)
    raidmessage = await raid_channel.send( content=raidmsg, embed=raid_embed)

    guild_dict[message.guild.id]['raidchannel_dict'][raid_channel] = {
        'reportcity': channel.id,
        'trainer_dict': {},
        'exp': None,  # No expiry
        'manual_timer': False,
        'active': True,
        'raidmessage': raidmessage.id,
        'raidreport': raidreport.id,
        'address': raid_details,
        'type': 'egg',
        'pokemon': '',
        'egglevel': 'EX',
        'suggested_start': False
    }

    await raid_channel.send( content=_("Beep Beep! Hey {member}, if you can, set the time the EX Raid begins using **!timerset <date and time>** so others can check it with **!timer**. **<date and time>** should look exactly as it appears on your invitation.").format(member=message.author.mention))

    event_loop.create_task(expiry_check(raid_channel))

