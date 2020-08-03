import asyncio
import json

import discord
from discord.ext import commands
from discord.ext.commands import BadArgument

from clembot.core.bot import group
from clembot.core.logs import Logger
from clembot.exts.config.channelconfigmanager import ChannelConfigCache
from clembot.exts.gymmanager.gym import Gym, GymRepository
from clembot.utilities.utils import pagination
from clembot.utilities.utils.embeds import Embeds
from clembot.utilities.utils.utilities import Utilities


class GymManagerCog(commands.Cog):
    """
    Loads Gym Manager Code
    """

    def __init__(self, bot):
        self._bot = bot
        self._dbi = bot.dbi
        self.utilities = Utilities()
        self.CityManager = ChannelConfigCache(bot.dbi, bot)
        self.gymRepository = GymRepository(self._dbi)

    @group(pass_context=True, hidden=True, aliases=["gym"])
    async def _command_gym(self, ctx):
        try:
            if ctx.invoked_subcommand is None:
                if ctx.subcommand_passed is None:
                    return await Embeds.error(ctx.channel,
                                              f"**{ctx.invoked_with}** can be used with various options.",
                                              user=ctx.message.author)

                city_state = ctx.message.content.split()[2] if len(ctx.message.content.split()) > 2 else None

                return await self.send_gym_embed(ctx, ctx.subcommand_passed, city_state)
        except Exception as error:
            Logger.error(error)


    @_command_gym.command(pass_context=True, hidden=True, aliases=["find"])
    async def _command_gym_find(self, ctx, gym_code, city=None):
        return await self.send_gym_embed(ctx, gym_code, city)


    @_command_gym.group(pass_context=True, hidden=True, aliases=["update"])
    # @checks.is_guild_owner()
    async def _command_gym_update(self, ctx, gym_id: int, attribute, value):

        gym = await self.gymRepository.to_gym_by_id(gym_id)

        if gym is None:
            return await Embeds.error(ctx.channel, f"No gym found by id: **{gym_id}.", user=ctx.message.author)

        if attribute not in Gym.attributes:
            return await Embeds.error(ctx.channel, f"Only following attributes can be updated : `{Gym.attributes}`.",
                                      user=ctx.message.author)

        await self.gymRepository.update(gym_id, attribute, value)

        updated_gym = await self.gymRepository.to_gym_by_id(gym_id)

        message_text = f"Gym **{updated_gym.gym_name} [{updated_gym.gym_code}]** has been updated successfully."
        await Embeds.message(ctx.message.channel, message_text, user=ctx.message.author, footer=updated_gym.summary)


    @_command_gym.command(pass_context=True, hidden=True, aliases=["add"])
    # @checks.is_guild_owner()
    async def _command_gym_add(self, ctx, *, raw_gym_list=None):
        Logger.info("_gym_add()")
        try:
            if raw_gym_list is None:
                return await Embeds.message(ctx.message.channel,
                                            f"Beep Beep! **{ctx.message.author.display_name}**, please provide gym information is following format. \n```!gym add \n{json.dumps(Gym.default_dict, indent=1)}```\n You can use https://www.csvjson.com/csv2json to convert CSV to JSON.")
            gym_list = json.loads(raw_gym_list)

            for gym_dict in gym_list:

                gym = self.gymRepository.construct_gym(**gym_dict)

                existing_gym = await self.gymRepository.to_gym_by_code_city(gym.gym_code, gym.city_state)

                if existing_gym:
                    message_text = f"Gym **{existing_gym.gym_name}** already exists for **{existing_gym.city_state}**."
                    await Embeds.error(ctx.message.channel, message_text, user=ctx.message.author)
                else:
                    await self.gymRepository.insert(**gym.to_db_dict())
                    new_gym = await self.gymRepository.to_gym_by_code_city(gym.gym_code, gym.city_state)

                    message_text = f"Gym **{new_gym.gym_name} [{new_gym.gym_code}]** has been added successfully for **{new_gym.city_state}**."
                    await Embeds.message(ctx.message.channel, message_text, user=ctx.message.author,
                                         footer=new_gym.summary)

        except Exception as error:
            Logger.error(error)
            await Embeds.error(ctx.message.channel, error)
        else:
            await asyncio.sleep(15)
            await ctx.message.delete()

        return

    async def send_gym_embed(self, ctx, gym_code, city=None):

        city = await ctx.city()

        gym = await self.gymRepository.to_gym_by_code_city(gym_code, city)

        if gym:
            return await GymManagerCog._generate_gym_embed(ctx.message, gym)
        else:
            await Embeds.error(ctx.message.channel,
                               f"I could not find any gyms with gym-code **{gym_code}** in **{city}**.\nPlease use **!gym list word** to see the list of gyms.",
                               user=ctx.message.author)

    @staticmethod
    async def _generate_gym_embed(message, gym: Gym):

        embed_title = f"Click here for direction to {gym.gym_name}!"
        embed_description = f"**Gym Code :** {gym.gym_code}\n**Gym Name :** {gym.gym_display_name}\n**City :** {gym.gym_city}"

        gym_embed = discord.Embed(title=f"Beep Beep! {embed_title}", url=gym['gym_url'],
                                  description=embed_description, color=message.guild.me.color)

        gym_embed.set_footer(text=gym.summary)
        gym_embed.set_image(url=Embeds.google_location_preview_url(f"{gym.latitude},{gym.longitude}"))

        if gym['gym_image']:
            gym_embed.set_thumbnail(url=gym['gym_image'])
        roster_message = "here are the gym details! "

        await message.channel.send(content=f"Beep Beep! {message.author.mention} {roster_message}", embed=gym_embed)




    @group(pass_context=True, hidden=True, aliases=["gyms"])
    async def _command_gyms(self, ctx, gym_code_or_name=None, city=None):
        city = city or await ctx.city()

        if gym_code_or_name is None or len(gym_code_or_name) < 1:
            raise BadArgument("I need at-least one character for lookup!")


        await self._gyms(ctx, ctx.message, gym_code_or_name, city)


    async def _gyms(self, ctx, message, gym_code_or_name = None, city_state=None):

        gym_code_or_name = gym_code_or_name.upper() if gym_code_or_name is not None else gym_code_or_name

        try:

            if not city_state:
                return await Embeds.error(message.channel, "this channel doesn't have a city assigned. Please contact an admin to assign a city.", user=message.author)

            list_of_gyms = await self.gymRepository.to_gym_list(gym_code_or_name, city_state)

            if len(list_of_gyms) < 1:
                return await Embeds.error (message.channel, f"I could not find any gym starting with **{gym_code_or_name}** for **{city_state}**!", user=message.author)

            gym_message_output = f"Here is a list of gyms for **{city_state}** :\n\n"

            list_of_gym_names = []

            for gym in list_of_gyms:
                list_of_gym_names.append(f"**{gym.gym_code.ljust(6)}** - {gym.gym_name}")

            p = pagination.TextPagination(ctx, list_of_gym_names, per_page=25, title="Gym information", embed_header=gym_message_output, plain_text=True)
            await p.paginate()

        except Exception as error:
            Logger.error(error)
            await Embeds.error(message.channel, f"No matches found for **{gym_code_or_name}** in **{city_state}**! **Tip:** Use first two letters of the gym-name to search.", user=message.author)



