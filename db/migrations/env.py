"""
env.py
Alembic migration environment.
Loads the ORM models so autogenerate can see the schema.

TODO:
  1. Import db.models to register all tables on Base.metadata
  2. Read DATABASE_URL from environment (fall back to alembic.ini)
  3. Configure target_metadata = Base.metadata
  4. Wire sqlalchemy.url dynamically in config.set_main_option()
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# TODO: from db.models import Base
# TODO: config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL', ...))

target_metadata = None


def run_migrations_offline():
    """
    Run migrations in 'offline' mode with no DB connection.
    TODO: emit SQL to stderr / file and invoke context.run_migrations()
    """
    pass


def run_migrations_online():
    """
    Run migrations in 'online' mode against a live connection.
    TODO: connect to engine, run migrations, handle batch mode
    """
    pass


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()