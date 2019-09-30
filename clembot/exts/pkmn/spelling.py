# Sourced from
# http://norvig.com/spell-correct.html
# Use set_dictionary to set the dictionary of words

import re
from collections import Counter


class SpellHelper:

    words = []
    n = None


    @classmethod
    def set_dictionary(cls, word_list):
        cls.words = Counter(word_list)
        cls.n = sum(cls.words.values())


    @classmethod
    def all_words(cls, text):
        return re.findall(r'\w+', text.upper())


    @classmethod
    def P(cls, word):
        "Probability of `word`."
        if not cls.n:
            return 0

        return cls, cls.words[word] / cls.n


    @classmethod
    def correction(cls, word):
        "Most probable spelling correction for word."
        return max(cls.candidates(word), key=cls.P)


    @classmethod
    def candidates(cls, word):
        "Generate possible spelling corrections for word."
        return (cls.known([word]) or cls.known(cls.edits1(word)) or cls.known(cls.edits2(word)) or [word])


    @classmethod
    def known(cls, words):
        "The subset of `words` that appear in the dictionary of WORDS."
        if not cls.words:
            return None

        return set(w.upper() for w in words if w.upper() in cls.words)

    @classmethod
    def edits1(cls, word):
        "All edits that are one edit away from `word`."
        letters    = 'abcdefghijklmnopqrstuvwxyz'
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
        inserts    = [L + c + R               for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)


    @classmethod
    def edits2(cls, word):
        "All edits that are two edits away from `word`."
        return (e2 for e1 in cls.edits1(word) for e2 in cls.edits1(e1))

