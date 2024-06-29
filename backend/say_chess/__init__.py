import os
from flask import Flask
from dotenv import load_dotenv
from . import db, game


def create_app(test_config=None):
    # Load environment variables from .env file
    load_dotenv()

    # Create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(DATABASE_URL=os.environ.get("DATABASE_URL"))

    if test_config:
        app.config.from_mapping(test_config)

    # Initialize the database
    db.init_app(app)

    # Register the game Blueprint
    app.register_blueprint(game.bp, url_prefix="/game")

    return app
