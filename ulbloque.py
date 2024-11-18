from getkey import *
import sys

def sorted_insert(t: list[list], e: list):
    """ Finds the right index to insert e, alphabetic order"""
    i = 0
    while (i < len(t) and e[0] > t[i][0]):
        i += 1;
    t.insert(i, e)

def parse_game(game_file_path: str) -> dict:
    """Parses game*.txt and returns game data"""
    with open(game_file_path) as f:
        game_data = f.readlines()
    grid = [line.rstrip() for line in game_data[1:len(game_data)-2]]
    max_moves = int(game_data[-1].rstrip())
    f.close()

    game = {
        'width': len(grid[0])-2,
        'height': len(grid),
        'max_moves': max_moves,
        'cars': []
    }
    # scanning grid
    memo = set()
    tmp_cars = []
    for y in range(game['height']):
        line = grid[y].replace('|', '')
        for x in range(game['width']):
            if x < len(line):
                char = line[x]
                if char.isalpha() and char not in memo:
                    memo.add(char) # found new car

                    # check horizontal size
                    size_h = 1
                    while (x+size_h)<game['width'] and line[x+size_h]==char:
                            size_h += 1
                    # check vertical size
                    size_v = 1
                    while (y+size_v)<game['height'] and grid[y+size_v].replace('|','')[x]==char:
                        size_v += 1

                    # add car to cars with correct orientation
                    if size_h > size_v:
                        car = [char, (x,y), 'h', size_h]
                    elif size_v > size_h:
                        car = [char, (x,y), 'v', size_v]
                    sorted_insert(tmp_cars, car)
    game['cars'] = [car[1:] for car in tmp_cars]
    return game

def get_car_color(index: int) -> str:
    """Return the color code for a car based on its index."""
    colors = [
        '\u001b[47m',  # white (car A)
        '\u001b[41m',  # red
        '\u001b[42m',  # green
        '\u001b[43m',  # yellow
        '\u001b[44m',  # blue
        '\u001b[45m',  # magenta
        '\u001b[46m'   # cyan
    ]
    return colors[0] if index == 0 else colors[1 + (index - 1) % 6]

def get_game_str(game: dict, current_move_number: int) -> str:
    """Return a string representation of the current game state."""

    # empty grid
    grid = [['.'] * game['width'] for _ in range(game['height'])]

    # place cars on grid with colors
    for i, car in enumerate(game['cars']):
        pos, orientation, size = car
        x, y = pos
        color = get_car_color(i)
        letter = chr(65 + i)

        # fill all positions occupied by the car
        dx = size if orientation == 'h' else 1
        dy = size if orientation == 'v' else 1
        for ny in range(y, y + dy):
            for nx in range(x, x + dx):
                grid[ny][nx] = f"{color}{letter}\u001b[0m"

    # prep header
    separator = "=" * (game['width'] * 3 + 4)
    border = "+" + "-" * (game['width'] * 3) + "+"
    moves_left = game['max_moves'] - current_move_number

    # prep output
    output = [
        separator,
        f"Moves: {current_move_number}/{game['max_moves']} ({moves_left} left)",
        separator,
        border
    ]

    # A's position
    a_y = game['cars'][0][0][1]  # y position of car A

    # add each row
    for y in range(game['height']):
        row = "|"
        for x in range(game['width']):
            row += f" {grid[y][x]} "

        # if this is A's row, don't add the right border
        if y == a_y:
            row = row.rstrip()
            output.append(f"{row}  ")  # two spaces for the opening
        else:
            output.append(f"{row}|")

    output.append(border)
    return "\n".join(output)

def move_car(game: dict, car_index: int, direction: str) -> bool:
    """Move a car in the specified direction if possible."""

    # check if car index is valid
    if 0 > car_index >= len(game['width']):
        return False

    car = game['cars'][car_index]
    pos, orientation, size = car
    x, y = pos

    # check movement validity depending on car's orientation
    if orientation == 'h' and direction not in ['LEFT', 'RIGHT']:
        return False
    if orientation == 'v' and direction not in ['UP', 'DOWN']:
        return False

    # new position
    new_x, new_y = x, y
    if direction == 'LEFT':
        new_x -= 1
    elif direction == 'RIGHT':
        new_x += 1
    elif direction == 'UP':
        new_y -= 1
    else:
        new_y += 1

    # check boundaries
    if orientation == 'h':
        if new_x < 0 or new_x + size > game['width']:
            return False
    else:
        if new_y < 0 or new_y + size > game['height']:
            return False

    # check for collisions
    for i, other_car in enumerate(game['cars']):
        if i == car_index:
            continue

        other_pos, other_orientation, other_size = other_car
        other_x, other_y = other_pos

        # all positions for both cars
        new_car_positions = set()
        other_car_positions = set()

        # moving car new positions
        if orientation == 'h':
            new_car_positions = {(new_x + j, y) for j in range(size)}
        else:
            new_car_positions = {(x, new_y + j) for j in range(size)}

        # other car positions
        if other_orientation == 'h':
            other_car_positions = {(other_x + j, other_y) for j in range(other_size)}
        else:
            other_car_positions = {(other_x, other_y + j) for j in range(other_size)}

        # check for overlap
        if new_car_positions & other_car_positions:
            return False
    # move valid, update position
    game['cars'][car_index][0] = (new_x, new_y)
    return True

def is_win(game: dict) -> bool:
    """Check if the game is won (car A has reached the right edge)."""
    if not game['cars']:
        return False

    # first car is always A
    car_a = game['cars'][0]
    pos, orientation, size = car_a

    # car A must be horizontal and reach the right edge
    res = orientation == 'h' and (pos[0] + size) >= game['width']
    return res

def play_game(game: dict) -> int:
    """Main game loop."""
    selected_car = None
    current_moves = 0

    def clear_screen():
        print("\033[H\033[J", end="")

    while current_moves < game['max_moves']:
        clear_screen()
        print(get_game_str(game, current_moves))

        if selected_car is None:
            print("\nSelect car (A-Z) or press ESC to quit:")
            key = getkey().upper()
            if key == 'ESCAPE':
                return 2  # abandoned

            # accept only key of size 1 letter
            if key.isalpha() and len(key) == 1:
                car_index = ord(key) - ord('A')
                if 0 <= car_index < len(game['cars']):
                    selected_car = car_index
        else:
            print(f"\nMove car {chr(65 + selected_car)} (arrow keys) or press any other key to cancel:")
            key = getkey()
            if key in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                move = move_car(game, selected_car, key)
                if move:
                    current_moves += 1
                if is_win(game):
                    clear_screen()
                    print(get_game_str(game, current_moves))
                    print(f"\nCongratulations! You've won in {current_moves} moves!")
                    return 0  # victory!
            selected_car = None

    clear_screen()
    print(get_game_str(game, current_moves))
    print("\nGame Over! You've run out of moves.")
    return 1  # defeat (out of moves)

def get_usage_str() -> str:
   """Return the usage string for the game."""
   return """
Usage: python3 ulbloque.py <game_file>

Controls:
 - Letters (A-Z): Select a car
 - Arrow keys: Move selected car
 - ESC: Quit game

Examples:
 python3 ulbloque.py game1.txt
 python3 ulbloque.py puzzle2.txt
"""


if __name__ == '__main__':
    moves = 0
    if len(sys.argv) != 2:
        print(get_usage_str())
        exit(1)
    game = parse_game(sys.argv[1])
    result = play_game(game)

