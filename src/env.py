from __future__ import with_statement

import logging
from logging.config import fileConfig
from typing import Any, Dict, List

from alembic import context
from flask import current_app

# Импортируем Base и метаданные
from models import Base  # Импортируем ваш Base из models

# Alembic Config объект, который предоставляет доступ к значениям из файла .ini
config = context.config

# Настройка логирования
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Добавляем метаданные для автогенерации
target_metadata = Base.metadata  # Установите target_metadata для автогенерации

# Устанавливаем URL базы данных
config.set_main_option(
    'sqlalchemy.url',
    str(
        current_app.extensions['migrate'].db.get_engine().url,
    ).replace('%', '%%'),
)


def run_migrations_offline() -> None:
    """Запускаем миграции в оффлайн-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запускаем миграции в онлайн-режиме."""
    def process_revision_directives(
            context: context.ContextImpl,
            revision: str,
            directives: List[Dict[str, Any]],
    ) -> None:
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('Нет изменений в схеме.')

    connectable = current_app.extensions['migrate'].db.get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():

    run_migrations_offline()
else:
    run_migrations_online()
