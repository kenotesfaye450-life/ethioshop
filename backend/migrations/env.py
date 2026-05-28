from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

from alembic import context

# Allow backend package imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from backend.extensions import db  # ← use extensions.py, not app.py (avoids circular import)
import backend.models               # noqa: F401 — ensure all models are registered on metadata

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def run_migrations_offline():
    """Run migrations without a live DB connection (generates SQL only)."""
    from backend.config import Config
    url = Config.SQLALCHEMY_DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations against a live DB connection."""
    app = create_app()
    with app.app_context():
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
