from flask import jsonify, make_response

ERROR_CODES = {
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


def create_success_response(data, message="Success"):
    response = {"message": message, "data": data}
    return jsonify(response)


def create_error_response(error_key):
    error_info = ERROR_CODES[error_key]
    response = jsonify(
        {"error": {"code": error_info["code"], "message": error_info["message"]}}
    )
    return make_response(response, 403)
