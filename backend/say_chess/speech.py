import os
from flask import Blueprint, abort, flash, jsonify, request
from werkzeug.utils import secure_filename
from google.cloud import speech


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


@bp.route("/transcribe-move", methods=["GET", "POST"])
def transcribe_move():
    if "file" not in request.files:
        abort(400, description="No file part in the request!")

    file = request.files["file"]

    if file.filename == "":
        abort(400, description="No selected file!")

    if file and allowed_file(file.filename):
        audio_content = file.read()

        transcript = transcribe_gcs(audio_content)

        san_move = get_move_from_transcription(transcript)
        if san_move is None:
            abort(
                403,
                {
                    "transcript": transcript,
                    "message": "Could not convert transcript to a valid move!",
                },
            )

        return jsonify({"transcript": transcript, "san_move": san_move})
    else:
        abort(400, description="Invalid file type!")


@bp.route("/upload-test", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file found!")
            return "Ok"

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file!")
            return "Ok"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join("./say_chess/", filename))
            return "Ok"

    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """


def transcribe_gcs(audio_content):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
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
    if piece not in san_mappings.keys():
        return None

    coord = split_transcription[1]
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
