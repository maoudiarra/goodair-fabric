import json
import io
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from minio_client import get_minio_client

load_dotenv()

client = get_minio_client()

# ==============================
# REGLES DE NETTOYAGE AQICN
# ==============================
def clean_aqicn(data, nom_fichier):
    errors = []
    
    aqi  = data.get("aqi")
    iaqi = data.get("iaqi", {})
    city = data.get("city", {})
    
    # Extraire le nom de ville depuis le nom du fichier
    # ex: "paris_12h.json" → "Paris"
    ville = nom_fichier.replace(".json", "").split("_")[0].capitalize()
    
    # Validation AQI
    if aqi is None:
        errors.append("aqi manquant")
    elif not (0 <= float(aqi) <= 500):
        errors.append(f"aqi hors plage : {aqi}")
    
    cleaned = {
        "source":        "AQICN",
        "fichier":       nom_fichier,
        "ville":         ville,   # ← nom extrait du fichier, pas de city.name
        "aqi":           float(aqi) if aqi is not None else None,
        "pm25":          iaqi.get("pm25", {}).get("v"),
        "pm10":          iaqi.get("pm10", {}).get("v"),
        "o3":            iaqi.get("o3",   {}).get("v"),
        "no2":           iaqi.get("no2",  {}).get("v"),
        "lat":           city.get("geo", [None, None])[0],
        "lon":           city.get("geo", [None, None])[1],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "qualite":       "OK" if not errors else "WARNING",
        "erreurs":       errors
    }
    return cleaned
# ==============================
# REGLES DE NETTOYAGE OPENWEATHER
# ==============================
def clean_openweather(data, nom_fichier):
    errors = []
    
    temp = data.get("main", {}).get("temp")
    hum  = data.get("main", {}).get("humidity")
    pres = data.get("main", {}).get("pressure")
    
    if temp is not None and not (-30 <= temp <= 60):
        errors.append(f"temperature aberrante : {temp}")
    if hum is not None and not (0 <= hum <= 100):
        errors.append(f"humidite aberrante : {hum}")
    if pres is not None and not (900 <= pres <= 1100):
        errors.append(f"pression aberrante : {pres}")
    
    cleaned = {
        "source":        "OpenWeatherMap",
        "fichier":       nom_fichier,
        "ville":         data.get("name", "").capitalize(),
        "temperature":   temp,
        "humidite":      hum,
        "pression":      pres,
        "vitesse_vent":  data.get("wind", {}).get("speed"),
        "precipitation": data.get("rain", {}).get("1h", 0.0),
        "lat":           data.get("coord", {}).get("lat"),
        "lon":           data.get("coord", {}).get("lon"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "qualite":       "OK" if not errors else "WARNING",
        "erreurs":       errors
    }
    return cleaned

# ==============================
# TRAITEMENT D'UN FICHIER
# ==============================
def process_file(bucket_src, object_name, cleaner, bucket_dst, prefix_dst):
    try:
        # Lire depuis Bronze
        response = client.get_object(bucket_src, object_name)
        data = json.loads(response.read().decode("utf-8"))
        response.close()

        # Nettoyer
        nom_fichier = object_name.split("/")[-1]
        cleaned = cleaner(data, nom_fichier)

        # Ecrire dans Silver avec meme structure de chemin
        parts = object_name.split("/")
        silver_path = prefix_dst + "/".join(parts[1:])  # retire le prefixe source

        content = json.dumps(cleaned, ensure_ascii=False, indent=2).encode("utf-8")
        client.put_object(
            bucket_name=bucket_dst,
            object_name=silver_path,
            data=io.BytesIO(content),
            length=len(content),
            content_type="application/json"
        )
        statut = cleaned["qualite"]
        print(f"  Silver {statut} : {silver_path}")
        return True

    except Exception as e:
        print(f"  ERREUR : {object_name} -> {e}")
        return False

# ==============================
# MAIN
# ==============================
def main():
    print("=" * 40)
    print("BRONZE → SILVER START")
    print("=" * 40)

    ok = ko = 0

    # Traiter AQICN
    print("\n[AQICN]")
    objects = client.list_objects("bronze", prefix="aqicn/", recursive=True)
    for obj in objects:
        print(f"  Traitement : {obj.object_name}")
        result = process_file(
            "bronze", obj.object_name,
            clean_aqicn,
            "silver", "aqicn/"
        )
        if result: ok += 1
        else: ko += 1

    # Traiter OpenWeather
    print("\n[OpenWeather]")
    objects = client.list_objects("bronze", prefix="openweather/", recursive=True)
    for obj in objects:
        print(f"  Traitement : {obj.object_name}")
        result = process_file(
            "bronze", obj.object_name,
            clean_openweather,
            "silver", "openweather/"
        )
        if result: ok += 1
        else: ko += 1

    print(f"\nBRONZE → SILVER DONE — OK: {ok} | KO: {ko}")

if __name__ == "__main__":
    main()