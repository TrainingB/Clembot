import test_parser
from clembot import time_util


def find_pokemon(text):
    if text in ['rayquaza','groudon','kyogre']:
        return True
    return False;

def parse_test(text, format, options_method={}):
    response = test_parser.parse(text, format, options_method)
    print("{text} = {response}".format(text=text, response=response))

    print(response.get('others',None))

def test():

    parameter ="!find-gym -all MESC".split()
    print(parameter)


    if (parameter.__contains__("-all")):
        parameter.remove("-all")
        print(parameter)

    # parse_test("!add kyogre clco 2:45pm", ['command', 'pokemon', 'gym_code', 'eta'], {'pokemon' : find_pokemon, 'eta' : time_util.convert_into_time})


    # parse_test("!raidegg 5 clco 2", ['command', 'egg', 'gym_code', 'timer', 'location'])
    #
    # parse_test("!raid groudon art mural 2 23", ['command', 'pokemon', 'gym_code', 'timer', 'location'], {'pokemon' : is_valid_pokemon})
    #
    # parse_test("!c 2 groudon kyogre", ['command', 'pokemon', 'gym_code', 'partysize', 'location'])
    #
    # parse_test("!raidegg 6 clco 5", ['command', 'egg', 'gym_code', 'timer', 'location'])
    #
    # parse_test("!raid groudon clco 23", ['command', 'pokemon', 'gym_code', 'timer', 'location'])
    #
    # parse_test("!c 6 m2 v3 groudon kyogre", ['command', 'pokemon', 'gym_code', 'partysize', 'location'])
    #
    #
    # parse_test("!update 3 groudon clco 3:00pm", ['command', 'index' ,'pokemon', 'gym_code', 'eta'])
    #
    # parse_test("!update 3 groudon", ['command', 'index' ,'pokemon', 'gym_code', 'eta'], {'pokemon' : is_valid_pokemon, 'eta' : convert_into_time})

def main():
    try:
        test()
        print("main() finished")
    except Exception as error:
        print(error)
    return

main()