# Pipeline: PostgreSQL → Kafka → ClickHouse
Система миграции данных с защитой от дубликатов.

## 📋 Описание проекта
Решение для миграции данных из реляционной базы PostgreSQL в колоночную ClickHouse через брокер сообщений Kafka. Система обеспечивает защиту от дублирования и мониторинг в реальном времени.

## ⚙️ Функционал системы
- **Извлечение данных:** выборка записей из PostgreSQL с контролем отправки через флаг `sent_to_kafka`
- **Трансформация в реальном времени:** конвертация данных в формат Kafka и подготовка для ClickHouse
- **Гарантированная доставка:** подтверждение отправки в Kafka перед пометкой записей как обработанных
- **Защита от дублирования:** идемпотентная обработка сообщений и контроль повторной отправки
- **Мониторинг пайплайна:** веб-интерфейс Kafka UI для отслеживания сообщений и потребителей
- **Обработка исключений:** комплексная система обработки ошибок с повторными попытками и логированием

## 🛠️ Технологический стек
- **PostgreSQL** - реляционная база данных-источник
- **Apache Kafka** - брокер сообщений для асинхронной передачи данных
- **ClickHouse** - колоночная база данных для аналитики
- **Kafka UI** - веб-интерфейс для мониторинга кластера Kafka
- **Python** - язык реализации пайплайна
- **Docker** - контейнеризация инфраструктуры
- **psycopg2** - драйвер для работы с PostgreSQL
- **kafka-python** - клиент для работы с Kafka
- **clickhouse-connect** - клиент для работы с ClickHouse

  

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/kafka-postgresql-clickhouse-pipeline.git
cd kafka-postgresql-clickhouse-pipeline
```

> Замените `your-username` на ваш реальный GitHub username.

### 2. Запуск инфраструктуры

```bash
# Запуск контейнеров в фоне
docker-compose up -d
```

Дождитесь полного запуска всех контейнеров (обычно 2–3 минуты). Проверить статус:

```bash
docker-compose ps
```

Ожидаемые запущенные сервисы:

- zookeeper
- kafka
- postgres
- clickhouse


### 3. Настройка PostgreSQL через DBeaver

**Установка DBeaver (если не установлен)**

Скачать: https://dbeaver.io/download/ (версия Community — бесплатная)

**Подключение к PostgreSQL**

Создайте новое подключение в DBeaver:

- `Database` → `New Database Connection`
- Выберите `PostgreSQL` → `Next`

Параметры подключения:

```
Host: localhost
Port: 5432
Database: test_db
Username: admin
Password: admin
```

Нажмите `Test Connection` — должно появиться "Connected" → `Finish`.

**Создание таблицы и данных**

1. Откройте SQL редактор: правой кнопкой на базе `test_db` → `SQL Editor` → `New SQL Script`.
2. Откройте файл `init.sql` в проекте, скопируйте содержимое и вставьте в редактор DBeaver.
3. Выполните скрипт (Ctrl+Enter или ▶️).

Проверьте создание таблицы: `test_db` → `Schemas` → `public` → `Tables` — должна появиться таблица `user_logins`.

Просмотреть данные: правый клик на таблице → `View Data`.

Проверка количества записей:

```sql
SELECT COUNT(*) as total_records FROM user_logins;
```

Ожидаемое значение: **52 записи**.


### 4. Проверка Kafka

**Проверка топиков через командную строку**

```bash
# Список топиков
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
# Просмотр сообщений (реальное время)
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_events \
  --from-beginning
```

Ожидается: топик `user_events` с JSON-сообщениями.

**Проверка через DBeaver (если установлен Kafka plugin)**

- `Database` → `New Database Connection` → `Apache Kafka`
- Bootstrap servers: `localhost:9092`
- Разверните подключение → `Topics` → `user_events` → правый клик → `View data` → `Start consumer`.


### 5. Проверка ClickHouse

**Через DBeaver**

Создайте подключение `ClickHouse` с параметрами:

```
Host: localhost
Port: 8123
Database: default
Username: user
Password: strongpassword
```

Проверка подключения:

```sql
-- Проверить версию ClickHouse
SELECT version();
```

**Через командную строку**

```bash
# Подключиться к ClickHouse
docker-compose exec clickhouse clickhouse-client --user user --password strongpassword
# В интерактивной сессии выполнить:
SHOW TABLES;
```


### 6. Установка зависимостей Python

```bash
# Создание виртуального окружения
python -m venv .venv

