import psycopg
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME",   "goodair_dw"),
    "user":     os.getenv("DB_USER",   "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host":     os.getenv("DB_HOST",   "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432))
}

SEUIL_COMPLETUDE = 80.0  # % minimum acceptable

# ==============================
# CONTROLES QUALITE AIR
# ==============================
def check_qualite_air(cur):
    print("\n[QUALITE AIR — mesure_qualite_air]")
    details = []

    # Total enregistrements
    cur.execute("SELECT COUNT(*) FROM mesure_qualite_air")
    total = cur.fetchone()[0]
    print(f"  Total enregistrements : {total}")

    # Doublons (meme ville, meme heure)
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT id_loc, id_temps, COUNT(*) as cnt
            FROM mesure_qualite_air
            GROUP BY id_loc, id_temps
            HAVING COUNT(*) > 1
        ) sub
    """)
    doublons = cur.fetchone()[0]
    print(f"  Doublons (ville+heure) : {doublons}")
    if doublons > 0:
        details.append(f"{doublons} doublons detectes")

    # Nulls AQI
    cur.execute("SELECT COUNT(*) FROM mesure_qualite_air WHERE aqi IS NULL")
    nulls_aqi = cur.fetchone()[0]
    print(f"  AQI null : {nulls_aqi}")

    # Nulls PM2.5
    cur.execute("SELECT COUNT(*) FROM mesure_qualite_air WHERE pm25 IS NULL")
    nulls_pm25 = cur.fetchone()[0]
    print(f"  PM2.5 null : {nulls_pm25}")

    # Total nulls
    nb_nulls = nulls_aqi + nulls_pm25

    # Valeurs aberrantes AQI
    cur.execute("""
        SELECT COUNT(*) FROM mesure_qualite_air
        WHERE aqi IS NOT NULL AND (aqi < 0 OR aqi > 500)
    """)
    aberrants_aqi = cur.fetchone()[0]
    print(f"  AQI aberrant (<0 ou >500) : {aberrants_aqi}")
    if aberrants_aqi > 0:
        details.append(f"{aberrants_aqi} valeurs AQI aberrantes")

    # Taux de completude
    if total > 0:
        nb_complets = total - nulls_aqi
        taux = round((nb_complets / total) * 100, 2)
    else:
        taux = 0.0

    statut = "OK" if taux >= SEUIL_COMPLETUDE and doublons == 0 else "WARNING"
    if taux < SEUIL_COMPLETUDE:
        details.append(f"Taux completude insuffisant : {taux}%")

    print(f"  Taux completude AQI : {taux}%")
    print(f"  Statut : {statut}")

    return {
        "source":             "AQICN",
        "nb_enregistrements": total,
        "nb_doublons":        doublons,
        "nb_nulls":           nb_nulls,
        "nb_aberrants":       aberrants_aqi,
        "taux_completude":    taux,
        "statut":             statut,
        "details":            " | ".join(details) if details else "Aucune anomalie"
    }

# ==============================
# CONTROLES QUALITE METEO
# ==============================
def check_qualite_meteo(cur):
    print("\n[QUALITE METEO — mesure_meteo]")
    details = []

    # Total
    cur.execute("SELECT COUNT(*) FROM mesure_meteo")
    total = cur.fetchone()[0]
    print(f"  Total enregistrements : {total}")

    # Doublons
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT id_loc, id_temps, COUNT(*) as cnt
            FROM mesure_meteo
            GROUP BY id_loc, id_temps
            HAVING COUNT(*) > 1
        ) sub
    """)
    doublons = cur.fetchone()[0]
    print(f"  Doublons (ville+heure) : {doublons}")
    if doublons > 0:
        details.append(f"{doublons} doublons detectes")

    # Nulls temperature
    cur.execute("SELECT COUNT(*) FROM mesure_meteo WHERE temperature IS NULL")
    nulls_temp = cur.fetchone()[0]
    print(f"  Temperature null : {nulls_temp}")

    # Nulls humidite
    cur.execute("SELECT COUNT(*) FROM mesure_meteo WHERE humidite IS NULL")
    nulls_hum = cur.fetchone()[0]
    print(f"  Humidite null : {nulls_hum}")

    nb_nulls = nulls_temp + nulls_hum

    # Valeurs aberrantes temperature
    cur.execute("""
        SELECT COUNT(*) FROM mesure_meteo
        WHERE temperature IS NOT NULL
        AND (temperature < -30 OR temperature > 60)
    """)
    aberrants_temp = cur.fetchone()[0]
    print(f"  Temperature aberrante : {aberrants_temp}")

    # Valeurs aberrantes humidite
    cur.execute("""
        SELECT COUNT(*) FROM mesure_meteo
        WHERE humidite IS NOT NULL
        AND (humidite < 0 OR humidite > 100)
    """)
    aberrants_hum = cur.fetchone()[0]
    print(f"  Humidite aberrante : {aberrants_hum}")

    # Valeurs aberrantes pression
    cur.execute("""
        SELECT COUNT(*) FROM mesure_meteo
        WHERE pression IS NOT NULL
        AND (pression < 900 OR pression > 1100)
    """)
    aberrants_pres = cur.fetchone()[0]
    print(f"  Pression aberrante : {aberrants_pres}")

    nb_aberrants = aberrants_temp + aberrants_hum + aberrants_pres
    if nb_aberrants > 0:
        details.append(f"{nb_aberrants} valeurs aberrantes detectees")

    # Taux completude
    if total > 0:
        nb_complets = total - nulls_temp
        taux = round((nb_complets / total) * 100, 2)
    else:
        taux = 0.0

    statut = "OK" if taux >= SEUIL_COMPLETUDE and doublons == 0 else "WARNING"
    if taux < SEUIL_COMPLETUDE:
        details.append(f"Taux completude insuffisant : {taux}%")

    print(f"  Taux completude : {taux}%")
    print(f"  Statut : {statut}")

    return {
        "source":             "OpenWeatherMap",
        "nb_enregistrements": total,
        "nb_doublons":        doublons,
        "nb_nulls":           nb_nulls,
        "nb_aberrants":       nb_aberrants,
        "taux_completude":    taux,
        "statut":             statut,
        "details":            " | ".join(details) if details else "Aucune anomalie"
    }

