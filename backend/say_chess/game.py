from flask import Blueprint, make_response, request, jsonify
from werkzeug.exceptions import HTTPException
from say_chess.db import get_db
from say_chess.utils import create_success_response, create_error_response, ERROR_CODES
import chess

ERROR_CODES.update(
    {
        "PLAYER_IN_GAME": {
            "code": 1001,
            "message": "One of the players is already in a game!",
        },
        "INVALID_MOVE": {"code": 1002, "message": "Move is invalid!"},
        "ILLEGAL_MOVE": {"code": 1003, "message": "Move is illegal!"},
        "AMBIGUOUS_MOVE": {"code": 1004, "message": "Ambiguous move!"},
        "GAME_NOT_FOUND": {"code": 1005, "message": "Game not found!"},
        "GAME_ENDED": {"code": 1006, "message": "Game has already ended!"},
        "GAME_STARTED": {
            "code": 1007,
            "message": "Game has already started, cannot abort!",
        },
        "UPDATE_FAILED": {"code": 1008, "message": "Failed to update game status!"},
    }
)

bp = Blueprint("game", __name__)


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(401)
@bp.errorhandler(500)
def handle_error(error):
    response = jsonify(
        {
            "error": {
                "type": error.name,
                "message": error.description,
                "code": error.code,
            }
        }
    )
    response.status_code = error.code
    return response


