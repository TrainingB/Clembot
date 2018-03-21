import datetime
import time
from datetime import timedelta
import calendar



def parse_arguments( text ):

    args = text.lower().split()

    # remove first command name
    del args[0]


    params = {}

    if len(args) > 0:
        pokemon_name = args[0]




