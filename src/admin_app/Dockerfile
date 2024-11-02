FROM python:3.11-slim

WORKDIR /app

COPY ./src/admin_app /app
COPY ./src/models.py /app/models.py

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]