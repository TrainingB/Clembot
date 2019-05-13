import discord
from discord.ext import commands


class LeaderBoard:


    filters = {}

    def __init__(self):
        pass

    def add_filter(self):

        new_filter = {}

        new_filter['level'] = []

        new_filter['channel'] = []


class LeaderBoardManager(commands.Cog):


    lifetime = LeaderBoard()

    def __init__(self, bot):
        self.bot = bot
        self.guild_dict = bot.guild_dict


    async def _send_error_message(self, channel, description):

        color = discord.Colour.red()
        error_embed = discord.Embed(description="{0}".format(description), colour=color)
        return await channel.send(embed=error_embed)

    async def _send_message(self, channel, description):
        try:

            error_message = "The output contains more than 2000 characters."
            if len(description) >= 2000:
                discord.Embed(description="{0}".format(error_message), colour=color)

            color = discord.Colour.green()
            message_embed = discord.Embed(title="Notes",   description="{0}".format(description), colour=color)

            return await channel.send(embed=message_embed)
        except Exception as error:
            print(error)


    # !notes

    # !list notes
    # !notes new-note
    # !notes clear
    # !add-notes
    # !

    @commands.group(pass_context=True, hidden=True, aliases=["notes"])
    async def _notes(self, ctx):
        if ctx.invoked_subcommand is None:

            print("_notes called()")

            raid_channel_notes = ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id].get('notes', [])

            if len(raid_channel_notes) < 1:
                return await self._send_error_message(ctx.channel, "Beep Beep! **{}** No note(s) found. Please use **!notes add <note>** to add a new note.".format(ctx.message.author.display_name))

            await self._send_message(ctx.channel, "🔰" + "\n🔰".join(raid_channel_notes))

            return



    @_notes.command(aliases=["add"])
    async def _add_notes(self, ctx):
        print("_notes add called()")

        guild_data = ctx.bot.guild_dict[ctx.guild.id]

        args = ctx.message.content.split()[2:]

        if len(args) == 0:
            await self._send_error_message(ctx.channel, "Beep Beep! **{}** No note provided to add.".format(ctx.message.author.display_name))

        ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id].setdefault('notes',[]).append(" ".join(args))

        raid_channel_notes = ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id].get('notes', [])

        await self._send_message(ctx.channel, "🔰"+"\n🔰".join(raid_channel_notes))




        return

    @_notes.command(aliases=["clear"])
    async def _clear_notes(self, ctx):
        print("_notes clear called()")

        ctx.bot.guild_dict[ctx.guild.id]['raidchannel_dict'][ctx.channel.id]['notes']=[]

        return await self._send_message(ctx.channel, "Beep Beep! **{}** All note(s) have been cleared.".format(ctx.message.author.display_name))

    beep_notes = ("""**{member}** here are the commands for notes management. 

**!notes ** - to list all the notes from a channel.
**!notes add <note>** - to add a note to the current channel.
**!notes clear** - to clear the note(s) for the current channel.

""")

    def get_beep_embed(self, title, description, usage=None, available_value_title=None, available_values=None, footer=None, mode="message"):

        if mode == "message":
            color = discord.Colour.green()
        else:
            color = discord.Colour.red()

        help_embed = discord.Embed(title=title, description=f"{description}", colour=color)

        # help_embed.add_field(name="**Usage :**", value = "**{0}**".format(usage))
        # help_embed.add_field(name="**{0} :**".format(available_value_title), value=_("**{0}**".format(", ".join(available_values))), inline=False)
        help_embed.set_footer(text=footer)
        return help_embed

    @classmethod
    async def _help(self, ctx):
        footer = "Tip: < > denotes required and [ ] denotes optional arguments."
        await ctx.message.channel.send(embed=self.get_beep_embed(self, title="Help - Note(s) Management", description=self.beep_notes.format(member=ctx.message.author.display_name), footer=footer))


def setup(bot):
    bot.add_cog(PropertiesHandler(bot))





