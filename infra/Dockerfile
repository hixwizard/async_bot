# Используем официальный Python 3.11
FROM python:3.11-slim

# Создаем директорию для приложения
WORKDIR /app

# Копируем весь код в контейнер
COPY ./src /app

RUN pip install --no-cache-dir -r requirements.txt

# Run the script to handle migrations and start Flask
CMD ["bash", "-c", "\
    flask db migrate -m 'initial migration' && \
    flask db upgrade && \
    flask run --host=0.0.0.0"]