from flask import jsonify, make_response

ERROR_CODES = {}


def create_success_response(data, message="Success"):
    response = {"message": message, "data": data}
    return jsonify(response)


def create_error_response(error_key: str, status_code: int):
    error_info = ERROR_CODES[error_key]
    response = jsonify(
        {"error": {"code": error_info["code"], "message": error_info["message"]}}
    )
    return make_response(response, status_code)
