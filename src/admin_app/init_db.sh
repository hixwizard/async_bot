#!/bin/bash

# Проверка существования директории migrations
if [ -d "migrations" ]; then
    echo "Директория migrations существует. Выполняю обновление базы данных..."
    flask db upgrade
    flask createsuperuser hix 1
    flask run --host=0.0.0.0
else
    echo "Директория migrations не найдена. Инициализация базы данных..."
    flask db init
    cp env.py migrations/env.py
    flask db migrate
    flask db upgrade
    flask createsuperuser hix 1
    flask run --host=0.0.0.0
fi
