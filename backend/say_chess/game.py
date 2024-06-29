from flask import Blueprint, request, jsonify, abort
from say_chess.db import get_db
import chess

bp = Blueprint("game", __name__)


@bp.route("/start", methods=["POST"])
def start_game():
    data = request.get_json()
    player1_id = data.get("player1_id")
    player2_id = data.get("player2_id")

    db = get_db()
    cursor = db.cursor()

    ongoing_game_query = """
        SELECT id FROM game
        WHERE game_status = %s
        AND (player1_id = %s OR player2_id = %s OR player2_id = %s OR player2_id = %s)
        LIMIT 1
    """
    cursor.execute(
        ongoing_game_query, ("ongoing", player1_id, player1_id, player2_id, player2_id)
    )
    ongoing_game = cursor.fetchone()

    if ongoing_game:
        cursor.close()
        abort(403, description="One of the players is already in a game!")

    game_status = "ongoing"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    insert_query = """
        INSERT INTO game (player1_id, player2_id, game_status, fen)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """

    cursor.execute(insert_query, (player1_id, player2_id, game_status, starting_fen))
    new_game_id = cursor.fetchone()[0]
    db.commit()
    cursor.close()

    return jsonify({"message": "Game started", "game_id": new_game_id})


@bp.route("/<int:game_id>", methods=["GET"])
def get_game_details(game_id):
    db = get_db()
    with db.cursor() as cursor:
        query = """
            SELECT id, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE id = %s
        """
        cursor.execute(query, (game_id,))
        game = cursor.fetchone()
        if game is None:
            cursor.close()
            abort(404, description=f"Game with ID {game_id} not found!")

        return jsonify(
            {
                "game_id": game[0],
                "player1_id": game[1],
                "player2_id": game[2],
                "started_at": game[3],
                "ended_at": game[4],
                "game_status": game[5],
                "fen": game[6],
            }
        )


@bp.route("/<int:game_id>/move", methods=["POST"])
def make_move(game_id):
    data = request.get_json()
    move = data.get("move")

    db = get_db()
    with db.cursor() as cursor:
        game_query = """
            SELECT id, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE id = %s
        """
        cursor.execute(game_query, (game_id,))
        game = cursor.fetchone()

        if game is None:
            abort(404, description=f"Could not find game with ID {game_id}!")

        game_status = game[5]
        if game_status != "ongoing":
            abort(403, description="Game has already ended!")

        game_fen = game[6]

        board = chess.Board(game_fen)
        try:
            board.push_san(move)
        except chess.InvalidMoveError:
            abort(403, description="Move is invalid!")
        except chess.IllegalMoveError:
            abort(403, description="Move is illegal!")
        except chess.AmbiguousMoveError:
            abort(403, description="Ambiguous move!")

        max_move_num_query = """
            SELECT COALESCE(MAX(move_number), 0)
            FROM "move"
            WHERE game_id = %s
        """
        cursor.execute(max_move_num_query, (game_id,))
        max_move = cursor.fetchone()[0]

        move_number = max_move + 1
        cur_fen = board.fen()

        new_move_query = """
            INSERT INTO "move" (game_id, move_number, move, fen)
            VALUES (
                %s, %s, %s, %s
            )
        """
        cursor.execute(new_move_query, (game_id, move_number, move, cur_fen))

        update_game_fen_query = """
            UPDATE game
            SET fen = %s
            WHERE id = %s
            RETURNING id, fen
        """
        cursor.execute(update_game_fen_query, (cur_fen, game_id))

        if board.is_game_over():
            cursor.execute("SELECT fen FROM game WHERE id = %s", (game_id,))
            result = cursor.fetchone()
            if result is None:
                abort(404, description=f"Could not find game with ID {game_id}")

            cur_player = result[0].split()[1]
            end_game_query = """
                UPDATE game
                SET game_status = %s
                WHERE id = %s
            """

            # TODO: Add other draw condition checks
            if board.is_checkmate():
                game_status = "white" if cur_player == "b" else "black"
            elif board.is_stalemate():
                game_status = "draw_stalemate"
            elif board.is_insufficient_material():
                game_status = "draw_insufficient"

            cursor.execute(end_game_query, (game_status, game_id))

        db.commit()

        return jsonify({"message": "Move processed!", "game_status": game_status})


@bp.route("/<int:game_id>/abort", methods=["POST"])
def abort_game(game_id):
    db = get_db()
    with db.cursor() as cursor:
        game_query = """
            SELECT id, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE id = %s
        """
        cursor.execute(game_query, (game_id,))
        game = cursor.fetchone()
        if game is None:
            abort(404, description=f"Could not find game with id {game_id}")

        game_status = game[5]
        if game_status != "ongoing":
            abort(403, description="Game has already ended!")

        moves_query = """
            SELECT id
            FROM "move"
            WHERE game_id = %s
        """

        cursor.execute(moves_query, (game_id,))
        if cursor.fetchone() is not None:
            abort(403, description="Game has already started, cannot abort!")

        game_abort_query = """
            UPDATE game
            SET game_status = %s, ended_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, game_status, ended_at
        """
        cursor.execute(game_abort_query, ("aborted", game_id))
        result = cursor.fetchone()

        if result is None:
            abort(404, description="Failed to update game status!")

        db.commit()

        return jsonify(
            {
                "result": f"Game {result[0]} ended at {result[2]}",
                "game_status": result[1],
            }
        )


@bp.route("/<int:game_id>/draw", methods=["POST"])
def draw_game(game_id):
    db = get_db()
    with db.cursor() as cursor:
        game_query = """
            SELECT id, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE id = %s
        """
        cursor.execute(game_query, (game_id,))
        game = cursor.fetchone()
        if game is None:
            abort(404, description=f"Could not find game with id {game_id}")

        game_status = game[5]
        if game_status != "ongoing":
            abort(403, description="Game has already ended!")

        game_end_query = """
            UPDATE game
            SET game_status = %s, ended_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, game_status, ended_at
        """
        cursor.execute(game_end_query, ("draw_agreement", game_id))
        result = cursor.fetchone()

        if result is None:
            abort(404, description="Failed to update game status!")

        db.commit()

        return jsonify(
            {
                "result": f"Game {result[0]} ended at {result[2]}",
                "game_status": result[1],
            }
        )


