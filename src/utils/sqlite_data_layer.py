import os
import sqlite3
from sqlite3 import Connection


class SQLiteDataLayer:
    def __init__(self, db_filepath=None):
        if db_filepath is None or db_filepath == "":
            db_filepath = "data.db"
        normalized_path = self.normalize_db_path(db_filepath)
        os.makedirs(os.path.dirname(normalized_path), exist_ok=True)

        self.conn = self.create_connection(normalized_path)
        self.create_tables()

    @staticmethod
    def normalize_db_path(db_path):
        abs_path = os.path.abspath(db_path)
        normalized_path = os.path.normpath(abs_path)
        return normalized_path

    def create_connection(self, db_file) -> Connection:
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            print(f"Connected to SQLite database: {db_file}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
        return conn

    def create_tables(self):
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS users (
            "id" TEXT PRIMARY KEY,
            "identifier" TEXT NOT NULL UNIQUE,
            "metadata" TEXT NOT NULL,
            "createdAt" TEXT
        );

        CREATE TABLE IF NOT EXISTS threads (
            "id" TEXT PRIMARY KEY,
            "createdAt" TEXT,
            "name" TEXT,
            "userId" TEXT,
            "userIdentifier" TEXT,
            "tags" TEXT[],
            "metadata" TEXT,
            FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS steps (
            "id" TEXT PRIMARY KEY,
            "name" TEXT NOT NULL,
            "type" TEXT NOT NULL,
            "threadId" TEXT NOT NULL,
            "parentId" TEXT,
            "disableFeedback" INTEGER NOT NULL DEFAULT 0,
            "streaming" INTEGER NOT NULL,
            "waitForAnswer" INTEGER,
            "isError" INTEGER,
            "metadata" TEXT,
            "tags" TEXT,
            "input" TEXT,
            "output" TEXT,
            "createdAt" TEXT,
            "start" TEXT,
            "end" TEXT,
            "generation" TEXT,
            "showInput" TEXT,
            "language" TEXT,
            "indent" INTEGER
        );

        CREATE TABLE IF NOT EXISTS elements (
            "id" TEXT PRIMARY KEY,
            "threadId" TEXT,
            "type" TEXT,
            "url" TEXT,
            "chainlitKey" TEXT,
            "name" TEXT NOT NULL,
            "display" TEXT,
            "objectKey" TEXT,
            "size" TEXT,
            "page" INTEGER,
            "language" TEXT,
            "forId" TEXT,
            "mime" TEXT
        );

        CREATE TABLE IF NOT EXISTS feedbacks (
            "id" TEXT PRIMARY KEY,
            "forId" TEXT NOT NULL,
            "threadId" TEXT NOT NULL,
            "value" INTEGER NOT NULL,
            "comment" TEXT
        );
        """
        try:
            c = self.conn.cursor()
            c.executescript(create_tables_sql)
            self.conn.commit()
            print("Tables created successfully")
            self.conn.close()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
