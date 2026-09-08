import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("Database connection error:", e)
        return None


def test_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return True, "Database connected successfully."
    except Error as e:
        return False, str(e)
    finally:
        if conn and conn.is_connected():
            conn.close()


def fetch_all(query, params=None):
    conn = get_connection()
    if conn is None:
        raise ConnectionError("Unable to connect to MySQL.")
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_connection()
    if conn is None:
        raise ConnectionError("Unable to connect to MySQL.")
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None):
    conn = get_connection()
    if conn is None:
        raise ConnectionError("Unable to connect to MySQL.")
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
