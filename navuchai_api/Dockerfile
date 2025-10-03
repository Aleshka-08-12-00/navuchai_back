FROM python:3.10-slim

WORKDIR /app

# Устанавливаем cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Копируем скрипты и cron файлы
COPY scripts/ /app/scripts/
COPY cron/ /app/cron/

# Делаем скрипт исполняемым
RUN chmod +x /app/scripts/check_deadlines.sh

# Устанавливаем cron задачу
# RUN crontab /app/cron/deadline_check

# Создаем директорию для логов
RUN mkdir -p /var/log && touch /var/log/deadline_check.log

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8012"]
