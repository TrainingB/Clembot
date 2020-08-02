import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.core.bot import group, command
from clembot.core.errors import wrap_error
from clembot.exts.profile.user_profile import UserProfile
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class ProfileCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utilities = Utilities()

    async def find_user_profile(self, ctx, member=None):

        if member:
            user = member
        elif len(ctx.message.mentions) > 0:
            user = ctx.message.mentions[0]
        else:
            user = ctx.get.member(ctx.subcommand_passed) or ctx.message.author

        user_profile = await UserProfile.find(self.bot, user.id)
        return user_profile



    @group(pass_context=True, aliases=["profile"])
    async def cmd_profile(self, ctx):
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                user_profile = await self.find_user_profile(ctx)
                return await ctx.send(embed=user_profile.embed(ctx))
            raise BadArgument(f"Valid options are: `trainer-code, ign, pokebattler, silph`")


    @cmd_profile.command(pass_context=True, aliases=["tc", "trainer-code"],
                         examples=["!profile trainer-code *0000-0000-0000*","!profile trainer-code clear"])
    @wrap_error
    async def cmd_profile_trainer_code(self, ctx, code):
        user_profile = await self.find_user_profile(ctx)


        if code == 'clear':
            user_profile['trainer_code'] = []
        else:
            user_profile['trainer_code'] = code

        await user_profile.update()
        await ctx.send(embed=user_profile.embed(ctx))



    @cmd_profile.command(pass_context=True, aliases=["ign"])
    @wrap_error
    async def cmd_profile_ign(self, ctx, ign):
        user_profile = await self.find_user_profile(ctx)

        if ign == 'clear':
            user_profile['ign'] = []
        else:
            user_profile['ign'] = ign
        await user_profile.update()

        await ctx.send(embed=user_profile.embed(ctx))


    @cmd_profile.command(pass_context=True, aliases=["pokebattler", "pb"])
    async def cmd_profile_pokebattler(self, ctx, pokebattler_id):
        user_profile = await self.find_user_profile(ctx)

        if pokebattler_id == 'clear':
            user_profile['pokebattler_id'] = pokebattler_id
        else:
            user_profile['pokebattler_id'] = None
        await user_profile.update()

        await ctx.send(embed=user_profile.embed(ctx))


    @cmd_profile.command(pass_context=True, aliases=["silph"])
    @wrap_error
    async def cmd_profile_silph(self, ctx, silph_user: str):
        """Links a server member to a Silph Road Travelers Card."""
        user_profile = await self.find_user_profile(ctx)

        if silph_user:
            if silph_user == 'clear':
                user_profile['silph_id'] = None
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
            await user_profile.update()

        await ctx.send(embed=card.embed(0))



    @command(pass_context=True, aliases=["tc","trainer-code"])
    async def cmd_trainer_code(self, ctx, member: discord.Member=None):
        user_profile = await self.find_user_profile(ctx, member)

        if user_profile['trainer_code']:
            for code in user_profile.trainer_code:
                await ctx.send(f"`{code}`")
            return
        else:
            return await Embeds.error(ctx.channel, f"I don't have a trainer-code for <@{user_profile.user_id}> on the record.")


    @command(aliases=["whois", "who-is"])
    async def cmd_who_is(self, ctx, ign=None):

        user_profile = await UserProfile.find_by_ign(self.bot, ign)

        if user_profile:
            return await ctx.send(embed=user_profile.embed(ctx, show_help=False))

        await Embeds.error(ctx.channel, f"I didn't find any match for IGN **{ign}**!", user=ctx.author)



    @command(pass_context=True, hicdden=True, aliases=["in-role"])
    async def cmd_in_role(self, ctx, role_name):

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        member_list = '\n'.join([member.mention for member in role.members])

        return await ctx.send(embed=Embeds.make_embed(header=f"Users with role {role_name}:",content=f"{member_list}"))
