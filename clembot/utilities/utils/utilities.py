import asyncio
import os
import random
import re
from itertools import cycle

import discord

from clembot.core.bot import command
from clembot.core.errors import wrap_error
from clembot.core.logs import Logger
from clembot.utilities.utils.embeds import Embeds


class TextUtil:

    # Convert an arbitrary string into something which
    # is acceptable as a Discord channel name.
    @staticmethod
    def sanitize(name):
        # Remove all characters other than alphanumerics,
        # dashes, underscores, and spaces
        ret = re.sub(r"[^a-zA-Z0-9 _\-]", "", name)
        # Replace spaces with dashes
        ret = ret.replace(" ", "-")
        return ret

    @staticmethod
    def extract_link_from_text(text: str):
        newloc = None
        mapsindex = text.find("/maps")
        newlocindex = text.rfind("http", 0, mapsindex)

        if newlocindex == -1:
            return newloc
        newlocend = text.find(" ", newlocindex)
        if newlocend == -1:
            newloc = text[newlocindex:]
        else:
            newloc = text[newlocindex:newlocend + 1]

        return newloc


class Utilities:

    numbers = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:", "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:"}

    @staticmethod
    def trim_to(text, length, delimiter=","):
        if len(text) == 0:
            return "None"
        if text and delimiter:
            return text[:text.rfind(delimiter, 0, length)] + " ** and more.**" if len(text) > length else text
        return text

    @staticmethod
    def emojify_numbers(number):
        number_emoji = ""

        reverse = "".join(reversed(str(number)))

        for digit in reverse[::-1]:

            emoji = Utilities.numbers.get(digit)
            if not emoji:
                emoji = ":regional_indicator_" + digit.lower() + ":"

            number_emoji = number_emoji + emoji

        return number_emoji

    @staticmethod
    def _normalize(emoji):
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


    @staticmethod
    def _demojify(emoji):
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

    @staticmethod
    def _emojify(emoji):
        if emoji.__contains__(">") and emoji.__contains__("<"):
            emoji = emoji.replace('<', '').replace('>', '')
        return emoji

    @staticmethod
    def _uuid(cls, id):
        try:
            return '%x' % (hash(id) % 10 ** 8)
        except Exception as error:
            Logger.error(error)
            return id

    @staticmethod
    async def _send_error_message(channel, description, user=None):

        color = discord.Colour.red()
        user_mention = ""
        if user:
            user_mention = f"Beep Beep! **{user.display_name}** "
        error_embed = discord.Embed(description=f"{user_mention}{description}", colour=color)
        return await channel.send(embed=error_embed)

    @staticmethod
    async def message(destination, description, user=None):

        color = discord.Colour.green()
        user_mention = ""
        if user:
            user_mention = f"Beep Beep! **{user.display_name}** "
        error_embed = discord.Embed(description=f"{user_mention}{description}", colour=color)
        return await destination.send(embed=error_embed)

    @staticmethod
    async def message_as_text(channel, description):
        return await channel.send(description)

    @staticmethod
    async def error(channel, description, user=None):

        color = discord.Colour.red()
        user_mention = ""
        if user:
            user_mention = f"Beep Beep! **{user.display_name}** "
        error_message = f"{user_mention}{description}"
        error_embed = discord.Embed(description=f"{error_message}", colour=color)
        Logger.error(error_message)
        return await channel.send(embed=error_embed)

    @staticmethod
    async def _send_message(channel, description, title=None, footer=None, user=None):
        try:

            error_message = "The output contains more than 2000 characters."

            user_mention = ""
            if user:
                user_mention = f"Beep Beep! **{user.display_name}** "

            if len(description) >= 2000:
                discord.Embed(description="{0}".format(error_message))

            color = discord.Colour.green()
            message_embed = discord.Embed(description=f"{user_mention}{description}", colour=color, title=title)
            if footer:
                message_embed.set_footer(text=footer)
            return await channel.send(embed=message_embed)
        except Exception as error:
            Logger.error(error)

    @staticmethod
    async def _send_embed(channel, description=None, title=None, additional_fields={}, footer=None):

        embed = discord.Embed(description=description, colour=discord.Colour.gold(), title=title)

        for label, value in additional_fields.items():
            if value:
                embed.add_field(name="**{0}**".format(label), value=value, inline=False)

        if footer:
            embed.set_footer(text=footer)

        try:
            return await channel.send(embed=embed)
        except Exception as error:
            return await channel.send(error)

    @command(name="export")
    async def _export(self, ctx):

        return await self._send_message(ctx.channel, "Beep Beep! **{}**, This feature is under-development!".format(ctx.message.author.display_name))

        Logger.error("_export() called!")

        raid_dict = ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id]

        channel_mentions = ctx.message.raw_channel_mentions

        if len(channel_mentions) < 1:
            await self._send_error_message(ctx.channel, "Beep Beep! **{}**, Please provide the channel reference to export the details!".format(ctx.message.author.display_name))

    @command(name="clean_content")
    async def _clean_content(self, message):

        message_content = {}
        content_without_mentions = message.content

        for mention in message.mentions:
            mention_text = mention.mention.replace("!", "")
            content_without_mentions = content_without_mentions.replace("<@!", "<@").replace(mention_text, '')

        # remove extra spaces
        message_content['content_without_mentions'] = re.sub(' +', ' ', content_without_mentions)

        return message_content

    @staticmethod
    def get_help_embed(description, usage, available_value_title, available_values, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed( description="**{0}**".format(description), colour=color)

        help_embed.add_field(name="**Usage :**", value = "**{0}**".format(usage))
        help_embed.add_field(name="**{0} :**".format(available_value_title), value=_("**{0}**".format(", ".join(available_values))), inline=False)

        return help_embed

    @staticmethod
    async def _send_error_message_and_cleanup(channel, message, user):
        log_message = await Embeds.error(channel, message, user=user)
        await asyncio.sleep(8)
        await log_message.delete()


    @staticmethod
    async def get_image_embed(channel, image_url):
        embed = discord.Embed(colour=channel.guild.me.colour)
        embed.set_thumbnail(url=image_url)
        return await channel.send(embed=embed)

    @staticmethod
    async def ask(message, destination, user_list=None, *, react_list=['✅', '❎']):
        if user_list and type(user_list) != __builtins__.list:
            user_list = [user_list]


        def check(reaction, user):
            if user_list and type(user_list) is __builtins__.list:
                return (user.id in user_list) and (reaction.message.id == message.id) and (reaction.emoji in react_list)
            elif not user_list:
                return (user.id != message.guild.me.id) and (reaction.message.id == message.id) and (reaction.emoji in react_list)


        for r in react_list:
            await asyncio.sleep(0.25)
            await message.add_reaction(r)
        try:
            reaction, user = await Clembot.wait_for('reaction_add', check=check, timeout=60)
            return reaction, user
        except asyncio.TimeoutError:
            await message.clear_reactions()
            return


    @staticmethod
    @wrap_error
    async def ask_confirmation(ctx, message, rusure_message, yes_message, no_message, timed_out_message):
        author = message.author
        channel = message.channel

        reaction_list = ['✅', '❎']
        # reaction_list = ['❔', '✅', '❎']

        rusure = await ctx.channel.send(f"Beep Beep! {rusure_message}")
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
            confirmation = await channel.send(f"Beep Beep! {timed_out_message}")
            await asyncio.sleep(1)
            await confirmation.delete()
            return False

        if reaction.emoji == "❎":
            await rusure.delete()
            confirmation = await channel.send(f"Beep Beep! {no_message}")
            await asyncio.sleep(1)
            await confirmation.delete()
            return False
        elif reaction.emoji == "✅":
            await rusure.delete()
            confirmation = await channel.send(f"Beep Beep! {yes_message}")
            await asyncio.sleep(1)
            await confirmation.delete()
            return True


    @staticmethod
    @wrap_error
    async def ask_via_reactions(ctx, message, question_message, accepted_message, rejected_message, timed_out_message, reaction_dict, error_response):
        author = message.author
        channel = message.channel

        rusure = await ctx.channel.send(f"{question_message}")

        for r in reaction_dict.keys():
            await rusure.add_reaction(r)

        def check(react, user):
            if user.id != author.id:
                return False
            return True

        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout=10)
        except asyncio.TimeoutError:
            await rusure.delete()
            confirmation = await channel.send(f"{timed_out_message}")
            await asyncio.sleep(1)
            await confirmation.delete()
            return error_response

        if reaction.emoji not in reaction_dict.keys():
            await rusure.delete()
            confirmation = await channel.send(f"{rejected_message}")
            await asyncio.sleep(1)
            await confirmation.delete()
            return error_response

        elif reaction.emoji in reaction_dict.keys():
            await rusure.delete()
            confirmation = await channel.send(f"{accepted_message}")
            await asyncio.sleep(1)
            await confirmation.delete()
            return reaction_dict.get(reaction.emoji, error_response)


    @staticmethod
    async def send_to_hastebin(destination, whatever):
        whatever = whatever.encode('ascii', errors='replace').decode('utf-8')
        print(whatever)


