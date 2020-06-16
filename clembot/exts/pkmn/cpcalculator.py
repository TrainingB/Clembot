import math
import os
import json
from discord.ext import commands

import tempfile

from clembot.utilities.utils.utilities import Utilities


# from exts.pokemon import Pokemon


class CPCalculator:
    cpM = {1: 0.094,
           1.5: 0.135137432,
           2: 0.16639787,
           2.5: 0.192650919,
           3: 0.21573247,
           3.5: 0.236572661,
           4: 0.25572005,
           4.5: 0.273530381,
           5: 0.29024988,
           5.5: 0.306057377,
           6: 0.3210876,
           6.5: 0.335445036,
           7: 0.34921268,
           7.5: 0.362457751,
           8: 0.37523559,
           8.5: 0.387592406,
           9: 0.39956728,
           9.5: 0.411193551,
           10: 0.42250001,
           10.5: 0.432926419,
           11: 0.44310755,
           11.5: 0.4530599578,
           12: 0.46279839,
           12.5: 0.472336083,
           13: 0.48168495,
           13.5: 0.4908558,
           14: 0.49985844,
           14.5: 0.508701765,
           15: 0.51739395,
           15.5: 0.525942511,
           16: 0.53435433,
           16.5: 0.542635767,
           17: 0.55079269,
           17.5: 0.558830576,
           18: 0.56675452,
           18.5: 0.574569153,
           19: 0.58227891,
           19.5: 0.589887917,
           20: 0.59740001,
           20.5: 0.604818814,
           21: 0.61215729,
           21.5: 0.619399365,
           22: 0.62656713,
           22.5: 0.633644533,
           23: 0.64065295,
           23.5: 0.647576426,
           24: 0.65443563,
           24.5: 0.661214806,
           25: 0.667934,
           25.5: 0.674577537,
           26: 0.68116492,
           26.5: 0.687680648,
           27: 0.69414365,
           27.5: 0.700538673,
           28: 0.70688421,
           28.5: 0.713164996,
           29: 0.71939909,
           29.5: 0.725571552,
           30: 0.7317,
           30.5: 0.734741009,
           31: 0.73776948,
           31.5: 0.740785574,
           32: 0.74378943,
           32.5: 0.746781211,
           33: 0.74976104,
           33.5: 0.752729087,
           34: 0.75568551,
           34.5: 0.758630378,
           35: 0.76156384,
           35.5: 0.764486065,
           36: 0.76739717,
           36.5: 0.770297266,
           37: 0.7731865,
           37.5: 0.776064962,
           38: 0.77893275,
           38.5: 0.781790055,
           39: 0.78463697,
           39.5: 0.787473578,
           40: 0.79030001
           }


    basestats = {
        "Ralts" : {
            "attack": 79,
            "defense": 59,
            "hp": 99
        },
        "Gallade": {
            "attack": 237,
            "defense": 195,
            "hp": 169
        },
        "Gardevoir": {
            "attack": 237,
            "defense": 195,
            "hp": 169
        },

        "Mudkip": {
            "attack": 126,
            "defense": 93,
            "hp": 137
        },
        "Kyogre": {
            "attack": 270,
            "defense": 251,
            "hp": 182
        },
        "Groudon": {
            "attack": 270,
            "defense": 251,
            "hp": 182
        },
        "Rayquaza": {
            "attack": 284,
            "defense": 170,
            "hp": 191
        },
        "Ho-Oh": {
            "attack": 239,
            "defense": 274,
            "hp": 193
        },
        "Tyranitar": {
            "attack": 251,
            "defense": 212,
            "hp": 200
        },
        "Latios": {
            "attack": 268,
            "defense": 228,
            "hp": 160
        },
        "Metagross": {
            "attack": 257,
            "defense": 247,
            "hp": 160
        },
        "Lugia": {
            "attack": 193,
            "defense": 323,
            "hp": 212
        },
        "Dragonite": {
            "attack": 263,
            "defense": 201,
            "hp": 182
        },
        "Salamence": {
            "attack": 277,
            "defense": 168,
            "hp": 190
        },
        "Entei": {
            "attack": 235,
            "defense": 176,
            "hp": 230
        },
        "Latias": {
            "attack": 228,
            "defense": 268,
            "hp": 160
        },
        "Snorlax": {
            "attack": 190,
            "defense": 190,
            "hp": 320
        },
        "Raikou": {
            "attack": 241,
            "defense": 210,
            "hp": 180
        },
        "Zapdos": {
            "attack": 253,
            "defense": 188,
            "hp": 180
        },
        "Rhydon": {
            "attack": 222,
            "defense": 206,
            "hp": 210
        },
        "Gyarados": {
            "attack": 237,
            "defense": 197,
            "hp": 190
        },
        "Moltres": {
            "attack": 251,
            "defense": 184,
            "hp": 180
        },
        "Blissey": {
            "attack": 129,
            "defense": 229,
            "hp": 510
        },
        "Slaking": {
            "attack": 290,
            "defense": 183,
            "hp": 273
        }
    }

    def __init__(self):
        self.utilities = Utilities()

    @commands.group(pass_context=True, hidden=True, aliases=["calc"])
    async def _calc(self, ctx):

        if ctx.invoked_subcommand is None:
            await self.utilities._send_message(ctx.channel, f"Beep Beep! **{ctx.message.author.display_name}**, **!trade** can be used with various options. See **!beep trade** for more details.")

    @_calc.command(aliases=["cp"])
    async def _calc_cp(self, ctx, pokemon, attack:int, defense:int, hp:int, min_level:int):
        try:
            output_message = ""

            if pokemon.title() not in self.basestats.keys():
                return await self.utilities._send_message(ctx.channel, f"No support for {pokemon}")

            pokemon_stats = self.basestats.get(pokemon.title())

            baseAtk = pokemon_stats['attack']
            baseDef = pokemon_stats['defense']
            baseHp = pokemon_stats['hp']

            for lvl in range(int(min_level), 40 + 1):
                for step in [0.0, 0.5]:
                    if lvl == 40 and step != 0:
                        continue
                    attack_stat = int(baseAtk) + attack
                    defense_stat = int(baseDef) + defense
                    hp_stat = int(baseHp) + hp
                    key = lvl + step
                    cp = max(10, math.floor((attack_stat * math.sqrt(defense_stat) * math.sqrt(hp_stat) * (self.cpM[key] ** 2)) / 10.0))
                    output_message = output_message + "\n" + f"{pokemon} {attack} / {defense} / {hp}  {key}    **{int(cp)}**"

            return await self.utilities._send_message(ctx.channel, f"Here are the CPs by levels: {output_message}")
        except Exception as error:
            return await self.utilities._send_message(ctx.channel, f"{error}")

    @_calc.command(aliases=["iv"])
    async def _calc_iv(self, ctx, required_cp:int, minAtkIV: int, minDefIV: int, minHpIV: int, min_level: int):
        try:
            output_message = ""

            for pokemon in self.basestats:

                pokemon_stats = self.basestats.get(pokemon.title())

                baseAtk = pokemon_stats['attack']
                baseDef = pokemon_stats['defense']
                baseHp = pokemon_stats['hp']


                for lvl in range(min_level, 40 + 1):
                    for step in [0.0, 0.5]:
                        if lvl == 40 and step != 0:
                            continue
                        key = lvl + step
                        minCp = self.calcCp( key, baseAtk, baseDef, baseHp, minAtkIV, minDefIV, minHpIV )
                        maxCp = self.calcCp( key, baseAtk, baseDef, baseHp, 15, 15, 15 )

                        if required_cp < minCp or required_cp > maxCp:
                            continue
                        for atkIV in range(minAtkIV, 16):
                            minCpForAttack = self.calcCp( key, baseAtk, baseDef, baseHp, atkIV, minDefIV, minHpIV )
                            if required_cp < minCpForAttack:
                                break

                            for defIV in range(minDefIV, 16):
                                minCpForAttackAndDefense = self.calcCp(key, baseAtk, baseDef, baseHp, atkIV, defIV, minHpIV)
                                if required_cp < minCpForAttackAndDefense:
                                    break

                                for hpIV in range(minHpIV, 16):
                                    cp = self.calcCp(key, baseAtk, baseDef, baseHp, atkIV, defIV, hpIV)
                                    if cp > required_cp:
                                        break
                                    if cp != required_cp:
                                        continue
                                    output_message = output_message + "\n" + f"**{pokemon}** ({atkIV} / {defIV} / {hpIV}) \t  {key}   \t **{int(cp)}**"

            return await self.utilities._send_message(ctx.channel, f"Here are the CPs by levels: {output_message}")
        except Exception as error :
            return await self.utilities._send_message(ctx.channel, f"{error}")

    def calcCp(self, key, baseAtk, baseDef, baseHp, atkIV, defIV, hpIV):
        attack = int(baseAtk) + atkIV
        defense = int(baseDef) + defIV
        hp = int(baseHp) + hpIV
        return max(10, math.floor((attack * math.sqrt(defense) * math.sqrt(hp) * (self.cpM[key] ** 2)) / 10.0))

    def calculateCP(self, key, level, indAttack, indDefense, indStam):

        if float(level)==int(level):
            level = int(level)
        m = self.cpM[level]

        baseAttack = self.basestats[key]['attack']
        baseDefense = self.basestats[key]['defense']
        baseStam = self.basestats[key]['hp']

        attack = (baseAttack + indAttack) * m
        defense = (baseDefense + indDefense) * m
        stamina = (baseStam + indStam) * m
        return max(10, math.floor(0.1 * math.sqrt(attack * attack * defense * stamina)))





    def pvpIV(self, key: str, level, indAttack, indDefense, indStam):

        m = self.cpM[level]

        baseAttack = self.basestats[key]['attack']
        baseDefense = self.basestats[key]['defense']
        baseStam = self.basestats[key]['hp']

        attack = (baseAttack + indAttack) * m
        defense = (baseDefense + indDefense) * m
        stamina = (baseStam + indStam) * m

        return round(attack * defense * math.floor(stamina))




