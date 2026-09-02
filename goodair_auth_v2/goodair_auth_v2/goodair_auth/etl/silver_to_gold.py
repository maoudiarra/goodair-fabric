import json
import io
import os
import csv
from datetime import datetime, timezone
from dotenv import load_dotenv
from minio_client import get_minio_client

load_dotenv()

client = get_minio_client()

# ==============================
# LIRE TOUS LES FICHIERS SILVER
# ==============================
def read_silver(prefix):
    results = []
    objects = client.list_objects("silver", prefix=prefix, recursive=True)
    for obj in objects:
        try:
            response = client.get_object("silver", obj.object_name)
            data = json.loads(response.read().decode("utf-8"))
            response.close()
            results.append(data)
        except Exception as e:
            print(f"  ERREUR lecture {obj.object_name} : {e}")
    return results

# ==============================
# AGGREGATION JOURNALIERE AQI
# ==============================
def aggregate_daily_aqi(records):
    villes = {}
    for r in records:
        if r.get("qualite") != "OK":
            continue
        ville = r.get("ville", "")
        aqi = r.get("aqi")
        if not ville or aqi is None:
            continue
        if ville not in villes:
            villes[ville] = []
        villes[ville].append(float(aqi))

    summary = []
    for ville, values in villes.items():
        summary.append({
            "ville":      ville,
            "aqi_moyen":  round(sum(values) / len(values), 2),
            "aqi_min":    round(min(values), 2),
            "aqi_max":    round(max(values), 2),
            "nb_mesures": len(values)
        })
    return sorted(summary, key=lambda x: x["aqi_moyen"], reverse=True)

# ==============================
# DATASET ML (jointure air + meteo)
# ==============================
def build_ml_dataset(aqicn_records, meteo_records):
    # Index meteo par ville
    meteo_index = {}
    for r in meteo_records:
        if r.get("qualite") == "OK":
            ville = r.get("ville", "").capitalize()
            meteo_index[ville] = r

    dataset = []
    for r in aqicn_records:
        if r.get("qualite") != "OK":
            continue
        ville = r.get("ville", "").capitalize()
        aqi   = r.get("aqi")
        if not ville or aqi is None:
            continue
        meteo = meteo_index.get(ville, {})
        if not meteo:
            continue

        now = datetime.now(timezone.utc)
        dataset.append({
            "ville":        ville,
            "aqi":          aqi,
            "pm25":         r.get("pm25"),
            "pm10":         r.get("pm10"),
            "o3":           r.get("o3"),
            "no2":          r.get("no2"),
            "temperature":  meteo.get("temperature"),
            "humidite":     meteo.get("humidite"),
            "pression":     meteo.get("pression"),
            "vitesse_vent": meteo.get("vitesse_vent"),
            "precipitation":meteo.get("precipitation"),
            "heure":        now.hour,
            "mois":         now.month,
            "jour_semaine": now.weekday()
        })
    return dataset

# ==============================
# SAUVEGARDER DANS GOLD
# ==============================
def save_json_to_gold(data, path):
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(
        bucket_name="gold",
        object_name=path,
        data=io.BytesIO(content),
        length=len(content),
        content_type="application/json"
    )
    print(f"  Gold OK (JSON) : {path}")

def save_csv_to_gold(records, path):
    if not records:
        print(f"  Aucune donnee pour : {path}")
        return

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

    content = output.getvalue().encode("utf-8")
    client.put_object(
        bucket_name="gold",
        object_name=path,
        data=io.BytesIO(content),
        length=len(content),
        content_type="text/csv"
    )
    print(f"  Gold OK (CSV)  : {path}")

# ==============================
# MAIN
# ==============================
def main():
    print("=" * 40)
    print("SILVER → GOLD START")
    print("=" * 40)

    today = datetime.now(timezone.utc)
    date_str = f"{today.year}/{today.month:02d}/{today.day:02d}"

    # 1. Lire Silver
    print("\n[Lecture Silver]")
    aqicn_records = read_silver("aqicn/")
    meteo_records  = read_silver("openweather/")
    print(f"  AQICN : {len(aqicn_records)} fichiers")
    print(f"  Meteo : {len(meteo_records)} fichiers")

    # 2. Agregation journaliere AQI → Gold JSON
    print("\n[Agregation journaliere AQI]")
    daily_summary = aggregate_daily_aqi(aqicn_records)
    save_json_to_gold(
        {"date": date_str, "villes": daily_summary},
        f"daily_summary/{date_str}/aqi_summary.json"
    )

    # 3. Dataset ML → Gold CSV
    print("\n[Dataset ML]")
    ml_dataset = build_ml_dataset(aqicn_records, meteo_records)
    save_csv_to_gold(
        ml_dataset,
        f"ml_features/{date_str}/dataset.csv"
    )
    print(f"  {len(ml_dataset)} lignes dans le dataset ML")

    print(f"\nSILVER → GOLD DONE")

if __name__ == "__main__":
    main()