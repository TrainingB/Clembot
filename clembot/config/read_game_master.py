import asyncio
import json
import os
import traceback
import urllib, urllib.request

import aiohttp


def get_from_game_master():

    load_from_web=False

    if load_from_web:
        url = "https://raw.githubusercontent.com/pokemongo-dev-contrib/pokemongo-game-master/master/versions/latest/V2_GAME_MASTER.json"
        file = urllib.request.urlopen(url)
        data = json.load(file)
    else:
        with open(os.path.join(os.path.abspath('.'),'clembot','config','V2_GAME_MASTER.json'), 'r') as fd:
            data = json.load(fd)



    # read batch id
    print(data.get('batchId'))


    # for template in data.get('template'):
    #     templateId = template.get('templateId')
    #     data = template.get('data')
    #     if templateId.startswith('FORMS_') and data.get('templateId', None):
    #         print(f"{templateId} => {data.get('templateId', None)}=> {json.dumps(data)}")

    for template in data.get('template'):
        templateId = template.get('templateId')
        data = template.get('data')
        splits = templateId.split('_')
        if len(splits) > 2 and splits[0].startswith('V') and splits[1] == 'POKEMON' and data.get('templateId', None):
            # print(f"{templateId} => {data.get('pokemon', None)}=> {json.dumps(data)}")
            print(f"{template}")

def fetch_pokebattler():
    async def get_from_pokebattler():

        async with aiohttp.ClientSession() as sess:
            async with sess.get('https://fight.pokebattler.com/pokemon') as resp:
                data = await resp.json()

        print(json.dumps(data))

    print("async_db_wrapper()")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(get_from_pokebattler())
    except Exception as error:
        print(f"{traceback.format_exc()}")






def main():
    # fetch_pokebattler()
    get_from_game_master()

if __name__=='__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")
