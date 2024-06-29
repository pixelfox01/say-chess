import click
import psycopg2
from flask import current_app, g


def get_db():
    if "db" not in g:
        db_url = current_app.config["DATABASE_URL"]
        g.db = psycopg2.connect(db_url)
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
