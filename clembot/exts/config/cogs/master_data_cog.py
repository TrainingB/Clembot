import json
import os
import urllib

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.config.constants import Icons
from clembot.core import checks
from clembot.core.bot import group
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.exts.config.globalconfigmanager import GlobalConfigCache
from clembot.exts.pkmn.gm_pokemon import Pokemon
from clembot.exts.pkmn.raid_boss import RaidMaster
from clembot.utilities.utils.embeds import Embeds


class MasterDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.bot.loop.create_task(RaidMaster.load(bot, True))

    @group(pass_context=True, hidden=True, aliases=["form"])
    async def cmd_form(self, ctx, form: Pokemon):
        print(form)
        if form:
            await ctx.send(embed=Embeds.make_embed(title=form.extended_label, thumbnail=form.preview_url, fields={
                'Fast Moves' : [True, '\n'.join(form.fast_moves_labels)],
                'Charge Moves': [True, '\n'.join(form.charge_moves_labels)],
                'CP Range': [True, '-'.join([str(cp) for cp in form.raid_cp_range])],
            }))


    @group(pass_context=True, hidden=True, aliases=["formx"])
    async def cmd_formx(self, ctx, alias):
        table = self.dbi.table('GM_POKEMON_FORMS')
        forms = await table.query().select().where(table['aliases'].icontains_(alias)).getjson()

        if forms:
            form = forms[0]
            data = json.loads(form.get("data"))

            pForm = Pokemon(data, form.get('pokedex_id'), form.get('aliases'))
            await ctx.send(embed=Embeds.make_embed(title=pForm.extended_label, thumbnail=pForm.preview_url, fields={
                'Fast Moves' : [True, '\n'.join(pForm.fast_moves_labels)],
                'Charge Moves': [True, '\n'.join(pForm.charge_moves_labels)]
            }))

        pass



    @group(pass_context=True, hidden=True, aliases=["migrate"])
    @checks.is_bot_owner()
    async def cmd_migrate(self, ctx):
        try:
            if ctx.invoked_subcommand is None:
                return await Embeds.error(ctx.channel,
                                          f"**{ctx.invoked_with}** can be only used with options **guild, channel**.",
                                          user=ctx.message.author)
        except Exception as error:
            Logger.error(error)


    @cmd_migrate.command(pass_context=True, hidden=True, aliases=["game-master"])
    @wrap_error
    @checks.is_bot_owner()
    async def cmd_migrate_game_master(self, ctx, force=False):
        try:
            current_game_master_version = GlobalConfigCache.by_config_name.get('game-master-version', None)


            rec_count = 10
            load_from_web = True

            if load_from_web:
                url = "https://raw.githubusercontent.com/pokemongo-dev-contrib/pokemongo-game-master/master/versions/latest/V2_GAME_MASTER.json"
                file = urllib.request.urlopen(url)
                data = json.load(file)
                game_master_version = data.get('batchId')
                if not force and current_game_master_version == game_master_version:
                    return await Embeds.message(ctx.channel, f"The latest game master version {game_master_version} is already loaded.")
            else:
                with open(os.path.join(os.path.abspath('.'), 'clembot', 'config', 'V2_GAME_MASTER.json'), 'r') as fd:
                    data = json.load(fd)

            async with ctx.typing():
                table = self.dbi.table('GM_POKEMON_FORMS')
                already_available = await table.query().select('template_id').get()
                templates = [record.get('template_id') for record in already_available]
                new_rows = []
                message: discord.Message = None
                new_rows_count = 0
                for template in data.get('template'):
                    templateId = template.get('templateId')
                    splits = templateId.split('_')
                    # print(templateId)
                    data = template.get('data')
                    if len(splits) > 2 and splits[0].startswith('V') and splits[1] == 'POKEMON' and data.get('templateId', None):

                        if data:
                            data.get('pokemon').pop('camera')
                            data.get('pokemon').pop('encounter')
                            data.get('pokemon').pop('animTime')
                            data.get('pokemon').pop('buddyOffsetMale')
                            data.get('pokemon').pop('buddyOffsetFemale')
                        else:
                            continue


                        form = data.get('pokemon').get('form')
                        record = {
                            'template_id' : template.get('templateId'),
                            'data' : json.dumps(template.get('data')),
                            'pokedex_id' : int(splits[0][1:]),
                            'pokemon_form_id' : "_".join(splits[2:])
                        }
                        if form:
                            alias = form.replace('_', '-')
                            record['aliases'] = [alias]
                        else:
                            record['aliases'] = [record.get('pokemon_form_id')]

                        if template.get('templateId') not in templates:
                            new_rows.append(record)
                            new_rows_count += 1
                        if len(new_rows) > rec_count:
                            table = self.dbi.table('GM_POKEMON_FORMS')
                            await table.insert.rows(new_rows).commit()

                            if message:
                                await message.edit(content=f"{new_rows_count} pokemon forms loaded.")
                            else:
                                message = await ctx.send(content=f"{new_rows_count} pokemon forms loaded.")



                            new_rows = []
                if new_rows:
                    table = self.dbi.table('GM_POKEMON_FORMS')
                    await table.insert.rows(new_rows).commit()

                await GlobalConfigCache.saveclembotconfig(self.bot, 'game-master-version', game_master_version)
                return await Embeds.message(ctx.channel, f"The latest game master version {game_master_version} is loaded successfully.")

        except Exception as error:
            Logger.info(error)

            raise BadArgument(error)


    @cmd_migrate.command(pass_context=True, hidden=True, aliases=["raid-boss"])
    @wrap_error
    @checks.is_bot_owner()
    async def cmd_migrate_raid_boss(self, ctx, force=False):




        pass


    @group(pass_context=True, hidden=True, aliases=["raid-boss"])
    async def cmd_raid_boss(self, ctx):
        """
        !raid-boss
        !raid-boss *level*
        !raid-boss list *level*
        !raid-boss add level *list of pokemon*
        !raid-boss remove level *list of pokemon*
        !raid-boss change level *list of pokemon*
        """

        await RaidMaster.load(ctx.bot, force=True)
        if ctx.invoked_subcommand is None:
            level = ctx.subcommand_passed if ctx.subcommand_passed in RaidMaster.by_level.keys() else None
            return await self.cmd_raid_boss_list(ctx, level)


    @cmd_raid_boss.command(pass_context=True, hidden=True, aliases=["list"])
    async def cmd_raid_boss_list(self, ctx, level=None):
        fields = {}
        raid_levels = [boss_level for boss_level in RaidMaster.by_level.keys() if boss_level == (level or boss_level)]
        title = f"(Level - {level})" if level else ""
        for raid_level in sorted(raid_levels):
            raid = RaidMaster.from_cache(raid_level)
            fields[f'Level {raid_level}'] = [True, '\n'.join(
                [(await Pokemon.convert(ctx, raid_boss)).extended_label for raid_boss in raid['raid_boss']])]

        await ctx.send(
            embed=Embeds.make_embed(header=f"Current Raid Bosses {title}", header_icon=Icons.raid_report, fields=fields,
                                    thumbnail=Icons.raid_report))


    @cmd_raid_boss.command(pass_context=True, hidden=True, aliases=["add"])
    @wrap_error
    @checks.is_guild_admin()
    async def cmd_raid_boss_add(self, ctx, level, *pokemon_list: Pokemon):

        Logger.info(pokemon_list)

        raid_boss_at_level = RaidMaster.from_cache(level)
        raid_bosses = set([pokemon.upper() for pokemon in raid_boss_at_level['raid_boss']])

        for pokeform in pokemon_list:
            raid_bosses.add(pokeform.id.upper())

        raid_boss_at_level['raid_boss'] = raid_bosses

        await raid_boss_at_level.update()
        await self.cmd_raid_boss_list(ctx, level)


    @cmd_raid_boss.command(pass_context=True, hidden=True, aliases=["change"])
    @checks.is_trusted()
    async def cmd_raid_boss_change(self, ctx, level, *pokemon_list: Pokemon):

        Logger.info(pokemon_list)

        raid_boss_at_level = RaidMaster.from_cache(level)
        raid_bosses = set()

        for pokeform in pokemon_list:
            raid_bosses.add(pokeform.id.upper())

        raid_boss_at_level['raid_boss'] = raid_bosses

        await raid_boss_at_level.update()
        await self.cmd_raid_boss_list(ctx, level)


    @cmd_raid_boss.command(pass_context=True, hidden=True, aliases=["remove"])
    @checks.is_trusted()
    @wrap_error
    async def cmd_raid_boss_remove(self, ctx, level, *pokemon_list: Pokemon):

        Logger.info(pokemon_list)

        raid_boss_at_level = RaidMaster.from_cache(level)
        raid_bosses = set([pokemon.upper() for pokemon in raid_boss_at_level['raid_boss']])

        for pokeform in pokemon_list:
            if pokeform.id.upper() in raid_bosses:
                raid_bosses.remove(pokeform.id.upper())

        raid_boss_at_level['raid_boss'] = raid_bosses

        await raid_boss_at_level.update()
        await self.cmd_raid_boss_list(ctx, level)

