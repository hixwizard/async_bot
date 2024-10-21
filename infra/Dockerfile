# Используем официальный Python 3.11
FROM python:3.11-slim

# Создаем директорию для приложения
WORKDIR /app

# Создаем директорию для миграций
RUN mkdir -p /app/migrations

# Копируем requirements.txt в контейнер
COPY ./src/requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код в контейнер
COPY ./src /app

# Применение миграций Alembic и запуск Flask
CMD ["bash", "-c", "flask db upgrade && flask run --host=0.0.0.0"]
