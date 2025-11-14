"""
Consumer: Kafka → ClickHouse

Модуль для потребления данных из Kafka и загрузки в ClickHouse.
Получает сообщения из топика user_events и сохраняет их в таблицу ClickHouse.
"""

import json
import logging
from datetime import datetime
from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord
import clickhouse_connect
from clickhouse_connect.driver.client import Client
import config

# Настройка логирования
logging.getLogger('kafka').setLevel(logging.WARNING)
logger = logging.getLogger('consumer')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def create_clickhouse_client() -> Client:
    """Создает и настраивает клиент ClickHouse.

    Returns:
        Настроенный клиент ClickHouse

    Raises:
        Exception: При ошибке подключения к ClickHouse
    """
    try:
        client = clickhouse_connect.get_client(**config.CLICKHOUSE_CONFIG)
        client.ping()
        logger.info("Клиент ClickHouse успешно создан")
        return client
    except Exception as e:
        logger.error("Ошибка создания клиента ClickHouse: %s", e)
        raise


def ensure_clickhouse_table(client: Client) -> None:
    """Создает таблицу в ClickHouse если ее нет.

    Args:
        client: Клиент ClickHouse

    Raises:
        Exception: При ошибке создания таблицы
    """
    try:
        create_table_query = """
            CREATE TABLE IF NOT EXISTS user_logins (
                id UInt64,
                character_name String,
                username String,
                event_type String,
                event_time DateTime64(3)
            ) ENGINE = MergeTree()
            ORDER BY (event_time, id)
        """
        client.command(create_table_query)
        logger.info("Таблица ClickHouse создана/проверена")
    except Exception as e:
        logger.error("Ошибка создания таблицы в ClickHouse: %s", e)
        raise


def create_kafka_consumer() -> KafkaConsumer:
    """Создает и настраивает Kafka consumer.

    Returns:
        Настроенный экземпляр consumer

    Raises:
        Exception: При ошибке создания consumer
    """
    try:
        consumer = KafkaConsumer(
            config.KAFKA_CONFIG["topic"],
            bootstrap_servers=config.KAFKA_CONFIG["bootstrap_servers"],
            group_id=config.KAFKA_CONFIG["consumer_group"],
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        topic = config.KAFKA_CONFIG['topic']
        logger.info("Kafka consumer создан, подписан на топик: %s", topic)
        return consumer
    except Exception as e:
        logger.error("Ошибка создания Kafka consumer: %s", e)
        raise


def prepare_clickhouse_data(message_data: dict) -> list:
    """Подготавливает данные для вставки в ClickHouse.

    Args:
        message_data: Данные из сообщения Kafka

    Returns:
        Данные в формате для вставки в ClickHouse
    """
    return [
        message_data['id'],
        message_data['character_name'],
        message_data['username'],
        message_data['event_type'],
        datetime.fromtimestamp(message_data['timestamp'])
    ]


def insert_into_clickhouse(client: Client, message_data: dict) -> None:
    """Вставляет данные в ClickHouse.

    Args:
        client: Клиент ClickHouse
        message_data: Данные для вставки

    Raises:
        Exception: При ошибке вставки данных
    """
    try:
        data = prepare_clickhouse_data(message_data)
        client.insert(
            'user_logins',
            [data],
            column_names=['id', 'character_name', 'username', 'event_type', 'event_time']
        )
        logger.debug("Данные вставлены в ClickHouse: %s", message_data)
    except Exception as e:
        logger.error("Ошибка вставки данных в ClickHouse: %s", e)
        raise


def process_message(client: Client, message: ConsumerRecord) -> bool:
    """Обрабатывает одно сообщение из Kafka.

    Args:
        client: Клиент ClickHouse
        message: Сообщение из Kafka

    Returns:
        True если обработка успешна, False в противном случае
    """
    try:
        data = message.value
        char_name = data['character_name']
        event_type = data['event_type']
        logger.info("Вставка записи: %s - %s", char_name, event_type)
        insert_into_clickhouse(client, data)
        return True
    except Exception as e:
        logger.error("Ошибка обработки сообщения: %s", e)
        return False


def main() -> None:
    """Основная функция consumer."""
    client = None
    consumer = None

    try:
        client = create_clickhouse_client()
        ensure_clickhouse_table(client)
        consumer = create_kafka_consumer()

        logger.info("Consumer запущен")

        for message in consumer:
            process_message(client, message)

    except KeyboardInterrupt:
        logger.info("Consumer остановлен пользователем")
    except Exception as e:
        logger.error("Критическая ошибка в consumer: %s", e)
    finally:
        if consumer:
            consumer.close()
            logger.debug("Kafka consumer закрыт")
        if client:
            client.close()
            logger.debug("Клиент ClickHouse закрыт")


if __name__ == "__main__":
    main()