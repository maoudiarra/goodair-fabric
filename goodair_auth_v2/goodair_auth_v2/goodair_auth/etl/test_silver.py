from minio_client import get_minio_client
import json

client = get_minio_client()

# AQICN Silver
r = client.get_object("silver", "aqicn/2026/06/17/paris_12h.json")
d = json.loads(r.read())
print("AQICN ville:", repr(d.get("ville")))

# OpenWeather Silver
r = client.get_object("silver", "openweather/2026/06/17/paris_12h.json")
d = json.loads(r.read())
print("Meteo ville:", repr(d.get("ville")))