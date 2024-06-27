import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask


def setup_db():
    db_url = os.environ.get("DATABASE_URL")
    connection = psycopg2.connect(db_url)

    try:
        connection = psycopg2.connect(db_url)
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


load_dotenv()
app = Flask(__name__)

setup_db()
