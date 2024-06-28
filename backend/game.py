from flask import Blueprint, request, jsonify, abort
from db import db
from models import Game, Move
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, func
import chess

game_bp = Blueprint("game", __name__)


@game_bp.route("/start", methods=["POST"])
def start_game():
    data = request.get_json()
    player1_id = data.get("player1_id")
    player2_id = data.get("player2_id")

    ongoing_game = Game.query.filter(
        Game.game_status == "ongoing",
        or_(
            Game.player1_id == player1_id,
            Game.player2_id == player1_id,
            Game.player1_id == player2_id,
            Game.player2_id == player2_id,
        ),
    ).first()

    if ongoing_game:
        abort(403, description="One of the players is already in a game.")
        # return jsonify({"error": "One of the players is already in a game."}, 400)

    game_status = "ongoing"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    new_game = Game(
        player1_id=player1_id,
        player2_id=player2_id,
        game_status=game_status,
        fen=starting_fen,
    )
    db.session.add(new_game)
    db.session.commit()
    return jsonify({"message": "Game started", "game_id": new_game.id})


@game_bp.route("/<int:game_id>", methods=["GET"])
def get_game_details(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify(
        {
            "game_id": game.id,
            "player1_id": game.player1_id,
            "player2_id": game.player2_id,
            "started_at": game.started_at,
            "ended_at": game.ended_at,
            "current_player": game.current_player,
            "game_result": game.game_result,
            "fen": game.fen,
        }
    )


@game_bp.route("/move", methods=["POST"])
def make_move():
    data = request.get_json()
    game_id = data.get("game_id")
    move = data.get("move")

    try:
        with db.session.begin():
            game = Game.query.get_or_404(game_id)

            if game.game_status != "ongoing":
                abort(403, description="Game has already ended.")

            board = chess.Board(game.fen)
            try:
                board.push_san(move)
            except chess.InvalidMoveError:
                abort(403, description="Move is invalid!")
            except chess.IllegalMoveError:
                abort(403, description="Move is illegal!")
            except chess.AmbiguousMoveError:
                abort(403, description="Ambiguous move!")

            current_max_move_number = (
                db.session.query(func.max(Move.move_number))
                .filter_by(game_id=game_id)
                .scalar()
                or 0
            )
            move_number = current_max_move_number + 1

            new_move = Move(game_id=game_id, move=move, move_number=move_number)

            game.fen = board.fen()
            db.session.add(new_move)
            db.session.commit()

        return jsonify({"status": "Move processed!"})

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, description="An error occurred while processing the move.")


@game_bp.route("/<int:game_id>/status", methods=["GET"])
def check_game_status(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify({"status": game.game_status})


@game_bp.route("/<int:game_id>/end", methods=["POST"])
def end_game(game_id):
    data = request.get_json()
    game_result = data.get("result")
    try:
        with db.session.begin():
            game = Game.query.get_or_404(game_id)
            if game.game_status != "ongoing":
                abort(403, description="Game has already ended!")
            game.game_status = game_result
            game.ended_at = db.func.current_timestamp()
            db.session.commit()

        return jsonify({"status": "Game ended", "result": game_result})

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, description="An error occurred while processing the move.")
