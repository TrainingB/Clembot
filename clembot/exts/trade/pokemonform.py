from clembot.exts.pkmn.pokemon import PokemonCache


class PokemonForm:

    alphabets = list('abcdefghijklmnopqrstuvwxyz."-!?')

    available_pokemon_forms = []

    def __init__(self, text):
        self.text = text
        self.wordmap = dict(map(lambda x: (x if text.count(x) != 0 else None, text.count(x)), self.alphabets))

    @classmethod
    async def load_forms(cls, bot):
        try:
            print("load_forms()")
            pokemon_forms = []
            pokemon_trade_forms_tbl = bot.dbi.table('pokemon_trade_form')
            pokemon_trade_forms_query = pokemon_trade_forms_tbl.query().select('pokemon_form')
            list_of_pokemon_forms = await pokemon_trade_forms_query.get()
            for pokemon_form_rcrd in list_of_pokemon_forms:
                pokemon_forms.append(dict(pokemon_form_rcrd)['pokemon_form'])
            cls.available_pokemon_forms = pokemon_forms
        except Exception as error:
            print(error)

    @classmethod
    async def add(cls, dbi, poke_form):
        pokemon_form_to_save = {
            "pokemon_form": poke_form
        }

        table = dbi.table('pokemon_trade_form')
        table.insert(**pokemon_form_to_save)
        await table.insert.commit()
        cls.available_pokemon_forms.append(poke_form)


    @classmethod
    async def remove(cls, dbi, poke_form):
        pokemon_form_to_delete = {
            "pokemon_form": poke_form
        }

        table = dbi.table('pokemon_trade_form')
        query = table.query().where(**pokemon_form_to_delete)
        await query.delete()
        cls.available_pokemon_forms.remove(poke_form)

    @classmethod
    def is_valid(cls, search_for):
        return True if search_for.lower() in PokemonForm.available_pokemon_forms or PokemonCache.to_pokemon(
            search_for) is not None else False

    @classmethod
    def extract_valid_pokemon_forms(cls, list_of_pokemon):
        pokemon_list = [e.lower() for e in list_of_pokemon if PokemonForm.is_valid(e.lower())]
        # pokemon_list.extend([ctx.bot.pkmn_info['pokemon_list'][int(e)-1] for e in list_of_pokemon if e.isdigit()])
        return pokemon_list

    def __str__(self):
        return self.text

    def __eq__(self, other):
        other_hash = dict(map(lambda x: (x if other.text.count(x) != 0 else None, other.text.count(x)), self.alphabets))
        return self.wordmap == other_hash

    def hash(self):
        return self.wordmap

def print_hash(text):
    print(hash(text))


def hash(text):
    hash = dict(map(lambda x : (x if text.count(x) != 0 else None ,text.count(x) ), alphabets))

    return hash

def test():

    a = PokemonForm('unown-!')
    b = PokemonForm('unown-?')
    c = PokemonForm('mr. mime-glasses-shiny-')

    print(a.hash())
    print(b.hash())
    print(c.hash())
    print(a.__eq__(b))
    print(b.__eq__(c))

def main():
    test()

#main()