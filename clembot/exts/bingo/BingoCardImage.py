from PIL import Image,ImageDraw,ImageFont
import textwrap
from random import randint
import os


class BingoCardImage:

    def __init__(self, bingo_board):
        self.bingo_board = bingo_board

    def generate_board_image(self, file_name='bingo', user_name='anon', template_file="december.png"):

        try:
            script_path = os.path.dirname(os.path.realpath(__file__))
            dir_path = script_path# os.path.join(script_path, "data")
            file_path = os.path.join(script_path, "templates")
            y_position = 190
            cell_width =  162
            cell_height = 110
            margin = 10
            font = ImageFont.truetype(os.path.join(script_path,"fonts","Helvetica-Bold.ttf"), 24, encoding="unic")
            special_font = ImageFont.truetype(os.path.join(script_path, "fonts","DejaVuSansMono.ttf"), 40, encoding="unic")
            small_font = ImageFont.truetype(os.path.join(script_path,"fonts","Helvetica-Bold.ttf"), 20, encoding="unic")

            path  = os.path.join(file_path, template_file)
            print(f"generate_board_image() : Template from : {path}")

            canvas = Image.open(os.path.join(file_path, template_file))
            draw = ImageDraw.Draw(canvas)

            colors = ['white','white','white','white','white','white','white','white','white']
            counter = 0
            for row in self.bingo_board:
                x_position = 25
                for cell in row:

                    if len(cell) == 1:
                        text = textwrap.fill(cell[0], 12)
                        draw.text((x_position, y_position), text, colors[counter], font)
                    else:
                        text = textwrap.fill(cell[0], 12)
                        draw.text((x_position, y_position - 15 ), text, colors[counter], font)

                        if len(cell[1]) == 1:
                            text = textwrap.fill(cell[1], 12)
                            draw.text((x_position + 55, y_position + 10 ), text, colors[counter], special_font)
                        else:
                            text = textwrap.fill(cell[1], 12)
                            draw.text((x_position + 12 , y_position + 20), text, colors[counter], small_font)
                    counter=counter+1

                    x_position += cell_width
                y_position += cell_height

            rand_file_int = randint(0, 1333337);
            file_name = os.path.join(dir_path,'bingo_boards', file_name + '_' + str(user_name) + '_' + str(rand_file_int) + '.png')
            canvas.save(file_name, "PNG", quality=20, optimize=True)


        except Exception as error:
            print(error)
        return file_name

