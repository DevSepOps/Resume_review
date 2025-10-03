import os

import sys

from dotenv import load_dotenv

from logging.config import fileConfig

from pathlib import Path

from sqlalchemy import engine_from_config

from sqlalchemy import pool

from alembic import context

from app.core.config import settings

from app.core.database import Base

from app.users.models import UsersModel

from app.CV.models import Resume

from app.auth.token_blacklist import BlacklistedToken

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(BASE_DIR / ".env")
else:
    print("Warning: .env file not found. Falling back to global environment variables.")

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

config = context.config
if SQLALCHEMY_DATABASE_URL:
    config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
else:
    raise ValueError("SQLALCHEMY_DATABASE_URL not found in environment variables")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata
def get_url():
    try:
        return settings.SQLALCHEMY_DATABASE_URL
    except:
        return config.get_main_option("sqlalchemy.url")


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
