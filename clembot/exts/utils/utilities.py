import asyncio

import discord
from discord.ext import commands


class RemoveComma(commands.Converter):
    async def convert(self, ctx, argument):
        return argument.replace(",", " ").strip()


class HandleAngularBrackets(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.__contains__("<") or argument.__contains__(">"):
            await Utilities._send_error_message(ctx.channel,f"Beep Beep! **{ctx.message.author.display_name}**, **< >** just represents the placeholder. You can provide the values directly!")
        return argument.replace("<", "").replace(">", "").strip()


class Utilities(commands.Cog):
    def __init__(self):
        return

    numbers = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:", "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:"}

    def trim_to(self, text, length, delimiter=","):
        if len(text) == 0:
            return "None"
        if text and delimiter:
            return text[:text.rfind(delimiter, 0, length)] + " ** and more.**" if len(text) > length else text
        return text

    def emojify_numbers(self, number):
        number_emoji = ""

        reverse = "".join(reversed(str(number)))

        for digit in reverse[::-1]:

            emoji = self.numbers.get(digit)
            if not emoji:
                emoji = ":regional_indicator_" + digit.lower() + ":"

            number_emoji = number_emoji + emoji

        return number_emoji


    def _normalize(self, emoji):
        initial_emoji = emoji
        if isinstance(emoji, discord.Reaction):
            emoji = emoji.emoji

        if isinstance(emoji, discord.Emoji):
            emoji = ':%s:%s' % (emoji.name, emoji.id)

        elif isinstance(emoji, discord.PartialEmoji):
            emoji = emoji._as_reaction()
        elif isinstance(emoji, str):
            pass

        if emoji.count(':') == 1 and not emoji.startswith(':'):
            emoji = f":{emoji}"

        if emoji.__contains__(">") and emoji.__contains__("<"):
            emoji = emoji.replace('<','').replace('>','')
        return emoji


    def _demojify(self, emoji):
        # convert emoji to id
        if isinstance(emoji, discord.Reaction):
            emoji = emoji.emoji.id

        if isinstance(emoji, discord.Emoji):
            emoji = emoji.id
        elif isinstance(emoji, discord.PartialEmoji):
            emoji = emoji.id if emoji.id else emoji.name
        elif isinstance(emoji, str):
            pass

        return emoji


    def _emojify(self, emoji):
        if emoji.__contains__(">") and emoji.__contains__("<"):
            emoji = emoji.replace('<', '').replace('>', '')
        return emoji

    @classmethod
    def _uuid(self, id):
        try:
            return '%x' % (hash(id) % 10 ** 8)
        except Exception as error:
            print(error)
            return id

    @classmethod
    async def _send_error_message(self, channel, description, user=None):

        color = discord.Colour.red()
        user_mention = ""
        if user:
            user_mention = f"Beep Beep! **{user.display_name}** "
        error_embed = discord.Embed(description=f"{user_mention}{description}", colour=color)
        return await channel.send(embed=error_embed)

    @classmethod
    async def _send_message(self, channel, description, user= None):

        color = discord.Colour.red()
        user_mention = ""
        if user:
            user_mention = f"Beep Beep! **{user.display_name}** "
        error_embed = discord.Embed(description=f"{user_mention}{description}", colour=color)
        return await channel.send(embed=error_embed)

    async def _send_message(self, channel, description, title=None, footer=None, user=None):
        try:

            error_message = "The output contains more than 2000 characters."

            user_mention = ""
            if user:
                user_mention = f"Beep Beep! **{user.display_name}** "

            if len(description) >= 2000:
                discord.Embed(description="{0}".format(error_message), colour=color)

            color = discord.Colour.green()
            message_embed = discord.Embed(description=f"{user_mention}{description}", colour=color, title=title)
            if footer:
                message_embed.set_footer(text=footer)
            return await channel.send(embed=message_embed)
        except Exception as error:
            print(error)

    @classmethod
    async def _send_embed(self, channel, description=None, title=None, additional_fields={}, footer=None):

        embed = discord.Embed(description=description, colour=discord.Colour.gold(), title=title)

        for label, value in additional_fields.items():
            embed.add_field(name="**{0}**".format(label), value=value, inline=True)

        if footer:
            embed.set_footer(text=footer)

        try:
            return await channel.send(embed=embed)
        except Exception as error:
            return await channel.send(error)

    @commands.command(name="export")
    async def _export(self, ctx):

        return await self._send_message(ctx.channel, "Beep Beep! **{}**, This feature is under-development!".format(ctx.message.author.display_name))

        print("_export() called!")

        raid_dict = ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id]

        channel_mentions = ctx.message.raw_channel_mentions

        if len(channel_mentions) < 1:
            await self._send_error_message(ctx.channel, "Beep Beep! **{}**, Please provide the channel reference to export the details!".format(ctx.message.author.display_name))

    @commands.command(name="clean_content")
    async def _clean_content(self, message):

        message_content = {}
        content_without_mentions = message.content

        for mention in message.mentions:
            mention_text = mention.mention.replace("!", "")
            content_without_mentions = content_without_mentions.replace("<@!", "<@").replace(mention_text, '')

        # remove extra spaces
        message_content['content_without_mentions'] = re.sub(' +', ' ', content_without_mentions)

        return message_content

    @classmethod
    def get_help_embed(self, description, usage, available_value_title, available_values, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed( description="**{0}**".format(description), colour=color)

        help_embed.add_field(name="**Usage :**", value = "**{0}**".format(usage))
        help_embed.add_field(name="**{0} :**".format(available_value_title), value=_("**{0}**".format(", ".join(available_values))), inline=False)

        return help_embed

    @classmethod
    async def _send_error_message_and_cleanup(self, channel, message, user):
        log_message = await self._send_error_message(channel, message, user=user)
        await asyncio.sleep(8)
        await log_message.delete()


    @classmethod
    async def get_image_embed(cls, channel, image_url):
        embed = discord.Embed(colour=channel.guild.me.colour)
        embed.set_thumbnail(url=image_url)
        return await channel.send(embed=embed)

    async def ask_confirmation(self, ctx, message, rusure_message, yes_message, no_message, timed_out_message):
        author = message.author
        channel = message.channel

        reaction_list = ['✅', '❎']
        # reaction_list = ['❔', '✅', '❎']

        rusure = await channel.send( _("Beep Beep! {message}".format(message=rusure_message)))
        await rusure.add_reaction( "✅")  # checkmark
        await rusure.add_reaction( "❎")  # cross

        def check(react, user):
            if user.id != author.id:
                return False
            return True

        # res = await Clembot.wait_for_reaction(reaction_list, message=rusure, check=check, timeout=60)
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout=10)
        except asyncio.TimeoutError:
            await rusure.delete()
            confirmation = await channel.send(_("Beep Beep! {message}".format(message=timed_out_message)))
            await asyncio.sleep(3)
            await confirmation.delete()
            return False

        if reaction.emoji == "❎":
            await rusure.delete()
            confirmation = await channel.send( _("Beep Beep! {message}".format(message=no_message)))
            await asyncio.sleep(3)
            await confirmation.delete()
            return False
        elif reaction.emoji == "✅":
            await rusure.delete()
            confirmation = await channel.send( _("Beep Beep! {message}".format(message=yes_message)))
            await asyncio.sleep(3)
            await confirmation.delete()
            return True




def setup(bot):
    bot.add_cog(Utilities())


def main():
    utilities = Utilities()

    print(utilities._uuid(499981743756148737))
    print(utilities._uuid("499981743756148737"))

    print(utilities._normalize("<:valor:460721754260766721>"))
    print(utilities._normalize("<valor:460721754260766721>"))

# main()
