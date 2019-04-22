import csv
import os
import random

from .BingoCardImage import BingoCardImage


class BingoCardGenerator:

    def __init__(self, grid_size = 3, file_name=None):
        self.grid_size = grid_size
        # self.bingo_options = self._read_file(file_name)

    def _read_file(self, file_name):
        script_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(script_path, file_name)
        bingo_file = open(file_path, 'rt', encoding="utf8")
        reader = csv.reader(bingo_file)
        bingo_options = list(reader)
        return bingo_options

    def generate_board(self, user_name, bingo_card = None, template_file=None):
        board_layout = self.generate_board_layout(bingo_card)
        bingo_board = BingoCardImage(board_layout)
        board_image = bingo_board.generate_board_image(user_name=user_name, template_file=template_file)

        return board_image

    def generate_old_board(self, user_name):
        board_layout = self.generate_board_layout()
        bingo_board = bingo_board_cog(board_layout)
        board_image = bingo_board.generate_board_image(user_name=user_name)

        return board_image


    def generate_board_layout(self, bingo_card = None):
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

    def generate_old_board_layout(self):
        randRange = range(0,len(self.bingo_options))

        option_pool = random.sample(randRange, self.grid_size * self.grid_size)

        board = []
        row = []

        for option in option_pool:
            if len(row) == self.grid_size:
                board.append(row)
                row = []
            row.append(self.bingo_options[option])
        board.append(row)

        return board
