import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)
db_url = os.environ.get("DATABASE_URL")
connection = psycopg2.connect(db_url)

with connection:
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute(open("schema.sql", "r").read())
