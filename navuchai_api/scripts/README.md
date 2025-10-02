# Скрипты для автоматизации

## Проверка истекших адаптаций

### Описание
Автоматическая проверка истекших сроков адаптаций с установкой статуса `is_failed = true`.

### Файлы
- `check_deadlines.sh` - bash скрипт для запуска проверки
- `../cron/deadline_check` - cron расписание (каждый час)

### Использование

#### Ручной запуск
```bash
# Внутри контейнера
/app/scripts/check_deadlines.sh

# Или через Python модуль
python -m app.utils.deadline_checker
```

#### Через Docker Compose
```bash
# Запуск всех сервисов (включая cron)
docker-compose -f docker-compose.dev.yml up -d

# Проверка логов cron
docker logs navuchai_cron_dev

# Проверка логов проверки дедлайнов
docker exec navuchai_cron_dev cat /var/log/deadline_check.log
```

#### Настройка расписания
Отредактируйте файл `cron/deadline_check`:

```bash
# Каждый час (текущее расписание)
0 * * * * /app/scripts/check_deadlines.sh

# Каждый день в 9:00
0 9 * * * /app/scripts/check_deadlines.sh

# Только в рабочие дни в 9:00
0 9 * * 1-5 /app/scripts/check_deadlines.sh

# Каждые 6 часов
0 */6 * * * /app/scripts/check_deadlines.sh
```

### Логи
- Логи cron: `docker logs navuchai_cron_dev`
- Логи проверки дедлайнов: `/var/log/deadline_check.log` внутри контейнера
- Логи приложения: стандартные логи FastAPI

### Мониторинг
```bash
# Проверка статуса cron
docker exec navuchai_cron_dev crontab -l

# Проверка последних логов
docker exec navuchai_cron_dev tail -f /var/log/deadline_check.log
```
