import click
import psycopg2
from flask import current_app, g
from google.cloud.sql.connector import Connector
import pg8000

connector = Connector()


def get_db_connection():
    db_user = current_app.config["DB_USER"]
    db_password = current_app.config["DB_PASSWORD"]
    db_name = current_app.config["DB_NAME"]
    db_instance = current_app.config["DB_INSTANCE"]

    conn = connector.connect(
        db_instance, "pg8000", user=db_user, password=db_password, db=db_name
    )
    return conn


def get_db():
    if "db" not in g:
        g.db = get_db_connection()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    try:
        db.autocommit = True
        with db.cursor() as cursor:
            with current_app.open_resource("schema.sql") as schema_file:
                schema_sql = schema_file.read()
                cursor.execute(schema_sql)
                print("Schema executed successfully.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error executing schema: {error}")


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Initialized database...")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