class PvpIVSpreadCalculator:


    def __init__(self, pkmn):
        self.pkmn = pkmn
        self.cpM = CPCalculator()
        self.initialize_pvp_iv_spread()

    sorted_cp_chart = {}

    def initialize_pvp_iv_spread(self):
        cp_chart = {}
        max_stat = 0
        max_stat_key = None
        for atkiv in range(0,16):
            for defiv in range(0,16):
                for hpiv in range(0,16):
                    level = 16
                    while True:
                        stat_product_at_level = 0
                        cp_at_level = self.cpM.calculateCP(self.pkmn, level, atkiv, defiv, hpiv)
                        if cp_at_level > 1500:
                            prev_level = level - 0.5
                            cp_at_level = self.cpM.calculateCP(self.pkmn, prev_level, atkiv, defiv, hpiv)
                            stat_product_at_level = self.cpM.pvpIV(self.pkmn, prev_level, atkiv, defiv, hpiv)

                            if stat_product_at_level > max_stat:
                                max_stat = stat_product_at_level
                                max_stat_key = f"{prev_level} {atkiv}/{defiv}/{hpiv}"
                            cp_chart[f"{atkiv}/{defiv}/{hpiv}"] = { "level":level, "stat_product" : stat_product_at_level, "cp" : cp_at_level}
                            break

                        level = level + 0.5

        for iv_spread in cp_chart.keys():
            cp_chart[iv_spread].update({"%age": round(cp_chart[iv_spread]["stat_product"]/max_stat * 100,2)})

        self.sorted_cp_chart = dict(sorted(cp_chart.items(), key=lambda k: k[1].get('%age'), reverse=True))

        rank = 0
        for iv_spread in self.sorted_cp_chart:
            self.sorted_cp_chart.get(iv_spread).update({"rank" : rank + 1})
            rank = rank + 1

        #print(self.sorted_cp_chart)

    def find_pvp_rank(self, atkIv, defIv, hpIv):
        key = f"{atkIv}/{defIv}/{hpIv}"
        rank_details = self.sorted_cp_chart.get(key)
        return rank_details



