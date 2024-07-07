import os
from flask import Flask
from flask_cors import CORS
from . import db, game, speech


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)
    # app.config.from_mapping(DATABASE_URL=os.environ.get("DATABASE_URL"))
    app.config["DB_USER"] = os.getenv("DB_USER")
    app.config["DB_PASSWORD"] = os.getenv("DB_PASSWORD")
    app.config["DB_NAME"] = os.getenv("DB_NAME")
    app.config["DB_INSTANCE"] = os.getenv("DB_INSTANCE")
    app.config["CORS_HEADERS"] = "Content-Type"

    if test_config:
        app.config.from_mapping(test_config)

    db.init_app(app)

    app.register_blueprint(game.bp, url_prefix="/game")
    app.register_blueprint(speech.bp, url_prefix="/speech")

    @app.route("/")
    def healthcheck():
        return "Server is running"

    return app
