#!/bin/bash

# Проверка существования директории migrations
if [ -d "migrations" ]; then
    echo "Директория migrations существует. Выполняю обновление базы данных..."
    flask db upgrade
    flask create_superuser
    flask create_questions
    flask create_statuses
    flask run --host=0.0.0.0
else
    echo "Директория migrations не найдена. Инициализация базы данных..."
    flask db init
    cp env.py migrations/env.py
    flask db migrate
    flask db upgrade
    flask create_superuser
    flask create_questions
    flask create_statuses
    flask run --host=0.0.0.0
fi