# ==============================
# CONTROLES COHERENCE
# ==============================
def check_coherence(cur):
    print("\n[COHERENCE — Villes sans donnees recentes]")
    details = []

    # Villes sans mesure AQI dans les 2 dernieres heures
    cur.execute("""
        SELECT l.nom_ville
        FROM localisation l
        WHERE NOT EXISTS (
            SELECT 1 FROM mesure_qualite_air mqa
            JOIN temps t ON mqa.id_temps = t.id_temps
            WHERE mqa.id_loc = l.id_loc
            AND t.timestamp_utc >= NOW() - INTERVAL '2 hours'
        )
    """)
    villes_sans_air = [r[0] for r in cur.fetchall()]
    if villes_sans_air:
        msg = f"Villes sans AQI recent : {', '.join(villes_sans_air)}"
        print(f"  {msg}")
        details.append(msg)
    else:
        print("  Toutes les villes ont des donnees AQI recentes")

    # Trous temporels
    cur.execute("""
        SELECT COUNT(DISTINCT DATE_TRUNC('hour', timestamp_utc)) as nb_heures
        FROM temps
        WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
    """)
    nb_heures = cur.fetchone()[0]
    print(f"  Heures distinctes dans les 24h : {nb_heures}/24")
    if nb_heures < 20:
        details.append(f"Trous temporels detectes : seulement {nb_heures}/24 heures")

    return details

# ==============================
# SAUVEGARDER RAPPORT EN BASE
# ==============================
def save_rapport(cur, rapport):
    cur.execute("""
        INSERT INTO rapport_qualite
        (date_controle, source, nb_enregistrements, nb_doublons,
         nb_nulls, nb_aberrants, taux_completude, statut, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        datetime.now(timezone.utc),
        rapport["source"],
        rapport["nb_enregistrements"],
        rapport["nb_doublons"],
        rapport["nb_nulls"],
        rapport["nb_aberrants"],
        rapport["taux_completude"],
        rapport["statut"],
        rapport["details"]
    ))
    print(f"  Rapport sauvegarde en base : {rapport['source']} — {rapport['statut']}")

# ==============================
# ALERTE SI PROBLEME
# ==============================
def check_alertes(rapports):
    print("\n[ALERTES]")
    alertes = []
    for r in rapports:
        if r["statut"] != "OK":
            alertes.append(f"ALERTE {r['source']} : {r['details']}")
        if r["taux_completude"] < SEUIL_COMPLETUDE:
            alertes.append(
                f"ALERTE CRITIQUE {r['source']} : "
                f"completude {r['taux_completude']}% < {SEUIL_COMPLETUDE}%"
            )

    if alertes:
        print("  PROBLEMES DETECTES :")
        for a in alertes:
            print(f"    -> {a}")
        return False  # Pipeline doit etre bloque
    else:
        print("  Aucune alerte — donnees dans les normes")
        return True

# ==============================
# MAIN
# ==============================
def main():
    print("=" * 40)
    print("DATA QUALITY CHECK START")
    print("=" * 40)

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:

            # Controles
            rapport_air   = check_qualite_air(cur)
            rapport_meteo = check_qualite_meteo(cur)
            details_coherence = check_coherence(cur)

            # Ajouter details coherence
            if details_coherence:
                rapport_air["details"] += " | " + " | ".join(details_coherence)

            # Sauvegarder rapports
            print("\n[SAUVEGARDE RAPPORTS]")
            save_rapport(cur, rapport_air)
            save_rapport(cur, rapport_meteo)

            # Alertes
            pipeline_ok = check_alertes([rapport_air, rapport_meteo])

    print("\n" + "=" * 40)
    if pipeline_ok:
        print("DATA QUALITY CHECK DONE — STATUT GLOBAL : OK")
    else:
        print("DATA QUALITY CHECK DONE — STATUT GLOBAL : WARNING")
        print("PIPELINE BLOQUE — verifier les donnees")
        exit(1)  # Code retour 1 = Airflow marquera la tache en echec

if __name__ == "__main__":
    main()