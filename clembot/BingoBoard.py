from PIL import Image,ImageDraw,ImageFont
import textwrap
from random import randint
import os


class BingoBoard:

    def __init__(self, bingo_board):
        self.bingo_board = bingo_board

    def generate_board_image(self, file_name='bingo', user_name='anon'):
        script_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(script_path, file_name)
        y_position = 150
        cell_width =  190
        cell_height = 130
        margin = 10
        font = ImageFont.truetype(os.path.join(script_path,"fonts/Helvetica-Bold.ttf"), 28, encoding="unic")
        canvas = Image.open(os.path.join(script_path, "bingo_template.png"))
        draw = ImageDraw.Draw(canvas)

        for row in self.bingo_board:
            x_position = 20
            for cell in row:
                text = textwrap.fill(cell, 12)
                draw.text((x_position, y_position), text, 'black', font)
                x_position += cell_width
            y_position += cell_height

        rand_file_int = randint(0, 1333337);
        file_name = os.path.join(script_path,'bingo_boards', file_name + '_' + user_name + '_' + str(rand_file_int) + '.png')
        canvas.save(file_name, "PNG")

        return file_name