# class SnakeDraft:
#
#     @staticmethod
#     def draft(cls, n, new_i = None):
#         if new_i:
#             i = new_i
#         while True:
#             for i in range(1, n + 1):
#                 yield i
#             for i in range(n, 0, -1):
#                 yield i

def draft(n, new_i = None):
    if new_i:
        i = new_i
    while True:
        for i in range(1, n + 1):
            yield i
        for i in range(n, 0, -1):
            yield i



def draft_next(size_of_team, players_already_drafted, current_player_index):

    direction = 0
    next_index = players_already_drafted % size_of_team
    if (players_already_drafted % (size_of_team * 2)) > size_of_team - 1:
        direction = 1
        next_index = size_of_team - next_index - 1

    Logger.error(f"({size_of_team}, {players_already_drafted}, {current_player_index}) {direction} => {next_index}")

    return next_index


def get_next(team_size):

    all_players = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']



    players = all_players[:team_size]

    turn = draft(players.__len__())

    text = ""

    for i in range(1, players.__len__() * 6 + 1):
        index = next(turn)
        draft_index = draft_next(players.__len__(), i - 1, index - 1)
        Logger.error(f"({i}) \t- {index - 1} => {draft_index} {index - 1 == draft_index}")



    return 1


number_list = [1,2,3,4,5,6,7,8,9,10,11,12,12,11,10,9,8,7,6,5,4,3,2,1]
def slot(n, x): # 0.03638 sec for 100,000x
    return number_list[x % (n*2)]

