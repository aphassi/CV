from datetime import date, timedelta
from typing import Optional
import os

import pandas as pd
import requests
from dotenv import load_dotenv
from prefect import flow, task, get_run_logger
from sqlalchemy import create_engine, text


load_dotenv()

SOURCE_SCHEMA = "cdm"
SOURCE_TABLE = "searchable_messages"
TARGET_SCHEMA = "cdm"
TARGET_TABLE = "message_embeddings"

EMBEDDING_URL = (
    "https://ai.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Не задана переменная окружения {name}")
    return value


def get_engine():
    """Создаёт подключение к PostgreSQL из DATABASE_URL."""
    database_url = require_env("DATABASE_URL")
    return create_engine(database_url)


def clean_value(value):
    if value is None or pd.isna(value):
        return None
    return value


def embedding_to_pgvector(embedding: list[float]) -> str:
    return "[" + ",".join(str(float(x)) for x in embedding) + "]"


def get_yandex_embedding(text_value: str) -> list[float]:
    api_key = require_env("YANDEX_API_KEY")
    folder_id = require_env("YANDEX_FOLDER_ID")
    model_uri = f"emb://{folder_id}/text-search-doc/latest"

    response = requests.post(
        EMBEDDING_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "x-folder-id": folder_id,
        },
        json={
            "modelUri": model_uri,
            "text": text_value,
        },
        timeout=60,
    )

    response.raise_for_status()
    data = response.json()

    return [float(value) for value in data["embedding"]]


def read_messages_for_date(dt_value: date) -> pd.DataFrame:
    query = text(
        f"""
        SELECT
            message_id,
            group_id,
            author_id,
            source_code,
            message_ts,
            message_text,
            dt
        FROM {SOURCE_SCHEMA}.{SOURCE_TABLE}
        WHERE dt = :dt
        """
    )

    with get_engine().connect() as connection:
        return pd.read_sql(query, connection, params={"dt": dt_value})


def partition_exists(dt_value: date) -> bool:
    query = text(
        f"""
        SELECT EXISTS (
            SELECT 1
            FROM {TARGET_SCHEMA}.{TARGET_TABLE}
            WHERE dt = :dt
        )
        """
    )

    with get_engine().connect() as connection:
        return bool(connection.execute(query, {"dt": dt_value}).scalar())


@task(retries=3, retry_delay_seconds=5)
def extract(dt_value: date) -> pd.DataFrame:
    logger = get_run_logger()
    df = read_messages_for_date(dt_value)

    logger.info(
        "Read %s records from %s.%s for %s",
        len(df),
        SOURCE_SCHEMA,
        SOURCE_TABLE,
        dt_value,
    )

    return df


@task(retries=3, retry_delay_seconds=5)
def transform(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    rows = []

    for _, row in df.iterrows():
        message_id = clean_value(row.get("message_id"))
        message_text = clean_value(row.get("message_text"))

        if not message_id or not message_text:
            continue

        message_text = str(message_text).strip()
        if not message_text:
            continue

        embedding = get_yandex_embedding(message_text)

        rows.append(
            {
                "message_id": str(message_id),
                "group_id": (
                    str(row.get("group_id"))
                    if clean_value(row.get("group_id")) is not None
                    else None
                ),
                "author_id": (
                    str(row.get("author_id"))
                    if clean_value(row.get("author_id")) is not None
                    else None
                ),
                "source_code": (
                    str(row.get("source_code"))
                    if clean_value(row.get("source_code")) is not None
                    else None
                ),
                "message_ts": clean_value(row.get("message_ts")),
                "message_text": message_text,
                "embedding": embedding_to_pgvector(embedding),
                "dt": row["dt"],
            }
        )

    result = pd.DataFrame(rows)
    logger.info("Prepared %s message embeddings", len(result))

    return result


@task(retries=3, retry_delay_seconds=5)
def load_embeddings(df: pd.DataFrame, dt_value: date) -> None:
    """
    Перезаписывает эмбеддинги за одну дату.

    CAST(:embedding AS vector) используется явно, чтобы PostgreSQL корректно
    преобразовал строковое представление в тип pgvector.
    """
    logger = get_run_logger()
    engine = get_engine()

    insert_query = text(
        f"""
        INSERT INTO {TARGET_SCHEMA}.{TARGET_TABLE} (
            message_id,
            group_id,
            author_id,
            source_code,
            message_ts,
            message_text,
            embedding,
            dt
        )
        VALUES (
            :message_id,
            :group_id,
            :author_id,
            :source_code,
            :message_ts,
            :message_text,
            CAST(:embedding AS vector),
            :dt
        )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                DELETE FROM {TARGET_SCHEMA}.{TARGET_TABLE}
                WHERE dt = :dt
                """
            ),
            {"dt": dt_value},
        )

        if not df.empty:
            connection.execute(insert_query, df.to_dict("records"))

    logger.info(
        "Loaded %s embeddings to %s.%s",
        len(df),
        TARGET_SCHEMA,
        TARGET_TABLE,
    )


@flow(name="Message Embeddings Date Flow")
def message_embeddings_date_flow(dt_value: date) -> None:
    df = extract(dt_value)

    if df.empty:
        get_run_logger().warning(
            "No source messages found for %s in %s.%s",
            dt_value,
            SOURCE_SCHEMA,
            SOURCE_TABLE,
        )

    embeddings_df = transform(df)
    load_embeddings(embeddings_df, dt_value)


@flow(name="Message Embeddings Flow")
def message_embeddings_flow(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    force: bool = False,
) -> None:
    logger = get_run_logger()

    current = start_date or (date.today() - timedelta(days=1))
    end = end_date or (date.today() - timedelta(days=1))
    failed_dates = []

    while current <= end:
        if force or not partition_exists(current):
            try:
                message_embeddings_date_flow(current)
            except Exception as exc:
                logger.error("Failed %s: %s", current, exc)
                failed_dates.append(current)

        current += timedelta(days=1)

    if failed_dates:
        raise RuntimeError(f"Flow failed for dates: {failed_dates}")


if __name__ == "__main__":
    message_embeddings_flow()
