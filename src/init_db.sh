#!/bin/bash

# Проверяем, существует ли папка миграций
if [ -d migrations ]; then
    echo "Папка миграций уже существует."

    # Проверяем, есть ли файлы в папке migrations/versions
    if [ "$(ls -A migrations/versions)" ]; then
        echo "Миграции уже существуют. Пропускаем создание новой миграции."
    else
        # Если папка миграций существует, но версия пустая, создаем новую миграцию
        echo "Создание миграции, так как версии миграций не найдены."
        flask db migrate -m 'some'

        if [ $? -ne 0 ]; then
            echo "Ошибка при создании миграции. Завершение работы."
            exit 1
        fi
    fi

    # Применяем миграции
    echo "Применение миграций..."
    flask db upgrade

    if [ $? -ne 0 ]; then
        echo "Ошибка при применении миграций. Завершение работы."
        exit 1
    fi

else
    # Если папка миграций не существует, инициализируем миграции
    echo "Папка миграций не найдена. Инициализация миграций..."
    flask db init

    echo "Копирование файла env.py в папку миграций..."
    cp env.py migrations/env.py

    if [ $? -ne 0 ]; then
        echo "Ошибка при копировании файла env.py в папку миграций."
        exit 1
    fi

    echo "Создание миграции..."
    flask db migrate -m 'jfjf'

    if [ $? -ne 0 ]; then
        echo "Ошибка при создании миграции. Завершение работы."
        exit 1
    fi

    echo "Применение миграций..."
    flask db upgrade

    if [ $? -ne 0 ]; then
        echo "Ошибка при применении миграций. Завершение работы."
        exit 1
    fi
fi

echo "Запуск Flask..."
flask run --host=0.0.0.0
