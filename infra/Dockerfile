# Используем официальный Python 3.11
FROM python:3.11-slim

# Создаем директорию для приложения
WORKDIR /app

# Копируем весь код в контейнер
COPY ./src /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем скрипт для инициализации миграций
COPY ./src/init_db.sh /app/init_db.sh
RUN chmod +x /app/init_db.sh

# Устанавливаем команду по умолчанию
CMD ["/app/init_db.sh"]
