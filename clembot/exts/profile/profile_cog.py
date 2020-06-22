import discord
from discord.ext import commands

from clembot.exts.profile.user_metadata import UserMetadata
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class ProfileCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

    async def find_user_metadata(self, ctx, member):

        if member:
            user = member
        elif len(ctx.message.mentions) > 0:
            user = ctx.message.mentions[0]
        else:
            user = ctx.get.member(ctx.subcommand_passed) or ctx.message.author

        user_metadata = await UserMetadata.data(self.bot, user.id, ctx.message.guild.id)
        return user_metadata

    @commands.group(pass_context=True, hidden=True, aliases=["profile"])
    async def cmd_profile(self, ctx):
        try:

            if ctx.invoked_subcommand is None:
                user_metadata = await self.find_user_metadata(ctx, None)
                await ctx.send(embed=user_metadata.embed(ctx))

        except Exception as error:
            print(error)


    @cmd_profile.command(pass_context=True, hidden=True, aliases=["tc", "trainer-code"])
    async def cmd_profile_trainer_code(self, ctx, trainer_code=None, member: discord.Member=None):
        try:
            user_metadata = await self.find_user_metadata(ctx, member)

            if trainer_code:
                user_metadata.trainer_code.append(trainer_code)
            else:
                user_metadata.trainer_code = []

            await user_metadata.update()
            await ctx.send(embed=user_metadata.embed(ctx))

        except Exception as error:
            print(error)

    @cmd_profile.command(pass_context=True, hidden=True, aliases=["ign"])
    async def cmd_profile_ign(self, ctx, ign=None, member: discord.Member=None):
        try:
            user_metadata = await self.find_user_metadata(ctx, member)

            if ign:
                user_metadata.ign.append(ign)
            else:
                user_metadata.ign = []

            await user_metadata.update()
            await ctx.send(embed=user_metadata.embed(ctx))

        except Exception as error:
            print(error)


    @cmd_profile.command(pass_context=True, hidden=True, aliases=["pokebattler", "pb"])
    async def cmd_profile_pokebattler(self, ctx, pokebattler_id=None, member: discord.Member=None):
        try:
            user_metadata = await self.find_user_metadata(ctx, member)

            user_metadata.pokebattler_id = pokebattler_id

            await user_metadata.update()
            await ctx.send(embed=user_metadata.embed(ctx))

        except Exception as error:
            print(error)


    @cmd_profile.command(pass_context=True, hidden=True, aliases=["silph"])
    # @commands.command(pass_context=True, hidden=True, aliases=["silph"])
    async def cmd_profile_silph(self, ctx, silph_user: str = None, member: discord.Member=None):
        """Links a server member to a Silph Road Travelers Card."""
        try:
            user_metadata = await self.find_user_metadata(ctx, member)

            if not silph_user:
                await Embeds.message(ctx.channel, f'Silph Road Travelers Card cleared!')

            else:
                silph_cog = ctx.bot.cogs.get('Silph')
                if not silph_cog:
                    return await Embeds.error(ctx.channel, f"The Silph Extension isn't accessible at the moment, sorry!")

                async with ctx.typing():
                    card = await silph_cog.get_silph_card(silph_user)
                    if not card:
                        return await Embeds.error(ctx.channel, f"Silph Card for {silph_user} not found.")

                if not card.discord_name:
                    return await Embeds.error(ctx.channel, f'No Discord account found linked to this Travelers Card!')

                if card.discord_name != str(ctx.author):
                    return await Embeds.error(ctx.channel, f'This Travelers Card is linked to another Discord account!')

            user_metadata.silph_id = silph_user
            await user_metadata.update()

            await ctx.send(embed=card.embed(0))
        except Exception as error:
            print(error)

    @commands.group(pass_context=True, hicdden=True, aliases=["tc","trainer-code"])
    async def cmd_trainer_code(self, ctx, member: discord.Member=None):
        if ctx.invoked_subcommand is None:
            try:

                user_metadata = await self.find_user_metadata(ctx, member)

                if user_metadata.trainer_code:
                    for code in user_metadata.trainer_code:
                        await ctx.send(f"`{code}`")
                    return
                else:
                    return await Embeds.error(ctx.channel, f"<@{user_metadata.user_id}> hasn't share the trainer-code with me yet.")

                await ctx.send(embed=user_metadata.embed(ctx))

            except Exception as error:
                print(error)

    @commands.command(aliases=["whois", "who-is"])
    async def cmd_who_is(self, ctx, ign=None):

        guild_id = ctx.guild.id
        user_table = self.bot.dbi.table('user_metadata')
        report_user_query = user_table.query()
        _data = report_user_query.where(user_table['ign'].icontains_(ign), guild_id=guild_id)
        db_records = await _data.get()

        if db_records:
            user_metadata = UserMetadata.from_db_dict(self.bot, db_records[0])

            return await ctx.send(embed=user_metadata.embed(ctx))

        await Embeds.error(ctx.channel, f"I didn't find any match for IGN **{ign}**!", user=ctx.author)



    @commands.command(pass_context=True, hicdden=True, aliases=["in-role"])
    async def cmd_in_role(self, ctx, role_name):

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        member_list = '\n'.join([member.mention for member in role.members])

        return await ctx.send(embed=Embeds.make_embed(header=f"Users with role {role_name}:",content=f"{member_list}"))
