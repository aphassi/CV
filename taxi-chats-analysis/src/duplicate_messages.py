from datetime import date, timedelta
from difflib import SequenceMatcher
from typing import Optional
import hashlib
import os
import re

import pandas as pd
from dotenv import load_dotenv
from prefect import flow, task, get_run_logger
from sqlalchemy import create_engine, text


load_dotenv()

SOURCE_SCHEMA = "cdm"
SOURCE_TABLE = "searchable_messages"
TARGET_SCHEMA = "cdm"

MIN_SIMILARITY_SCORE = 95.0
MAX_LEN_DIFFERENCE = 15


def get_engine():
    """Создаёт подключение к PostgreSQL из DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Не задана переменная окружения DATABASE_URL. "
            "Пример: postgresql+psycopg2://user:password@localhost:5432/dbname"
        )
    return create_engine(database_url)


def clean_value(value):
    if value is None or pd.isna(value):
        return None
    return value


def normalize_text(text_value: str) -> str:
    """Нормализует текст перед поиском дублей."""
    if clean_value(text_value) is None:
        return ""

    normalized = str(text_value).lower().replace("ё", "е")
    normalized = re.sub(r"https?://\S+", " ", normalized)
    normalized = re.sub(r"www\.\S+", " ", normalized)
    normalized = re.sub(r"t\.me/\S+", " ", normalized)
    normalized = re.sub(r"@\w+", " ", normalized)
    normalized = re.sub(r"\+?\d[\d\-\(\)\s]{8,}\d", " ", normalized)
    normalized = re.sub(r"[^a-zа-я0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def make_text_hash(normalized_text: str) -> str:
    return hashlib.md5(normalized_text.encode("utf-8")).hexdigest()


def to_str_or_none(value):
    value = clean_value(value)
    return None if value is None else str(value)


def build_normalized_messages(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in df.iterrows():
        message_id = clean_value(row.get("message_id"))
        message_text = clean_value(row.get("message_text"))

        if not message_id or not message_text:
            continue

        normalized_text = normalize_text(message_text)
        if not normalized_text:
            continue

        rows.append(
            {
                "message_id": str(message_id),
                "message_group_id": to_str_or_none(row.get("group_id")),
                "author_id": to_str_or_none(row.get("author_id")),
                "source_code": to_str_or_none(row.get("source_code")),
                "message_ts": clean_value(row.get("message_ts")),
                "message_text": str(message_text).strip(),
                "normalized_text": normalized_text,
                "text_hash": make_text_hash(normalized_text),
                "text_length": len(normalized_text),
                "dt": row["dt"],
            }
        )

    return pd.DataFrame(rows)


def get_empty_exact_groups() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "group_id",
            "text_hash",
            "normalized_text",
            "messages_count",
            "first_message_ts",
            "last_message_ts",
            "dt",
        ]
    )


def get_empty_exact_items() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "group_id",
            "message_id",
            "author_id",
            "source_code",
            "message_ts",
            "message_text",
            "normalized_text",
            "dt",
        ]
    )


def get_empty_near_pairs() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "message_id_1",
            "message_id_2",
            "similarity_score",
            "rule_name",
            "dt",
        ]
    )


def build_exact_duplicate_groups(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return get_empty_exact_groups(), get_empty_exact_items()

    exact_groups = (
        df.groupby(["dt", "text_hash", "normalized_text"], as_index=False)
        .agg(
            messages_count=("message_id", "count"),
            first_message_ts=("message_ts", "min"),
            last_message_ts=("message_ts", "max"),
        )
    )

    exact_groups = exact_groups[exact_groups["messages_count"] > 1].copy()
    exact_groups = exact_groups.reset_index(drop=True)

    if exact_groups.empty:
        return get_empty_exact_groups(), get_empty_exact_items()

    exact_groups["group_id"] = exact_groups.index + 1

    exact_items = (
        df.merge(
            exact_groups[["group_id", "dt", "text_hash", "normalized_text"]],
            on=["dt", "text_hash", "normalized_text"],
            how="inner",
        )[
            [
                "group_id",
                "message_id",
                "author_id",
                "source_code",
                "message_ts",
                "message_text",
                "normalized_text",
                "dt",
            ]
        ]
        .sort_values(["group_id", "message_ts", "message_id"])
        .reset_index(drop=True)
    )

    exact_groups = exact_groups[
        [
            "group_id",
            "text_hash",
            "normalized_text",
            "messages_count",
            "first_message_ts",
            "last_message_ts",
            "dt",
        ]
    ]

    return exact_groups, exact_items


def build_near_duplicate_pairs(
    df: pd.DataFrame,
    exact_duplicate_message_ids: set[str],
    min_similarity_score: float = MIN_SIMILARITY_SCORE,
    max_length_diff: int = MAX_LEN_DIFFERENCE,
) -> pd.DataFrame:
    if df.empty:
        return get_empty_near_pairs()

    work_df = df[~df["message_id"].isin(exact_duplicate_message_ids)].copy()
    if work_df.empty:
        return get_empty_near_pairs()

    work_df = work_df.sort_values(
        ["dt", "message_group_id", "text_length", "message_id"]
    ).reset_index(drop=True)

    near_duplicate_rows = []

    for (dt_value, message_group_id), group_df in work_df.groupby(
        ["dt", "message_group_id"],
        dropna=False,
    ):
        rows = group_df.to_dict("records")

        for i in range(len(rows)):
            row_i = rows[i]

            for j in range(i + 1, len(rows)):
                row_j = rows[j]

                if row_j["text_length"] - row_i["text_length"] > max_length_diff:
                    break

                if abs(row_i["text_length"] - row_j["text_length"]) > max_length_diff:
                    continue

                score = (
                    SequenceMatcher(
                        None,
                        row_i["normalized_text"],
                        row_j["normalized_text"],
                    ).ratio()
                    * 100
                )

                if score >= min_similarity_score:
                    near_duplicate_rows.append(
                        {
                            "message_id_1": row_i["message_id"],
                            "message_id_2": row_j["message_id"],
                            "similarity_score": float(score),
                            "rule_name": (
                                f"sequence_matcher_ge_{int(min_similarity_score)}"
                            ),
                            "dt": dt_value,
                        }
                    )

    if not near_duplicate_rows:
        return get_empty_near_pairs()

    return pd.DataFrame(near_duplicate_rows)


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


def partition_exists(table_name: str, dt_value: date) -> bool:
    query = text(
        f"""
        SELECT EXISTS (
            SELECT 1
            FROM {TARGET_SCHEMA}.{table_name}
            WHERE dt = :dt
        )
        """
    )

    with get_engine().connect() as connection:
        return bool(connection.execute(query, {"dt": dt_value}).scalar())


def replace_partition(
    df: pd.DataFrame,
    table_name: str,
    dt_value: date,
) -> None:
    """Перезаписывает одну дневную партицию результата."""
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                DELETE FROM {TARGET_SCHEMA}.{table_name}
                WHERE dt = :dt
                """
            ),
            {"dt": dt_value},
        )

        if not df.empty:
            df.to_sql(
                table_name,
                connection,
                schema=TARGET_SCHEMA,
                if_exists="append",
                index=False,
                method="multi",
            )


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
def transform(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger = get_run_logger()

    normalized_df = build_normalized_messages(df)
    logger.info("Prepared %s normalized messages", len(normalized_df))

    exact_groups, exact_items = build_exact_duplicate_groups(normalized_df)
    exact_duplicate_message_ids = set(exact_items["message_id"].tolist())

    near_pairs = build_near_duplicate_pairs(
        normalized_df,
        exact_duplicate_message_ids=exact_duplicate_message_ids,
    )

    logger.info("Found %s exact duplicate groups", len(exact_groups))
    logger.info("Found %s exact duplicate items", len(exact_items))
    logger.info("Found %s near duplicate pairs", len(near_pairs))

    return exact_groups, exact_items, near_pairs


@task(retries=3, retry_delay_seconds=5)
def load_duplicate_results(
    exact_groups: pd.DataFrame,
    exact_items: pd.DataFrame,
    near_pairs: pd.DataFrame,
    dt_value: date,
) -> None:
    logger = get_run_logger()

    replace_partition(exact_groups, "duplicate_exact_groups", dt_value)
    replace_partition(exact_items, "duplicate_exact_items", dt_value)
    replace_partition(near_pairs, "duplicate_near_pairs", dt_value)

    logger.info("Loaded duplicate detection results to %s", TARGET_SCHEMA)


@flow(name="Duplicate Messages Date Flow")
def duplicate_messages_date_flow(dt_value: date) -> None:
    df = extract(dt_value)

    if df.empty:
        get_run_logger().warning(
            "No source messages found for %s in %s.%s",
            dt_value,
            SOURCE_SCHEMA,
            SOURCE_TABLE,
        )

    exact_groups, exact_items, near_pairs = transform(df)
    load_duplicate_results(exact_groups, exact_items, near_pairs, dt_value)


@flow(name="Duplicate Messages Flow")
def duplicate_messages_flow(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    force: bool = False,
) -> None:
    logger = get_run_logger()

    current = start_date or (date.today() - timedelta(days=1))
    end = end_date or (date.today() - timedelta(days=1))
    failed_dates = []

    while current <= end:
        if force or not partition_exists("duplicate_exact_groups", current):
            try:
                duplicate_messages_date_flow(current)
            except Exception as exc:
                logger.error("Failed %s: %s", current, exc)
                failed_dates.append(current)

        current += timedelta(days=1)

    if failed_dates:
        raise RuntimeError(f"Flow failed for dates: {failed_dates}")


if __name__ == "__main__":
    duplicate_messages_flow()
