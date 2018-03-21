from clembot import time_util


def pokemon_validator_mock(text):
    if text in ['kyogre','groudon','rayquaza']:
        return True
    return False;

def egg_validator_mock(text):
    if text in ['1','2','3','4','5']:
        return True
    return False;

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

def gym_validator_mock(gym_code):

    gym_codes = ['stem','clco']
    gym_info = {}
    if gym_code in gym_codes:
        gym_info['gym_code'] = gym_code
        return gym_info
    return None


def parse(text, list_of_options, options_methods={}):

    args = text.split()
    command = args[0]
    del args[0]

    response = {}

    pokemon_method = options_methods.get('pokemon', pokemon_validator_mock)
    egg_method = options_methods.get('egg', egg_validator_mock)
    gym_lookup_method = options_methods.get('gym-code', gym_validator_mock)
    eta_method = options_methods.get('eta', eta_validator_mock)

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
        # identify egg level is specified
        elif option == 'egg':
            for arg in list(args):
                if arg.isdigit():
                    if egg_method(arg):
                        response['egg'] = int(arg)
                        args.remove(arg)
                    else:
                        other_list = response.get('others', [])
                        other_list.append(arg)
                        response['others'] = other_list
                        args.remove(arg)
                        break

        # identify gym_code
        elif option == 'gym_code':
            for arg in list(args):
                if gym_lookup_method(arg):
                    response['gym_code'] = arg
                    args.remove(arg)

        # identify partysize or index
        elif option == 'partysize' or option == 'index':
            for arg in list(args):
                if arg.isdigit():
                    response[option] = int(arg)
                    args.remove(arg)
        # identify timer as the last number
        elif option == 'timer' :
            for arg in list(args):
                if arg.isdigit():
                    existig_timer = response.get(option,None)
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
    # all remaining arguments in others
    for arg in list(args):
        other_list = response.get('others', [])
        other_list.append(arg)
        response['others'] = other_list
        args.remove(arg)

    return response

def parse_test(text, format, options_method={}):
    response = parse(text, format, options_method)
    print("{text} = {response}".format(text=text, response=response))

    print(response.get('others',None))

def test():

    parse_test("!add groudon clco 2:45pm", ['command', 'pokemon', 'gym_code', 'eta'], {'pokemon' : pokemon_validator_mock, 'eta' : time_util.convert_into_time})

    parse_test("!raidegg 5 clco 2", ['command', 'egg', 'gym_code', 'timer', 'location'])

    parse_test("!raid groudon art mural 2 23", ['command', 'pokemon', 'gym_code', 'timer', 'location'], {'pokemon' : pokemon_validator_mock})

    parse_test("!c 2 groudon kyogre", ['command', 'pokemon', 'gym_code', 'partysize', 'location'])

    parse_test("!raidegg 6 clco 5", ['command', 'egg', 'gym_code', 'timer', 'location'])

    parse_test("!raid groudon clco 23", ['command', 'pokemon', 'gym_code', 'timer', 'location'])

    parse_test("!c 6 m2 v3 groudon kyogre", ['command', 'pokemon', 'gym_code', 'partysize', 'location'])


    parse_test("!update 3 groudon clco 3:00pm", ['command', 'index' ,'pokemon', 'gym_code', 'eta'])

    parse_test("!update 3 groudon", ['command', 'index' ,'pokemon', 'gym_code', 'eta'], {'pokemon' : pokemon_validator_mock, 'eta' : eta_validator_mock})

def main():
    try:
        test()
        print("main() finished")
    except Exception as error:
        print(error)
    return

main()