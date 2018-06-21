import re
import discord
import time_util
from discord.ext import commands
from exts.utilities import Utilities


import json

class ProfileManager:

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict
        self.utilities = Utilities()

    @commands.group(pass_context=True, hidden=True)
    async def profile(self, ctx):
        # , user: discord.Member = None
        user = None

        print(ctx.invoked_subcommand)

        if ctx.invoked_subcommand is None:

            if not user:
                user = ctx.message.author
            silph = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {}).get('silphid', None)
            if silph:
                silph = f"[Traveler Card](https://sil.ph/{silph.lower()})"
            embed = discord.Embed(title=f"{user.display_name}\'s Trainer Profile", colour=user.colour)
            embed.set_thumbnail(url=user.avatar_url)

            trainer_code = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id,{}).get('trainer_code','')
            if trainer_code:
                embed.add_field(name="**Trainer Code**", value=f"**{trainer_code.upper()}**", inline=False)
            else:
                embed.add_field(name="**Trainer Code**", value="Set with **!profile trainer-code**", inline=False)

            trainer_profile = ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id, {})

            embed.add_field(name="**Silph Road**", value=f"{silph}", inline=True)
            embed.add_field(name="**Pokebattler Id**", value=f"{ctx.bot.guild_dict[ctx.guild.id]['trainers'].setdefault(user.id,{}).get('pokebattlerid',None)}", inline=True)


            leaderboard_list = ['lifetime']
            # addtional_leaderboard = get_guild_local_leaderboard(ctx.guild.id)
            # if addtional_leaderboard:
            #     leaderboard_list.append(addtional_leaderboard)

            for leaderboard in leaderboard_list:
                reports_text = "**Raids : {} | Eggs : {} | Wilds : {} | Research : {}**".format(trainer_profile.setdefault(leaderboard, {}).get('raid_reports', 0), trainer_profile.setdefault(leaderboard, {}).get('egg_reports', 0), trainer_profile.setdefault(leaderboard, {}).get('wild_reports', 0), trainer_profile.setdefault(leaderboard, {}).get('research_reports', 0))

                embed.add_field(name="**Leaderboard ({}) :**".format(leaderboard.capitalize()), value=f"{reports_text}", inline=True)

            await ctx.send(embed=embed)



    @profile.command(aliases=["pokebattler","pb"])
    async def _pokebattler(self, ctx, pbid: int = 0):
        if not pbid:
            await self.utilities._send_message(ctx, _(f'Beep Beep! **{ctx.message.author.display_name}**, Pokebattler ID has been cleared.'))
            try:
                del ctx.bot.guild_dict[ctx.guild.id]['trainers'][ctx.author.id]['pokebattlerid']
            except:
                pass
            return
        trainers = ctx.bot.guild_dict[ctx.guild.id].get('trainers', {})
        author = trainers.get(ctx.author.id, {})
        author['pokebattlerid'] = pbid
        trainers[ctx.author.id] = author
        ctx.bot.guild_dict[ctx.guild.id]['trainers'] = trainers

        await self.utilities._send_message(ctx, (_(f'Beep Beep! **{ctx.message.author.display_name}** Pokebattler ID set to {pbid}!')))

    @profile.command(aliases=["trainer-code","code"])
    async def _trainer_code(self, ctx, trainer_code = None):
        if not trainer_code:
            await self.utilities._send_message(ctx, _(f'Beep Beep! **{ctx.message.author.display_name}**, Trainer code has been cleared.'))
            try:
                del ctx.bot.guild_dict[ctx.guild.id]['trainers'][ctx.author.id]['trainer_code']
            except:
                pass
            return
        trainers = ctx.bot.guild_dict[ctx.guild.id].get('trainers', {})
        author = trainers.get(ctx.author.id, {})
        author['trainer_code'] = trainer_code
        trainers[ctx.author.id] = author
        ctx.bot.guild_dict[ctx.guild.id]['trainers'] = trainers

        await self.utilities._send_message(ctx, (_(f'Beep Beep! **{ctx.message.author.display_name}** your trainer code is set to **{trainer_code}**!')))

    @profile.command(aliases=["silph"])
    async def _silph(self, ctx, silph_user: str = None):
        """Links a server member to a Silph Road Travelers Card."""
        try:
            if not silph_user:
                await ctx.send(_('Silph Road Travelers Card cleared!'))
                try:
                    del ctx.bot.guild_dict[ctx.guild.id]['trainers'][ctx.author.id]['silphid']
                except:
                    pass
                return

            silph_cog = ctx.bot.cogs.get('Silph')
            if not silph_cog:
                return await ctx.send(_("The Silph Extension isn't accessible at the moment, sorry!"))

            async with ctx.typing():
                card = await silph_cog.get_silph_card(silph_user)
                if not card:
                    return await ctx.send(_('Silph Card for {silph_user} not found.').format(silph_user=silph_user))

            if not card.discord_name:
                return await ctx.send(_('No Discord account found linked to this Travelers Card!'))

            if card.discord_name != str(ctx.author):
                return await ctx.send(_('This Travelers Card is linked to another Discord account!'))

            try:
                offset = ctx.bot.guild_dict[ctx.guild.id]['configure_dict']['settings']['offset']
            except KeyError:
                offset = None

            trainers = ctx.bot.guild_dict[ctx.guild.id].get('trainers', {})
            author = trainers.get(ctx.author.id, {})
            author['silphid'] = silph_user
            trainers[ctx.author.id] = author
            ctx.bot.guild_dict[ctx.guild.id]['trainers'] = trainers

            await ctx.send(_('This Travelers Card has been successfully linked to you!'), embed=card.embed(offset))
        except Exception as error:
            print(error)
    # @commands.command(pass_context=True, hidden=True, aliases=["code"])
    # async def _code(self, ctx):
    #     await self._send_message(ctx.channel, "code has been called.")


    async def _send_error_message(self, channel, description):

        color = discord.Colour.red()
        error_embed = discord.Embed(description="{0}".format(description), colour=color)
        return await channel.send(embed=error_embed)



    beep_notes = ("""**{member}** here are the commands for Profile management. 

**!profile silph <traveler-card-id>** - to set silph card username in your profile.
**!profile pokebattler <pokebattler-id>** - to set pokebattler id in your profile.
**!profile trainer-code <code>** - to set the Pokemon Go trainer code in your profile.

**!profile** - brings up your profile.

""")

    def get_beep_embed(self, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - Profile Management", description=self.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


def setup(bot):
    bot.add_cog(ProfileManager(bot))


