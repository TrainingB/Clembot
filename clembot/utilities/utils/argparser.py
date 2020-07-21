import asyncio
import os
import re
import traceback

import discord

from clembot.core import time_util
from clembot.core.data_manager.dbi import DatabaseInterface
from clembot.core.logs import Logger
from clembot.exts.config.channel_metadata import ChannelMetadata
from clembot.exts.gymmanager.gym import Gym, GymRepository
from clembot.exts.pkmn.gm_pokemon import Pokemon


class GymLookupExtension:

    def __init__(self, dbi):
        self.dbi = dbi
        self.GymRepository = GymRepository(dbi)

    async def get_gym_by_gym_code_city(self, gym_code, message: discord.Message) -> Gym:

        channel_city = await ChannelMetadata.city({dbi: self.dbi}, message.channel.id)

        return await self.GymRepository.to_gym_by_code_city(gym_code, channel_city)





class ArgParser:

    def __init__(self, dbi=None):
        self.gymLookupExtension = None
        self.dbi = dbi
        if dbi:
            self.gymLookupExtension = GymLookupExtension(dbi)


    def pokemon_validator_mock(text):
        if text in ['kyogre', 'groudon', 'rayquaza', 'magikarp', 'azelf', 'latios']:
            return True
        return False

    def egg_validator_mock(text):
        if text in ['1', '2', '3', '4', '5']:
            return True
        return False

    def eta_validator_mock(time_as_text, require_am_pm=True):
        return time_util.convert_into_time(time_as_text, require_am_pm)

    def translate_team(text):
        if text.lower() == 'm' or 'mystic' or 'blue':
            return 'mystic'

        if text.lower() == 'i' or 'instinct' or 'yellow':
            return 'instinct'

        if text.lower() == 'r' or 'valor' or 'red':
            return 'red'

        return None

    def gym_validator_mock(gym_code, message):

        gym_codes = ['stem', 'clco', 'mesc']
        gym_info = {}
        if gym_code in gym_codes:
            gym_info['gym_info'] = gym_code
            return gym_info
        return None

    def discord_username_mock(self, username):
        if re.match(r'@(.*)\#\d{4}', username):
            return True
        else:
            return re.match(r'(#\d{18})*', username)

    def extract_link_from_text(text):
        text = str(text)
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


    async def parse_arguments(self, text, list_of_options, options_methods={}, options_method_optional_parameters={}, ctx=None):
        response = {}

        args = text.split()

        response['length'] = len(args)

        if 'command' in list_of_options:
            command = args[0]
            del args[0]

        pokemon_method = options_methods.get('pokemon', ArgParser.pokemon_validator_mock)
        eta_method = options_methods.get('eta', ArgParser.eta_validator_mock)
        link_method = options_method_optional_parameters.get('link', ArgParser.extract_link_from_text)

        gym_lookup_message = options_method_optional_parameters.get('message', None)

        for option in list_of_options:
            # first check for command
            if option == 'command':
                response['command'] = command
            # identify pokemons
            elif option == 'pokemon':
                for arg in list(args):
                    if pokemon_method(arg):
                        poke_list = response.get('pokemon', [])
                        poke_list.append(arg)
                        response['pokemon'] = poke_list
                        args.remove(arg)
            elif option == 'subcommand':
                for arg in list(args):
                    if arg == 'assume':
                        response['subcommand'] = 'assume'
                        args.remove(arg)
                        break
            elif option == 'cp':
                for arg in list(args):
                    if arg.lower().__contains__('cp'):
                        cp_value = arg.replace('cp','')
                        if cp_value.isdigit():
                            args.remove(arg)
                            response['cp'] = int(cp_value)
                            break
            elif option == 'lvl':
                for arg in list(args):
                    if arg.lower().__contains__('lvl') or arg.__contains__('level'):
                        lvl_value = arg.replace('lvl','').replace('level','')
                        if lvl_value.isdigit():
                            if 1<= int(lvl_value) <= 40:
                                args.remove(arg)
                                response['lvl'] = int(lvl_value)
                                break
            elif option == 'iv':
                for arg in list(args):
                    if arg.lower().__contains__('iv'):
                        iv_value = arg.replace('iv','')
                        if iv_value.isdigit():
                            if 0 <= int(iv_value) <= 100:
                                args.remove(arg)
                                response['iv'] = int(iv_value)
                                break
            elif option == 'latlong':
                for arg in list(args):
                    match = re.match('^(?P<lat>-?\d*(.\d+)),(?P<long>-?\d*(.\d+))$', arg)
                    if match is not None:
                        args.remove(arg)
                        response['lat'] = float(match.group('lat'))
                        response['long'] = float(match.group('long'))

            # identify egg level is specified
            elif option == 'egg':
                for arg in list(args):
                    if arg.isdigit():
                        if response.get('egg', None) == None:
                            response['egg'] = int(arg)
                            args.remove(arg)
                        else:
                            break

            # identify count is specified
            elif option == 'count':
                for arg in list(args):
                    if arg.isdigit():
                        if response.get('count', None) == None:
                            response['count'] = int(arg)
                            args.remove(arg)
                        else:
                            break
            # identify gym_code
            elif option == 'gym':
                for arg in list(args):
                    try:
                        if not self.gymLookupExtension:
                            raise ValueError("Database interface is not set. call set_dbi() for gym lookup.")
                        if response.get('gym', None) is None and len(arg) > 1:
                            # gym_info = await gym_lookup_method(arg.upper(), message=gym_lookup_message)
                            # if gym_info:
                            #     response['gym_info'] = gym_info
                            #     args.remove(arg)

                            gym_lookup_method = options_methods.get('gym', self.gymLookupExtension.get_gym_by_gym_code_city)
                            gym = await gym_lookup_method(self.dbi, arg.upper(), gym_lookup_message)

                            if gym:
                                response['gym'] = gym
                                args.remove(arg)

                    except Exception as error:
                        Logger.error(f"{traceback.format_exc()}")
                        raise ValueError(error)

            # identify discord username
            elif option == 'mentions':
                for arg in list(args):
                    try:
                        if self.discord_username_mock(arg):
                            mention_list = response.get('mentions', [])
                            mention_list.append(arg)
                            response['mentions'] = mention_list
                            args.remove(arg)
                    except Exception as error:
                        Logger.error(f"{traceback.format_exc()}")
                        pass
            # identify partysize or index
            elif option == 'partysize' or option == 'index':
                for arg in list(args):
                    if arg.isdigit():
                        response[option] = int(arg)
                        args.remove(arg)
            # identify timer as the last number
            elif option == 'timer':
                for arg in list(args):
                    if arg.isdigit():
                        existig_timer = response.get(option, None)
                        if existig_timer:
                            args.append(existig_timer)
                        response[option] = int(arg)
                        args.remove(arg)

            # identify eta as valid time
            elif option == 'eta':
                for arg in list(args):
                    eta = eta_method(arg)
                    if eta:
                        response['eta'] = eta
                        args.remove(arg)
            elif option == 'link':
                for arg in list(args):
                    link = link_method(arg)
                    if link:
                        response['link'] = link
                        args.remove(arg)
                        # identify pokemons

        # all remaining arguments in others
        if 'pkmn' in list_of_options:
            for arg in list(args):
                try:
                    pkmn = await Pokemon.convert(ctx, arg)
                    if pkmn:
                        response['pkmn'] = pkmn
                        args.remove(arg)
                except Exception as error:
                    Logger.error(f"{traceback.format_exc()}")
                    pass

        for arg in list(args):

            response.setdefault('others', []).append(arg)
            args.remove(arg)


        return response






