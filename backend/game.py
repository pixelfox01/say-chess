import chess


class Game:
    def __init__(self) -> None:
        self.board = chess.Board()
        self.cur_player = 0

    def make_move(self, move_san: str) -> bool:
        try:
            self.board.push_san(move_san)
            self.cur_player = 1 if self.cur_player == 0 else 0
            return True
        except chess.InvalidMoveError:
            print("Move is syntactically invalid!\n")
            return False
        except chess.IllegalMoveError:
            print("Illegal move!!!\n")
            return False
        except chess.AmbiguousMoveError:
            print("Move is ambiguous! Please try again...\n")
            return False

    def is_over(self) -> bool:
        return (
            self.board.is_checkmate()
            or self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.can_claim_threefold_repetition()
            or self.board.can_claim_fifty_moves()
        )

    def display_board(self) -> None:
        print(self.board)
