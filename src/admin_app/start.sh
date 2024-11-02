#!/bin/bash

# Выполнение миграций и начальной инициализации данных
echo "Инициализация базы данных..."
if [ -d "migrations" ]; then
    echo "Директория migrations существует. Выполняю обновление базы данных..."
    flask db upgrade
else
    echo "Директория migrations не найдена. Инициализация базы данных..."
    flask db init
    cp env.py migrations/env.py
    flask db migrate
    flask db upgrade
fi

# Добавление начальных данных
flask create_superuser hix 1
flask create_questions
flask create_statuses

# Запуск приложения через Gunicorn на 4 процессах
echo "Запуск Gunicorn..."
exec gunicorn -w 4 -b 0.0.0.0:8000 admin:app
