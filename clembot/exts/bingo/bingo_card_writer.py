import os
import textwrap
from random import randint

from PIL import Image, ImageDraw, ImageFont


class BingoCardWriter:

    @staticmethod
    def generate_board(user_name, bingo_card = None, template_file=None):
        board_layout = BingoCardWriter.generate_board_layout(bingo_card)
        board_image = BingoCardWriter.generate_board_image(board_layout, user_name=user_name, template_file=template_file)
        return board_image


    @staticmethod
    def generate_board_layout(bingo_card = None):
        board = []
        row = []

        row.append(bingo_card['1'])
        row.append(bingo_card['2'])
        row.append(bingo_card['3'])

        board.append(row)

        row = []

        row.append(bingo_card['4'])
        row.append(bingo_card['5'])
        row.append(bingo_card['6'])

        board.append(row)

        row = []

        row.append(bingo_card['7'])
        row.append(bingo_card['8'])
        row.append(bingo_card['9'])

        board.append(row)

        return board


    @staticmethod
    def generate_board_image(bingo_board,  file_name='bingo', user_name='anon', template_file="dec2019.png"):

        try:
            script_path = os.path.dirname(os.path.realpath(__file__))
            dir_path = os.path.join(script_path)
            file_path = os.path.join(script_path, "templates")
            y_position = 190
            cell_width =  162
            cell_height = 110
            margin = 10
            font = ImageFont.truetype(os.path.join(script_path,"fonts","Helvetica-Bold.ttf"), 24, encoding="unic")
            special_font = ImageFont.truetype(os.path.join(script_path, "fonts","DejaVuSansMono.ttf"), 40, encoding="unic")
            small_font = ImageFont.truetype(os.path.join(script_path, "fonts","Helvetica-Bold.ttf"), 20, encoding="unic")

            path  = os.path.join(file_path, template_file)
            print(path)

            canvas = Image.open(os.path.join(file_path, template_file))
            draw = ImageDraw.Draw(canvas)

            colors = ['white','white','white','white','white','white','white','white','white']
            counter = 0
            for row in bingo_board:
                x_position = 25
                for cell in row:

                    if len(cell) == 1:
                        text = textwrap.fill(cell[0], 12)
                        draw.text((x_position, y_position), text, colors[counter], small_font)
                    else:
                        text = textwrap.fill(cell[0], 12)
                        draw.text((x_position, y_position - 15 ), text, colors[counter], small_font)

                        if len(cell[1]) == 1:
                            text = textwrap.fill(cell[1], 12)
                            draw.text((x_position + 55, y_position + 10 ), text, colors[counter], special_font)
                        else:
                            text = textwrap.fill(cell[1], 12)
                            draw.text((x_position + 22 , y_position + 20), text, colors[counter], small_font)
                    counter=counter+1

                    x_position += cell_width
                y_position += cell_height

            rand_file_int = randint(0, 1333337);
            file_name = os.path.join(dir_path,'bingo_boards', file_name + '_' + str(user_name) + '_' + str(rand_file_int) + '.png')
            canvas.save(file_name, "PNG", quality=20, optimize=True)


        except Exception as error:
            Logger.error(f"{traceback.format_exc()}")
        return file_name