class CachedIVCalculator:

    def __init__(self):
        self._memoized_cp_chart = {}
        self.spread_key_count = 0
        self.baseStats = {}
        self.load_pokedex()
        self.read_spread()



    cpM = {1: 0.094,
           1.5: 0.135137432,
           2: 0.16639787,
           2.5: 0.192650919,
           3: 0.21573247,
           3.5: 0.236572661,
           4: 0.25572005,
           4.5: 0.273530381,
           5: 0.29024988,
           5.5: 0.306057377,
           6: 0.3210876,
           6.5: 0.335445036,
           7: 0.34921268,
           7.5: 0.362457751,
           8: 0.37523559,
           8.5: 0.387592406,
           9: 0.39956728,
           9.5: 0.411193551,
           10: 0.42250001,
           10.5: 0.432926419,
           11: 0.44310755,
           11.5: 0.4530599578,
           12: 0.46279839,
           12.5: 0.472336083,
           13: 0.48168495,
           13.5: 0.4908558,
           14: 0.49985844,
           14.5: 0.508701765,
           15: 0.51739395,
           15.5: 0.525942511,
           16: 0.53435433,
           16.5: 0.542635767,
           17: 0.55079269,
           17.5: 0.558830576,
           18: 0.56675452,
           18.5: 0.574569153,
           19: 0.58227891,
           19.5: 0.589887917,
           20: 0.59740001,
           20.5: 0.604818814,
           21: 0.61215729,
           21.5: 0.619399365,
           22: 0.62656713,
           22.5: 0.633644533,
           23: 0.64065295,
           23.5: 0.647576426,
           24: 0.65443563,
           24.5: 0.661214806,
           25: 0.667934,
           25.5: 0.674577537,
           26: 0.68116492,
           26.5: 0.687680648,
           27: 0.69414365,
           27.5: 0.700538673,
           28: 0.70688421,
           28.5: 0.713164996,
           29: 0.71939909,
           29.5: 0.725571552,
           30: 0.7317,
           30.5: 0.734741009,
           31: 0.73776948,
           31.5: 0.740785574,
           32: 0.74378943,
           32.5: 0.746781211,
           33: 0.74976104,
           33.5: 0.752729087,
           34: 0.75568551,
           34.5: 0.758630378,
           35: 0.76156384,
           35.5: 0.764486065,
           36: 0.76739717,
           36.5: 0.770297266,
           37: 0.7731865,
           37.5: 0.776064962,
           38: 0.77893275,
           38.5: 0.781790055,
           39: 0.78463697,
           39.5: 0.787473578,
           40: 0.79030001,
           40.5: 0.806754}

    filename = 'pvp_iv_spread.json'

    def save_spread(self, override=False):

        if override or (len(self._memoized_cp_chart.keys())) > self.spread_key_count:
            try:
                with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(os.path.join('data')), delete=False) as tf:
                    json.dump(self._memoized_cp_chart, tf)

                    tempname = tf.name

                os.rename(tempname, os.path.join('data', self.filename))
            except Exception as error:
                print(error)


        #
        # try:
        #     os.remove(os.path.join('data', f"{self.filename}.backup"))
        # except OSError as e:
        #     pass
        # try:
        #     os.rename(os.path.join('data', self.filename), os.path.join('data', f"{self.filename}.backup"))
        # except OSError as e:
        #     os.rename(tempname, os.path.join('data', self.filename))
        # return

    def read_spread(self):
        try:
            with open(os.path.join('data', self.filename), "r") as fd:
                self._memoized_cp_chart = json.load(fd)
            self.spread_key_count = len(self._memoized_cp_chart.keys())
            print(f"Read {self.spread_key_count} spreads!")
            return
        except Exception as error:
            print(f"No file found!")

    def load_pokedex(self):
        basestats = {}
        if not self.baseStats:
            with open(os.path.join('data', "pokemon.json"), "r") as fd:
                pokemon_master = json.load(fd)



            for pokedex_info in pokemon_master['pokemon']:
                if pokedex_info['pokedex']['pokemonNum'] not in basestats.keys():
                    basestats.update({f"{pokedex_info['pokedex']['pokemonNum']}":
                        {
                            "attack": pokedex_info['stats']['baseAttack'],
                            "defense": pokedex_info['stats']['baseDefense'],
                            "hp": pokedex_info['stats']['baseStamina']
                        }
                    })

        self.baseStats = basestats

    def print_stats(self):
        print(self.baseStats)


    def calculateCP(self, key: int, level, indAttack, indDefense, indStam):
        try:
            if float(level)==int(level) and level <= 40.0:
                level = int(level)


            m = self.cpM[level]

            baseAttack = self.baseStats[key]['attack']
            baseDefense = self.baseStats[key]['defense']
            baseStam = self.baseStats[key]['hp']

            attack = (baseAttack + indAttack) * m
            defense = (baseDefense + indDefense) * m
            stamina = (baseStam + indStam) * m
            return max(10, math.floor(0.1 * math.sqrt(attack * attack * defense * stamina)))

        except Exception as error:
            print(error)
            return None

    def pvpIV(self, key: int, level, indAttack, indDefense, indStam):

        m = self.cpM[level]

        baseAttack = self.baseStats[key]['attack']
        baseDefense = self.baseStats[key]['defense']
        baseStam = self.baseStats[key]['hp']

        attack = (baseAttack + indAttack) * m
        defense = (baseDefense + indDefense) * m
        stamina = (baseStam + indStam) * m

        return round(attack * defense * math.floor(stamina))




    def initialize_pvp_iv_spread(self, pokedex):
        print(f"========================================initialized pvp spread for {pokedex}")
        sorted_cp_chart = {}
        cp_chart = {}
        max_stat = 0
        max_stat_key = None
        for atkiv in range(0,16):
            for defiv in range(0,16):
                for hpiv in range(0,16):
                    level = 16
                    if self.calculateCP(pokedex, level, atkiv, defiv, hpiv) > 1500:
                        level = 10

                    while True and level <= 40:
                        stat_product_at_level = 0

                        cp_at_level = self.calculateCP(pokedex, level, atkiv, defiv, hpiv)
                        stat_product_at_level = self.pvpIV(pokedex, level, atkiv, defiv, hpiv)
                        # print(f"{atkiv} {defiv} {hpiv} at {level} = {cp_at_level}")
                        if cp_at_level > 1500:
                            prev_level = level - 0.5
                            cp_at_level = self.calculateCP(pokedex, prev_level, atkiv, defiv, hpiv)
                            stat_product_at_level = self.pvpIV(pokedex, prev_level, atkiv, defiv, hpiv)
                            if stat_product_at_level > max_stat:
                                max_stat = stat_product_at_level
                                max_stat_key = f"{prev_level} {atkiv}/{defiv}/{hpiv}"

                            cp_chart[f"{atkiv}/{defiv}/{hpiv}"] = { "level":prev_level, "stat_product" : stat_product_at_level, "cp" : cp_at_level}
                            break

                        if level == 40.0:
                            max_stat = stat_product_at_level
                            cp_chart[f"{atkiv}/{defiv}/{hpiv}"] = {"level": level, "stat_product": stat_product_at_level, "cp": cp_at_level}

                        level = level + 0.5

        for iv_spread in cp_chart.keys():
            cp_chart[iv_spread].update({"%age": round(cp_chart[iv_spread]["stat_product"]/max_stat * 100, 2)})

        sorted_cp_chart = dict(sorted(cp_chart.items(), key=lambda k: k[1].get('%age'), reverse=True))


        rank = 0
        for iv_spread in sorted_cp_chart:
            sorted_cp_chart.get(iv_spread).update({"rank" : rank + 1})
            rank = rank + 1

        self._memoized_cp_chart.update({f"{pokedex}": sorted_cp_chart})


    def find_pvp_rank(self, pokedex, atkIv, defIv, hpIv):

        if not self._memoized_cp_chart.__contains__(f"{pokedex}"):
            self.initialize_pvp_iv_spread(f"{pokedex}")

        key = f"{atkIv}/{defIv}/{hpIv}"
        rank_details = self._memoized_cp_chart.get(f"{pokedex}").get(key)
        return rank_details


def main():

    cpC = CachedIVCalculator()
    # galladeIVSpread = PvpIVSpreadCalculator(387)

    for level in range(1, 41):

        iv_0_cp = cpC.calculateCP('273', level, 0, 0, 0)
        iv_100_cp = cpC.calculateCP('273', level, 15, 15, 15)
        # iv_0_pvprank = galladeIVSpread.find_pvp_rank(0,0,0)

        print(f"{level} - {iv_100_cp} ")

    #
    # myC = CachedIVCalculator()
    # myC.print_stats()
    #



if __name__ == '__main__':
    print(f"[{os.path.basename(__file__)}] main() started.")
    main()
    print(f"[{os.path.basename(__file__)}] main() finished.")