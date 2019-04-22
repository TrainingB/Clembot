class PokemonForm:
    alphabets = list('abcdefghijklmnopqrstuvwxyz."-!?')

    def __init__(self, text):
        self.text = text
        self.wordmap = dict(map(lambda x: (x if text.count(x) != 0 else None, text.count(x)), self.alphabets))

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