# Активация (Linux/Mac)
source .venv/bin/activate

# Активация (Windows)
.venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```


### 7. Запуск Consumer

В отдельном терминале/вкладке:

```bash
python consumer_to_clickhouse.py
```

Ожидаемые логи:

```text
2024-01-15 10:30:20 - consumer_to_clickhouse - INFO - Клиент ClickHouse успешно создан
2024-01-15 10:30:20 - consumer_to_clickhouse - INFO - Таблица ClickHouse создана/проверена
2024-01-15 10:30:20 - consumer_to_clickhouse - INFO - Kafka consumer создан, подписан на топик: user_events
2024-01-15 10:30:20 - consumer_to_clickhouse - INFO - Consumer запущен
```


### 8. Запуск Producer

В другом терминале/вкладке:

```bash
python producer_pg_to_kafka.py
```

Ожидаемые логи:

```text
2024-01-15 10:30:15 - producer_pg_to_kafka - INFO - Kafka producer успешно создан
2024-01-15 10:30:15 - producer_pg_to_kafka - INFO - Соединение с PostgreSQL установлено
2024-01-15 10:30:15 - producer_pg_to_kafka - INFO - Producer запущен
2024-01-15 10:30:15 - producer_pg_to_kafka - INFO - Найдено 52 неотправленных записей
2024-01-15 10:30:15 - producer_pg_to_kafka - INFO - Обработана запись: Шерлок Холмс - registration
...
2024-01-15 10:30:16 - producer_pg_to_kafka - INFO - Отправлено 52 записей
```


---

## ✅ Проверка работоспособности пайплайна

### 1. Проверка передачи данных через Kafka

```bash
# В реальном времени следить за сообщениями в Kafka
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_events \
  --property print.key=true \
  --property print.value=true \
  --from-beginning
```

Должны отображаться JSON-сообщения в формате:

```json
{
  "id": 1,
  "character_name": "Шерлок Холмс",
  "username": "sherlock",
  "event_type": "registration",
  "timestamp": 1762798313.27121
}
```


### 2. Проверка данных в ClickHouse

**Через DBeaver:**

```sql
-- Проверить общее количество записей
SELECT COUNT(*) as total_records FROM user_logins;

-- Просмотреть последние 10 записей
SELECT * FROM user_logins
ORDER BY event_time DESC
LIMIT 10;

-- Статистика по типам событий
SELECT event_type, COUNT(*) as count
FROM user_logins
GROUP BY event_type
ORDER BY count DESC;
```

**Через командную строку:**

```bash
docker-compose exec clickhouse clickhouse-client \
  --user user \
  --password strongpassword \
  --query "SELECT COUNT(*) FROM user_logins"
```


### 3. Проверка обновления флагов в PostgreSQL

**Через DBeaver:**

```sql
-- Проверить сколько записей обработано
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN sent_to_kafka THEN 1 ELSE 0 END) as sent,
  SUM(CASE WHEN NOT sent_to_kafka THEN 1 ELSE 0 END) as not_sent
FROM user_logins;

-- После работы Producer все записи должны быть sent_to_kafka = TRUE
SELECT COUNT(*) as unsent_count
FROM user_logins
WHERE sent_to_kafka = FALSE;
```


---

## 🔧 Мониторинг в реальном времени

Одновременный мониторинг всех компонентов (рекомендуется использовать 4 терминала):

**Терминал 1 — Consumer:**

```bash
python consumer_to_clickhouse.py
```

**Терминал 2 — Producer:**

```bash
python producer_pg_to_kafka.py
```

**Терминал 3 — Kafka messages:**

```bash
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic user_events
```

**Терминал 4 — ClickHouse data:**

```bash
# Linux/Mac
watch -n 5 'docker-compose exec clickhouse clickhouse-client \
  --user user \
  --password strongpassword \
  --query "SELECT COUNT(*) as records FROM user_logins"'

