import json

import requests

from clembot.config import config_template
from clembot.config.constants import MyEmojis
from clembot.core import checks, commands
from clembot.core.bot import group, command
from clembot.core.commands import Cog
from clembot.exts.pokebattler.pokebattler import PokeBattler
from clembot.exts.raid.raid import Raid
from clembot.exts.trade.pokemonform import PokemonForm
from clembot.utilities.utils.embeds import Embeds


class PokeBattlerCog(commands.Cog):

    PB_CREATE_RAID_PARTY_URL = "https://fight.pokebattler.com/secure/raidParties"

    PB_ADD_DISCORD_USER_RAID_PARTY_URL = "https://fight.pokebattler.com/secure/raidParties/:pbraidpartyid:/users"

    HEADERS = {
        'X-Authorization': f'Bearer: {config_template.pokebattler_api_key}',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'application/json',
        'Accept': 'application/json',
    }


    def __init__(self, bot):
        self.bot = bot
        self.dbi = bot.dbi


    @group(pass_context=True, hidden=True, aliases=["pbraidparty"])
    async def cmd_pb(self, ctx, raid_party_id, *, json_text=None):
        print(ctx.message)

        # if json_text is not None:
        #     data = json.loads(json_text)
           # await Embeds.message(ctx.channel, f"Oooh! I see an update for #{raid_party_id} \n {json.dumps(data, indent=2)}")

        if len(ctx.message.embeds) > 0:
            embed = ctx.message.embeds[0]

            raid = Raid.by_poke_battler_id.get(int(raid_party_id), None)

            if raid is not None:
                pokebattler_message = await raid.channel.send(embed=embed)


                # await ctx.send(embed=embed)

