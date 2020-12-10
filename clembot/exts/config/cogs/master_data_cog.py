import json
import os
import pickle
import traceback
import urllib

import aiohttp
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
from clembot.exts.pkmn.raid_boss import RaidLevelMaster
from clembot.exts.profile.user_profile import UserProfile
from clembot.utilities.utils.embeds import Embeds
import pydash as _

class MasterDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi
        self.bot.loop.create_task(RaidLevelMaster.load(bot, True))

    @group(pass_context=True, category='Bot Info', aliases=["form"])
    async def cmd_form(self, ctx, form: Pokemon):
        print(form)
        if form:
            await ctx.send(embed=Embeds.make_embed(title=form.extended_label, thumbnail=form.preview_url, fields={
                'Fast Moves' : [True, '\n'.join(form.fast_moves_labels)],
                'Charge Moves': [True, '\n'.join(form.charge_moves_labels)],
                'CP Range': [True, '-'.join([str(cp) for cp in form.raid_cp_range])],
            }))


    # @group(pass_context=True, category='Bot Info', aliases=["formx"])
    # async def cmd_formx(self, ctx, alias):
    #     table = self.dbi.table('PB_POKEMON_FORM')
    #     forms = await table.query().select().where(table['aliases'].icontains_(alias)).getjson()
    #
    #     if forms:
    #         form = forms[0]
    #         data = json.loads(form.get("data"))
    #
    #         pForm = Pokemon(data, form.get('pokedex_id'), form.get('aliases'), form.get('pokemon_form_id'))
    #         await ctx.send(embed=Embeds.make_embed(title=pForm.extended_label, thumbnail=pForm.preview_url, fields={
    #             'Fast Moves' : [True, '\n'.join(pForm.fast_moves_labels)],
    #             'Charge Moves': [True, '\n'.join(pForm.charge_moves_labels)]
    #         }))
    #
    #     pass



    @group(pass_context=True, category='Bot Info', aliases=["migrate"])
    @checks.is_bot_owner()
    async def cmd_migrate(self, ctx):
        if ctx.invoked_subcommand is None:
            raise BadArgument("`!migrate` can be used with `game-master, user-profile, raid-boss`")

    @cmd_migrate.command(pass_context=True, category='Bot Info', aliases=["pb-game-master"])
    @wrap_error
    @checks.is_bot_owner()
    async def cmd_migrate_pb_game_master(self, ctx, update=False):
        try:
            rec_count = 25
        
            async with aiohttp.ClientSession() as sess:
                async with sess.get('https://fight.pokebattler.com/pokemon') as resp:
                    data = await resp.json()
                    
            async with ctx.typing():
                table = self.dbi.table('PB_POKEMON_FORM')
                already_available = await table.query().select('pokemon_form_id').get()
                templates = [record.get('pokemon_form_id') for record in already_available]
                new_rows = []
                message: discord.Message = None
                new_rows_count = 0
                
                for pb_form in data.get('pokemon'):
    
                    pokemon_id = pb_form.get('pokemonId')
                    
                    pokeform_id = pokemon_id.replace('_FORM','')
                    
                    record = {
                                'pokemon_form_id': pokeform_id,
                                'pokedex_id': _.get(pb_form, 'pokedex.pokemonNum'),
                                'aliases': [pokeform_id.replace('_', '-')],
                                'data': json.dumps(pb_form),
                                }
                    
                    print(f"{pokeform_id} ({record['pokedex_id']}) => {record['aliases']}  ")

                    if not update and pokeform_id not in templates:
                        new_rows.append(record)
                        new_rows_count += 1
                    if len(new_rows) > rec_count:
                        table = self.dbi.table('PB_POKEMON_FORM')
                        await table.insert.rows(new_rows).commit()
        
                        if message:
                            await message.edit(content=f"{new_rows_count} pokemon forms loaded.")
                        else:
                            message = await ctx.send(content=f"{new_rows_count} pokemon forms loaded.")
                        new_rows = []


                if new_rows:
                    table = self.dbi.table('PB_POKEMON_FORM')
                    await table.insert.rows(new_rows).commit()

                return await Embeds.message(ctx.channel, f"The latest game master version is loaded successfully.")
    
        except Exception as error:
        
            Logger.info(error)
        
            raise BadArgument(error)

    @cmd_migrate.command(pass_context=True, category='Bot Info', aliases=["game-master"])
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
                table = self.dbi.table('PB_POKEMON_FORM')
                already_available = await table.query().select('template_id').get()
                templates = [record.get('template_id') for record in already_available]
                new_rows = []
                message: discord.Message = None
                new_rows_count = 0
                for template in data.get('template'):
                    
                    try:
                    
                        templateId = template.get('templateId')
                        splits = templateId.split('_')
                        # print(templateId)
                        data = template.get('data')
                        if len(splits) > 2 and splits[0].startswith('V') and splits[1] == 'POKEMON' and data.get('templateId', None):
    
                            if data:
                                data.get('pokemon').pop('camera', 0)
                                data.get('pokemon').pop('encounter', 0)
                                data.get('pokemon').pop('animTime', 0)
                                data.get('pokemon').pop('buddyOffsetMale', 0)
                                data.get('pokemon').pop('buddyOffsetFemale', 0)
                            else:
                                continue
    
    
                            form = data.get('pokemon').get('form')
                            print(f"{splits} => {'_'.join(splits[2:])}")
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
                                table = self.dbi.table('PB_POKEMON_FORM')
                                await table.insert.rows(new_rows).commit()
    
                                if message:
                                    await message.edit(content=f"{new_rows_count} pokemon forms loaded.")
                                else:
                                    message = await ctx.send(content=f"{new_rows_count} pokemon forms loaded.")
                                new_rows = []
                        

                        
                    
                    except Exception as error:
                        print(error)
                        print(template)
                        continue
                    #
                    # if new_rows:
                    #     table = self.dbi.table('PB_POKEMON_FORM')
                    #     await table.insert.rows(new_rows).commit()

                await GlobalConfigCache.saveclembotconfig(self.bot, 'game-master-version', game_master_version)
                return await Embeds.message(ctx.channel, f"The latest game master version {game_master_version} is loaded successfully.")

        except Exception as error:
            
            Logger.info(error)

            raise BadArgument(error)


    @cmd_migrate.command(pass_context=True, category='Bot Info', aliases=["leaderboard"])
    @wrap_error
    @checks.is_bot_owner()
    async def cmd_migrate_leaderboard(self, ctx, guild_id, trainer_id, force=False):
        try:
            with open(os.path.join(os.path.abspath('.'), 'data', 'guilddict_clembot_202008020605'), "rb") as fd:
                server_dict_old = pickle.load(fd)

            # message = await ctx.send(content=f"Migrating user profiles...")


            guild_id = int(guild_id) if guild_id else ctx.guild.id
            trainer_id = int(trainer_id)
            guild_dict = server_dict_old.get(guild_id)
            trainers_dict = guild_dict.get('trainers')

            if trainer_id is not None:
                trainer_dict = trainers_dict.get(trainer_id)

                await ctx.send(content=json.dumps(trainer_dict, indent=1))

            # async with ctx.typing():
            #
            #     # for guild_id in server_dict_old.keys():
            #     await message.edit(content=f"Processing {guild_id}")
            #
            #     total_trainers = len(trainers_dict.keys())
            #     processed_trainers = 0
            #     await message.edit(content=f"Processed {processed_trainers}/{total_trainers} trainers.")
            #
            #     for trainer_id in trainers_dict.keys():
            #         processed_trainers+=1
            #         trainer_dict = trainers_dict.get(trainer_id)
            #         trainer_dict.pop('leaderboard-stats', None)
            #         trainer_dict.pop('lifetime', None)
            #         trainer_dict.pop('badges', None)
            #
            #         if processed_trainers % 20 == 0:
            #             await message.edit(content=f"Processed {processed_trainers}/{total_trainers} trainers.")
            #         if not bool(trainer_dict):
            #             continue
            #
            #
            #         user_profile = await UserProfile.find(self.bot, trainer_id)
            #         if user_profile['status'] == batch:
            #             continue
            #
            #         user_profile['trade_requests'] = trainer_dict.get('trade_requests')
            #         user_profile['trade_offers'] = trainer_dict.get('trade_offers')
            #         user_profile['trainer_code'] = trainer_dict.get('profile',{}).get('trainer-code')
            #         user_profile['ign'] = trainer_dict.get('profile', {}).get('ign')
            #         user_profile['silph_id'] = trainer_dict.get('profile', {}).get('silph-id')
            #         user_profile['pokebattler_id'] = trainer_dict.get('profile', {}).get('pokebattler_id')
            #         user_profile['status'] = batch
            #         await user_profile.update()

                    # break
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")




    @cmd_migrate.command(aliases=["user-profile"])
    @wrap_error
    async def cmd_migrate_user_profile(self, ctx, guild_id=None, batch='migrated'):
        try:
            with open(os.path.join(os.path.abspath('.'), 'data', 'guilddict_clembot_20200910'), "rb") as fd:
                server_dict_old = pickle.load(fd)

            message = await ctx.send(content=f"Migrating user profiles...")


            if guild_id is None:
                server_info = {}

                for gid in server_dict_old.keys():

                    guild_dict = server_dict_old.get(gid)
                    #
                    # one_guild = self.bot.get_guild(int(gid))
                    #
                    # if one_guild is None:
                    #     continue
                    #
                    # guild_name = one_guild.name
                    trainers = len(guild_dict.get('trainers',{}).keys())
                    if trainers != 0:
                        server_info[gid] = [False, f"{trainers} trainers."]

                return await ctx.send(embed=Embeds.make_embed(fields=server_info))


            guild_id = int(guild_id) if guild_id else ctx.guild.id

            async with ctx.typing():

                # for guild_id in server_dict_old.keys():
                await message.edit(content=f"Processing {guild_id}")
                guild_dict = server_dict_old.get(guild_id)

                trainers_dict = guild_dict.get('trainers')
                total_trainers = len(trainers_dict.keys())
                processed_trainers = 0
                await message.edit(content=f"Processed {processed_trainers}/{total_trainers} trainers.")

                for trainer_id in trainers_dict.keys():
                    processed_trainers+=1
                    trainer_dict = trainers_dict.get(trainer_id)
                    trainer_dict.pop('leaderboard-stats', None)
                    trainer_dict.pop('lifetime', None)
                    trainer_dict.pop('badges', None)

                    if processed_trainers % 20 == 0:
                        await message.edit(content=f"Processed {processed_trainers}/{total_trainers} trainers.")
                    if not bool(trainer_dict):
                        continue


                    user_profile = await UserProfile.find(self.bot, trainer_id)
                    if user_profile['status'] == batch:
                        continue

                    user_profile['trade_requests'] = trainer_dict.get('trade_requests')
                    user_profile['trade_offers'] = trainer_dict.get('trade_offers')
                    user_profile['trainer_code'] = trainer_dict.get('profile',{}).get('trainer-code')
                    user_profile['ign'] = trainer_dict.get('profile', {}).get('ign')
                    user_profile['silph_id'] = trainer_dict.get('profile', {}).get('silph-id')
                    user_profile['pokebattler_id'] = trainer_dict.get('profile', {}).get('pokebattler_id')
                    user_profile['status'] = batch
                    await user_profile.update()

                    # break
            await message.edit(content=f"Processed {processed_trainers}/{total_trainers} trainers.")
        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")













    @cmd_migrate.command(pass_context=True, category='Bot Info', aliases=["raid-boss"])
    @wrap_error
    @checks.is_bot_owner()
    async def cmd_migrate_raid_boss(self, ctx, force=False):




        pass


    @group(pass_context=True, category='Bot Info', aliases=["raid-boss"])
    async def cmd_raid_boss(self, ctx):
        """
        !raid-boss
        !raid-boss *level*
        !raid-boss list *level*
        !raid-boss add level *list of pokemon*
        !raid-boss remove level *list of pokemon*
        !raid-boss change level *list of pokemon*
        """

        await RaidLevelMaster.load(ctx.bot, force=True)
        if ctx.invoked_subcommand is None:
            level = ctx.subcommand_passed if ctx.subcommand_passed in RaidLevelMaster.by_level.keys() else None
            return await self.cmd_raid_boss_list(ctx, level)


    @cmd_raid_boss.command(pass_context=True, category='Bot Info', aliases=["list"])
    async def cmd_raid_boss_list(self, ctx, level=None):
        fields = { }
        raid_levels = [boss_level for boss_level in RaidLevelMaster.by_level.keys() if boss_level == (level or boss_level)]
        title = f"(Level - {level})" if level else ""
        for raid_level in sorted(raid_levels):
            raid = RaidLevelMaster.from_cache(raid_level)
            fields[f'Level {raid_level}'] = [True, '\n'.join(
                [(await Pokemon.convert(ctx, raid_boss)).extended_label for raid_boss in raid['raid_boss']])]

        await ctx.send(
            embed=Embeds.make_embed(header=f"Current Raid Bosses {title}", header_icon=Icons.raid_report, fields=fields,
                                    thumbnail=Icons.raid_report))


    @cmd_raid_boss.command(pass_context=True, category='Bot Info', aliases=["add"])
    @wrap_error
    @checks.is_guild_admin()
    async def cmd_raid_boss_add(self, ctx, level, *pokemon_list: Pokemon):

        Logger.info(pokemon_list)

        raid_boss_at_level = RaidLevelMaster.from_cache(level)
        raid_bosses = set([pokemon.upper() for pokemon in raid_boss_at_level['raid_boss']])

        for pokeform in pokemon_list:
            raid_bosses.add(pokeform.id.upper())

        raid_boss_at_level['raid_boss'] = raid_bosses

        await raid_boss_at_level.update()
        await self.cmd_raid_boss_list(ctx, level)


    @cmd_raid_boss.command(pass_context=True, category='Bot Info', aliases=["change"])
    @checks.is_trusted()
    async def cmd_raid_boss_change(self, ctx, level, *pokemon_list: Pokemon):

        Logger.info(pokemon_list)

        raid_boss_at_level = RaidLevelMaster.from_cache(level)
        raid_bosses = set()

        for pokeform in pokemon_list:
            raid_bosses.add(pokeform.id.upper())

        raid_boss_at_level['raid_boss'] = raid_bosses

        await raid_boss_at_level.update()
        await self.cmd_raid_boss_list(ctx, level)


    @cmd_raid_boss.command(pass_context=True, category='Bot Info', aliases=["remove"])
    @checks.is_trusted()
    @wrap_error
    async def cmd_raid_boss_remove(self, ctx, level, *pokemon_list: Pokemon):

        Logger.info(pokemon_list)

        raid_boss_at_level = RaidLevelMaster.from_cache(level)
        raid_bosses = set([pokemon.upper() for pokemon in raid_boss_at_level['raid_boss']])

        for pokeform in pokemon_list:
            if pokeform.id.upper() in raid_bosses:
                raid_bosses.remove(pokeform.id.upper())

        raid_boss_at_level['raid_boss'] = raid_bosses

        await raid_boss_at_level.update()
        await self.cmd_raid_boss_list(ctx, level)

