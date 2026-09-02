import psycopg
import joblib
import os
import numpy as np
from functools import wraps

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# ══════════════════════════════════════════════
# DÉCORATEURS DE SÉCURITÉ
# ══════════════════════════════════════════════

def role_required(*roles):
    """
    Décorateur : vérifie que l'utilisateur connecté a l'un des rôles autorisés.
    Usage : @role_required('admin') ou @role_required('admin', 'editeur')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            try:
                profil = request.user.profil
            except Exception:
                return HttpResponseForbidden("Profil non configuré. Contactez l'administrateur.")
            if profil.role not in roles:
                return HttpResponseForbidden(
                    f"Accès refusé. Votre rôle '{profil.get_role_display()}' "
                    f"ne permet pas d'accéder à cette ressource."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ══════════════════════════════════════════════
# AUTHENTIFICATION
# ══════════════════════════════════════════════

def login_view(request):
    """Page de connexion GoodAir."""
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, 'Identifiant ou mot de passe incorrect.')

    return render(request, 'registration/login.html')


def logout_view(request):
    """Déconnexion — redirige vers login."""
    logout(request)
    return redirect('/login/')


# ══════════════════════════════════════════════
# UTILITAIRES INTERNES
# ══════════════════════════════════════════════

def get_db():
    db = settings.DATABASES['default']
    return psycopg.connect(
        dbname=db['NAME'], user=db['USER'],
        password=db['PASSWORD'], host=db['HOST'], port=db['PORT']
    )


MODEL_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'etl', 'model_aqi.joblib'
)

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def get_niveau_aqi(aqi):
    if aqi <= 50:   return "Bon"
    if aqi <= 100:  return "Modéré"
    if aqi <= 150:  return "Mauvais pour groupes sensibles"
    if aqi <= 200:  return "Mauvais"
    if aqi <= 300:  return "Très mauvais"
    return "Dangereux"

def get_couleur_aqi(aqi):
    if aqi <= 50:   return "#00E400"
    if aqi <= 100:  return "#FFFF00"
    if aqi <= 150:  return "#FF7E00"
    if aqi <= 200:  return "#FF0000"
    if aqi <= 300:  return "#8F3F97"
    return "#7E0023"


# ══════════════════════════════════════════════
# PAGE PRINCIPALE — accessible à tous les rôles
# ══════════════════════════════════════════════

@login_required
def index(request):
    profil = request.user.profil
    return render(request, 'dashboard/index.html', {
        'user':  request.user,
        'role':  profil.role,
        'role_label': profil.get_role_display(),
    })


# ══════════════════════════════════════════════
# API — AQI (viewer, editeur, admin)
# ══════════════════════════════════════════════

@login_required
@role_required('viewer', 'editeur', 'admin')
def api_aqi(request):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (l.nom_ville)
                    l.nom_ville, l.latitude, l.longitude,
                    mqa.aqi, mqa.pm25, mqa.pm10, mqa.o3, mqa.no2,
                    t.timestamp_utc
                FROM mesure_qualite_air mqa
                JOIN localisation l ON mqa.id_loc = l.id_loc
                JOIN temps t ON mqa.id_temps = t.id_temps
                ORDER BY l.nom_ville, t.timestamp_utc DESC
            """)
            rows = cur.fetchall()

    pkg = load_model()
    predictions_ml = {}

    if pkg:
        model   = pkg["model"]
        encoder = pkg["encoder"]
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT ON (l.nom_ville)
                        l.nom_ville, mm.temperature, mm.humidite,
                        mm.pression, mm.vitesse_vent, mm.precipitation,
                        t.heure, t.mois, t.jour
                    FROM mesure_meteo mm
                    JOIN localisation l ON mm.id_loc = l.id_loc
                    JOIN temps t ON mm.id_temps = t.id_temps
                    ORDER BY l.nom_ville, t.timestamp_utc DESC
                """)
                meteo_rows = cur.fetchall()
        for r in meteo_rows:
            ville = r[0]
            try:
                if ville in encoder.classes_:
                    ville_enc = encoder.transform([ville])[0]
                    X = np.array([[r[1] or 0, r[2] or 0, r[3] or 1013,
                                   r[4] or 0, r[5] or 0, r[6] or 12,
                                   r[7] or 6, r[8] or 17, ville_enc]])
                    predictions_ml[ville] = round(float(model.predict(X)[0]), 1)
            except Exception:
                continue

    aqis = [float(r[3]) for r in rows if r[3]]
    all_same = len(set(aqis)) == 1

    data = []
    for r in rows:
        ville = r[0]
        aqi_reel = float(r[3]) if r[3] else 0
        if all_same and ville in predictions_ml:
            aqi_display = predictions_ml[ville]
            source_aqi  = "ML"
        else:
            aqi_display = aqi_reel
            source_aqi  = "AQICN"
        data.append({
            "ville":      ville,
            "lat":        float(r[1]),
            "lon":        float(r[2]),
            "aqi":        aqi_display,
            "aqi_reel":   aqi_reel,
            "source_aqi": source_aqi,
            "pm25":       float(r[4]) if r[4] else None,
            "pm10":       float(r[5]) if r[5] else None,
            "o3":         float(r[6]) if r[6] else None,
            "no2":        float(r[7]) if r[7] else None,
            "niveau":     get_niveau_aqi(aqi_display),
            "couleur":    get_couleur_aqi(aqi_display),
            "timestamp":  r[8].isoformat() if r[8] else None,
        })

    return JsonResponse({"villes": data})


# ══════════════════════════════════════════════
# API — MÉTÉO (viewer, editeur, admin)
# ══════════════════════════════════════════════

@login_required
@role_required('viewer', 'editeur', 'admin')
def api_meteo(request):
    ville = request.GET.get('ville', '')
    with get_db() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT DISTINCT ON (l.nom_ville)
                    l.nom_ville, mm.temperature, mm.humidite,
                    mm.pression, mm.vitesse_vent, mm.precipitation,
                    t.timestamp_utc
                FROM mesure_meteo mm
                JOIN localisation l ON mm.id_loc = l.id_loc
                JOIN temps t ON mm.id_temps = t.id_temps
            """
            if ville:
                query += " WHERE l.nom_ville = %s"
                query += " ORDER BY l.nom_ville, t.timestamp_utc DESC"
                cur.execute(query, (ville,))
            else:
                query += " ORDER BY l.nom_ville, t.timestamp_utc DESC"
                cur.execute(query)
            rows = cur.fetchall()

    data = [{
        "ville":         r[0],
        "temperature":   float(r[1]) if r[1] else None,
        "humidite":      float(r[2]) if r[2] else None,
        "pression":      float(r[3]) if r[3] else None,
        "vitesse_vent":  float(r[4]) if r[4] else None,
        "precipitation": float(r[5]) if r[5] else None,
        "timestamp":     r[6].isoformat() if r[6] else None,
    } for r in rows]

    return JsonResponse({"meteo": data})


