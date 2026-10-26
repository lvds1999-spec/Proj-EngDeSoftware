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
    responsavel_id INTEGER REFERENCES jogadores (id) ON DELETE SET NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS participantes (
    partida_id INTEGER NOT NULL,
    jogador_id INTEGER NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (partida_id, jogador_id),
    FOREIGN KEY (partida_id) REFERENCES partidas (id) ON DELETE CASCADE,
    FOREIGN KEY (jogador_id) REFERENCES jogadores (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cartas (
    partida_id INTEGER NOT NULL,
    jogador_id INTEGER NOT NULL,
    valor TEXT NOT NULL,
    naipe TEXT NOT NULL,
    posicao INTEGER NOT NULL CHECK (posicao IN (1, 2)),
    PRIMARY KEY (partida_id, jogador_id, posicao),
    UNIQUE (partida_id, valor, naipe),
    FOREIGN KEY (partida_id, jogador_id)
        REFERENCES participantes (partida_id, jogador_id) ON DELETE CASCADE
);
"""

SAMPLE_MATCHES = (
    ("Mesa Iniciante", 1, 6, "aberta"),
    ("Mesa Intermediária", 3, 6, "aberta"),
    ("Mesa Lotada", 6, 6, "aberta"),
    ("Mesa em Andamento", 4, 6, "em_andamento"),
    ("Mesa Finalizada", 0, 6, "finalizada"),
)

def create_tables(conn):
    conn.executescript(SCHEMA)
    # Adiciona a coluna de responsável também em bancos criados antes desta versão.
    colunas_partidas = {
        coluna[1] for coluna in conn.execute("PRAGMA table_info(partidas)")
    }
    if "responsavel_id" not in colunas_partidas:
        conn.execute(
            """
            ALTER TABLE partidas
            ADD COLUMN responsavel_id INTEGER
            REFERENCES jogadores (id) ON DELETE SET NULL
            """
        )
    conn.commit()

def seed_sample_matches(conn):
    for match in SAMPLE_MATCHES:
        conn.execute(
            """
            INSERT INTO partidas (nome, participantes, capacidade, status)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM partidas WHERE nome = ?
            )
            """,
            (*match, match[0])
        )
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
        if app.config.get("SEED_SAMPLE_DATA", False):
            seed_sample_matches(db)