async def parse_test(text, format, options_method={}):
    global argParser

    response = await argParser.parse_arguments(text, format, options_method)
    print("{text} = {response}\n".format(text=text, response=response))

    return response

    print(response.get('others',None))



async def test():
    await parse_test("!raidegg 7 clco 3", ['command', 'egg', 'gym_info', 'timer', 'location'])

    await parse_test("!raidegg 5 clco 2", ['command', 'egg', 'gym_info', 'timer', 'location'])


    await parse_test("!add groudon clco 2:45pm", ['command', 'pokemon', 'gym_info', 'eta'], {'pokemon' : ArgParser.pokemon_validator_mock, 'eta' : time_util.convert_into_time})

    await parse_test("!raid groudon", ['command', 'pokemon', 'gym_info', 'timer', 'location'], {'pokemon': ArgParser.pokemon_validator_mock})

    await parse_test("!raid gkroudon art mural 2 23", ['command', 'pokemon', 'gym_info', 'timer', 'location'], {'pokemon' : ArgParser.pokemon_validator_mock})

    await parse_test("!c 2 groudon kyogre", ['command', 'pokemon', 'gym_info', 'partysize', 'location'])

    await parse_test("!raidegg 6 clco 5", ['command', 'egg', 'gym_info', 'timer', 'location'])

    await parse_test("!raid groudon clco 23", ['command', 'pokemon', 'gym_info', 'timer', 'location'])

    await parse_test("!c 6 m2 v3 groudon kyogre", ['command', 'pokemon', 'gym_info', 'partysize', 'location'])


    await parse_test("!update 3 groudon clco 3:00pm", ['command', 'index' ,'pokemon', 'gym_info', 'eta'])

    await parse_test("!update 3 groudon", ['command', 'index' ,'pokemon', 'gym_info', 'eta'], {'pokemon' : ArgParser.pokemon_validator_mock, 'eta' : ArgParser.eta_validator_mock})


