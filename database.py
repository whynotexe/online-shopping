"""Shared MySQL connection helper.

Connection settings come from environment variables so local credentials are
never required in source control.  The console application can continue to
import :func:`get_connection` unchanged.
"""

import os

import mysql.connector
from mysql.connector import Error

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "online_shopping")


def get_connection():
    """Return a new database connection, or ``None`` when unavailable."""
    try:
        return mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
        )
    except Error as error:
        print(f"[ERROR] Could not connect to the database: {error}")
        return None
