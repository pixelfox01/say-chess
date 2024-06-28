import os
from flask import Flask
from dotenv import load_dotenv
from . import db, game

# from game import game_bp  # Import the Blueprint


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

    # # Setup the database (execute schema.sql and create tables)
    # with app.app_context():
    #     setup_db(app)

    # Register the game Blueprint
    app.register_blueprint(game.bp, url_prefix="/game")

    return app


# import os
# from flask import Flask
# from dotenv import load_dotenv
# from db import db, setup_db
# from game import game_bp  # Import the Blueprint

# # Load environment variables from .env file
# load_dotenv()

# # Create and configure the app
# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # Initialize the database
# db.init_app(app)

# # Setup the database (execute schema.sql and create tables)
# setup_db(app)

# # Register the game Blueprint
# app.register_blueprint(game_bp, url_prefix="/game")

# if __name__ == "__main__":
#     app.run(debug=True)
