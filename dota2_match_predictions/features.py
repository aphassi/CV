from __future__ import annotations

import numpy as np
import pandas as pd
import category_encoders
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics import roc_auc_score


class HeroesEncoder:
    """Кодирует пики героев в разреженный вектор. Герой Radiant получает значение +1, герой Dire -1"""

    def __init__(self, player_df: pd.DataFrame, heroes_df: pd.DataFrame):
        self.player_df = player_df
        self.heroes_df = heroes_df

    def fit(self, X: pd.DataFrame, y=None):
        self.ids = sorted(self.heroes_df["id"].unique())
        self.hero_indx = {}

        for i, hero_id in enumerate(self.ids):
            self.hero_indx[hero_id] = i

        return self

    def transform(self, X: pd.DataFrame, y=None):
        now = self.player_df[
            self.player_df["match_id"].isin(X["match_id"])
        ].copy()
        now = now[now["hero_id"].isin(self.ids)]

        matches = {}
        for i, match_id in enumerate(X["match_id"].values):
            matches[match_id] = i

        row = []
        col = []
        numb = []

        for _, player in now.iterrows():
            row.append(matches[player["match_id"]])
            col.append(self.hero_indx[player["hero_id"]])

            if player["player_slot"] < 128:
                numb.append(1)
            else:
                numb.append(-1)

        return csr_matrix(
            (numb, (row, col)),
            shape=(X.shape[0], len(self.ids)),
        )


def gini_score(y_true, y_score) -> float:
    """Gini = 2 * ROC-AUC - 1."""
    return 2 * roc_auc_score(y_true, y_score) - 1.0


def prepare_basic_features(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Генерирует признаки по дате, региону и пропускам MMR."""

    df_train = df_train.copy()
    df_test = df_test.copy()

    df_train["date"] = pd.to_datetime(df_train["date"])
    df_test["date"] = pd.to_datetime(df_test["date"])

    df_train["day"] = df_train["date"].dt.day
    df_test["day"] = df_test["date"].dt.day

    df_train["dayofweek"] = df_train["date"].dt.dayofweek
    df_test["dayofweek"] = df_test["date"].dt.dayofweek

    y_train = df_train["radiant_win"]

    common_columns = [
        column for column in df_train.columns
        if column in df_test.columns
    ]

    region_encoder = category_encoders.OneHotEncoder(
        cols=["region"],
        use_cat_names=True,
    )
    X_train = region_encoder.fit_transform(
        df_train[common_columns]
    )
    X_test = region_encoder.transform(
        df_test[common_columns]
    )

    df_train = X_train.copy()
    df_train["radiant_win"] = y_train.values
    df_test = X_test.copy()

    y_train = df_train["radiant_win"]

    weekday_encoder = category_encoders.OneHotEncoder(
        cols=["dayofweek"],
        use_cat_names=True,
    )
    common_columns = [
        column for column in df_train.columns
        if column in df_test.columns
    ]

    X_train = weekday_encoder.fit_transform(
        df_train[common_columns]
    )
    X_test = weekday_encoder.transform(
        df_test[common_columns]
    )

    df_train = X_train.copy()
    df_train["radiant_win"] = y_train.values
    df_test = X_test.copy()

    df_train = df_train.sort_values("date").reset_index(drop=True)

    df_train["mmr_missing"] = df_train["avg_mmr"].isna()
    df_test["mmr_missing"] = df_test["avg_mmr"].isna()

    return df_train, df_test


def base_feature_columns(df: pd.DataFrame) -> list[str]:
    """Возвращает набор табличных признаков финальной модели."""
    return (
        ["day"]
        + [
            column
            for column in df.columns
            if column.startswith("dayofweek_")
        ]
        + [
            column
            for column in df.columns
            if column.startswith("region_")
        ]
        + ["mmr_missing", "sqrt_mmr"]
    )


def build_validation_matrices(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    player_df: pd.DataFrame,
    heroes_df: pd.DataFrame,
    train_fraction: float = 0.8,
):
    """Строит train/validation/test matrices по логике финального ноутбука."""

    split_index = int(df_train.shape[0] * train_fraction)

    train = df_train.iloc[:split_index].copy()
    valid = df_train.iloc[split_index:].copy()
    test = df_test.copy()

    mmr_median = train["avg_mmr"].median()

    train["avg_mmr"] = train["avg_mmr"].fillna(mmr_median)
    valid["avg_mmr"] = valid["avg_mmr"].fillna(mmr_median)
    test["avg_mmr"] = test["avg_mmr"].fillna(mmr_median)

    train["sqrt_mmr"] = np.sqrt(train["avg_mmr"])
    valid["sqrt_mmr"] = np.sqrt(valid["avg_mmr"])
    test["sqrt_mmr"] = np.sqrt(test["avg_mmr"])

    train_columns = base_feature_columns(train)
    valid_columns = base_feature_columns(valid)
    test_columns = base_feature_columns(test)

    X_train_base = train[train_columns]
    X_valid_base = valid[valid_columns]
    X_test_base = test[test_columns]

    encoder = HeroesEncoder(player_df, heroes_df)
    encoder.fit(df_train[["match_id"]])

    X_train_heroes = encoder.transform(train[["match_id"]])
    X_valid_heroes = encoder.transform(valid[["match_id"]])
    X_test_heroes = encoder.transform(test[["match_id"]])

    X_train_full = hstack(
        [
            csr_matrix(X_train_base.astype(float).values),
            X_train_heroes,
        ],
        format="csr",
    )
    X_valid_full = hstack(
        [
            csr_matrix(X_valid_base.astype(float).values),
            X_valid_heroes,
        ],
        format="csr",
    )
    X_test_full = hstack(
        [
            csr_matrix(X_test_base.astype(float).values),
            X_test_heroes,
        ],
        format="csr",
    )

    return {
        "train": train,
        "valid": valid,
        "test": test,
        "X_train": X_train_full,
        "X_valid": X_valid_full,
        "X_test": X_test_full,
        "y_train": train["radiant_win"],
        "y_valid": valid["radiant_win"],
        "mmr_median": mmr_median,
        "heroes_encoder": encoder,
    }


def build_full_training_matrix(
    df_train: pd.DataFrame,
    mmr_median: float,
    heroes_encoder: HeroesEncoder,
):
    """Собирает признаки для переобучения финальной модели на всём train."""

    df_train_full = df_train.copy()
    df_train_full["avg_mmr"] = (
        df_train_full["avg_mmr"].fillna(mmr_median)
    )
    df_train_full["sqrt_mmr"] = np.sqrt(
        df_train_full["avg_mmr"]
    )

    columns = base_feature_columns(df_train_full)
    X_train_base_full = df_train_full[columns]

    X_train_heroes_full = heroes_encoder.transform(
        df_train_full[["match_id"]]
    )

    X_train_full = hstack(
        [
            csr_matrix(
                X_train_base_full.astype(float).values
            ),
            X_train_heroes_full,
        ],
        format="csr",
    )

    y_train_full = df_train_full["radiant_win"]

    return X_train_full, y_train_full
