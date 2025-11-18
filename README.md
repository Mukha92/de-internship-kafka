# Pipeline: PostgreSQL → Kafka → ClickHouse
Система миграции данных с защитой от дубликатов.

## 📋 Описание проекта
Решение для миграции данных из реляционной базы PostgreSQL в колоночную ClickHouse через брокер сообщений Kafka. Система обеспечивает защиту от дублирования и мониторинг в реальном времени.


 ![Архитектура](diagram.png)

 

## ⚙️ Функционал системы
- **Извлечение данных:** выборка записей из PostgreSQL с контролем отправки через флаг `sent_to_kafka`
- **Трансформация в реальном времени:** конвертация данных в формат Kafka и подготовка для ClickHouse
- **Гарантированная доставка:** подтверждение отправки в Kafka перед пометкой записей как обработанных
- **Защита от дублирования:** идемпотентная обработка сообщений и контроль повторной отправки
- **Мониторинг пайплайна:** веб-интерфейс Kafka UI для отслеживания сообщений и потребителей
- **Обработка исключений:** комплексная система обработки ошибок с повторными попытками и логированием

## 🛠️ Технологический стек
- **PostgreSQL** - реляционная база данных 
- **Apache Kafka** - брокер сообщений 
- **ClickHouse** - колоночная база данных для аналитики
- **Kafka UI** - веб-интерфейс для мониторинга кластера Kafka
- **Python** - язык реализации пайплайна
- **Docker** - контейнеризация инфраструктуры
- **psycopg2** - драйвер для работы с PostgreSQL
- **kafka-python** - клиент для работы с Kafka
- **clickhouse-connect** - клиент для работы с ClickHouse
  

## 📁 Структура проекта

```
de-internship-kafka/
├── 📄 .gitignore              # Игнорируемые файлы 
├── 📄 README.md               # Документация проекта
├── 📄 docker-compose.yml      # Docker-инфраструктура 
├── 📄 requirements.txt        # Python-зависимости 
├── 📄 config.py               # Конфигурация компонентов
├── 📄 producer.py             # Producer: PostgreSQL → Kafka
├── 📄 consumer.py             # Consumer: Kafka → ClickHouse
└── 📄 init.sql                # Инициализация PostgreSQL (таблица + тестовые записи)
```


## 🚀 Быстрый старт

### 1. Клонирование репозитория

```
git clone https://github.com/Mukha92/de-internship-kafka.git
cd de-internship-kafka
```

---

### 2. Запуск инфраструктуры

```
docker-compose up -d
docker-compose ps
```

Ожидаемые сервисы:

- ✅ zookeeper(2181) - координатор для управления Kafka кластером 
- ✅ kafka (9092) - брокер сообщений, принимает и хранит сообщения  
- ✅ postgresql (5432) - источник данных с таблицей user_logins   
- ✅ clickhouse (8123) - целевая аналитическая БД для приема данных  
- ✅ kafka-ui (8080)- веб-интерфейс для мониторинга Kafka  → http://localhost:8080  

---

### 3. Настройка PostgreSQL (DBeaver)

Создайте новое подключение:

```
Host: localhost
Port: 5432
Database: test_db
Username: admin
Password: admin
```

Выполните SQL-скрипт `init.sql`, затем проверьте данные:

```sql
SELECT COUNT(*) FROM user_logins;
SELECT * FROM user_logins LIMIT 5;
```

---

### 4. Установка Python-зависимостей

```
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Проверка:

```
python -c "import psycopg2, kafka-python, clickhouse_connect; print('Все зависимости установлены')"
```

---

### 5. Запуск приложения

#### Терминал 1 — Producer (PostgreSQL → Kafka)

```
python producer.py
```

Пример логов:

```
2025-11-14 22:44:57 - producer - INFO - Kafka producer успешно создан
2025-11-14 22:44:57 - producer - INFO - Соединение с PostgreSQL установлено
2025-11-14 22:44:57 - producer - INFO - Producer запущен
2025-11-14 22:45:02 - producer - INFO - Найдено 52 неотправленных записей
2025-11-14 22:45:02 - producer - INFO - Обработана запись: Шерлок Холмс - registration
............................
2025-11-14 22:45:02 - producer - INFO - Отправлено 52 записей
```

#### Терминал 2 — Consumer (Kafka → ClickHouse)

```
python consumer.py
```

Пример логов:

```
2025-11-14 22:47:14 - consumer - INFO - Клиент ClickHouse успешно создан
2025-11-14 22:47:14 - consumer - INFO - Таблица ClickHouse создана/проверена
2025-11-14 22:47:14 - consumer - INFO - Kafka consumer создан, подписан на топик: user_events
2025-11-14 22:47:14 - consumer - INFO - Consumer запущен
2025-11-14 22:47:18 - consumer - INFO - Вставка записи: Шерлок Холмс - registration
...............................
```

---

### 6. 📊 Мониторинг системы

- **Kafka UI:** http://localhost:8080 — проверьте топик `user_events`, сообщения и группу `clickhouse_consumer_group`.
  
- **PostgreSQL:** localhost:5432
Проверка отправленных записей в PostgreSQL:
```
SELECT COUNT(*) as sent_count FROM user_logins WHERE sent_to_kafka = true;
-- Должно быть 52 после работы Producer
```
- **ClickHouse:** localhost:8123
Проверка полученных данных в ClickHouse:
```
SELECT COUNT(*) as total_records FROM user_logins;
-- Должно быть 52 после работы Consumer
```

## 🛠️ Технологический стек

## 🛠️ Технологический стек

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)

[![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?logo=clickhouse&logoColor=black)](https://clickhouse.com/)

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://python.org/)

[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com/)

