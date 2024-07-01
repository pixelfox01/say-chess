import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from . import db, game, speech


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)
    cors = CORS(app)
    app.config.from_mapping(DATABASE_URL=os.environ.get("DATABASE_URL"))
    app.config["CORS_HEADERS"] = "Content-Type"

    if test_config:
        app.config.from_mapping(test_config)

    db.init_app(app)

    app.register_blueprint(game.bp, url_prefix="/game")
    app.register_blueprint(speech.bp, url_prefix="/speech")

    return app
