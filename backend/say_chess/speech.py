from chess import Move
from flask import Blueprint, jsonify, request
from google.cloud import speech
from say_chess.utils import (
    ERROR_CODES,
    create_error_response,
    create_success_response,
)

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


PIECES = ["King", "Queen", "Rook", "Bishop", "Knight", "Pawn"]
FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANKS = ["1", "2", "3", "4", "5", "6", "7", "8"]

ALL_MOVES = []
ALL_COORDS = []
for piece in PIECES:
    for rank in RANKS:
        for file in FILES:
            move = f"{piece} {file}{rank}"
            coord = f"{file}{rank}"
            ALL_MOVES.append(move)
            ALL_COORDS.append(coord)


ALL_MOVES.extend(["Castle short", "Castle long", "Castle kingside", "Castle queenside"])
ALL_COORDS.extend(["long", "short", "kingside", "queenside"])


SPEECH_CONTEXT = speech.SpeechContext(phrases=ALL_MOVES)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


bp = Blueprint("speech", __name__)


@bp.route("/transcribe-move", methods=["POST"])
def transcribe_move():
    if "file" not in request.files:
        create_error_response("NO_FILE_PART", 400)

    file = request.files["file"]

    if file.filename == "":
        create_error_response("NO_SELECTED_FILE", 400)

    if file and allowed_file(file.filename):
        audio_content = file.read()

        transcript = transcribe_gcs(audio_content)

        san_move = get_move_from_transcription(transcript)
        if san_move is None:
            create_error_response("INVALID_MOVE_TRANSCRIPT", 403)

        response = {"transcript": transcript, "san_move": san_move}

        return create_success_response(response, "Move transcribed successfully")
    else:
        create_error_response("INVALID_FILE_TYPE", 400)


def transcribe_gcs(audio_content):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        audio_channel_count=1,
        speech_contexts=[SPEECH_CONTEXT],
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript

    return transcript


def get_move_from_transcription(transcription):
    """
    Get move in SAN notation from gcs transcription.
    Transcribed move text should be in the form: <piece> <file>rank
    """
    san_mappings = {
        "king": "K",
        "queen": "Q",
        "rook": "R",
        "bishop": "B",
        "knight": "N",
        "pawn": "",
        "castle": "o-o",
    }

    transcription = transcription.lower()
    split_transcription = transcription.split()

    if len(split_transcription) == 1 and split_transcription[0] in ALL_COORDS:
        return split_transcription[0]

    if len(split_transcription) != 2:
        return None

    piece = split_transcription[0]
    coord = split_transcription[1]

    if piece in [
        "a8",
        "b8",
        "c8",
        "d8",
        "e8",
        "f8",
        "g8",
        "h8",
    ] and coord in PIECES.remove("Pawn"):
        return f"{piece}={coord}"

    if piece not in san_mappings.keys():
        return None

    if coord not in ALL_COORDS:
        return None

    san_move = transcription

    if piece == "castle":
        if coord == "short" or coord == "kingside":
            return "O-O"
        elif coord == "long" or coord == "queenside":
            return "O-O-O"

    san_move = san_move.replace(piece, san_mappings[piece])
    san_move = san_move.replace(" ", "")

    return san_move
