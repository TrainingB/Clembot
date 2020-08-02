import functools
import textwrap

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from clembot.config import config_template
from clembot.config.constants import Icons
from clembot.core.bot import command, group
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.pagination import Pagination


class Cog(Cog):


    pass

class Core(Cog):
    """General bot functions"""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @command(pass_context=True, hidden=True, name="shutdown", category='Owner')
    # @checks.is_owner()
    async def cmd_shutdown(self, ctx):
        """Shuts the bot down."""
        embed = Embeds.make_embed(title='Shutting down...', msg_color='red', header_icon="https://i.imgur.com/uBYS8DR.png")
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.shutdown()


    @command(pass_context=True, hidden=True, name="restart", category='Owner')
    # @checks.is_owner()
    async def cmd_restart(self, ctx):
        """Restarts the bot"""
        embed = Embeds.make_embed(title='Restarting...', msg_color='red', header_icon="https://i.imgur.com/uBYS8DR.png")
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.shutdown(restart=True)


    @command(name="uptime", category='Bot Info')
    async def cmd_uptime(self, ctx):
        """Shows bot's uptime"""
        uptime_str = ctx.bot.uptime_str
        try:
            await ctx.embed('Uptime', uptime_str, colour='blue', icon=Icons.uptime)
        except discord.errors.Forbidden:
            await ctx.send("Uptime: {}".format(uptime_str))


    @command(name="bot-invite", category='Bot Info')
    async def cmd_bot_invite(self, ctx, plain_url: bool = False):
        """Shows bot's invite url"""
        invite_url = ctx.bot.invite_url
        if plain_url:
            await ctx.send("Invite URL: <{}>".format(invite_url))
            return
        else:
            embed = Embeds.make_embed(
                header="Invite link",
                content=f'[Click to invite me to your server!]({invite_url})',
                title_url=invite_url,
                msg_color='blue',
                header_icon="https://i.imgur.com/DtPWJPG.png")
        try:
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            await ctx.send("Invite URL: <{}>".format(invite_url))


    @command(pass_context=True, hidden=True, aliases=["list-servers"], category='Bot Info')
    # @checks.is_owner()
    async def cmd_list_servers(self, ctx):

        recipient = {}
        recipient_text = ""

        for guild in self.bot.guilds:
            recipient[guild.name] = guild.owner.mention
            recipient_text+= f"\n**{guild.name}** - {guild.owner.mention}"

        await ctx.send(recipient_text)
        return


    @group(pass_context=True, hidden=True, aliases=["about"])
    @wrap_error
    async def cmd_about(self, ctx):
        try:
            # if ctx.invoked_subcommand is not None:
            #     return
            #
            # if len(ctx.message.mentions) > 0:
            #     author = ctx.message.mentions[0]
            #     if author:
            #         await _about_user(author, ctx.message.channel)
            #         return

            """Shows info about Clembot"""
            INVITE_CODE = config_template.invite_code
            original_author_repo = "https://github.com/FoglyOgly"
            original_author_name = "FoglyOgly"

            INVITE_BOT_LINK = f"https://discord.com/oauth2/authorize?client_id={config_template.bot_client_id}&scope=bot&permissions=268822608"

            author_repo = "https://github.com/TrainingB"
            author_name = "TrainingB"
            bot_repo = author_repo + "/Clembot"
            guild_url = "https://discord.gg/{invite}".format(invite=INVITE_CODE)
            owner = self.bot.get_user(self.bot.owner_id)
            channel = ctx.message.channel
            uptime_str = self.bot.uptime_str
            yourguild = ctx.message.guild.name
            yourmembers = len(ctx.message.guild.members)
            embed_colour = ctx.message.guild.me.colour or discord.Colour.lighter_grey()

            member_count = 0
            guild_count = 0
            for guild in self.bot.guilds:
                guild_count += 1
                member_count += len(guild.members)

            embed = Embeds.make_embed(msg_color=discord.Color.blue(),
                                      header_icon=Icons.avatar(self.bot.user),
                                      header="About Clembot")
            embed.add_field(name="**Bot Information**", value="--------------------------------------", inline=False)

            embed.add_field(name="**Owner**", value=owner)
            embed.add_field(name="**Servers**", value=guild_count)
            embed.add_field(name="**Members**", value=member_count)
            embed.add_field(name="**Current Server**", value=yourguild)
            embed.add_field(name="**Your Members**", value=yourmembers)
            embed.add_field(name="**Uptime**", value=uptime_str)

            embed.add_field(name="**Credits**", value="--------------------------------------", inline=False)


            embed.add_field(name="**Inspired (and Forked) from:**", value="Meowth, That's right! - [Meowth by FoglyOgly](https://github.com/FoglyOgly/Meowth)", inline=False)
            embed.add_field(name="**Bingo Cards designed by**", value="@Rogue Beatz#3940, @NPlumb#8841, @CptShuckle#4419", inline=False)
            embed.add_field(name="**(Most) Icons designed using**", value="https://icons8.com/", inline=False)

            embed.add_field(name="**Links**", value="--------------------------------------", inline=False)

            embed.add_field(name="**Contact us**", value=f"[Join guild](https://discord.gg/{INVITE_CODE})", inline=True)
            embed.add_field(name="**Want Clembot?**", value=f"[Invite Clembot]({INVITE_BOT_LINK})", inline=True)
            embed.add_field(name="**:heart: Clembot**", value=f"[Buy me a :coffee:](https://paypal.me/directtob)", inline=True)
            embed.set_footer(text="You can tap 🗑️ to delete this message.")

            try:
                about_msg = await channel.send(embed=embed)
            except discord.HTTPException:
                about_msg = await channel.send("I need the `Embed links` permission to send this")

            await ctx.message.delete()
            await about_msg.add_reaction('🗑️')
        except Exception as error:
            Logger.info(error)

    @command(pass_context=True, hidden=True, aliases=["perms"])
    async def cmd_perms(self, ctx, *, channel_id: int = None):

        channel = ctx.bot.get(ctx.bot.get_all_channels(), id=channel_id)
        guild = channel.guild if channel else ctx.guild
        channel = channel or ctx.channel

        guild.audit_logs

        guild_perms = guild.me.guild_permissions
        channel_perms = channel.permissions_for(guild.me)
        req_perms = ctx.bot.req_perms

        embed = discord.Embed(title="Bot Permissions")
        wrap = functools.partial(textwrap.wrap, width=20)
        names = [wrap(channel.name), wrap(guild.name)]
        if channel.category:
            names.append(wrap(channel.category.name))
        name_len = max(len(n) for n in names)

        def same_len(text):
            return '\n'.join(text + ([' '] * (name_len-len(text))))

        names = [same_len(n) for n in names]
        channel_msg = [f"**{names[0]}** \n {channel.id} \n"]
        guild_msg = [f"**{names[1]}** \n {guild.id} \n"]

        def perms_result(perms):
            data = []
            meet_req = perms >= req_perms
            result = "**PASS**" if meet_req else "**FAIL**"
            data.append(f"{result} - {perms.value} \n")
            true_perms = [k for k, v in dict(perms).items() if v is True]
            false_perms = [k for k, v in dict(perms).items() if v is False]
            req_perms_list = [k for k, v in dict(req_perms).items() if v is True]
            true_perms_str = '\n'.join(true_perms)
            if not meet_req:
                missing = '\n'.join([p for p in false_perms if p in req_perms_list])
                data.append(f"**MISSING** \n{missing} \n")
            if true_perms_str:
                data.append(f"**ENABLED** \n{true_perms_str} \n")
            return '\n'.join(data)

        guild_msg.append(perms_result(guild_perms))
        channel_msg.append(perms_result(channel_perms))
        embed.add_field(name='GUILD', value="\n".join(guild_msg))
        if channel.category:
            cat_perms = channel.category.permissions_for(guild.me)
            cat_msg = [f"**{names[2]}** \n{channel.category.id} \n"]
            cat_msg.append(perms_result(cat_perms))
            embed.add_field(name='CATEGORY', value='\n'.join(cat_msg))
        embed.add_field(name='CHANNEL', value="\n".join(channel_msg))

        try:
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            # didn't have permissions to send a message with an embed
            try:
                msg = "I couldn't send an embed here, so I've sent you a DM"
                await ctx.send(msg)
            except discord.errors.Forbidden:
                # didn't have permissions to send a message at all
                pass
            await ctx.author.send(embed=embed)


    @command(pass_context=True, hidden=True)
    # @checks.is_owner()
    async def mysetup(ctx):
        text=[]
        current_guild = ctx.message.guild

        user = ctx.message.guild.me

        for permission in user.guild_permissions:
            if permission[1]:
                text.append("{permission}".format(permission=permission[0]) )

        raid_embed = discord.Embed(colour=discord.Colour.gold())
        raid_embed.add_field(name="**Username:**", value=_("{option}").format(option=user.name))
        raid_embed.add_field(name="**Roles:**", value=_("{roles}").format(roles=" \ ".join(text)))
        raid_embed.set_thumbnail(url=_("https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.{format}".format(user=user, format="jpg")))
        await ctx.send(embed=raid_embed)

    @cmd_about.command(pass_context=True)
    async def me(self, ctx):
        author = ctx.message.author

        await self._about_user(author, ctx.message.channel)


    async def _about_user(self, user, target_channel):
        text = []
        for role in user.roles:
            text.append(role.name)
        roles_text = ' \ '.join(text)
        raid_embed = discord.Embed(colour=discord.Colour.gold())
        raid_embed.add_field(name="**Username:**", value=f"{user.name}")
        raid_embed.add_field(name="**Roles:**", value=f"{roles_text}")
        raid_embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.jpg")
        await target_channel.send(embed=raid_embed)


    @command(pass_context=True, hidden=True, aliases=["about-me"])
    async def _about_me(self, ctx):
        author = ctx.message.author

        await self._about_user(author, ctx.message.channel)

    @command(name='help', category='Bot Info')
    async def _help(self, ctx, *, command_name: str = None):
        """Shows help on available commands."""
        try:
            if command_name is None:
                p = await Pagination.from_bot(ctx)
            else:
                entity = (#self.bot.get_category(command_name) or
                          self.bot.get_cog(command_name) or
                          self.bot.get_command(command_name))
                if entity is None:
                    clean = command_name.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await Pagination.from_command(ctx, entity)
                elif isinstance(entity, str):
                    p = await Pagination.from_category(ctx, entity)
                else:
                    p = await Pagination.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Core(bot))
