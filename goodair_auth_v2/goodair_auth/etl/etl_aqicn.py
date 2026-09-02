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

AQICN_API_KEY = os.getenv("AQICN_API_KEY")

VILLES = [
    "paris", "lyon", "marseille", "lille", "toulouse",
    "bordeaux", "nantes", "strasbourg", "nice", "montpellier"
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
        "AQICN_API_KEY": AQICN_API_KEY,
        "DB_PASSWORD":   DB_CONFIG["password"],
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Variables manquantes : {missing}")

# ==============================
# EXTRACTION
# ==============================
def extract_aqicn(ville):
    url = f"https://api.waqi.info/feed/{ville}/?token={AQICN_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
    except Exception as e:
        print(f"  Erreur requete API pour {ville} : {e}")
        return None

    if data.get("status") != "ok":
        print(f"  Erreur API AQICN pour {ville} : {data}")
        return None

    return data["data"]

# ==============================
# SAUVEGARDE BRONZE (MinIO)
# ==============================
def save_to_bronze(data, ville, timestamp):
    try:
        client = get_minio_client()
        
        # Chemin : bronze/aqicn/2026/06/17/paris_14h.json
        path = (
            f"aqicn/"
            f"{timestamp.year}/{timestamp.month:02d}/{timestamp.day:02d}/"
            f"{ville}_{timestamp.hour:02d}h.json"
        )
        
        # Serialisation JSON
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
def transform_aqicn(data, ville):
    iaqi = data.get("iaqi", {})
    try:
        return {
            "aqi":       data.get("aqi"),
            "pm25":      iaqi.get("pm25", {}).get("v"),
            "pm10":      iaqi.get("pm10", {}).get("v"),
            "o3":        iaqi.get("o3",   {}).get("v"),
            "no2":       iaqi.get("no2",  {}).get("v"),
            "ville":     ville.capitalize(),
            "lat":       data["city"]["geo"][0],
            "lon":       data["city"]["geo"][1],
            "timestamp": datetime.now(timezone.utc)
        }
    except Exception as e:
        print(f"  Erreur transformation : {e}")
        return None

# ==============================
# VALIDATION QUALITE
# ==============================
def validate_mesure(m):
    errors = []
    if m["aqi"] is None:
        errors.append("aqi est NULL")
    elif not (0 <= float(m["aqi"]) <= 500):
        errors.append(f"aqi hors plage : {m['aqi']}")
    if m["pm25"] is not None and float(m["pm25"]) > 999:
        errors.append(f"pm25 aberrant : {m['pm25']}")
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

            cur.execute("SELECT id_source FROM source WHERE nom_source='AQICN'")
            res = cur.fetchone()
            if not res:
                print("  Source AQICN non trouvee")
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

            cur.execute("SELECT id_loc FROM localisation WHERE nom_ville=%s", (m["ville"],))
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
                INSERT INTO mesure_qualite_air
                (aqi,pm25,pm10,o3,no2,id_source,id_loc,id_temps)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                m["aqi"], m["pm25"], m["pm10"], m["o3"], m["no2"],
                id_source, id_loc, id_temps
            ))

# ==============================
# MAIN
# ==============================
def main():
    print("=" * 40)
    print("ETL AQICN START")
    print("=" * 40)

    validate_config()
    timestamp = datetime.now(timezone.utc)

    ok, ko = 0, 0
    for ville in VILLES:
        print(f"\nTraitement : {ville}")

        data = extract_aqicn(ville)
        if not data:
            ko += 1
            continue

        # 1. Sauvegarde Bronze (JSON brut)
        save_to_bronze(data, ville, timestamp)

        # 2. Transformation
        mesure = transform_aqicn(data, ville)
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

    print(f"\nETL AQICN DONE — OK: {ok} | KO: {ko}")

if __name__ == "__main__":
    main()