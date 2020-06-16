__author__ = 'Olivier Evers'


from PySide2 import QtWidgets, QtCore
from random import randint
from functools import partial


class CELL:
    COORDINATES = 'coord'
    IS_BOMB = 'bomb'
    HINT = 'hint'  # number of neighbour bombs
    BUTTON = 'button'


class MinesweeperGame:
    """
    Minesweeper game logic.
    """
    def __init__(self, grid_width, grid_height, number_of_bombs):
        """Create game and populate with bombs"""
        self.width = grid_width
        self.height = grid_height

        self._grid = []
        self._known_cells_coordinates = []  # (x, y)
        self._number_of_cells_to_uncover = (
            grid_width * grid_height - number_of_bombs)
        assert self._number_of_cells_to_uncover > 0

        # Create grid:
        for y in range(grid_height):
            self._grid.append([])
            for x in range(grid_width):
                self._grid[y].append({
                    CELL.COORDINATES: (x, y),
                    CELL.HINT: 0,
                    CELL.IS_BOMB: False})

        # Randomly place bombs:
        self.bombs = []
        while len(self.bombs) < number_of_bombs:
            x, y = randint(0, grid_width - 1), randint(0, grid_height - 1)
            if not self.cell(x, y)[CELL.IS_BOMB]:
                self.cell(x, y)[CELL.IS_BOMB] = True
                self.bombs.append((x, y))

        # Set hint value for each cell (count number of neighbour bombs):
        for x, y in self.bombs:
            for cell in self._neighbour_cells(x, y):
                cell[CELL.HINT] += 1

    def __repr__(self):
        lines = []
        for line in self._grid:
            str_line = []
            for cell in line:
                if cell[CELL.IS_BOMB]:
                    str_line.append('X')
                else:
                    str_line.append(str(cell[CELL.HINT] or '-'))
            lines.append(' '.join(str_line))
        return '\n'.join(lines)

    def cell(self, x, y):
        """Readability counts."""
        return self._grid[y][x]

    def _neighbour_cells(self, x, y):
        """Iterate over the 8 (or less) cells around specified cell."""
        for u in [-1, 0, 1]:
            for v in [-1, 0, 1]:
                # dont return self:
                if (u, v) == (0, 0):
                    continue
                nx, ny = x + u, y + v
                # dont return negative index (other side of board):
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    yield self.cell(nx, ny)

    def play(self, x, y):
        """
        If a bomb is clicked, returns False.
        Otherwise returns list of (coordinates, number_of_neighbour_bombs) but
            only for unknown cells so far.
        """
        # If cell is bomb, return False:
        if self.cell(x, y)[CELL.IS_BOMB]:
            return False  # game lost

        # List of hints as list of ((x, y), hint):
        hints = []
        cells_to_check = [self.cell(x, y)]
        while cells_to_check:
            cell = cells_to_check.pop()
            coordinates = cell[CELL.COORDINATES]
            if coordinates in self._known_cells_coordinates:
                continue
            hints.append((coordinates, cell[CELL.HINT]))
            self._known_cells_coordinates.append(coordinates)
            if cell[CELL.HINT] == 0:
                # Add neighbours to cells to check (if unknown):
                for neighbour_cell in self._neighbour_cells(*coordinates):
                    cells_to_check.append(neighbour_cell)

        # Check if game is won:
        known_cells_count = len(self._known_cells_coordinates)
        if known_cells_count == self._number_of_cells_to_uncover:
            return True  # game won
        else:
            return hints


class Button(QtWidgets.QPushButton):
    """QPushButton with 'rightClicked' signal."""
    rightClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(Button, self).__init__(*args, **kwargs)

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            self.rightClicked.emit()


class MinesweeperGameUI(QtWidgets.QWidget, MinesweeperGame):
    def __init__(self, width=10, height=10, mines=7, parent=None):
        QtWidgets.QWidget.__init__(self)
        MinesweeperGame.__init__(self, width, height, mines)

        self.setWindowTitle('Minesweeper')

        self.game_over = False

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        for x in range(width):
            for y in range(height):
                button = Button(' ', maximumWidth=24)
                # button.setStyleSheet('background-color: white')
                button.clicked.connect(partial(self._update_game, x, y))
                button.released.connect(partial(button.setDown, True))
                button.rightClicked.connect(partial(self._set_flag, x, y))
                # Use game dictionnary to store buttons references:
                self.cell(x, y)[CELL.BUTTON] = button
                layout.addWidget(button, x, y)

    def _show_win_pannel(self):
        QtWidgets.QWidget().setLayout(self.layout())
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        button = QtWidgets.QPushButton('you won !')
        button.clicked.connect(sys.exit)
        layout.addWidget(button)

    def _set_flag(self, x, y):
        flag_text = u'\u2691'
        button = self.cell(x, y)[CELL.BUTTON]
        current_text = button.text().strip()
        if current_text == flag_text:
            self.cell(x, y)[CELL.BUTTON].setText('')
        elif not current_text:
            self.cell(x, y)[CELL.BUTTON].setText(flag_text)

    def _update_game(self, x, y):
        if self.game_over:
            return

        # Get hints:
        hints = self.play(x, y)
        # Win/Lose:
        if hints is True:
            self._show_win_pannel()
            self.game_over = True
            return
        elif hints is False:
            self.game_over = True
            self.cell(x, y)[CELL.BUTTON].setStyleSheet('background-color:red')
            for x, y in self.bombs:
                self.cell(x, y)[CELL.BUTTON].setText(u'\U0001F4A3')
            for line in self._grid:
                for cell in line:
                    cell[CELL.BUTTON].clicked.connect(sys.exit)
            return
        # Update board:
        for (x, y), hint in hints:
            button = self.cell(x, y)[CELL.BUTTON]
            label = str(hint) if hint else ' '
            button.setText(label)
            button.setDown(True)


if __name__ == '__main__':
    import sys
    try:
        width, height, bombs = [int(a) for a in sys.argv[-3:]]
    except (ValueError, IndexError):
        print('Using default size and bomb count: 10x10 with 7 bombs.')
        width, height, bombs = 10, 10, 7
    app = QtWidgets.QApplication(sys.argv)
    game = MinesweeperGameUI(width, height, bombs)
    game.show()
    sys.exit(app.exec_())
