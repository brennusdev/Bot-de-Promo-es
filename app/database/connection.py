import os
import logging

import sqlite3
from pathlib import Path

from app.config.settings import DB_PATH, DATABASE_URL

logger = logging.getLogger("pricebot.database")


def get_placeholder():
    """Retorna o placeholder SQL correto para o backend ativo (? SQLite, %s PostgreSQL)."""
    return "%s" if get_database_backend() == "postgresql" else "?"


def get_connection():
    """Cria conexão para SQLite ou PostgreSQL conforme configuração atual."""
    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        try:
            import psycopg

            return psycopg.connect(DATABASE_URL)
        except Exception as exc:
            logger.warning("Falha ao conectar no PostgreSQL: %s", exc)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_database_backend():
    """Retorna o backend ativo para logs e debug."""
    return "postgresql" if DATABASE_URL and DATABASE_URL.startswith("postgresql") else "sqlite"


def supports_returning():
    """PostgreSQL suporta RETURNING id; SQLite não."""
    return get_database_backend() == "postgresql"


def fetch_new_id(cursor):
    """Obtém o id do registro inserido (RETURNING no Postgres, lastrowid no SQLite)."""
    if supports_returning():
        return cursor.fetchone()[0]
    return cursor.lastrowid


def ensure_indexes(conn):
    """Cria índices de performance para as consultas mais frequentes.

    ESTUDO (banco): a tabela prices cresce indefinidamente e quase toda
    consulta filtra por product_id e ordena por collected_at/id. Sem índice,
    cada busca vira um table scan — com milhares de registros o dashboard
    e o worker ficam visivelmente lentos.
    """
    cursor = conn.cursor()

    # ESTUDO: os índices são idênticos no SQLite e no PostgreSQL — um único
    # conjunto de statements serve para ambos os backends.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_product_id ON prices (product_id, id DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_collected_at ON prices (collected_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user_product ON alerts (user_id, product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_product ON alerts (product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_ip ON rate_limit_hits (ip, created_at)")

    conn.commit()


def cleanup_old_prices(days_to_keep=90):
    """Remove registros de preços mais antigos que X dias (retenção de dados).

    Sem isso, a tabela prices cresce para sempre e o banco fica enorme.
    O worker chama isso a cada ciclo; 90 dias é um padrão razoável.
    """
    conn = get_connection()
    cursor = conn.cursor()
    ph = get_placeholder()
    backend = get_database_backend()

    if backend == "postgresql":
        cursor.execute(
            f"DELETE FROM prices WHERE collected_at < NOW() - INTERVAL '{int(days_to_keep)} days'")
    else:
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).isoformat()
        cursor.execute(
            f"DELETE FROM prices WHERE collected_at < {ph}", (cutoff,))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def ensure_sqlite_migrations(conn):
    """Adiciona colunas faltantes em bancos SQLite já existentes."""
    cursor = conn.cursor()

    for table, columns in {
        "products": [
            ("market", "TEXT DEFAULT 'mercado'"),
            ("category", "TEXT DEFAULT 'outros'"),
            ("specifications", "TEXT DEFAULT '{}'"),
            ("reference_price", "REAL DEFAULT 0"),
            ("promotion_score", "INTEGER DEFAULT 0"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
        "alerts": [
            ("threshold_percent", "REAL DEFAULT 10.0"),
            ("active", "INTEGER DEFAULT 1"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
        "users": [
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
        "prices": [
            ("collected_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
    }.items():
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            for column_name, definition in columns:
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {definition}")
        except sqlite3.DatabaseError:
            continue

    conn.commit()


def init_db():
    """Cria as tabelas principais do sistema."""
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                url TEXT NOT NULL UNIQUE,
                store VARCHAR(120) NOT NULL,
                market VARCHAR(80) DEFAULT 'mercado',
                category VARCHAR(60) DEFAULT 'outros',
                specifications JSONB DEFAULT '{}',
                reference_price NUMERIC(12,2) DEFAULT 0,
                promotion_score INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                value NUMERIC(12,2) NOT NULL,
                collected_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150),
                phone VARCHAR(30) NOT NULL UNIQUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                threshold_percent NUMERIC(5,2) DEFAULT 10.00,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limit_hits (
                id SERIAL PRIMARY KEY,
                ip VARCHAR(64) NOT NULL,
                created_at DOUBLE PRECISION NOT NULL
            )
            """
        )
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                store TEXT NOT NULL,
                market TEXT DEFAULT 'mercado',
                category TEXT DEFAULT 'outros',
                specifications TEXT DEFAULT '{}',
                reference_price REAL DEFAULT 0,
                promotion_score INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                value REAL NOT NULL,
                collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                threshold_percent REAL DEFAULT 10.0,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limit_hits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )

        ensure_sqlite_migrations(conn)

    ensure_indexes(conn)

    conn.commit()
    conn.close()

    return DB_PATH
