

@Clembot.command()
async def leaderboard(ctx, lb_type="lifetime" , r_type="total"):
    """Displays the top ten reporters of a server.

    Usage: !leaderboard [type]
    Accepted types: raids, eggs, exraids, wilds, research"""
    try:
        leaderboard = []
        rank = 1
        typelist = ["total", "raids", "wilds", "research", "eggs"]
        type = r_type.lower()

        leaderboard_list = ['lifetime']
        addtional_leaderboard = await get_guild_local_leaderboard(ctx.guild.id)
        if addtional_leaderboard :
            leaderboard_list.extend(addtional_leaderboard)

        leaderboard_type = lb_type if lb_type in leaderboard_list else 'lifetime'

        report_type = r_type if r_type in typelist else 'total'

        if leaderboard_type != lb_type and report_type == 'total':
            report_type = lb_type if lb_type in typelist else 'total'

        if r_type != type and leaderboard != leaderboard_type and leaderboard != type:
            return await _send_error_message(ctx.message.channel, _("Beep Beep! **{0}** Leaderboard type not supported. Please select from: **{1}**").format(ctx.message.author.display_name, ", ".join(typelist)))

        trainers = copy.deepcopy(guild_dict[ctx.guild.id]['trainers'])

        for trainer in trainers.keys():
            raids = trainers[trainer].setdefault('leaderboard-stats',{}).setdefault(leaderboard_type,{}).setdefault('raids', 0)
            wilds = trainers[trainer].setdefault('leaderboard-stats',{}).setdefault(leaderboard_type,{}).setdefault('wilds', 0)
            exraids = trainers[trainer].setdefault('leaderboard-stats',{}).setdefault(leaderboard_type,{}).setdefault('ex_reports', 0)
            eggs = trainers[trainer].setdefault('leaderboard-stats',{}).setdefault(leaderboard_type,{}).setdefault('eggs', 0)
            research = trainers[trainer].setdefault('leaderboard-stats',{}).setdefault(leaderboard_type,{}).setdefault('quests', 0)
            total_reports = raids + wilds + exraids + eggs + research
            trainer_stats = {'trainer':trainer, 'total':total_reports, 'raids':raids, 'wilds':wilds, 'research':research, 'eggs':eggs}
            if trainer_stats[type] > 0:
                leaderboard.append(trainer_stats)

        leaderboard = sorted(leaderboard, key=lambda x: x[report_type], reverse=True)[:10]
        embed = discord.Embed(colour=ctx.guild.me.colour)
        embed.set_author(name=_("Leaderboard Type: {leaderboard_type} ({report_type})").format(leaderboard_type=leaderboard_type.title(), report_type=report_type.title()), icon_url=Clembot.user.avatar_url)
        for trainer in leaderboard:
            user = ctx.guild.get_member(int(trainer['trainer']))
            if user:
                embed.add_field(name=f"{rank}. {user.display_name} - {type.title()}: **{trainer[type]}**", value=f"Raids: **{trainer['raids']}** | Eggs: **{trainer['eggs']}** | Wilds: **{trainer['wilds']}** | Research: **{trainer['research']}**", inline=False)
                rank += 1
        await ctx.send(embed=embed)
    except Exception as error:
        Logger.info(error)



@Clembot.command(pass_context=True, hidden=True, aliases=["reset-leaderboard"])
@checks.is_owner()
async def _reset_leaderboard(ctx, leaderboard_type=None):
    """Displays the top ten reporters of a server.

    Usage: !leaderboard [type]
    Accepted types: raids, eggs, exraids, wilds, research"""

    leaderboard_list = ['lifetime']

    addtional_leaderboard = await get_guild_local_leaderboard(ctx.guild.id)
    if addtional_leaderboard:
        leaderboard_list.extend(addtional_leaderboard)

    if not leaderboard_type:
        return await _send_error_message(ctx.channel, "Beep Beep! **{}**, please provide leaderboard to be cleared.".format(ctx.author.mention))

    if leaderboard_type not in leaderboard_list:
        return await _send_error_message(ctx.message.channel, _("Beep Beep! **{0}** Leaderboard type not supported. Please select from: **{1}**").format(ctx.message.author.display_name, ", ".join(leaderboard_list)))
    trainers = copy.deepcopy(guild_dict[ctx.guild.id]['trainers'])

    for trainer in trainers.keys():
        guild_dict[ctx.guild.id]['trainers'][trainer].setdefault('leaderboard-stats',{})[leaderboard_type] = {}

    await _send_message(ctx.channel, "Beep Beep! **{}**, **{}** has been cleared.".format(ctx.author.mention, leaderboard_type))


