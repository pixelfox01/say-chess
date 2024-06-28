from flask_sqlalchemy import SQLAlchemy
import os
import psycopg2

db = SQLAlchemy()


def setup_db(app):
    with app.app_context():
        execute_schema()
        setup_test_rows()  # WARN: DELETE THIS
        db.create_all()
        print("Database setup complete.")


# WARN: DELETE THIS
def setup_test_rows():
    db_url = os.environ.get("DATABASE_URL")
    connection = psycopg2.connect(db_url)
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            schema_sql = """
            INSERT INTO \"user\" (username, password)
            VALUES
                ('imran', '12345'),
                ('cinan', '12345'),
                ('frank', '12345'),
                ('alex', '12345');
            """
            cursor.execute(schema_sql)
            print("Schema executed successfully.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error executing schema: {error}")
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")


def execute_schema():
    db_url = os.environ.get("DATABASE_URL")
    connection = psycopg2.connect(db_url)
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            with open("schema.sql", "r") as schema_file:
                schema_sql = schema_file.read()
                cursor.execute(schema_sql)
                print("Schema executed successfully.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error executing schema: {error}")
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")
