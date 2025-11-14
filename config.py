"""
Конфигурация пайплайна
"""

POSTGRES_CONFIG = {
    "dbname": "test_db",
    "user": "admin",
    "password": "admin",
    "host": "localhost",
    "port": 5432
}

KAFKA_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "topic": "user_events",
    "consumer_group": "clickhouse_consumer_group"
}

CLICKHOUSE_CONFIG = {
    "host": "localhost",
    "port": 8123,
    "username": "user",
    "password": "strongpassword"
}