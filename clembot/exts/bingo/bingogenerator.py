import json
import os
from random import *
from clembot.exts.bingo.pokemondataprovider import PokemonDataProvider
# https://json-csv.com/

script_path = os.path.dirname(os.path.realpath(__file__))

class BingoDataGenerator:

    def __init__(self):
        self._cache = {}
        self._new_cache = {}
        self.cpProvider = PokemonDataProvider()


    pokemon_cp_level = {}

    def cache(self, event_pokemon):

        if event_pokemon in self._cache.keys():
            return self._cache.get(event_pokemon, {})

        self.load_pokemon_data()
        if event_pokemon in self._cache.keys():
            return self._cache.get(event_pokemon, {})

    def keep_number_in_range(self, number, spread, min_cp, max_cp):

        low = number - int(spread/2)
        high = number + int(spread/2)

        if low < min_cp or low < 11:
            high = min_cp + spread
            low = min_cp

        if high > max_cp:
            low = max_cp - spread
            high = max_cp

        if low < 10:
            print(f"----------------------{low} {high} {number} {spread} {min_cp} {max_cp}")

        return "{0:>3}-{1}".format(low,high)

    def test_cp_extractor(self, cp_values):
        try:

            cp_data = [s.split(None, 6) for s in cp_values.splitlines()]
            cp_master = {}
            for level_info in cp_data[1:60:2]:  # leave first row, use alternate there after
                cp_range = int(level_info[3]) - int(level_info[2])
                level_details = {
                    "Stardust": int(level_info[0]),
                    "Level": int(level_info[1]),
                    "Min CP": int(level_info[2]),
                    "Max CP": int(level_info[3]),
                    "Spread":
                        round((cp_range / 5) if int(level_info[1]) <= 5 else
                              (max(cp_range / 6, 10) if int(level_info[1]) < 10 else
                               (max(cp_range / 7, 16) if int(level_info[1]) < 15 else
                                (max(cp_range / 7, 24) if int(level_info[1]) < 20 else
                                 (max(cp_range / 8, 20) if int(level_info[1]) < 25 else
                                  max(cp_range / 9, 28)
                                  )))))
                }
                cp_master[level_info[1]] = level_details;

            print(json.dumps(cp_master, indent=4));

            return cp_master
        except Exception as error:
            print(error)
            return {}



    gender_master = { 'mareep' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2642", u"\u2640", u"\u2640",u"\u2640",u"\u2640"] ,
                      'charmander' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2640",u"\u2642",u"\u2642",u"\u2642",u"\u2642"],
                      'squirtle' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2640",u"\u2642",u"\u2642",u"\u2642",u"\u2642"],
                      'eevee' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2640",u"\u2642",u"\u2642",u"\u2642",u"\u2642"],
                      'chikorita' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2640",u"\u2642",u"\u2642",u"\u2642",u"\u2642"],
                      'beldum': ["", "", "", "", "", "", "", ""],
                      'cyndaquil' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2640",u"\u2642",u"\u2642",u"\u2642",u"\u2642"],
                      'totodile' : [u"\u2642" , u"\u2642", u"\u2642", u"\u2640",u"\u2642",u"\u2642",u"\u2642",u"\u2642"]
                    }


    box_pokemon = [ 'free', 'charmander' , 'squirtle', 'beldum' , 'larvitar' , 'shiny', 'pikachu', 'bulbasaur', 'dratini', 'eevee' ]

    box_5_pokemon = [ 'free' , 'mareep', 'cyndaquil', 'chikorita' ]

    def generate_mixed_card (self):


        MALE_SIGN = u"\u2642"
        FEMALE_SIGN = u"\u2640"

        stats = ['Attack','Defense','Stamina']

        category = []
        size = ['XL','XL','XL','XL','XS','XS','XS','XS']
        # gender = gender_master.get(event_pokemon,[u"\u2642" , u"\u2642", u"\u2642", u"\u2642", u"\u2640", u"\u2640",u"\u2640",u"\u2640"])

        bingo_card = self.generate_default_card()

        weight_box = randint(1, 4)
        height_box = randint(6, 9)

        for bingo_cell in list(bingo_card.keys()) :
            range_multiplier = 1
            box_pokemon_name = self.box_pokemon[int(bingo_cell)]
            if int(bingo_cell) == 5:
                box_pokemon_name = self.box_5_pokemon[randint(1,3)]
                range_multiplier = 1.25
            elif int(bingo_cell) == weight_box or int(bingo_cell) == height_box:
                range_multiplier = 1.6

            cell_level = randint(int(randint(10, 12)*range_multiplier), randint(22, 28))
            cell_json = self.pokemon_cp_level[box_pokemon_name]["{0}".format(cell_level)]
            cell_cp = randint(cell_json['Min CP'], cell_json['Max CP'])
            cell_range = self.keep_number_in_range(cell_cp, int(randint(120, 160) * range_multiplier), cell_json['Min CP'], cell_json['Max CP'])
            cell_value = ["CP : {:>0}".format(cell_range)]

            bingo_card[bingo_cell] = cell_value

        bingo_card[f"{weight_box}"] = [bingo_card[f"{weight_box}"][0], "Weight = {0}".format(size[randint(0, 7)])]
        bingo_card[f"{height_box}"] = [bingo_card[f"{height_box}"][0], "Height = {0}".format(size[randint(0, 7)])]
        bingo_card['5'] = ['']


        return bingo_card

    def load_pokemon_data(self, pokemon):

        for pokemon in ['mudkip','ralts']:
            level_json = {}
            for level in range(1, 31):
                level_json.update(
                    { f"{level}": {
                    "level": level,
                    "Max CP": self.cpProvider.calculateCP(pokemon, level, 15, 15, 15),
                    "Min CP": self.cpProvider.calculateCP(pokemon, level, 0, 0, 0),
                    "Spread" : int ((self.cpProvider.calculateCP(pokemon, level, 15, 15, 15) - self.cpProvider.calculateCP(pokemon, level, 0, 0, 0)) / 6) + 1
                }
                })

            print(json.dumps(level_json, indent=2))
            self.pokemon_cp_level[pokemon] = level_json

    def generate_card(self, event_pokemon='ralts'):

        if event_pokemon not in self.pokemon_cp_level.keys():
            self.load_pokemon_data(event_pokemon)

        pokemon_cp = self.pokemon_cp_level.get(event_pokemon, self.pokemon_cp_level[f'{event_pokemon}'])


        MALE_SIGN = u"\u2642"
        FEMALE_SIGN = u"\u2640"

        stats = ['Attack','Defense','Stamina']

        category = []
        size = ['XL','XL','XL','XL','XS','XS','XS','XS']
        gender = self.gender_master.get(event_pokemon,[MALE_SIGN, MALE_SIGN, MALE_SIGN, MALE_SIGN, FEMALE_SIGN, MALE_SIGN, MALE_SIGN, MALE_SIGN])

        bingo_card = {}

        cell_1_level = randint(6,9)
        cell_1_json = pokemon_cp["{0}".format(cell_1_level)]
        cell_1_cp = randint(cell_1_json['Min CP'], cell_1_json['Max CP'])
        cell_1_range = self.keep_number_in_range(cell_1_cp, cell_1_json['Spread'], cell_1_json['Min CP'],cell_1_json['Max CP'])
        cell_1_value = ["CP : {:>0}".format(cell_1_range)]

        cell_2_level = randint(4,14)
        cell_2_json = pokemon_cp["{0}".format(cell_2_level)]
        cell_2_low_json = pokemon_cp["{0}".format(cell_2_level - 2)]
        cell_2_high_json = pokemon_cp["{0}".format(cell_2_level + 2)]
        cell_2_cp = randint(cell_2_json['Min CP'], cell_2_json['Max CP'])
        cell_2_spread = ( pokemon_cp["12"]["Spread"] + pokemon_cp["13"]["Spread"] + pokemon_cp["14"]["Spread"] ) * 2
        cell_2_range = self.keep_number_in_range(cell_2_cp, cell_2_spread, cell_2_low_json['Min CP'], cell_2_high_json['Max CP'])
        cell_2_value = ["CP: {0}".format(cell_2_range), "Weight = {0}".format(size[randint(0, 7)])]

        cell_3_level = randint(18,21)
        cell_3_json = pokemon_cp["{0}".format(cell_3_level)]
        cell_3_cp = randint(cell_3_json['Min CP'], cell_3_json['Max CP'])
        cell_3_range = self.keep_number_in_range(cell_3_cp, cell_3_json['Spread'], cell_3_json['Min CP'],cell_3_json['Max CP'])
        cell_3_value = ["CP : {0} ".format(cell_3_range)]


        cell_4_level = randint(10,13)
        cell_4_json = pokemon_cp["{0}".format(cell_4_level)]
        cell_4_cp = randint(cell_4_json['Min CP'], cell_4_json['Max CP'])
        cell_4_range = self.keep_number_in_range(cell_4_cp, cell_4_json['Spread'] * 2, cell_4_json['Min CP'], cell_4_json['Max CP']) #cell_4_json['Spread'] * 2
        cell_4_value = ["CP : {0} ".format(cell_4_range) , "{0}".format(gender[randint(0,7)])] #

        cell_5_value = [ "" , ""]
        # ["{0}".format(event_pokemon.capitalize().center(13, ' ')), "✩"]

        cell_6_level = randint(22, 25)
        cell_6_json = pokemon_cp["{0}".format(cell_6_level)]
        cell_6_cp = randint(cell_6_json['Min CP'], cell_6_json['Max CP'])
        cell_6_range = self.keep_number_in_range(cell_6_cp, cell_6_json['Spread'] * 2, cell_6_json['Min CP'], cell_6_json['Max CP']) #cell_6_json['Spread'] * 2
        cell_6_value = ["CP : {0} ".format(cell_6_range), "{0}".format(gender[randint(0, 7)])] # , "{0}".format(gender[randint(0, 7)])


        cell_7_level = randint(14, 17)
        cell_7_json = pokemon_cp["{0}".format(cell_7_level)]
        cell_7_cp = randint(cell_7_json['Min CP'], cell_7_json['Max CP'])
        cell_7_range = self.keep_number_in_range(cell_7_cp, cell_7_json['Spread'], cell_7_json['Min CP'], cell_7_json['Max CP'])
        cell_7_value = ["CP : {0} ".format(cell_7_range)]


        cell_8_level = randint(16,26)
        cell_8_json = pokemon_cp["{0}".format(cell_8_level)]
        cell_8_low_json = pokemon_cp["{0}".format(cell_8_level - 1)]
        cell_8_high_json = pokemon_cp["{0}".format(cell_8_level + 1)]
        cell_8_cp = randint(cell_8_json['Min CP'], cell_8_json['Max CP'])
        cell_8_spread = (pokemon_cp["8"]["Spread"] + pokemon_cp["9"]["Spread"] + pokemon_cp["10"]["Spread"]) * 2
        cell_8_range = self.keep_number_in_range(cell_8_cp, cell_8_spread, cell_8_low_json['Min CP'], cell_8_high_json['Max CP'])
        cell_8_value = ["CP: {0}".format(cell_8_range), "Height = {0}".format(size[randint(0, 7)])]

        cell_9_level = randint(26, 30)
        cell_9_json = pokemon_cp["{0}".format(cell_9_level)]
        cell_9_cp = randint(cell_9_json['Min CP'], cell_9_json['Max CP'])
        cell_9_range = self.keep_number_in_range(cell_9_cp, cell_9_json['Spread'], cell_9_json['Min CP'],cell_9_json['Max CP'])
        cell_9_value = ["CP : {0} ".format(cell_9_range)]


        bingo_card['1'] = cell_1_value
        bingo_card['2'] = cell_2_value
        bingo_card['3'] = cell_3_value
        bingo_card['4'] = cell_4_value
        bingo_card['5'] = cell_5_value
        bingo_card['6'] = cell_6_value
        bingo_card['7'] = cell_7_value
        bingo_card['8'] = cell_8_value
        bingo_card['9'] = cell_9_value

        return bingo_card




    def generate_default_card(self):

        bingo_card = {}

        bingo_card['1'] = 'Level 2 , 30 CP'
        bingo_card['2'] = 'Level 2 , 30 CP'
        bingo_card['3'] = 'Level 2 , 30 CP'
        bingo_card['4'] = 'Level 2 , 30 CP'
        bingo_card['5'] = 'Level 2 , 30 CP'
        bingo_card['6'] = 'Level 2 , 30 CP'
        bingo_card['7'] = 'Level 2 , 30 CP'
        bingo_card['8'] = 'Level 2 , 30 CP'
        bingo_card['9'] = 'Level 2 , 30 CP'

        return bingo_card


    def print_card(self, bingo_card):
        print("")

        print("|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['1'],bingo_card['2'],bingo_card['3']))
        print("|\t{0}\t|\t\t{1}\t\t\t|\t{2}\t|".format(bingo_card['4'], bingo_card['5'], bingo_card['6']))
        print("|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['7'], bingo_card['8'], bingo_card['9']))



    def print_card_as_text(self, bingo_card):

        text = "|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['1'],bingo_card['2'],bingo_card['3'])
        text = text + "\n"+ "|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['4'], bingo_card['5'], bingo_card['6'])
        text = text + "\n" +"|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['7'], bingo_card['8'], bingo_card['9'])

        return text


self = BingoDataGenerator()

def main():
    test()

def test1():
    self.print_card(self.generate_mixed_card())

    self.print_card(self.generate_mixed_card())

    self.print_card(self.generate_mixed_card())

def test():


    self.print_card(self.generate_default_card())

    self.print_card(self.generate_card('ralts'))

    for i in range(1, 200):
        self.print_card(self.generate_card())

    self.print_card(self.generate_card())

    self.print_card(self.generate_card())

    self.print_card(self.generate_card())

    self.print_card(self.generate_card())

    print(self.generate_card())

    print(self.print_card_as_text(self.generate_card()))


def test3():
    # self.test_cp_extractor(self.torchic_cp_chart)

    self.print_card(self.generate_card('ralts'))



#main()

#test()



# https://pokemongo.gamepress.gg/pokemon/133