# ══════════════════════════════════════════════
# API — HISTORIQUE (viewer, editeur, admin)
# ══════════════════════════════════════════════

@login_required
@role_required('viewer', 'editeur', 'admin')
def api_historique(request):
    ville = request.GET.get('ville', 'Paris')
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.timestamp_utc, t.heure, mqa.aqi
                FROM mesure_qualite_air mqa
                JOIN localisation l ON mqa.id_loc = l.id_loc
                JOIN temps t ON mqa.id_temps = t.id_temps
                WHERE l.nom_ville = %s
                  AND t.timestamp_utc >= NOW() - INTERVAL '24 hours'
                ORDER BY t.timestamp_utc
            """, (ville,))
            rows = cur.fetchall()

    data = [{
        "timestamp": r[0].isoformat(),
        "heure":     r[1],
        "aqi":       float(r[2]) if r[2] else None,
    } for r in rows]

    return JsonResponse({"ville": ville, "historique": data})


# ══════════════════════════════════════════════
# API — PRÉDICTIONS ML (viewer, editeur, admin)
# ══════════════════════════════════════════════

@login_required
@role_required('viewer', 'editeur', 'admin')
def api_predictions(request):
    pkg = load_model()
    if not pkg:
        return JsonResponse({"error": "Modele ML non disponible"}, status=404)

    model   = pkg["model"]
    encoder = pkg["encoder"]

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (l.nom_ville)
                    l.nom_ville, mm.temperature, mm.humidite,
                    mm.pression, mm.vitesse_vent, mm.precipitation,
                    t.heure, t.mois, t.jour
                FROM mesure_meteo mm
                JOIN localisation l ON mm.id_loc = l.id_loc
                JOIN temps t ON mm.id_temps = t.id_temps
                ORDER BY l.nom_ville, t.timestamp_utc DESC
            """)
            rows = cur.fetchall()

    predictions = []
    for r in rows:
        ville = r[0]
        try:
            if ville not in encoder.classes_:
                continue
            ville_enc = encoder.transform([ville])[0]
            X = np.array([[r[1] or 0, r[2] or 0, r[3] or 1013,
                           r[4] or 0, r[5] or 0, r[6] or 12,
                           r[7] or 6, r[8] or 17, ville_enc]])
            aqi_predit = float(model.predict(X)[0])
            predictions.append({
                "ville":      ville,
                "aqi_predit": round(aqi_predit, 1),
                "niveau":     get_niveau_aqi(aqi_predit),
                "couleur":    get_couleur_aqi(aqi_predit),
            })
        except Exception:
            continue

    return JsonResponse({"predictions": predictions})


# ══════════════════════════════════════════════
# API — RAPPORT QUALITÉ (admin uniquement)
# ══════════════════════════════════════════════

@login_required
@role_required('admin')
def api_qualite(request):
    """Accès restreint : admin uniquement."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date_controle, source, nb_enregistrements,
                       nb_doublons, nb_nulls, nb_aberrants,
                       taux_completude, statut, details
                FROM rapport_qualite
                ORDER BY date_controle DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

    data = [{
        "date":               r[0].isoformat(),
        "source":             r[1],
        "nb_enregistrements": r[2],
        "nb_doublons":        r[3],
        "nb_nulls":           r[4],
        "nb_aberrants":       r[5],
        "taux_completude":    float(r[6]) if r[6] else None,
        "statut":             r[7],
        "details":            r[8],
    } for r in rows]

    return JsonResponse({"rapports": data})


# ══════════════════════════════════════════════
# VUE — GESTION UTILISATEURS (admin uniquement)
# ══════════════════════════════════════════════

@login_required
@role_required('admin')
def admin_users(request):
    """Liste des utilisateurs — visible uniquement par l'admin."""
    from django.contrib.auth.models import User
    users = User.objects.select_related('profil').all().order_by('username')
    return render(request, 'dashboard/admin_users.html', {
        'users': users,
        'role':  request.user.profil.role,
    })
