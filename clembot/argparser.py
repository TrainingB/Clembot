

def process_join(text, length, delimiter=","):

    if text and delimiter:
        return text[:text.rfind(delimiter, 0 , length)] + " and more." if len(text) > length else text
    return text

def test():

    text_to_test = "charmander, charmeleon, \n-charizard, bulbasaur, ivysaur, \n-venusaur, farfetch'd\n, kang-askhan, \ncorsola, h-eracross, \nmagikarp-shiny, gyarados-shiny"

    # print(process_join(text_to_test, 70, delimiter="-"))
    #
    # print(process_join(text_to_test, 120, delimiter="-"))
    #
    # print(process_join(text_to_test, 400, delimiter="-"))
    #
    # print(process_join(text_to_test, 0, delimiter="-"))

    print("----------------------------------")

    print(process_join(text_to_test, 120, delimiter="\n"))

    print(process_join(text_to_test, 120, None))

    print(process_join(None, 0))