async def test6():
    await parse_test("!xraid alolan-vulpix mesc 2", ['command', 'pkmn', 'gym_info', 'timer', 'location'])

    await parse_test("!raidegg 5 clco 2", ['command', 'egg', 'gym_info', 'timer', 'location'])


    await parse_test("!add groudon clco 2:45pm", ['command', 'pkmn', 'gym_info', 'eta'], {'pokemon' : ArgParser.pokemon_validator_mock, 'eta' : time_util.convert_into_time})

    await parse_test("!raid groudon", ['command', 'pkmn', 'gym_info', 'timer', 'location'], {'pokemon': ArgParser.pokemon_validator_mock})

    await parse_test("!raid gkroudon art mural 2 23", ['command', 'pkmn', 'gym_info', 'timer', 'location'], {'pokemon' : ArgParser.pokemon_validator_mock})

    await parse_test("!c 2 groudon kyogre", ['command', 'pkmn', 'gym_info', 'partysize', 'location'])

    await parse_test("!raidegg 6 clco 5", ['command', 'egg', 'gym_info', 'timer', 'location'])

    await parse_test("!raid groudon clco 23", ['command', 'pkmn', 'gym_info', 'timer', 'location'])

    await parse_test("!c 6 m2 v3 groudon kyogre", ['command', 'pkmn', 'gym_info', 'partysize', 'location'])


    await parse_test("!update 3 groudon clco 3:00pm", ['command', 'index' ,'pkmn', 'gym_info', 'eta'])

    await parse_test("!update 3 groudon", ['command', 'index' ,'pkmn', 'gym_info', 'eta'], {'pokemon' : ArgParser.pokemon_validator_mock, 'eta' : ArgParser.eta_validator_mock})




async def test1():
    await parse_test("!raidegg 1 clco 0", ['command', 'egg', 'gym_info', 'timer', 'location'])

    await parse_test("!raid assume groudon", ['command', 'subcommand', 'pokemon'])





async def test2():
    parameters = await parse_test("!raidegg 5 gewa43 38", ['command', 'egg', 'gym_info', 'timer', 'location'],{'pokemon' : ArgParser.pokemon_validator_mock, 'link' : ArgParser.extract_link_from_text })
    print(" ".join(str(x) for x in parameters.get('others')))

    await parse_test("!nest Squirtle Tonga Park ( some city ) https://goo.gl/maps/suEo9zDBCCP2", ['command','pokemon','link'])

    await parse_test("!exraid mesc", ['command', 'gym_info'])


# ---------------uncomment this line to test stand alone-------------------------

async def test3():

    if re.match(r'@(.*)\#\d{4}', '@G. (๑˃̵ᴗ˂̵)و-☆z#3529'):
        print('matched')

    print(re.match(r'@(.*)\#\d{4}', '@G. (๑˃̵ᴗ˂̵)و-☆z#3529'))
    await parse_test("!raidegg 5 600 Corp Pointe 13", ['command', 'egg', 'pokemon' , 'gym_info', 'timer', 'location' , 'link'])

    await parse_test("!c 3 @Bronzor#0409 2 @MEE6#4876 where are you", ['command' 'count', 'mentions'])

    await parse_test("!c", ['command', 'count'] )

    await parse_test("!c 5", ['command', 'count'] )
    await parse_test("!c @G. (๑˃̵ᴗ˂̵)و-☆z#3529  @B!#2022 4 @Bronzor#0409 @MEE6#4876", ['command', 'count', 'mentions'] )




async def test5():

    await parse_test("!spawn squirtle -23.0932303,43.93232 23CP 100IV", ['command', 'pokemon', 'latlong', 'cp', 'iv'])

    await parse_test("!spawn squirtle -23.0932303,43.93232 23CP 102IV", ['command', 'pokemon', 'latlong', 'cp', 'iv'])

    await parse_test("!spawn azelf -23.0932303,43.93232 23CP 102IV", ['command', 'pokemon', 'latlong', 'cp', 'iv'])


async def test4():


    await parse_test("!raid groudon MESC 23", ['command', 'pokemon', 'gym', 'timer', 'location'])


event_loop = asyncio.get_event_loop()



dbi = None

async def initialize():
    global dbi
    dbi = DatabaseInterface.get_instance() # DatabaseInterface()
    await dbi.start()


async def cleanup():
    global dbi
    await dbi.stop()


async def test_suite():
    try:
        await initialize()
        await Pokemon.load({dbi: dbi})
        # await test()
        # await test1()
        # await test2()
        # await test3()
        # await test4()
        await test6()
    finally:
        await cleanup()

argParser = None

def main():

    global argParser
    dbi = DatabaseInterface.get_instance() # DatabaseInterface(**config_template.db_config_details)

    argParser = ArgParser(dbi)

    try:
        event_loop.run_until_complete(test_suite())

        print("main() finished")
    except Exception as error:
        Logger.error(f"{traceback.format_exc()}")
    return



if __name__=='__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")

