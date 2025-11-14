"""
Producer: PostgreSQL → Kafka

Модуль для передачи данных из PostgreSQL в Kafka.
Отправляет записи из таблицы user_logins в Kafka топик
и помечает их как отправленные.
"""

import json
import time
import logging
from kafka import KafkaProducer
from kafka.producer.future import FutureRecordMetadata
import psycopg2
from psycopg2.extensions import connection as pg_connection
from psycopg2.extensions import cursor as pg_cursor
import config

# Настройка логирования
logging.getLogger('kafka').setLevel(logging.WARNING)
logger = logging.getLogger('producer')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def create_producer() -> KafkaProducer:
    """Создает и настраивает Kafka producer.

    Returns:
        Настроенный экземпляр продюсера

    Raises:
        Exception: При ошибке создания продюсера
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_CONFIG["bootstrap_servers"],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka producer успешно создан")
        return producer
    except Exception as e:
        logger.error("Ошибка создания Kafka producer: %s", e)
        raise


def create_postgres_connection() -> tuple[pg_connection, pg_cursor]:
    """Создает соединение с PostgreSQL.

    Returns:
        Кортеж с соединением и курсором

    Raises:
        Exception: При ошибке подключения к БД
    """
    try:
        conn = psycopg2.connect(**config.POSTGRES_CONFIG)
        cursor = conn.cursor()
        logger.info("Соединение с PostgreSQL установлено")
        return conn, cursor
    except Exception as e:
        logger.error("Ошибка подключения к PostgreSQL: %s", e)
        raise


def get_unsent_records(cursor: pg_cursor) -> list[tuple]:
    """Извлекает неотправленные записи из PostgreSQL.

    Args:
        cursor: Курсор для выполнения SQL-запросов

    Returns:
        Список кортежей с данными записей

    Raises:
        Exception: При ошибке выполнения запроса
    """
    try:
        query = """
            SELECT id, character_name, username, event_type, 
                   extract(epoch FROM event_time) 
            FROM user_logins 
            WHERE sent_to_kafka = FALSE 
            ORDER BY event_time
        """
        cursor.execute(query)
        records = cursor.fetchall()
        if records:
            logger.info("Найдено %d неотправленных записей", len(records))
        return records
    except Exception as e:
        logger.error("Ошибка получения неотправленных записей: %s", e)
        raise


def prepare_kafka_message(record: tuple) -> dict:
    """Подготавливает данные для отправки в Kafka.

    Args:
        record: Кортеж с данными из PostgreSQL

    Returns:
        Структурированные данные для Kafka
    """
    record_id, character_name, username, event_type, timestamp = record
    return {
        "id": record_id,
        "character_name": character_name,
        "username": username,
        "event_type": event_type,
        "timestamp": float(timestamp)
    }


def send_to_kafka(producer: KafkaProducer, message: dict) -> FutureRecordMetadata:
    """Отправляет сообщение в Kafka.

    Args:
        producer: Kafka producer
        message: Данные для отправки

    Returns:
        Future объект отправки

    Raises:
        Exception: При ошибке отправки
    """
    try:
        future = producer.send(config.KAFKA_CONFIG["topic"], message)
        future.get(timeout=10)
        logger.debug("Сообщение отправлено в Kafka: %s", message)
        return future
    except Exception as e:
        logger.error("Ошибка отправки сообщения в Kafka: %s", e)
        raise


def mark_record_as_sent(
        conn: pg_connection,
        cursor: pg_cursor,
        record_id: int
) -> None:
    """Отмечает запись как отправленную в PostgreSQL.

    Args:
        conn: Соединение с БД
        cursor: Курсор для выполнения запросов
        record_id: ID записи для обновления

    Raises:
        Exception: При ошибке обновления записи
    """
    try:
        cursor.execute(
            "UPDATE user_logins SET sent_to_kafka = TRUE WHERE id = %s",
            (record_id,)
        )
        conn.commit()
        logger.debug("Запись %d помечена как отправленная", record_id)
    except Exception as e:
        logger.error("Ошибка отметки записи %d как отправленной: %s", record_id, e)
        raise


def process_record(
        producer: KafkaProducer,
        conn: pg_connection,
        cursor: pg_cursor,
        record: tuple
) -> bool:
    """Обрабатывает одну запись.

    Args:
        producer: Kafka producer
        conn: Соединение с БД
        cursor: Курсор для выполнения запросов
        record: Запись для обработки

    Returns:
        True если обработка успешна, False в противном случае
    """
    try:
        message = prepare_kafka_message(record)
        record_id = record[0]

        send_to_kafka(producer, message)
        mark_record_as_sent(conn, cursor, record_id)

        char_name = message['character_name']
        event_type = message['event_type']
        logger.info("Обработана запись: %s - %s", char_name, event_type)
        return True

    except Exception as e:
        logger.error("Ошибка обработки записи %d: %s", record[0], e)
        return False


def process_batch(
        producer: KafkaProducer,
        conn: pg_connection,
        cursor: pg_cursor,
        records: list[tuple]
) -> int:
    """Обрабатывает пакет записей.

    Args:
        producer: Kafka producer
        conn: Соединение с БД
        cursor: Курсор для выполнения запросов
        records: Список записей для обработки

    Returns:
        Количество успешно обработанных записей
    """
    count = 0
    for record in records:
        if process_record(producer, conn, cursor, record):
            count += 1
    return count


def main() -> None:
    """Основная функция producer."""
    producer = None
    conn = None
    cursor = None

    try:
        producer = create_producer()
        conn, cursor = create_postgres_connection()

        logger.info("Producer запущен")

        while True:
            records = get_unsent_records(cursor)

            if not records:
                logger.debug("Неотправленные записи не найдены, ожидание...")
                time.sleep(5)
                continue

            count = process_batch(producer, conn, cursor, records)
            logger.info("Отправлено %d записей", count)

    except KeyboardInterrupt:
        logger.info("Producer остановлен пользователем")
    except Exception as e:
        logger.error("Критическая ошибка в producer: %s", e)
    finally:
        if producer:
            producer.close()
            logger.debug("Kafka producer закрыт")
        if conn:
            conn.close()
            logger.debug("Соединение с PostgreSQL закрыто")


if __name__ == "__main__":
    main()