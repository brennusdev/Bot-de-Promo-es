from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
from app.config.settings import DB_PATH
from app.database.connection import get_database_backend
def backup_database() -> Path:
    """Copia o banco SQLite. No PostgreSQL, backup deve ser pg_dump do provedor."""
    if get_database_backend() != "sqlite":
        raise RuntimeError(
            "Backend ativo é PostgreSQL — use pg_dump (ou o backup do provedor "
            "ex.: pg_dump $DATABASE_URL > backup.sql). Este script é só para SQLite."
        )
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    destination = DB_PATH.parent / f"price_bot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, destination)
    return destination


if __name__ == "__main__":
    result = backup_database()
    print(f"Backup criado em: {result}")
