# Используем официальный Python 3.11
FROM python:3.11-slim

# Создаем директорию для приложения
WORKDIR /app

# Копируем весь код в контейнер
COPY ./src /app

RUN pip install --no-cache-dir -r requirements.txt

# Применение миграций Alembic, копирование исправленного env.py и запуск Flask
CMD ["bash", "-c", "\
    flask db init && \
    cp /app/src/migrations/env.py /app/migrations/env.py && \
    flask db migrate -m 'initial migration' && \
    flask db upgrade && \
    flask run --host=0.0.0.0"]