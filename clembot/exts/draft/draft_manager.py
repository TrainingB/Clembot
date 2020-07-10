import json

import discord
from discord.ext import commands
from discord.ext.commands import UserConverter

from clembot.core import checks
from clembot.core.bot import group, command
from clembot.core.commands import Cog
from clembot.exts.draft.draft import DraftStatus, Draft, DraftInterface
from clembot.exts.pkmn.pokemon import PokemonConverter, PokemonCache, OptionalPokemonConverter
from clembot.utilities.utils.utilities import Utilities


class DraftManagerCog(Cog):


    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()
        self.dbi = bot.dbi
        self.draft_interface = DraftInterface(bot.dbi)

    async def fetch_draft_for_channel(self, guild_id, channel_id):

        guild_channel_key = f"{guild_id}_{channel_id}"

        draft_from_db = await self.draft_interface.find_draft(guild_id, channel_id)
        if draft_from_db:
            return draft_from_db
        else:
            raise Exception("No draft found.")



    @group(pass_context=True, hidden=True, aliases=["draft", "d"])
    async def _draft(self, ctx):
        if ctx.invoked_subcommand is None:
            return await Utilities.message(ctx.message.channel, f"Draft feature is under development!", user=ctx.author)


    @_draft.command(aliases=["check"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_check(self, ctx, text):

        try:

            pokemon = await PokemonConverter.convert(text, ctx, text)

            if pokemon:
                await Utilities.message(ctx.channel, f"{pokemon} details {pokemon.to_dict}")

        except Exception as error:
            await Utilities.error(ctx.channel, error)



    @_draft.command(aliases=["create", "new"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_create(self, ctx, draft_channel: discord.TextChannel = None):

        if draft_channel is None:
            draft_channel = ctx.channel

        draft = await self.draft_interface.find_draft(guild_id=ctx.guild.id, channel_id=draft_channel.id)
        if draft:
            return await Utilities.message(ctx.message.channel, f"A draft already exists for {draft_channel.mention} with code **{draft.draft_code}**")


        draft = Draft(guild_id=ctx.guild.id, channel_id=draft_channel.id)
        await self.draft_interface.save_draft(draft)

        return await Utilities.message(ctx.message.channel, f"A new draft can be managed in {draft_channel.mention} with code **{draft.draft_code}**")


    @_draft.command(aliases=["info"], pass_context=True)
    async def _draft_info(self, ctx):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
            if draft:
                print(draft.draft_content)
                return await Utilities._send_embed(ctx.channel, "", f"**Draft [{draft.draft_code}] - {draft.status} **", draft.embed_fields, footer=f"Managed by : {draft.draft_code} | check mark - Auto draft enabled!")
            else:
                return await Utilities.error(ctx.message.channel, f"No draft found for **{ctx.channel.mention}**")
        except Exception as error:
            print(error)
            return await Utilities.error(ctx.message.channel, f"{error}")


    @_draft.command(aliases=["reset"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_reset(self, ctx, mode=None):
        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        if mode == 'team':
            draft.reset_teams()
        else:
            draft.reset(ctx.guild.id, ctx.channel.id)

        await self.draft_interface.save_draft(draft)

        await Utilities.message(ctx.channel, f"Draft **{draft}** has been reset.")


    @_draft.command(aliases=["shuffle"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_shuffle(self, ctx):
        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        draft.shuffle_player_list()

        await self.draft_interface.save_draft(draft)

        await Utilities.message(ctx.channel, f"Current draft order is : {draft.player_draft_order_mentions}")

    @_draft.command(aliases=["add-player", "ap"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_add_player(self, ctx, *player_list: discord.Member):

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
        if DraftStatus.value(draft.status) >= DraftStatus.value(DraftStatus.DRAFT):
            return await Utilities.error(ctx.channel, f"Draft {draft} is in {draft.status} status. New players can not be added to the draft anymore.")


        for player in player_list:
            if draft.is_player_exists(player):
                await Utilities.error(ctx.channel, f"{player.mention} is already on the player list.")
                continue
            if draft.add_player(player):
                await Utilities.message(ctx.channel, f"**[{draft.number_of_players}/{draft.max_number_of_players}]** {player.mention} has been added to the draft.")
                await self.draft_interface.save_draft(draft)

        print(draft)


    @_draft.command(aliases=["join"], pass_context=True)
    async def _draft_join(self, ctx):

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
        if DraftStatus.value(draft.status) >= DraftStatus.value(DraftStatus.DRAFT):
            return await Utilities.error(ctx.channel, f"Draft {draft} is in {draft.status} status. New players can not be added to the draft anymore.")

        player = ctx.message.author
        if draft.is_player_exists(player):
            await Utilities.error(ctx.channel, f"{player.mention} you are already on the player list.")

        if draft.add_player(player):
            await Utilities.message(ctx.channel, f"**[{draft.number_of_players}/{draft.max_number_of_players}]** {player.mention} has been added to the draft.")
            await self.draft_interface.save_draft(draft)

        print(draft)







    @command(aliases=["dump-form"], pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def _dump_pokeform(self, ctx):

        await Utilities.send_to_hastebin(ctx.channel, json.dumps(PokemonCache.cache()))


    @command(aliases=["debug-form"], pass_context=True)
    async def _debug_pokemon_form(self, ctx):
        try:

            result_record = await self.dbi.table('tbl_pokemon_master').query().select().getjson()

            await Utilities.send_to_hastebin(ctx.channel, json.dumps(result_record))

        except Exception as error:
            await Utilities.error(ctx.channel, error)


    @command(aliases=["refresh-cache"], pass_context=True)
    async def _refresh_cache(self, ctx):
        try:
            results = await PokemonCache.load_cache_from_dbi(self.dbi)

            await Utilities.send_to_hastebin(ctx.channel, json.dumps(results))

            await Utilities.message(ctx.channel, f"The current cache size for pokemon is **{PokemonCache.cache_size()}**!")
        except Exception as error:
            await Utilities.error(ctx.channel, error)


    async def send_dm_for_auto_draft(self, ctx, player, draft, message_content, new_selection):

        await Utilities.message(ctx.channel, f"{player.mention} check your DM for auto-draft updates!")

        if not player.bot:
            await Utilities.message(player, f"**Guild**: **{ctx.channel.guild.name}** \n**Draft**: {draft} in {ctx.channel.mention} "
            f"\n**You entered**: `{message_content}`"
            f"\n**Your current auto-draft selection**: {new_selection}")



    @_draft.group(aliases=["auto"], pass_context=True)
    async def _draft_auto(self, ctx):
        if ctx.invoked_subcommand is None:
            return await Utilities.message(ctx.message.channel, f"!draft auto allows following options `add, clear, remove`", user=ctx.author)


    @_draft_auto.command(aliases=["enable"], pass_context=True)
    async def _draft_auto_enable(self, ctx):
        await self._draft_auto_change(ctx, True)


    @_draft_auto.command(aliases=["disable"], pass_context=True)
    async def _draft_auto_disable(self, ctx):
        await self._draft_auto_change(ctx, False)


    async def _draft_auto_change(self, ctx, auto_draft_mode):
        player = ctx.message.author
        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        change_auto_draft = await Utilities.ask_confirmation(ctx, ctx.message,
                                                             f"Are you sure you want to change auto draft for {player.mention} to **{auto_draft_mode}**?",
                                                             "Alright, sit tight!",
                                                             "Okay, just wanted to make sure!", "Timed out! No change done.")
        if change_auto_draft:
            draft.set_auto_draft(player.id, auto_draft_mode)
            await self.draft_interface.save_draft(draft)

        await Utilities.message(ctx.channel, f"For Draft **{draft}**, auto draft has been set to **{auto_draft_mode}** for {player.mention}")


    async def get_member_and_pokemon(self, ctx, args):
        player = None
        list_of_pokemon = []
        pokemon_converter = OptionalPokemonConverter()
        for arg in args:

            pokemon = await pokemon_converter.convert(ctx, argument=arg)
            if pokemon:
                list_of_pokemon.append(pokemon)
                continue

            member = await get_member(ctx, [arg], False)
            if member:
                player = member
                continue

        return player, list_of_pokemon

    @_draft_auto.command(aliases=["add"], pass_context=True)
    async def _draft_auto_add(self, ctx, *args):

        player, list_of_pokemon = await self.get_member_and_pokemon(ctx, args)

        message_content = ctx.message.content

        if player and checks.guildowner_or_permissions(manage_channels=True):
            player = player
        else:
            player = ctx.message.author

        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        new_selection = draft.add_to_player_auto_draft_selection(player.id, list_of_pokemon)

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)


    @_draft_auto.command(aliases=["remove"], pass_context=True)
    async def _draft_auto_remove(self, ctx, *provided_list_of_pokemon: OptionalPokemonConverter):

        list_of_pokemon = OptionalPokemonConverter.remove_empty_members(provided_list_of_pokemon)
        message_content = ctx.message.content

        player = ctx.message.author
        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        new_selection = draft.remove_from_player_auto_draft_selection(player.id, list_of_pokemon)

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)


    @_draft_auto.command(aliases=["set"], pass_context=True)
    async def _draft_auto_set(self, ctx, *provided_list_of_pokemon: OptionalPokemonConverter):

        list_of_pokemon = OptionalPokemonConverter.remove_empty_members(provided_list_of_pokemon)
        message_content = ctx.message.content

        player = ctx.message.author
        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        draft.set_player_auto_draft_selection(player.id, [pokemon.pokemon_id for pokemon in list_of_pokemon])

        new_selection = draft.get_player_auto_draft_selection(player.id)

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)


    @_draft_auto.command(aliases=["clear"], pass_context=True)
    async def _draft_auto_clear(self, ctx):

        message_content = ctx.message.content

        player = ctx.message.author
        await ctx.message.delete()

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

        new_selection = draft.set_player_auto_draft_selection(player.id, [])

        await self.draft_interface.save_draft(draft)

        await self.send_dm_for_auto_draft(ctx, player, draft, message_content, new_selection)



    @_draft.command(aliases=["set"], pass_context=True)
    @checks.guildowner_or_permissions(manage_channels=True)
    async def _draft_update_attributes(self, ctx, key=None, *argument_list):

        available_keys = ['status', 'admin', 'exclude', 'auto']
        new_value = None
        if key is None or key not in available_keys:
            raise Exception("Not enough details to set/change configuration. Usage `!draft set key value``")

        draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
        print(f"For {ctx.channel.id} =====> {draft}")
        if key == 'auto':

            player = await get_member(ctx, argument_list) if argument_list else ctx.message.author

            current_auto_draft_selection = draft.get_auto_draft(player.id)

            change_auto_draft = await Utilities.ask_confirmation(ctx, ctx.message, f"Auto draft for {player.mention} is set to **{current_auto_draft_selection}**. Are you sure you want to change to **{not current_auto_draft_selection}**?", "Alright, sit tight!",
                                                                 "Okay, just wanted to make sure!", "Timed out! No change done.")
            if change_auto_draft:
                current_auto_draft_selection = not current_auto_draft_selection
                draft.set_auto_draft(player.id, current_auto_draft_selection)

            new_value = f"{current_auto_draft_selection} for {player.mention}"

        elif key == 'status':
            value = argument_list[0]
            if value.upper() in DraftStatus.status_by_rank:
                status = value.upper()
                if status == DraftStatus.DRAFT:
                    shuffle_list = await Utilities.ask_confirmation(ctx, ctx.message, "Do you want to shuffle the player list for draft?", "Alright, shuffling player list.",
                                                                    "Alright, leaving order intact.", "Timed out!")
                    if shuffle_list:
                        draft.shuffle_player_list()
                        await Utilities.message(ctx.channel, f"Current draft order is : {draft.player_draft_order_mentions}")

                draft.status = status


                new_value = status
            else:
                raise Exception(f"Invalid value for status. Acceptable status are {', '.join(DraftStatus.status_by_rank)}")

        elif key == 'admin':

            try:
                if not argument_list:
                    draft.admin = []
                    new_value = draft.admin
                else:
                    member = await get_member(ctx, argument_list)
                    if member:
                        if member.id not in draft.admin:
                            draft.admin.append(member.id)
                            new_value = draft.admin_mention
                        else:
                            raise Exception(f"{member.mention} is already an admin for this draft.")
                    else:
                        raise Exception("Invalid user information. Only valid user can be set as draft admin.")

            except Exception as error:
                raise Exception(error)


        elif key == 'exclude':

            for pkmn in argument_list:
                pokemon = await PokemonConverter.convert(PokemonConverter, ctx, pkmn)
                if pokemon:
                    draft.add_as_excluded(pokemon)

            new_value = ", ".join(draft.excluded)

        await self.draft_interface.update_draft(draft)
        await Utilities.message(ctx.channel, f"For Draft **{draft}** the **{key}** is set to **{new_value}**")


    async def auto_draft_for_current_player(self, ctx, draft):

        while True:
            current_player_id = draft.current_player
            auto_draft_enabled = draft.get_auto_draft(current_player_id)

            if not auto_draft_enabled:
                return await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")

            await Utilities.message(ctx.channel, f"Trying to auto draft for <@{draft.current_player}>")

            pokemon_id_to_draft = None
            for pokemon_id in draft.get_player_auto_draft_selection(current_player_id):
                print(f"{pokemon_id} for {current_player_id}")
                if pokemon_id in draft.drafted:
                    continue
                else:
                    pokemon_id_to_draft = pokemon_id
                    break

            if not pokemon_id_to_draft:
                return await Utilities.message(ctx.channel, f"<@{draft.current_player}> has no valid pokemon remaining in auto-draft. Make the next pick!")

            player = await get_member(ctx, [current_player_id])
            pokemon = PokemonCache.to_pokemon(pokemon_id_to_draft)

            try:
                draft.draft_pokemon(player, pokemon)
                await Utilities.message(ctx.channel, f"**[{draft.current_drafted_slots}/{draft.total_drafted_slots}]** Player {player.mention} has drafted **{pokemon}** successfully. **[Auto Drafted]**")
                await self.draft_interface.save_draft(draft)

            except Exception as error:
                return await Utilities.message(ctx.channel, f"<@{draft.current_player}> error happened while auto-drafting. Make the next pick!")


            if draft.complete:
                return await Utilities.message(ctx.channel, f"The draft is complete now. You can head over to the silph.gg and choose teams.")
            else:
                await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")


    @_draft.command(aliases=["pick"], pass_context=True)
    async def _draft_pick(self, ctx, pokemon: PokemonConverter, player: discord.Member = None):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

            if DraftStatus.value(draft.status) != DraftStatus.value(DraftStatus.DRAFT):
                return await Utilities.error(ctx.channel, f"Draft {draft} is in {draft.status} status. Drafting new pokemon is allowed during {DraftStatus.DRAFT} status only.")

            if player:
                if ctx.author.id not in draft.admin:
                    raise Exception("Only draft admin can pick pokemon for other players.")
            else:
                player = ctx.author

            if pokemon:
                draft.draft_pokemon(player, pokemon)
                await Utilities.message(ctx.channel, f"**[{draft.current_drafted_slots}/{draft.total_drafted_slots}]** Player {player.mention} has drafted **{pokemon}** successfully.")
                await self.draft_interface.save_draft(draft)

            if draft.complete:
                await Utilities.message(ctx.channel, f"The draft is complete now. You can head over to the silph.gg and choose teams.")
            else:
                await self.auto_draft_for_current_player(ctx, draft)
                # await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")

        except Exception as error:
            await Utilities.error(ctx.channel, error, ctx.author)

    @_draft.command(aliases=["next"], pass_context=True)
    async def _draft_next(self, ctx):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)
            await Utilities.message_as_text(ctx.channel, f"<@{draft.current_player}> its your turn to make the next pick!")
        except Exception as error:
            await Utilities.error(ctx.channel, error, ctx.author)

    @_draft.command(aliases=["dump"], pass_context=True)
    async def _draft_dump(self, ctx):
        try:
            draft = await self.fetch_draft_for_channel(ctx.guild.id, ctx.channel.id)

            await Utilities.send_to_hastebin(ctx.channel, json.dumps(draft.draft_content))


        except Exception as error:
            await Utilities.error(ctx.channel, error, ctx.author)



    @_draft.command(aliases=["help"], pass_context=True)
    async def _draft_help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(
            embed=DraftManagerCog.get_beep_embed(title="Help - Draft Management", description=DraftManagerCog.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


    beep_notes = ("""**{member}** here are the commands for draft management. 

**Player commands**
**!draft join** - join the current draft for the channel.
**!draft pick pokemon** - drafts a pokemon for you if it is available for drafting purposes.
**!draft next** - send a mention to next person to make the selection
**!draft auto enable** - enable auto-drafting
**!draft auto disable** - disable auto-drafting

**!draft auto add pokemon-list** - add pokemon to your auto-draft list
**!draft auto remove pokemon-list** - remove pokemon from your auto-draft list
**!draft auto set pokemon-list** - set the pokemon list as your auto-draft list
**!draft auto clear** - clears your auto-draft list


**Admin commands (will need manage channel permissions)** 
**!draft create** - creates a draft in the current channel. One channel can hold only one draft.
**!draft set admin @user** - makes the user admin for the draft ( they need to have manage_channel permission )

**!draft set status *status_value*** - changes the status of the draft. 
**Drafts go from CREATED -> SIGN_UP -> DRAFT -> COMPLETE.**

**!draft add-player @user** - adds user to draft player team
**!draft info** - display draft information

""")

    @classmethod
    def get_beep_embed(cls, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(cls, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=DraftManagerCog.get_beep_embed(title="Help - Trade Management", description=DraftManagerCog.beep_notes.format(member=ctx.message.author.display_name), footer=footer))

    @command(aliases=["add-emoji"], pass_context=True)
    async def _add_emoji(self, ctx, *pokemon_list: PokemonConverter):
        try:
            if pokemon_list:
                for pokemon in pokemon_list:
                    print(pokemon.emoji)
                    if not pokemon.emoji:
                        emoji = await PokemonCache.create_emoji(ctx, self.dbi, pokemon.pokemon_id)
                        await Utilities.message(ctx.channel, f"[{len(ctx.guild.emojis)}/50]{pokemon.pokemon_id}{emoji} can be accessed by \\{str(emoji)}!")

            else:
                list_of_pokemon = await self.dbi.table('tbl_pokemon_master').query().select().order_by('pokemon_id').getjson()
                for pokemon_record in list_of_pokemon:
                    print(pokemon_record['emoji_key'])
                    if not pokemon_record['emoji_key']:
                        emoji = await PokemonCache.create_emoji(ctx, self.dbi, pokemon_record['pokemon_id'])
                        await Utilities.message(ctx.channel, f"[{len(ctx.guild.emojis)}/50]{pokemon_record['pokemon_id']}{emoji} can be accessed by \\{str(emoji)}!")

        except Exception as error:
            await Utilities.error(ctx.channel, error)



async def get_member(ctx, argument_list, error_when_not_found=True):

    user_converter = UserConverter()

    # converter = MemberConverter()
    if argument_list is None:
        return None
    else:
        member = None
        try:
            member = await user_converter.convert(ctx=ctx, argument=str(argument_list[0]))
            return member
        except Exception as error:
            if error_when_not_found:
                print(error)
                raise Exception("Member not found!")
            else:
                return None


