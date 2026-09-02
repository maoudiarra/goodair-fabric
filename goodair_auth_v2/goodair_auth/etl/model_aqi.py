import pandas as pd
import numpy as np
import psycopg
import os
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

load_dotenv()

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME",   "goodair_dw"),
    "user":     os.getenv("DB_USER",   "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host":     os.getenv("DB_HOST",   "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432))
}

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================
# EXTRACTION FEATURES
# ==============================
def extract_features():
    print("\n[EXTRACTION DES DONNEES]")
    query = """
        SELECT
            mqa.aqi,
            mqa.pm25,
            mqa.pm10,
            mqa.o3,
            mqa.no2,
            mm.temperature,
            mm.humidite,
            mm.pression,
            mm.vitesse_vent,
            mm.precipitation,
            l.nom_ville,
            t_air.heure,
            t_air.mois,
            t_air.jour
        FROM mesure_qualite_air mqa
        JOIN temps t_air ON mqa.id_temps = t_air.id_temps
        JOIN mesure_meteo mm ON mqa.id_loc = mm.id_loc
        JOIN temps t_met ON mm.id_temps = t_met.id_temps
        JOIN localisation l ON mqa.id_loc = l.id_loc
        WHERE t_air.date_ = t_met.date_
          AND t_air.heure = t_met.heure
          AND mqa.aqi IS NOT NULL
          AND mm.temperature IS NOT NULL
        ORDER BY t_air.timestamp_utc
    """
    rows = []
    cols = ["aqi","pm25","pm10","o3","no2","temperature","humidite",
            "pression","vitesse_vent","precipitation","nom_ville",
            "heure","mois","jour"]

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=cols)
    print(f"  Lignes extraites : {len(df)}")
    return df

# ==============================
# PREPARATION DES DONNEES
# ==============================
def prepare_data(df):
    print("\n[PREPARATION DES DONNEES]")

    df = df.dropna(subset=["aqi"])
    print(f"  Apres suppression nulls AQI : {len(df)} lignes")

    le = LabelEncoder()
    df["ville_encoded"] = le.fit_transform(df["nom_ville"])
    print(f"  Villes encodees : {list(le.classes_)}")

    cols_num = ["pm25","pm10","o3","no2","temperature","humidite",
                "pression","vitesse_vent","precipitation"]
    for col in cols_num:
        nulls = df[col].isnull().sum()
        if nulls > 0:
            median = df[col].median()
            df[col] = df[col].fillna(median)
            print(f"  {col} : {nulls} nulls remplis par mediane ({median:.2f})")

    return df, le

# ==============================
# ENTRAINEMENT
# ==============================
def train_model(df):
    print("\n[ENTRAINEMENT DU MODELE]")

    FEATURES = [
        "temperature", "humidite", "pression",
        "vitesse_vent", "precipitation",
        "heure", "mois", "jour",
        "ville_encoded"
    ]
    TARGET = "aqi"

    X = df[FEATURES]
    y = df[TARGET].astype(float)

    print(f"  Dataset : {len(X)} lignes x {len(FEATURES)} features")
    print(f"  AQI min: {y.min():.1f} | max: {y.max():.1f} | moy: {y.mean():.1f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Train : {len(X_train)} | Test : {len(X_test)}")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"\n  === METRIQUES ===")
    print(f"  R2   : {r2:.4f}  {'OK' if r2 >= 0.5 else 'INSUFFISANT'}")
    print(f"  MAE  : {mae:.4f}")
    print(f"  RMSE : {rmse:.4f}")

    importance = pd.DataFrame({
        "feature":    FEATURES,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    print(f"\n  === IMPORTANCE DES VARIABLES ===")
    for _, row in importance.iterrows():
        bar = "█" * int(row["importance"] * 50)
        print(f"  {row['feature']:20s} {bar} {row['importance']:.4f}")

    return model, y_test, y_pred, r2, mae, rmse, importance, FEATURES

# ==============================
# GRAPHIQUES
# ==============================
def save_plots(y_test, y_pred, importance):
    print("\n[GENERATION DES GRAPHIQUES]")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Predictions vs Reel
    axes[0].scatter(y_test, y_pred, alpha=0.6, color="#2980B9", s=30)
    min_val = float(min(y_test.min(), y_pred.min()))
    max_val = float(max(y_test.max(), y_pred.max()))
    axes[0].plot([min_val, max_val], [min_val, max_val],
                 'r--', linewidth=2, label="Prediction parfaite")
    axes[0].set_xlabel("AQI Reel", fontsize=12)
    axes[0].set_ylabel("AQI Predit", fontsize=12)
    axes[0].set_title("Predictions vs Valeurs Reelles", fontsize=13, fontweight="bold")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Feature Importance
    colors = ["#7B2D8B" if i == 0 else "#AED6F1" for i in range(len(importance))]
    axes[1].barh(importance["feature"], importance["importance"], color=colors)
    axes[1].set_xlabel("Importance", fontsize=12)
    axes[1].set_title("Importance des variables", fontsize=13, fontweight="bold")
    axes[1].invert_yaxis()
    axes[1].grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "ml_results.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Graphique sauvegarde : {path}")
    return path

# ==============================
# EXPORT MODELE
# ==============================
def save_model(model, le, features):
    path = os.path.join(OUTPUT_DIR, "model_aqi.joblib")
    joblib.dump({
        "model":    model,
        "encoder":  le,
        "features": features,
        "date":     datetime.now().isoformat()
    }, path)
    print(f"  Modele exporte : {path}")
    return path

# ==============================
# MAIN
# ==============================
def main():
    print("=" * 40)
    print("MACHINE LEARNING — PREDICTION AQI")
    print("=" * 40)

    df = extract_features()

    if len(df) < 20:
        print(f"\nINSUFFISANT : seulement {len(df)} lignes.")
        return

    df, le = prepare_data(df)
    model, y_test, y_pred, r2, mae, rmse, importance, features = train_model(df)
    save_plots(y_test, y_pred, importance)
    save_model(model, le, features)

    print("\n" + "=" * 40)
    print("BILAN MACHINE LEARNING")
    print("=" * 40)
    print(f"  R2   : {r2:.4f}  {'OBJECTIF ATTEINT (>0.5)' if r2 >= 0.5 else 'OBJECTIF NON ATTEINT'}")
    print(f"  MAE  : {mae:.4f} points AQI en moyenne")
    print(f"  RMSE : {rmse:.4f}")
    print(f"  Variable la plus influente : {importance.iloc[0]['feature']}")

if __name__ == "__main__":
    main()