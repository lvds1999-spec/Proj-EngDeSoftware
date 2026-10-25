import sqlite3
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS jogadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS partidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    participantes INTEGER NOT NULL DEFAULT 0,
    capacidade INTEGER NOT NULL DEFAULT 6,
    status TEXT NOT NULL DEFAULT 'aberta',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def create_tables(conn):
    conn.executescript(SCHEMA)
    conn.commit()

def get_db():
    """
    Retorna a conexão com o banco de dados SQLite associada ao contexto da requisição atual.
    """
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE_PATH', 'poker.db')
        is_uri = db_path.startswith("file:")
        g.db = sqlite3.connect(db_path, uri=is_uri)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        create_tables(g.db)
    return g.db

def close_db(e=None):
    """
    Fecha a conexão ao final da requisição.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """
    Inicializa o banco de dados no startup da aplicação.
    """
    with app.app_context():
        db = get_db()