@Clembot.command(pass_context=True, hidden=True, aliases=["extract-leaderboard"])
@checks.is_owner()
async def extract_leaderboard(ctx):
    guild_id = ctx.guild.id

    try:
        user_reports = {}
        for trainer_id in guild_dict[ctx.guild.id]['trainers'].keys():
            user = ctx.guild.get_member(trainer_id)
            if user:
                # for leaderboard in applicable_leaderboards:
                t_d = dict.copy(guild_dict[ctx.guild.id]['trainers'])

                text=f"[{user.mention}] "
                if t_d.get('wilds',0) + t_d.get('raids',0) + t_d.get('eggs',0) + t_d.get('quests',0) > 0:
                    text = f"{text} {t_d.get('wilds',0)} Wild Reports, {t_d.get('raids',0)} Raid Reports, {t_d.get('eggs',0)} Egg Reports, {t_d.get('quests',0)} Research Reports"

                guild_leaderboards = await get_guild_local_leaderboard(guild_id)
                guild_leaderboard_configuration = await get_guild_leaderboard_configuration(guild_id)

                for leaderboard_name in guild_leaderboards:
                    # applicable_leaderboards.append(leaderboard_name)

                    l_d = t_d.setdefault('leaderboard-stats',{}).get(leaderboard_name, {})
                    if l_d.get('wilds', 0) + l_d.get('raids', 0) + l_d.get('eggs', 0) + l_d.get('quests', 0) > 0:
                        text = f"{text}\t\n [{user.mention}][{leaderboard_name}]{l_d.get('wilds',0)} Wild Reports, {l_d.get('raids',0)} Raid Reports, {l_d.get('eggs',0)} Egg Reports, {l_d.get('quests',0)} Research Reports"

                await utilities._send_message(ctx.channel, text)

    except Exception as error:
        await utilities._send_message(ctx.channel, error)
        print(error)



async def record_reported_by(guild_id, channel_name, author_id, report_type):
    try:
        applicable_leaderboards = ['lifetime']

        guild_leaderboards = await get_guild_local_leaderboard(guild_id)
        guild_leaderboard_configuration = await get_guild_leaderboard_configuration(guild_id)

        if guild_leaderboards:
            for leaderboard_name in guild_leaderboards:
                channel_leaderboard = guild_leaderboard_configuration.get(leaderboard_name,{})
                if channel_name in channel_leaderboard.get('channels',[channel_name]) :
                    # if raid_level in channel_leaderboard.get('level', [raid_level]) :
                    applicable_leaderboards.append(leaderboard_name)

        for leaderboard in applicable_leaderboards:
            existing_reports = guild_dict[guild_id].setdefault('trainers', {}).setdefault(author_id, {}).setdefault('leaderboard-stats', {}).setdefault(leaderboard, {}).setdefault(report_type, 0) + 1
            guild_dict[guild_id]['trainers'][author_id]['leaderboard-stats'][leaderboard][report_type] = existing_reports
            Logger.debug(f"{author_id} has reported {existing_reports} {report_type} for {leaderboard}")

    except Exception as error:
        Logger.error("Error while recording in leaderboard " + error)

async def record_error_reported_by(guild_id, channel_name, author_id, report_type):
    try:
        applicable_leaderboards = ['lifetime']
        guild_leaderboards = await get_guild_local_leaderboard(guild_id)
        guild_leaderboard_configuration = await get_guild_leaderboard_configuration(guild_id)


        if guild_leaderboards:
            for leaderboard_name in guild_leaderboards:
                channel_leaderboard = guild_leaderboard_configuration.get(leaderboard_name,{})
                if channel_name in channel_leaderboard.get('channels',[channel_name]) :
                    # if raid_level in channel_leaderboard.get('level', [raid_level]) :
                    applicable_leaderboards.append(leaderboard_name)

        for leaderboard in applicable_leaderboards:
            existing_reports = guild_dict[guild_id].setdefault('trainers', {}).setdefault(author_id, {}).setdefault('leaderboard-stats', {}).setdefault(leaderboard, {}).setdefault(report_type, 0) - 1
            guild_dict[guild_id]['trainers'][author_id]['leaderboard-stats'][leaderboard][report_type] = existing_reports
            Logger.debug(f"{author_id} has reported {existing_reports} {report_type}")

    except Exception as error:
        Logger.error("Error while recording in leaderboard " + error)
