from game import Game

game = Game()

cur_player = "White"

while not game.is_over():
    # TODO: Swap this out for voice commands
    move = input(f"{cur_player} to move: ")
    while not game.make_move(move):
        move = input(f"{cur_player} to move: ")

    print()
    game.display_board()
    print()

    cur_player = "Black" if cur_player == "White" else "White"

print("Game Over!")
