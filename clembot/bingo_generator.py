import os
from os import name
import json
from random import *

bulbasaur_cp = {}
script_path = os.path.dirname(os.path.realpath(__file__))

def load_data():
    global bulbasaur_cp

    directory = os.path.join(script_path,"..","data")
    filename = "bulbasaur.json"
    print("Loading..." + os.path.join(directory, filename))

    with open(os.path.join(directory, filename), "r") as fd:
        bulbasaur_cp = json.load(fd)


load_data()

print(bulbasaur_cp)


def keep_number_in_range(number, spread, min_cp, max_cp):

    low = number - int(spread/2)
    high = number + int(spread/2)

    if low < min_cp:
        high = min_cp + spread
        low = min_cp

    if high > max_cp:
        low = max_cp - spread
        high = max_cp

    return "{0}-{1}".format(low,high)

def generate_card():

    stats = ['Attack','Defense','Stamina']

    category = []
    size = ['XS','XL','XL','XS','XS','XL']

    bingo_card = {}

    cell_1_level = randint(1,5)
    cell_1_json = bulbasaur_cp["{0}".format(cell_1_level)]
    cell_1_cp = randint(cell_1_json['Min CP'], cell_1_json['Max CP'])
    cell_1_range = keep_number_in_range(cell_1_cp, cell_1_json['Spread'], cell_1_json['Min CP'],cell_1_json['Max CP'])
    cell_1_value = "CP : {0} ".format(cell_1_range, size[randint(0,1)], cell_1_json['Stardust'])


    cell_2_level = randint(4,14)
    cell_2_json = bulbasaur_cp["{0}".format(cell_2_level)]
    cell_2_low_json = bulbasaur_cp["{0}".format(cell_2_level - 2 )]
    cell_2_high_json = bulbasaur_cp["{0}".format(cell_2_level + 2)]
    cell_2_cp = randint(cell_2_json['Min CP'], cell_2_json['Max CP'])
    cell_2_range = keep_number_in_range(cell_2_cp, randint(80,110), cell_2_low_json['Min CP'], cell_2_high_json['Max CP'])
    cell_2_value = "CP: {0} Weight = {1}".format(cell_2_range,size[randint(0,5)])

    cell_3_level = randint(16,20)
    cell_3_json = bulbasaur_cp["{0}".format(cell_3_level)]
    cell_3_cp = randint(cell_3_json['Min CP'], cell_3_json['Max CP'])
    cell_3_range = keep_number_in_range(cell_3_cp, cell_3_json['Spread'], cell_3_json['Min CP'],cell_3_json['Max CP'])
    cell_3_value = "CP : {0} ".format(cell_3_range, size[randint(0, 1)], cell_3_json['Stardust'])


    cell_4_level = randint(6,10)
    cell_4_json = bulbasaur_cp["{0}".format(cell_4_level)]
    cell_4_cp = randint(cell_4_json['Min CP'], cell_4_json['Max CP'])
    cell_4_range = keep_number_in_range(cell_4_cp, cell_4_json['Spread'], cell_4_json['Min CP'], cell_4_json['Max CP'])
    cell_4_value = "CP : {0} ".format(cell_4_range, size[randint(0, 1)], cell_4_json['Stardust'])

    cell_5_value = "-Shiny Bulbasaur-"

    cell_6_level = randint(21, 25)
    cell_6_json = bulbasaur_cp["{0}".format(cell_6_level)]
    cell_6_cp = randint(cell_6_json['Min CP'], cell_6_json['Max CP'])
    cell_6_range = keep_number_in_range(cell_6_cp, cell_6_json['Spread'], cell_6_json['Min CP'], cell_6_json['Max CP'])
    cell_6_value = "CP : {0} ".format(cell_6_range, size[randint(0, 1)], cell_6_json['Stardust'])


    cell_7_level = randint(11, 15)
    cell_7_json = bulbasaur_cp["{0}".format(cell_7_level)]
    cell_7_cp = randint(cell_7_json['Min CP'], cell_7_json['Max CP'])
    cell_7_range = keep_number_in_range(cell_7_cp, cell_7_json['Spread'], cell_7_json['Min CP'], cell_7_json['Max CP'])
    cell_7_value = "CP : {0} ".format(cell_7_range, size[randint(0, 1)], cell_7_json['Stardust'])


    cell_8_level = randint(16,26)
    cell_8_json = bulbasaur_cp["{0}".format(cell_8_level)]
    cell_8_low_json = bulbasaur_cp["{0}".format(cell_8_level - 1 )]
    cell_8_high_json = bulbasaur_cp["{0}".format(cell_8_level + 1)]
    cell_8_cp = randint(cell_8_json['Min CP'], cell_8_json['Max CP'])
    cell_8_range = keep_number_in_range(cell_8_cp, randint(80,110), cell_8_low_json['Min CP'], cell_8_high_json['Max CP'])
    cell_8_value = "CP: {0} Height = {1}".format(cell_8_range,size[randint(0,5)])

    cell_9_level = randint(26, 30)
    cell_9_json = bulbasaur_cp["{0}".format(cell_9_level)]
    cell_9_cp = randint(cell_9_json['Min CP'], cell_9_json['Max CP'])
    cell_9_range = keep_number_in_range(cell_9_cp, cell_9_json['Spread'], cell_9_json['Min CP'],cell_9_json['Max CP'])
    cell_9_value = "CP : {0} ".format(cell_9_range, size[randint(0, 1)], cell_9_json['Stardust'])


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




def generate_default_card():

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


def print_card(bingo_card):
    print("")

    print("|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['1'],bingo_card['2'],bingo_card['3']))
    print("|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['4'], bingo_card['5'], bingo_card['6']))
    print("|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['7'], bingo_card['8'], bingo_card['9']))



def print_card_as_text(bingo_card):

    text = "|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['1'],bingo_card['2'],bingo_card['3'])
    text = text + "\n"+ "|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['4'], bingo_card['5'], bingo_card['6'])
    text = text + "\n" +"|\t{0}\t|\t{1}\t|\t{2}\t|".format(bingo_card['7'], bingo_card['8'], bingo_card['9'])

    return text

print_card(generate_default_card())

print_card(generate_card())

print_card(generate_card())

print_card(generate_card())

print_card(generate_card())

print_card(generate_card())

print_card(generate_card())

print(generate_card())

# print(print_card_as_text(generate_card()))