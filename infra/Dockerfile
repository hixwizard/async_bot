# Используем официальный Python 3.11
FROM python:3.11-slim

# Создаем директорию для приложения
WORKDIR /app

# Копируем весь код в контейнер
COPY ./src /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/init_db.sh

# Run the script to handle migrations and start Flask
CMD ["bash", "/app/init_db.sh"]