#
# def parse_test(text, format, options_method={}):
#     response = parse_arguments(text, format, options_method)
#     print("{text} = {response}\n".format(text=text, response=response))
#
#     return response
#
#     # print(response.get('others',None))
#
# def test():
#     parse_test("!raidegg 7 clco 3", ['command', 'egg', 'gym_info', 'timer', 'location'])
#
#     parse_test("!raidegg 5 clco 2", ['command', 'egg', 'gym_info', 'timer', 'location'])
#
#
#     parse_test("!add groudon clco 2:45pm", ['command', 'pokemon', 'gym_info', 'eta'], {'pokemon' : pokemon_validator_mock, 'eta' : time_util.convert_into_time})
#
#     parse_test("!raid groudon", ['command', 'pokemon', 'gym_info', 'timer', 'location'], {'pokemon': pokemon_validator_mock})
#
#     parse_test("!raid gkroudon art mural 2 23", ['command', 'pokemon', 'gym_info', 'timer', 'location'], {'pokemon' : pokemon_validator_mock})
#
#     parse_test("!c 2 groudon kyogre", ['command', 'pokemon', 'gym_info', 'partysize', 'location'])
#
#     parse_test("!raidegg 6 clco 5", ['command', 'egg', 'gym_info', 'timer', 'location'])
#
#     parse_test("!raid groudon clco 23", ['command', 'pokemon', 'gym_info', 'timer', 'location'])
#
#     parse_test("!c 6 m2 v3 groudon kyogre", ['command', 'pokemon', 'gym_info', 'partysize', 'location'])
#
#
#     parse_test("!update 3 groudon clco 3:00pm", ['command', 'index' ,'pokemon', 'gym_info', 'eta'])
#
#     parse_test("!update 3 groudon", ['command', 'index' ,'pokemon', 'gym_info', 'eta'], {'pokemon' : pokemon_validator_mock, 'eta' : eta_validator_mock})
#
#
# def test1():
#     parse_test("!raidegg 1 clco 0", ['command', 'egg', 'gym_info', 'timer', 'location'])
#
#     parse_test("!raid assume groudon", ['command', 'subcommand', 'pokemon'])
#
#
#
#
#
# def test2():
#     parameters = parse_test("!raidegg 5 gewa43 38", ['command', 'egg', 'gym_info', 'timer', 'location'],{'pokemon' : pokemon_validator_mock, 'link' : extract_link_from_text })
#     print(" ".join(str(x) for x in parameters.get('others')))
#
#     parse_test("!nest Squirtle Tonga Park ( some city ) https://goo.gl/maps/suEo9zDBCCP2", ['command','pokemon','link'])
#
#     parse_test("!exraid mesc", ['command', 'gym_info'])
#
#
# # ---------------uncomment this line to test stand alone-------------------------
#
# def test3():
#
#     if re.match(r'@(.*)\#\d{4}', '@G. (๑˃̵ᴗ˂̵)و-☆z#3529'):
#         print('matched')
#
#     print(re.match(r'@(.*)\#\d{4}', '@G. (๑˃̵ᴗ˂̵)و-☆z#3529'))
#     parse_test("!raidegg 5 600 Corp Pointe 13", ['command', 'egg', 'pokemon' , 'gym_info', 'timer', 'location' , 'link'])
#
#     parse_test("!c 3 @Bronzor#0409 2 @MEE6#4876 where are you", ['command', 'count', 'mentions'])
#
#     parse_test("!c", ['command', 'count'] )
#
#     parse_test("!c 5", ['command', 'count'] )
#
#     parse_test("!c @G. (๑˃̵ᴗ˂̵)و-☆z#3529  @B!#2022 4 @Bronzor#0409 @MEE6#4876", ['command', 'count', 'mentions'] )
#
#
#
# def main():
#     try:
#         test3()
#         print("main() finished")
#     except Exception as error:
#         print(error)
#     return
#
# main()