def main():
    words = ['BIDOOF', 'CHERRIM-SUNNY', 'TURTWIG', 'MISMAGIUS', 'SHUPPET', 'GLISCOR', 'KRICKETUNE', 'RATTATA', 'SHIELDON', 'SEVIPER', 'ELECTRODE', 'WEEZING', 'DRIFLOON', 'MUK', 'DEOXYS-SPEED',
             'GLALIE', 'ALOLA-DIGLETT', 'ALOLAN-DIGLETT', 'DIGLETT-ALOLA', 'DIGLETT-ALOLAN', 'ABRA', 'ALOLA-RAICHU', 'ALOLAN-RAICHU', 'RAICHU-ALOLA', 'RAICHU-ALOLAN', 'ALOLA-RATICATE',
             'ALOLAN-RATICATE', 'RATICATE-ALOLA', 'RATICATE-ALOLAN', 'ALOLA-MEOWTH', 'ALOLAN-MEOWTH', 'MEOWTH-ALOLA', 'MEOWTH-ALOLAN', 'ALOLA-MUK', 'ALOLAN-MUK', 'MUK-ALOLA', 'MUK-ALOLAN',
             'ALOLA-GOLEM', 'ALOLAN-GOLEM', 'GOLEM-ALOLA', 'GOLEM-ALOLAN', 'ALOLA-DUGTRIO', 'ALOLAN-DUGTRIO', 'DUGTRIO-ALOLA', 'DUGTRIO-ALOLAN', 'ALOLA-SANDSLASH', 'ALOLAN-SANDSLASH',
             'SANDSLASH-ALOLA', 'SANDSLASH-ALOLAN', 'ALOLA-PERSIAN', 'ALOLAN-PERSIAN', 'PERSIAN-ALOLA', 'PERSIAN-ALOLAN', 'ALOLA-RATTATA', 'ALOLAN-RATTATA', 'RATTATA-ALOLA', 'RATTATA-ALOLAN',
             'ALOLA-VULPIX', 'ALOLAN-VULPIX', 'VULPIX-ALOLA', 'VULPIX-ALOLAN', 'ALOLA-GRAVELER', 'ALOLAN-GRAVELER', 'GRAVELER-ALOLA', 'GRAVELER-ALOLAN', 'ALOLA-MAROWAK', 'ALOLAN-MAROWAK',
             'MAROWAK-ALOLA', 'MAROWAK-ALOLAN', 'ALOLA-NINETALES', 'ALOLAN-NINETALES', 'NINETALES-ALOLA', 'NINETALES-ALOLAN', 'ALOLA-GRIMER', 'ALOLAN-GRIMER', 'GRIMER-ALOLA', 'GRIMER-ALOLAN',
             'ALOLA-SANDSHREW', 'ALOLAN-SANDSHREW', 'SANDSHREW-ALOLA', 'SANDSHREW-ALOLAN', 'ALOLA-GEODUDE', 'ALOLAN-GEODUDE', 'GEODUDE-ALOLA', 'GEODUDE-ALOLAN', 'ALOLA-EXEGGUTOR', 'ALOLAN-EXEGGUTOR',
             'EXEGGUTOR-ALOLA', 'EXEGGUTOR-ALOLAN', 'LOMBRE', 'CARVANHA', 'WIGGLYTUFF', 'BIBAREL', 'ARCEUS-ICE', 'KRICKETOT', 'BEEDRILL', 'HAPPINY', 'MOTHIM', 'AERODACTYL', 'SHELGON', 'MACHOKE',
             'MANECTRIC', 'GIRATINA-ORIGIN', 'RAMPARDOS', 'GENGAR', 'EXPLOUD', 'FLAREON', 'SHUCKLE', 'BLAZIKEN', 'ARCEUS-DRAGON', 'NIDORINA', 'WOBBUFFET', 'JIGGLYPUFF', 'GIRAFARIG', 'CROBAT',
             'DRAGONITE', 'ARCEUS-POISON', 'RATICATE', 'ARCEUS-FAIRY', 'TEDDIURSA', 'PIDGEOTTO', 'CUBONE', 'CASTFORM-RAINY', 'LINOONE', 'ZAPDOS', 'DELIBIRD', 'MUNCHLAX', 'YANMEGA', 'LATIOS', 'MUDKIP',
             'BELLOSSOM', 'DRAGONAIR', 'BURMY-SANDY', 'FEEBAS', 'RALTS', 'CARNIVINE', 'LOUDRED', 'DUSKULL', 'BANETTE', 'TYRANITAR', 'REMORAID', 'WORMADAM-TRASH', 'PERSIAN', 'CRESSELIA', 'BURMY-TRASH',
             'LEDIAN', 'SHAYMIN-LAND', 'CROAGUNK', 'MANTINE', 'BURMY', 'KABUTO', 'MANKEY', 'LUXIO', 'MOLTRES', 'HORSEA', 'INFERNAPE', 'SLOWKING', 'ARCEUS-GROUND', 'TORCHIC', 'POLIWAG', 'OMANYTE',
             'XATU', 'ARTICUNO', 'MAGBY', 'SKARMORY', 'AZURILL', 'POLIWHIRL', 'FEAROW', 'GLIGAR', 'STARAPTOR', 'GIBLE', 'SWABLU', 'WAILMER', 'FARFETCHD', 'HONCHKROW', 'CHIMECHO', 'VOLBEAT',
             'URSARING', 'CHANSEY', 'LICKILICKY', 'STARYU', 'ARCEUS-ELECTRIC', 'LUNATONE', 'METANG', 'MEWTWO', 'KRABBY', 'ARBOK', 'PICHU', 'UXIE', 'JUMPLUFF', 'BLASTOISE', 'MIGHTYENA', 'LICKITUNG',
             'GRAVELER', 'TOXICROAK', 'SHELLOS-WEST-SEA', 'MURKROW', 'SHELLOS-EAST-SEA', 'PSYDUCK', 'DRAPION', 'BUNEARY', 'CHERRIM-OVERCAST', 'SPHEAL', 'OMASTAR', 'CATERPIE', 'POOCHYENA', 'TORTERRA',
             'REGISTEEL', 'FLAAFFY', 'NIDORAN-MALE', 'WORMADAM', 'CHARMANDER', 'YANMA', 'AMBIPOM', 'AZELF', 'WHISCASH', 'MONFERNO', 'CAMERUPT', 'QUILAVA', 'IGGLYBUFF', 'LUXRAY', 'FERALIGATR',
             'SLOWBRO', 'BUIZEL', 'MARILL', 'ARON', 'DODRIO', 'GOLBAT', 'ANORITH', 'TENTACOOL', 'LARVITAR', 'ODDISH', 'KIRLIA', 'PINSIR', 'COMBEE', 'FURRET', 'CRAWDAUNT', 'MAGMAR', 'SNOVER',
             'RELICANTH', 'MANAPHY', 'MANTYKE', 'PRINPLUP', 'PHIONE', 'ARCEUS-FLYING', 'LUDICOLO', 'ELECTRIKE', 'PINECO', 'CYNDAQUIL', 'HIPPOPOTAS', 'CLAMPERL', 'VIGOROTH', 'HERACROSS', 'DODUO',
             'ARCANINE', 'GROWLITHE', 'CHIMCHAR', 'DUGTRIO', 'SEALEO', 'LILEEP', 'DUSTOX', 'QUAGSIRE', 'HARIYAMA', 'MIME-JR', 'CROCONAW', 'GULPIN', 'KINGDRA', 'SWINUB', 'MARSHTOMP', 'GROVYLE',
             'ROTOM', 'BURMY-PLANT', 'SHIFTRY', 'GASTRODON-WEST-SEA', 'FINNEON', 'GRUMPIG', 'GARCHOMP', 'TRAPINCH', 'GRIMER', 'ENTEI', 'PILOSWINE', 'DROWZEE', 'CLEFABLE', 'PALKIA', 'ARMALDO',
             'PORYGON2', 'TORKOAL', 'PRIMEAPE', 'ALAKAZAM', 'SLAKING', 'HEATRAN', 'COMBUSKEN', 'WEAVILE', 'UNOWN', 'BUTTERFREE', 'PROBOPASS', 'MR-MIME', 'SLOWPOKE', 'BARBOACH', 'MEDITITE', 'CRANIDOS',
             'KANGASKHAN', 'NUMEL', 'GARDEVOIR', 'SUNKERN', 'AMPHAROS', 'HIPPOWDON', 'SCIZOR', 'MELTAN', 'OCTILLERY', 'WEEPINBELL', 'SEADRA', 'VILEPLUME', 'ROTOM-MOW', 'GROTLE', 'GOLEM', 'MEOWTH',
             'ELEKID', 'POLIWRATH', 'DIALGA', 'SMOOCHUM', 'PIPLUP', 'REGICE', 'PIKACHU', 'CRADILY', 'KECLEON', 'TYROGUE', 'ARCEUS-STEEL', 'PURUGLY', 'LUGIA', 'CHIKORITA', 'ROTOM-FAN', 'LANTURN',
             'ELECTIVIRE', 'PLUSLE', 'VESPIQUEN', 'SPINDA', 'STANTLER', 'EXEGGCUTE', 'SNORUNT', 'HITMONTOP', 'GABITE', 'NOSEPASS', 'TANGELA', 'VOLTORB', 'SCEPTILE', 'TYPHLOSION', 'SANDSLASH',
             'BELDUM', 'GRANBULL', 'JIRACHI', 'BULBASAUR', 'BONSLY', 'SKIPLOOM', 'SEEDOT', 'CASTFORM-SUNNY', 'SHROOMISH', 'DITTO', 'DUNSPARCE', 'PARAS', 'STARAVIA', 'WYNAUT', 'CASCOON', 'PARASECT',
             'MEGANIUM', 'CHATOT', 'MILOTIC', 'KINGLER', 'LEAFEON', 'WOOPER', 'HO-OH', 'VIBRAVA', 'SMEARGLE', 'FLOATZEL', 'SPIRITOMB', 'WORMADAM-SANDY', 'CHARIZARD', 'MINUN', 'TAUROS', 'HOUNDOOM',
             'LATIAS', 'ROTOM-FROST', 'KABUTOPS', 'GASTRODON-EAST-SEA', 'CACTURNE', 'RIOLU', 'MAKUHITA', 'CACNEA', 'ZUBAT', 'DUSKNOIR', 'SLAKOTH', 'ELECTABUZZ', 'SABLEYE', 'REGIGIGAS', 'GOLDEEN',
             'ABSOL', 'GLAMEOW', 'MAMOSWINE', 'SURSKIT', 'ARCEUS-DARK', 'DEOXYS', 'FORRETRESS', 'CHERUBI', 'DRIFBLIM', 'STARLY', 'KAKUNA', 'BRELOOM', 'NIDOKING', 'ONIX', 'SQUIRTLE', 'WARTORTLE',
             'SALAMENCE', 'MAGCARGO', 'ILLUMISE', 'EXEGGUTOR', 'CLAYDOL', 'SENTRET', 'SHINX', 'CHERRIM', 'HYPNO', 'TOGEKISS', 'TOTODILE', 'JYNX', 'SPEAROW', 'MISDREAVUS', 'DRATINI', 'BRONZONG',
             'ARCEUS-BUG', 'GALLADE', 'ZANGOOSE', 'VENUSAUR', 'EKANS', 'MELMETAL', 'HITMONCHAN', 'SHAYMIN', 'BRONZOR', 'DONPHAN', 'JOLTEON', 'SHAYMIN-SKY', 'RAIKOU', 'NIDORINO', 'DEWGONG', 'HUNTAIL',
             'DELCATTY', 'PORYGON-Z', 'CHINCHOU', 'VAPOREON', 'NIDOQUEEN', 'REGIROCK', 'GROUDON', 'AIPOM', 'BAGON', 'ARCEUS-FIRE', 'RHYHORN', 'SHARPEDO', 'WAILORD', 'VULPIX', 'FROSLASS', 'WALREIN',
             'EMPOLEON', 'RAPIDASH', 'LOTAD', 'HOPPIP', 'SCYTHER', 'HITMONLEE', 'ZIGZAGOON', 'ROSELIA', 'PORYGON', 'KOFFING', 'SANDSHREW', 'CHARMELEON', 'ARCEUS-PSYCHIC', 'ARCEUS-ROCK', 'RAICHU',
             'BUDEW', 'ROTOM-WASH', 'AZUMARILL', 'SEAKING', 'SHELLDER', 'MAGIKARP', 'CELEBI', 'SKORUPI', 'CLEFFA', 'GYARADOS', 'BEAUTIFLY', 'BELLSPROUT', 'TOGEPI', 'ARCEUS-GHOST', 'CORSOLA',
             'PUPITAR', 'NOCTOWL', 'ABOMASNOW', 'MILTANK', 'GOLDUCK', 'BALTOY', 'TOGETIC', 'DIGLETT', 'PACHIRISU', 'LUMINEON', 'RAYQUAZA', 'METAGROSS', 'MAGMORTAR', 'CORPHISH', 'TANGROWTH', 'NATU',
             'NINCADA', 'WHISMUR', 'SLUGMA', 'LUVDISC', 'MEW', 'RHYPERIOR', 'NIDORAN-FEMALE', 'KYOGRE', 'MAWILE', 'TREECKO', 'ROSERADE', 'WINGULL', 'CASTFORM', 'SNEASEL', 'SWELLOW', 'BLISSEY',
             'EEVEE', 'SNORLAX', 'NINETALES', 'SNUBBULL', 'AGGRON', 'ARCEUS-GRASS', 'GLOOM', 'TENTACRUEL', 'QWILFISH', 'GEODUDE', 'GLACEON', 'TAILLOW', 'BAYLEEF', 'LOPUNNY', 'VENOMOTH', 'WURMPLE',
             'LAIRON', 'CHINGLING', 'ROTOM-HEAT', 'DUSCLOPS', 'FLYGON', 'POLITOED', 'DARKRAI', 'PONYTA', 'LUCARIO', 'GOREBYSS', 'CLEFAIRY', 'MAROWAK', 'SKITTY', 'IVYSAUR', 'SKUNTANK', 'SHELLOS',
             'KADABRA', 'MAGNEMITE', 'ARCEUS-FIGHTING', 'PELIPPER', 'ESPEON', 'MESPRIT', 'SPINARAK', 'CLOYSTER', 'MAGNEZONE', 'DEOXYS-ATTACK', 'LEDYBA', 'CASTFORM-SNOWY', 'ALTARIA', 'STEELIX',
             'SHEDINJA', 'ARCEUS', 'WORMADAM-PLANT', 'PHANPY', 'NINJASK', 'PIDGEY', 'WEEDLE', 'NUZLEAF', 'UMBREON', 'MACHOP', 'TROPIUS', 'SWALOT', 'STUNKY', 'PIDGEOT', 'MEDICHAM', 'BASTIODON',
             'HOOTHOOT', 'GASTLY', 'SUNFLORA', 'ARIADOS', 'LAPRAS', 'GIRATINA', 'GASTRODON', 'MASQUERAIN', 'SWAMPERT', 'STARMIE', 'SUDOWOODO', 'SUICUNE', 'HAUNTER', 'MAREEP', 'HOUNDOUR', 'VENONAT',
             'METAPOD', 'VICTREEBEL', 'SILCOON', 'DEOXYS-DEFENSE', 'MACHAMP', 'ARCEUS-WATER', 'SOLROCK', 'RHYDON', 'SPOINK', 'SEEL', 'MAGNETON']

    SpellHelper.set_dictionary(words)

    print(SpellHelper.correction('VENASAUR'))



main()