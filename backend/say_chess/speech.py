from chess import Board
from flask import Blueprint, request
from google.cloud import speech
from say_chess.utils import (
    ERROR_CODES,
    create_error_response,
    create_success_response,
)
from fuzzywuzzy import process


ERROR_CODES.update(
    {
        "NO_FILE_PART": {"code": 1009, "message": "No file part in the request!"},
        "NO_SELECTED_FILE": {"code": 1010, "message": "No selected file!"},
        "INVALID_FILE_TYPE": {"code": 1011, "message": "Invalid file type!"},
        "INVALID_MOVE_TRANSCRIPT": {
            "code": 1012,
            "message": "Could not convert transcript to a valid move!",
        },
    }
)

ALLOWED_EXTENSIONS = {"wav"}

bp = Blueprint("speech", __name__)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def san_to_spoken(san_move):
    piece_names = {
        "K": "King",
        "Q": "Queen",
        "R": "Rook",
        "N": "Knight",
        "B": "Bishop",
        "": "",
    }

    if san_move == "O-O":
        return "Castle short"
    elif san_move == "O-O-O":
        return "Castle long"

    spoken = ""
    if san_move[0] in piece_names:
        spoken += piece_names[san_move[0]] + " "
        san_move = san_move[1:]

    if "=" in san_move:
        coord, promotion = san_move.split("=")
        return f"{coord} {piece_names[promotion]}"

    return spoken + "".join(san_move)


def get_speech_context_from_board(board):
    legal_moves = list(board.legal_moves)
    print([board.san(move) for move in legal_moves])
    spoken_moves = [san_to_spoken(board.san(move)) for move in legal_moves]
    return speech.SpeechContext(phrases=spoken_moves, boost=20)


@bp.route("/transcribe-move", methods=["POST"])
def transcribe_move():
    if "file" not in request.files:
        create_error_response("NO_FILE_PART", 400)

    file = request.files["file"]

    if file.filename == "":
        create_error_response("NO_SELECTED_FILE", 400)

    if file and allowed_file(file.filename):
        audio_content = file.read()

        fen = request.form.get(
            "fen",
            Board(
                "r1bqkb1r/ppp1nppp/3p1n2/4p3/2BNP3/2N5/PPPP1PPP/R1BQK2R w KQkq - 0 6"
            ).fen(),
        )
        board = Board(fen)

        speech_context = get_speech_context_from_board(board)
        transcript = transcribe_gcs(audio_content, speech_context)

        san_move = get_move_from_transcription(transcript, board)
        if san_move is None:
            return create_error_response("INVALID_MOVE_TRANSCRIPT", 403)

        response = {"transcript": transcript, "san_move": san_move}

        return create_success_response(response, "Move transcribed successfully")
    else:
        create_error_response("INVALID_FILE_TYPE", 400)


def transcribe_gcs(audio_content, speech_context):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        audio_channel_count=1,
        speech_contexts=[speech_context],
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript

    return transcript.lower()


def get_move_from_transcription(transcription, board):
    legal_moves = [board.san(move) for move in board.legal_moves]
    spoken_moves = [san_to_spoken(move).lower() for move in legal_moves]

    best_match = process.extractOne(transcription, spoken_moves)

    if best_match and best_match[1] > 80:
        return legal_moves[spoken_moves.index(best_match[0])]
    return None
