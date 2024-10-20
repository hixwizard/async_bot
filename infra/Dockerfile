# Используем официальный Python 3.11
FROM python:3.11-slim

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Создаем директорию для приложения
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска
CMD ["flask", "run", "--host=0.0.0.0"]
