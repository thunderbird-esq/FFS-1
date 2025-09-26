#!/bin/bash
# Complete database setup with SQLAlchemy and Alembic

DB_TYPE="${1:-postgresql}"
DB_NAME="${2:-app_db}"

python3 << EOF
import os
from pathlib import Path

db_type = "$DB_TYPE"
db_name = "$DB_NAME"

# Create database directory
db_dir = Path("app/db")
db_dir.mkdir(parents=True, exist_ok=True)

# Generate database.py
database_content = '''from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "''' + db_type + ''':///./''' + db_name + '''")

# Adjust for async
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite:"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:", "sqlite+aiosqlite:")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
'''

# Generate base model
base_model_content = '''from sqlalchemy import Column, Integer, DateTime, func
from app.db.database import Base
from datetime import datetime

class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
'''

# Generate user model
user_model_content = '''from sqlalchemy import Column, String, Boolean
from app.db.models.base import BaseModel

class User(BaseModel):
    """User model."""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
'''

# Generate alembic.ini
alembic_content = '''[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = ''' + db_type + ''':///./''' + db_name + '''

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''

# Generate migration env.py
migration_env = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import all models
from app.db.database import Base
from app.db.models.base import BaseModel
from app.db.models.user import User

config = context.config

# Set database URL from environment
if os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()

if context.is_offline_mode():
    print("Offline mode not supported for async")
else:
    asyncio.run(run_migrations_online())
'''

# Create directory structure
models_dir = db_dir / "models"
models_dir.mkdir(exist_ok=True)
alembic_dir = Path("alembic")
alembic_dir.mkdir(exist_ok=True)

# Write files
with open(db_dir / "database.py", "w") as f:
    f.write(database_content)

with open(models_dir / "base.py", "w") as f:
    f.write(base_model_content)

with open(models_dir / "user.py", "w") as f:
    f.write(user_model_content)

with open(models_dir / "__init__.py", "w") as f:
    f.write("")

with open("alembic.ini", "w") as f:
    f.write(alembic_content)

with open(alembic_dir / "env.py", "w") as f:
    f.write(migration_env)

print(f"✓ Database setup complete:")
print(f"  - app/db/database.py")
print(f"  - app/db/models/base.py")
print(f"  - app/db/models/user.py")
print(f"  - alembic.ini")
print(f"  - alembic/env.py")
print(f"  Database Type: {db_type}")
print(f"  Database Name: {db_name}")
print("")
print("Next steps:")
print("  1. Run: alembic revision --autogenerate -m 'Initial migration'")
print("  2. Run: alembic upgrade head")
EOF

# Handle additional database arguments
if [ -n "$ARGUMENTS" ]; then
    echo "Additional database configuration: $ARGUMENTS"
fi
