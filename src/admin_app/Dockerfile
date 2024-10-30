# Используем официальный Python 3.11
FROM python:3.11-slim

# Создаем в контейнере директорию /app
WORKDIR /app

# Копируем весь код в контейнер  
COPY ./src/admin_app /app
COPY ./src/models.py /app/models.py

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Добавляем право на выполнение для всех пользователей (Linux)
RUN chmod +x /app/init_db.sh

# Устанавливаем команду по умолчанию
CMD ["/app/init_db.sh"]