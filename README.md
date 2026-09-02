# GoodAir sur Microsoft Fabric

Portage de la plateforme Big Data environnementale [GoodAir](https://github.com/maoudiarra/goodair-mspr2)
(Apache Airflow / MinIO / PostgreSQL / Django) vers Microsoft Fabric.

Collecte horaire de la qualité de l'air (AQICN) et des conditions
météorologiques (OpenWeatherMap) sur 10 villes françaises.

## Architecture

| GoodAir (v1) | Fabric (v2) |
|---|---|
| MinIO | OneLake / Lakehouse |
| Scripts Python + Airflow | Notebooks PySpark + Data Factory |
| PostgreSQL (schéma étoile) | Warehouse Fabric |
| Django + Leaflet | Power BI Direct Lake |

## Avancement

Voir [le journal de projet](JOURNAL_PROJET_GOODAIR_FABRIC.md).

## Configuration

Copier `secrets.example.json` en `secrets.json` et renseigner les clés API
AQICN et OpenWeatherMap, puis charger le fichier dans `Files/` du Lakehouse.
