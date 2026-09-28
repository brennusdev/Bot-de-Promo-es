from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from app.config.settings import DB_PATH


def backup_database() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    destination = DB_PATH.parent / f"price_bot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, destination)
    return destination


if __name__ == "__main__":
    result = backup_database()
    print(f"Backup criado em: {result}")