def test_slot():

    Logger.error(slot(18,46))




def test_shuffle():

    my_list = [1, 2, 3, 4, 5]
    list_copy = list(my_list)
    random.shuffle(list_copy)
    random.shuffle(list_copy)

    Logger.error(my_list)
    Logger.error(list_copy)


class ListIterator:

    _index = -1
    _item_list = []
    __list_size = 0

    def __init__(self, item_list, current_index=-1):
        self._item_list = item_list
        self.__list_size = len(self._item_list)
        self._index = current_index if current_index == -1 else current_index - 1

    def current(self):
        return self._item_list[self._index]

    def next(self):
        self._index += 1
        if self._index >= self.__list_size:
            self._index = 0
        return self._item_list[self._index]

    def prev(self):
        self._index -= 1;
        if self._index < 0:
            self._index = len(self._item_list) - 1
        return self._item_list[self._index]



def test_cycle():

    my_list = [1, 2, 3, 4, 5]
    pool = cycle(my_list)

    for i in range(1, 40):
        print(f"{i} -> {pool.__next__()}")

def test_myclass():

    my_list = [1, 2, 3, 4, 5]
    random.shuffle(my_list)
    print(my_list)
    pool = ListIterator(my_list)

    for i in range(1, 40):
        print(f"{i} -> {pool.next()}")
        if i % 5 == 0:
            print(f"{i} -> {pool.prev()}")


    random.shuffle(my_list)
    print(my_list)
    pool = ListIterator(my_list, 3)

    for i in range(1, 40):
        print(f"{i} -> {pool.next()}")
        if i % 5 == 0:
            print(f"{i} -> {pool.prev()}")



def setup(bot):
    bot.add_cog(Utilities())


def main():
    get_next(3)



if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")
