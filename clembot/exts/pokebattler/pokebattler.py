import json

import discord
import requests

from clembot.config import config_template
from clembot.core.logs import Logger



class PokeBattler:

    PB_CREATE_RAID_PARTY_URL = "https://fight.pokebattler.com/secure/raidParties"

    PB_ADD_DISCORD_USER_RAID_PARTY_URL = "https://fight.pokebattler.com/secure/raidParties/:pbraidpartyid:/users"

    HEADERS = {
        'X-Authorization': f'Bearer: {config_template.pokebattler_api_key}',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'application/json',
        'Accept': 'application/json',
    }



    @staticmethod
    def pb_raid_level(level):
        level_map = {
            '1' : 'RAID_LEVEL_1',
            '2': 'RAID_LEVEL_2',
            '3': 'RAID_LEVEL_3',
            '4': 'RAID_LEVEL_4',
            '5': 'RAID_LEVEL_5',
            'M': 'RAID_LEVEL_MEGA',
            'E': 'RAID_LEVEL_EX',
        }

        return level_map.get(level, 'UNRECOGNIZED')




    @staticmethod
    def create_raid_party(raid_boss, raid_level):

        # create_payload = {
        #     "defender": "HEATRAN",
        #     "tier": "RAID_LEVEL_5"
        # }

        create_payload = {
            "defender": raid_boss,
            "tier": PokeBattler.pb_raid_level(raid_level)
        }


        response = requests.request("POST", PokeBattler.PB_CREATE_RAID_PARTY_URL, headers=PokeBattler.HEADERS, data=json.dumps(create_payload) )

        pb_raid_party = response.json()
        pb_raid_party_id = pb_raid_party['id']
        Logger.info(f"({raid_boss}, {raid_level}) : {pb_raid_party_id}")
        return pb_raid_party_id


    @staticmethod
    def get_raid_party_url(pb_raid_party_id):

        raid_party_url = f"http://www.pokebattler.com/raidParty/{pb_raid_party_id}"

        return raid_party_url


    @staticmethod
    def add_user_to_raid_party(raid_party_id, member: discord.Member):
        pb_raid_party_id = raid_party_id
        url = f"https://fight.pokebattler.com/secure/raidParties/{pb_raid_party_id}/users"

        # add_payload = {
        #     "user": {
        #         "discordName": f"tinyturtle#2230"
        #     }
        # }
        # # "celandro#5137"
        # response = requests.request("POST", url, headers=PokeBattler.HEADERS, data=json.dumps(add_payload) )
        # pb_add_user_response = response.json()
        # pb_raid_party_user_id = pb_add_user_response['id']
        # Logger.info(f"({raid_party_id}, {member.name}#{member.discriminator}) : {pb_raid_party_user_id}")

        add_payload = {
            "user": {
                "discordName": f"{member.name}#{member.discriminator}"
            }
        }

        response = requests.request("POST", url, headers=PokeBattler.HEADERS, data=json.dumps(add_payload) )

        pb_add_user_response = response.json()
        pb_raid_party_user_id = pb_add_user_response['id']
        Logger.info(f"({raid_party_id}, {member.name}#{member.discriminator}) : {pb_raid_party_user_id}")

        return pb_raid_party_user_id



