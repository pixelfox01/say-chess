from flask import Blueprint, request, jsonify, abort
from db import db
from models import Game, Move
from sqlalchemy.exc import SQLAlchemyError

game_bp = Blueprint("game", __name__)


@game_bp.route("/start", methods=["POST"])
def start_game():
    data = request.get_json()
    player1_id = data.get("player1_id")
    player2_id = data.get("player2_id")
    current_player = "white"
    game_status = "ongoing"
    new_game = Game(
        player1_id=player1_id,
        player2_id=player2_id,
        current_player=current_player,
        game_status=game_status,
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
        }
    )


@game_bp.route("/move", methods=["POST"])
def make_move():
    data = request.get_json()
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    move = data.get("move")
    move_number = data.get("move_number")

    try:
        with db.session.begin():
            game = Game.query.get_or_404(game_id)

            if player_id not in [game.player1_id, game.player2_id]:
                abort(403, description="Player is not part of the game.")

            new_move = Move(
                game_id=game_id, player_id=player_id, move=move, move_number=move_number
            )
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
