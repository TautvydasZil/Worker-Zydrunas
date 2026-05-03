"""
Database backup script.
SQLite: copies the .db file to backups/ with a timestamp.
Postgres: runs pg_dump if DATABASE_URL starts with postgres.

Usage:
    python backup.py

Schedule with cron (Linux/Mac):
    0 3 * * * cd /path/to/backend && ./venv/bin/python backup.py

Schedule with Task Scheduler (Windows):
    Action: python.exe backup.py
    Start in: C:\path\to\backend
"""

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_URL  = os.getenv('DATABASE_URL', 'sqlite:///worker_hours.db')
KEEP    = int(os.getenv('BACKUP_KEEP_DAYS', '30'))
BACKUPS = Path('backups')
BACKUPS.mkdir(exist_ok=True)

stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')


def backup_sqlite():
    # Extract file path from sqlite:///relative or sqlite:////absolute
    db_path = DB_URL.replace('sqlite:///', '', 1)
    src = Path(db_path)
    if not src.exists():
        print(f'[backup] SQLite file not found: {src}')
        return
    dst = BACKUPS / f'worker_hours_{stamp}.db'
    shutil.copy2(src, dst)
    print(f'[backup] SQLite → {dst}')
    _prune_old('.db')


def backup_postgres():
    dst = BACKUPS / f'worker_hours_{stamp}.sql'
    try:
        result = subprocess.run(
            ['pg_dump', '--no-password', DB_URL, '-f', str(dst)],
            check=True, capture_output=True, text=True
        )
        print(f'[backup] Postgres → {dst}')
        _prune_old('.sql')
    except FileNotFoundError:
        print('[backup] pg_dump not found — install postgresql-client')
    except subprocess.CalledProcessError as e:
        print(f'[backup] pg_dump failed: {e.stderr}')


def _prune_old(ext: str):
    cutoff = datetime.now(timezone.utc).timestamp() - KEEP * 86400
    removed = 0
    for f in BACKUPS.glob(f'worker_hours_*{ext}'):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
    if removed:
        print(f'[backup] Pruned {removed} old backup(s)')


if DB_URL.startswith('postgresql') or DB_URL.startswith('postgres'):
    backup_postgres()
else:
    backup_sqlite()
