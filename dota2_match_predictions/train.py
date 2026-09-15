from __future__ import annotations

import argparse
from pathlib import Path

import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.features import (
    build_full_training_matrix,
    build_validation_matrices,
    gini_score,
    prepare_basic_features,
)


def load_data(data_dir: Path):
    df_train = pd.read_csv(
        data_dir / "matches_df_train.csv"
    )
    df_test = pd.read_csv(
        data_dir / "matches_df_test.csv"
    )
    player_df = pd.read_csv(
        data_dir / "player_df.csv"
    )
    heroes_df = pd.read_csv(
        data_dir / "Constants.Heroes.csv"
    )

    return df_train, df_test, player_df, heroes_df


def optimize_model(
    X_train,
    y_train,
    X_valid,
    y_valid,
    n_trials: int,
):
    def objective(trial):
        params = {
            "C": trial.suggest_float(
                "C",
                2.0,
                4.0,
                log=True,
            ),
            "solver": "lbfgs",
            "max_iter": trial.suggest_int(
                "max_iter",
                2500,
                5000,
                step=500,
            ),
        }

        model = LogisticRegression(**params)
        model.fit(X_train, y_train)

        prediction = model.predict_proba(
            X_valid
        )[:, 1]

        return gini_score(y_valid, prediction)

    study = optuna.create_study(
        direction="maximize"
    )
    study.optimize(
        objective,
        n_trials=n_trials,
    )

    return study


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Предсказание победы Radiant "
            "в матчах Dota 2."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Папка с CSV-файлами.",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=8,
        help="Количество trials Optuna.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("submission.csv"),
        help="Путь к итоговому submission.",
    )
    args = parser.parse_args()

    (
        df_train,
        df_test,
        player_df,
        heroes_df,
    ) = load_data(args.data_dir)

    df_train, df_test = prepare_basic_features(
        df_train,
        df_test,
    )

    matrices = build_validation_matrices(
        df_train,
        df_test,
        player_df,
        heroes_df,
    )

    study = optimize_model(
        matrices["X_train"],
        matrices["y_train"],
        matrices["X_valid"],
        matrices["y_valid"],
        n_trials=args.trials,
    )

    print("Best parameters:", study.best_params)
    print("Best validation Gini:", study.best_value)

    X_train_full, y_train_full = (
        build_full_training_matrix(
            df_train,
            matrices["mmr_median"],
            matrices["heroes_encoder"],
        )
    )

    final_model = LogisticRegression(
        **study.best_params
    )
    final_model.fit(
        X_train_full,
        y_train_full,
    )

    predictions = final_model.predict_proba(
        matrices["X_test"]
    )[:, 1]

    submission = pd.DataFrame(
        {
            "ID": matrices["test"]["match_id"],
            "Value": predictions,
        }
    )
    submission.to_csv(
        args.output,
        index=False,
    )

    print(f"Saved predictions to {args.output}")


if __name__ == "__main__":
    main()
