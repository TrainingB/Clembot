import json

import discord
import requests

from clembot.config import config_template
from clembot.core.logs import Logger



class PokeBattler:

    PB_CREATE_RAID_PARTY_URL = "https://fight.pokebattler.com/secure/raidParties"

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
    def create_raid_party(raid_level, raid_boss):
        Logger.info(f"create_raid_party({raid_level},{raid_boss})")
        try:
            create_payload = {
                "tier": PokeBattler.pb_raid_level(raid_level)
            }

            if raid_boss:
                create_payload['defender'] = raid_boss


            response = requests.request("POST", PokeBattler.PB_CREATE_RAID_PARTY_URL, headers=PokeBattler.HEADERS, data=json.dumps(create_payload) )

            pb_raid_party = response.json()
            pb_raid_party_id = pb_raid_party['id']
            Logger.info(f"({raid_boss}, {raid_level}) : {pb_raid_party_id}")
            return pb_raid_party_id
        except Exception as error:
            return None


    @staticmethod
    def update_raid_party(pb_raid_id, raid_level, raid_boss):
        Logger.info(f"update_raid_party({pb_raid_id},{raid_boss})")
        try:
            update_payload = {
                "defender": raid_boss,
                "tier" : raid_level
            }

            raid_party_url = f"https://fight.pokebattler.com/secure/raidParties/{pb_raid_id}"

            response = requests.request("POST", raid_party_url, headers=PokeBattler.HEADERS, data=json.dumps(update_payload) )

            pb_raid_party = response.json()
            pb_raid_party_id = pb_raid_party['id']
            return pb_raid_party_id
        except Exception as error:
            return None

    @staticmethod
    def get_raid_party_url(pb_raid_party_id):

        raid_party_url = f"http://www.pokebattler.com/raidParty/{pb_raid_party_id}"

        return raid_party_url


    @staticmethod
    def add_user_to_raid_party(raid_party_id, member: discord.Member):
        try:
            pb_raid_party_id = raid_party_id
            url = f"https://fight.pokebattler.com/secure/raidParties/{pb_raid_party_id}/users"

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

        except Exception as error:
            return None

