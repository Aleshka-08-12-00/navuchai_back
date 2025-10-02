#!/bin/bash

# Скрипт для проверки истекших адаптаций
# Запускается через cron

# Переходим в директорию приложения
cd /app

# Активируем виртуальное окружение (если используется)
# source venv/bin/activate

# Запускаем проверку истекших сроков
python -m app.utils.deadline_checker

# Логируем время выполнения
echo "$(date): Deadline check completed" >> /var/log/deadline_check.log
