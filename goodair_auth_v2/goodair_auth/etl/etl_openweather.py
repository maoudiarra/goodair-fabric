import requests
import psycopg
import os
import json
import io
from datetime import datetime, timezone
from dotenv import load_dotenv
from minio_client import get_minio_client

# ==============================
# CONFIG
# ==============================
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

VILLES = [
    "Paris", "Lyon", "Marseille", "Lille", "Toulouse",
    "Bordeaux", "Nantes", "Strasbourg", "Nice", "Montpellier"
]

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME",   "goodair_dw"),
    "user":     os.getenv("DB_USER",   "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host":     os.getenv("DB_HOST",   "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432))
}

# ==============================
# VALIDATION CONFIG
# ==============================
def validate_config():
    missing = [k for k, v in {
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "DB_PASSWORD":         DB_CONFIG["password"],
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Variables manquantes : {missing}")

# ==============================
# EXTRACTION
# ==============================
def extract_meteo(ville):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={ville}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
    except Exception as e:
        print(f"  Erreur requete API pour {ville} : {e}")
        return None

    if data.get("cod") != 200:
        print(f"  Erreur API OpenWeather pour {ville} : {data}")
        return None

    return data

# ==============================
# SAUVEGARDE BRONZE (MinIO)
# ==============================
def save_to_bronze(data, ville, timestamp):
    try:
        client = get_minio_client()

        # Chemin : bronze/openweather/2026/06/17/paris_14h.json
        path = (
            f"openweather/"
            f"{timestamp.year}/{timestamp.month:02d}/{timestamp.day:02d}/"
            f"{ville.lower()}_{timestamp.hour:02d}h.json"
        )

        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

        client.put_object(
            bucket_name="bronze",
            object_name=path,
            data=io.BytesIO(content),
            length=len(content),
            content_type="application/json"
        )
        print(f"  Bronze OK : {path}")
        return True
    except Exception as e:
        print(f"  Bronze ERREUR : {e}")
        return False

# ==============================
# TRANSFORMATION
# ==============================
def transform_meteo(data, ville):
    try:
        return {
            "temperature":   data["main"]["temp"],
            "humidite":      data["main"]["humidity"],
            "pression":      data["main"]["pressure"],
            "vitesse_vent":  data["wind"]["speed"],
            "precipitation": data.get("rain", {}).get("1h", 0.0),
            "indice_uv":     None,
            "ville":         ville,
            "lat":           data["coord"]["lat"],
            "lon":           data["coord"]["lon"],
            "timestamp":     datetime.now(timezone.utc)
        }
    except Exception as e:
        print(f"  Erreur transformation : {e}")
        return None

# ==============================
# VALIDATION QUALITE
# ==============================
def validate_mesure(m):
    errors = []
    if not (-30 <= m["temperature"] <= 60):
        errors.append(f"temperature aberrante : {m['temperature']}")
    if not (0 <= m["humidite"] <= 100):
        errors.append(f"humidite aberrante : {m['humidite']}")
    if not (900 <= m["pression"] <= 1100):
        errors.append(f"pression aberrante : {m['pression']}")
    if errors:
        print(f"  QUALITE KO : {errors}")
        return False
    return True

# ==============================
# LOAD PostgreSQL
# ==============================
def load_postgres(m):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            print(f"  PostgreSQL : {m['ville']}")

            cur.execute(
                "SELECT id_source FROM source WHERE nom_source='OpenWeatherMap'"
            )
            res = cur.fetchone()
            if not res:
                print("  Source OpenWeatherMap non trouvee")
                return
            id_source = res[0]

            cur.execute("""
                INSERT INTO temps (date_,heure,jour,mois,annee,timestamp_utc)
                VALUES (%s,%s,%s,%s,%s,%s) RETURNING id_temps
            """, (
                m["timestamp"].date(), m["timestamp"].hour,
                m["timestamp"].day,   m["timestamp"].month,
                m["timestamp"].year,  m["timestamp"]
            ))
            id_temps = cur.fetchone()[0]

            cur.execute(
                "SELECT id_loc FROM localisation WHERE nom_ville=%s",
                (m["ville"],)
            )
            res = cur.fetchone()
            if res:
                id_loc = res[0]
            else:
                cur.execute("""
                    INSERT INTO localisation (nom_ville,pays,latitude,longitude)
                    VALUES (%s,%s,%s,%s) RETURNING id_loc
                """, (m["ville"], "France", m["lat"], m["lon"]))
                id_loc = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO mesure_meteo
                (temperature,humidite,pression,vitesse_vent,
                 precipitation,indice_uv,id_source,id_loc,id_temps)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                m["temperature"], m["humidite"],    m["pression"],
                m["vitesse_vent"],m["precipitation"],m["indice_uv"],
                id_source, id_loc, id_temps
            ))

# ==============================
# MAIN
# ==============================
def main():
    print("=" * 40)
    print("ETL METEO START")
    print("=" * 40)

    validate_config()
    timestamp = datetime.now(timezone.utc)

    ok, ko = 0, 0
    for ville in VILLES:
        print(f"\nTraitement : {ville}")

        data = extract_meteo(ville)
        if not data:
            ko += 1
            continue

        # 1. Sauvegarde Bronze (JSON brut)
        save_to_bronze(data, ville, timestamp)

        # 2. Transformation
        mesure = transform_meteo(data, ville)
        if not mesure:
            ko += 1
            continue

        # 3. Validation qualite
        if not validate_mesure(mesure):
            ko += 1
            continue

        # 4. Load PostgreSQL
        load_postgres(mesure)
        ok += 1

    print(f"\nETL METEO DONE — OK: {ok} | KO: {ko}")

if __name__ == "__main__":
    main()