# Windows (PowerShell)
while ($true) {
  docker-compose exec clickhouse clickhouse-client --user user --password strongpassword --query "SELECT COUNT(*) as records FROM user_logins"
  Start-Sleep -Seconds 5
}
```


---

## 🐛 Устранение неполадок

### Проблема: Kafka не запускается

```bash
# Проверить логи Kafka
docker-compose logs kafka

# Перезапустить сервисы
docker-compose restart zookeeper kafka

# Проверить, что Zookeeper работает
docker-compose exec zookeeper zkServer.sh status
```


### Проблема: ClickHouse недоступен

```bash
# Проверить статус ClickHouse
docker-compose exec clickhouse clickhouse-client --user user --password strongpassword --query "SELECT 1"

# Проверить логи
docker-compose logs clickhouse

# Проверить доступность порта
# Windows:
netstat -an | findstr :8123
# Linux:
ss -tuln | grep 8123
```


### Проблема: Нет данных в ClickHouse

- Убедитесь, что Consumer запущен и получает сообщения.
- Проверьте, что Producer отправляет данные в Kafka.
- Проверьте подключение ClickHouse в логах Consumer.
- Проверьте, что таблица создана в ClickHouse.


### Проблема: Повторная отправка данных

```sql
-- Сбросить флаги для повторного тестирования
UPDATE user_logins SET sent_to_kafka = FALSE;
```


### Проблема: Ошибки подключения в DBeaver

- Убедитесь, что Docker контейнеры запущены: `docker-compose ps`.
- Проверьте правильность параметров подключения.
- Убедитесь, что порты не заняты другими приложениями.


---

## 📊 Валидация результатов

После успешного запуска убедитесь, что:

- **PostgreSQL:** 52 записи, все `sent_to_kafka = TRUE`
- **Kafka:** 52 сообщения в топике `user_events`
- **ClickHouse:** 52 записи в таблице `user_logins`
- **Логи:** Producer и Consumer работают без ошибок

**Финальная проверка всех компонентов:**

```bash
# PostgreSQL - количество обработанных записей
docker-compose exec postgres psql -U admin -d test_db -c "SELECT COUNT(*) as sent_count FROM user_logins WHERE sent_to_kafka = TRUE"

# Kafka - количество сообщений (приблизительно)
docker-compose exec kafka kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic user_events

# ClickHouse - количество записей
docker-compose exec clickhouse clickhouse-client --user user --password strongpassword --query "SELECT COUNT(*) as ch_records FROM user_logins"
```

Все три команды должны показывать число **52** (или близкое к нему).


---

## 📈 Дополнительные проверки

**Проверка качества данных в ClickHouse:**

```sql
SELECT
  min(event_time) as first_event,
  max(event_time) as last_event,
  count(distinct id) as unique_ids,
  count(distinct username) as unique_users
FROM user_logins;
```

**Проверка производительности:**

(если добавлено поле `_processed_time`)

```sql
SELECT
  max(_processed_time) - min(_processed_time) as processing_time
FROM user_logins;
```


---

## 🧹 Очистка

```bash
# Остановка контейнеров
docker-compose down

# Полная очистка с удалением данных
docker-compose down -v

# Удаление виртуального окружения (опционально)
deactivate
rm -rf .venv
```


---

## 🔧 Конфигурация

Все основные настройки находятся в `config.py`:

- PostgreSQL: `localhost:5432`, база `test_db`
- Kafka: `localhost:9092`, топик `user_events`
- ClickHouse: `localhost:8123`, таблица `user_logins`


---

## 📝 Логирование

- Логи выводятся в консоль с временными метками
- Уровень логирования: `INFO`
- Формат: `ВРЕМЯ - ИМЯ_МОДУЛЯ - УРОВЕНЬ - СООБЩЕНИЕ`


---

## 🛠️ Ручной запуск SQL

Если автоматическое выполнение `init.sql` не сработало, выполните вручную:

```bash
docker-compose exec postgres psql -U admin -d test_db
# Затем вставьте и выполните команды из init.sql
```


---

## 👥 Разработчики

- [Ваше имя] - [ваш email]


---

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT License**.

---

Если хотите, могу также сформировать `docker-compose`/`config.py` примеры или короткий `CONTRIBUTING.md` — скажите, какие дополнительные файлы нужны.