@bp.errorhandler(Exception)
def handle_exception(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    response = jsonify(
        {"error": {"type": "Internal Server Error", "message": str(e), "code": code}}
    )
    return make_response(response, code)


@bp.route("/start", methods=["POST"])
def start_game():
    data = request.get_json()
    player1_id = data.get("player1_id")
    player2_id = data.get("player2_id")

    print()

    db = get_db()
    cursor = db.cursor()

    player1_game_query = """
        SELECT uid FROM game
        WHERE game_status = %s
        AND (player1_id = %s OR player2_id = %s)
    """
    player2_game_query = """
        SELECT uid FROM game
        WHERE game_status = %s
        AND (player1_id = %s OR player2_id = %s)
    """

    cursor.execute(player1_game_query, ("ongoing", player1_id, player1_id))
    player1_game = cursor.fetchone()

    cursor.execute(player2_game_query, ("ongoing", player2_id, player2_id))
    player2_game = cursor.fetchone()

    if player1_game or player2_game:
        return create_error_response(
            "PLAYER_IN_GAME",
            403,
            {"player1_game": player1_game, "player2_game": player2_game},
        )

    game_status = "ongoing"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    insert_query = """
        INSERT INTO game (player1_id, player2_id, game_status, fen)
        VALUES (%s, %s, %s, %s)
        RETURNING uid
    """

    cursor.execute(insert_query, (player1_id, player2_id, game_status, starting_fen))
    new_game_id = cursor.fetchone()[0]
    db.commit()
    cursor.close()

    return create_success_response(new_game_id, "Game started successfully")


@bp.route("/<uuid:game_uid>", methods=["GET"])
def get_game_details(game_uid):
    db = get_db()
    cursor = db.cursor()
    try:
        query = """
            SELECT  uid, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE uid = %s
        """
        cursor.execute(query, (str(game_uid),))
        game = cursor.fetchone()
        if game is None:
            return create_error_response("GAME_NOT_FOUND", 404, {"id": game_uid})

        response_data = {
            "uid": game[0],
            "player1_id": game[1],
            "player2_id": game[2],
            "started_at": game[3],
            "ended_at": game[4],
            "game_status": game[5],
            "fen": game[6],
        }

        return create_success_response(
            response_data, "Game details retrieved successfully"
        )
    finally:
        cursor.close()


@bp.route("/<uuid:game_uid>/status", methods=["GET"])
def game_status(game_uid):
    db = get_db()
    cursor = db.cursor()
    try:
        game_query = """
            SELECT game_status
            FROM game
            WHERE uid = %s
        """
        cursor.execute(game_query, (str(game_uid),))
        game = cursor.fetchone()

        if game is None:
            return create_error_response("GAME_NOT_FOUND", 404, {"id": game_uid})

        return create_success_response(game[0], "Game status retrieved successfully")
    finally:
        cursor.close()


@bp.route("/<uuid:game_uid>/move", methods=["POST"])
def make_move(game_uid):
    data = request.get_json()
    san_move = data.get("move")

    db = get_db()
    cursor = db.cursor()
    try:
        game_query = """
            SELECT id, uid, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE uid = %s
        """
        cursor.execute(game_query, (str(game_uid),))
        game = cursor.fetchone()

        if game is None:
            return create_error_response("GAME_NOT_FOUND", 404, {"id": game_uid})

        game_status = game[6]
        if game_status != "ongoing":
            return create_error_response("GAME_ENDED", 403, {"game": game})

        game_fen = game[7]

        board = chess.Board(game_fen)
        try:
            uci_move = board.parse_san(san_move)
            board.push_san(san_move)
        except chess.InvalidMoveError:
            return create_error_response("INVALID_MOVE", 403, {"move": san_move})
        except chess.IllegalMoveError:
            return create_error_response("ILLEGAL_MOVE", 403, {"move": san_move})
        except chess.AmbiguousMoveError:
            return create_error_response("AMBIGUOUS_MOVE", 403, {"move": san_move})

        max_move_num_query = """
            SELECT COALESCE(MAX(move_number), 0)
            FROM "move"
            WHERE game_id = %s
        """
        game_id = game[0]
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
        cursor.execute(new_move_query, (game_id, move_number, san_move, cur_fen))

        update_game_fen_query = """
            UPDATE game
            SET fen = %s
            WHERE id = %s
            RETURNING uid, fen
        """
        cursor.execute(update_game_fen_query, (cur_fen, game_id))

        if board.is_game_over():
            cursor.execute("SELECT fen FROM game WHERE id = %s", (game_id,))
            result = cursor.fetchone()
            if result is None:
                return create_error_response("GAME_NOT_FOUND", 404)

            cur_player = result[0].split()[1]
            end_game_query = """
                UPDATE game
                SET game_status = %s, ended_at = CURRENT_TIMESTAMP
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

        response = {"uci_move": uci_move, "game_status": game_status, "fen": cur_fen}

        return create_success_response(response, "Move processed successfully")
    finally:
        cursor.close()


@bp.route("/<uuid:game_uid>/abort", methods=["POST"])
def abort_game(game_uid):
    db = get_db()
    cursor = db.cursor()
    try:
        game_query = """
            SELECT id, uid, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE uid = %s
        """
        cursor.execute(game_query, (str(game_uid),))
        game = cursor.fetchone()
        if game is None:
            return create_error_response("GAME_NOT_FOUND", 404, {"id": game_uid})

        game_status = game[6]
        if game_status != "ongoing":
            return create_error_response("GAME_ENDED", 403, {"game": game})

        moves_query = """
            SELECT id
            FROM "move"
            WHERE game_id = %s
        """
        game_id = game[0]
        cursor.execute(moves_query, (game_id,))
        if cursor.fetchone() is not None:
            return create_error_response("GAME_STARTED", 403, {"game": game})

        game_abort_query = """
            UPDATE game
            SET game_status = %s, ended_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING uid, player1_id, player2_id, started_at, ended_at, game_status, fen
        """
        cursor.execute(game_abort_query, ("aborted", game_id))
        result = cursor.fetchone()

        if result is None:
            return create_error_response("UPDATE_FAILED", 500, {"id": game_uid})

        db.commit()

        response_data = {
            "id": result[0],
            "player1_id": result[1],
            "player2_id": result[2],
            "started_at": result[3],
            "ended_at": result[4],
            "game_status": result[5],
            "fen": result[6],
        }

        return create_success_response(response_data, "Game aborted successfully")
    finally:
        cursor.close()


@bp.route("/<uuid:game_uid>/draw", methods=["POST"])
def draw_game(game_uid):
    db = get_db()
    cursor = db.cursor()
    try:
        game_query = """
            SELECT id, uid, player1_id, player2_id, started_at, ended_at, game_status, fen
            FROM game
            WHERE uid = %s
        """
        cursor.execute(game_query, (str(game_uid),))
        game = cursor.fetchone()
        if game is None:
            return create_error_response("GAME_NOT_FOUND", 404, {"id": game_uid})

        game_status = game[6]
        if game_status != "ongoing":
            return create_error_response("GAME_ENDED", 403, {"game": game})

        game_end_query = """
            UPDATE game
            SET game_status = %s, ended_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING uid, player1_id, player2_id, started_at, ended_at, game_status, fen
        """
        game_id = game[0]
        cursor.execute(game_end_query, ("draw_agreement", game_id))
        result = cursor.fetchone()

        if result is None:
            return create_error_response("UPDATE_FAILED", 500, {"game": game})

        db.commit()

        response_data = {
            "id": result[0],
            "player1_id": result[1],
            "player2_id": result[2],
            "started_at": result[3],
            "ended_at": result[4],
            "game_status": result[5],
            "fen": result[6],
        }

        return create_success_response(response_data, "Game drawn successfully")
    finally:
        cursor.close()
