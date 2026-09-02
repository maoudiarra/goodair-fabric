"""
Script à exécuter UNE SEULE FOIS après les migrations :
    python manage.py shell < create_users.py

Crée les 3 utilisateurs GoodAir avec leurs rôles.
"""

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goodair_viz.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Profil

USERS = [
    {
        "username":     "mdiarra",
        "password":     "Diarra1997!",          # ton mot de passe actuel
        "first_name":   "Maou",
        "last_name":    "DIARRA",
        "email":        "maou.diarra@goodair.fr",
        "role":         "admin",
        "organisation": "GoodAir — Direction technique",
    },
    {
        "username":     "editeur_goodair",
        "password":     "GoodAir_Edit_2026!",
        "first_name":   "Éditeur",
        "last_name":    "GoodAir",
        "email":        "editeur@goodair.fr",
        "role":         "editeur",
        "organisation": "GoodAir — Pôle Data",
    },
    {
        "username":     "chercheur_goodair",
        "password":     "GoodAir_View_2026!",
        "first_name":   "Chercheur",
        "last_name":    "GoodAir",
        "email":        "chercheur@goodair.fr",
        "role":         "viewer",
        "organisation": "GoodAir — Laboratoire",
    },
]

for u_data in USERS:
    role   = u_data.pop("role")
    org    = u_data.pop("organisation")
    pwd    = u_data.pop("password")

    user, created = User.objects.get_or_create(username=u_data["username"])
    if created:
        user.set_password(pwd)
        user.first_name = u_data.get("first_name", "")
        user.last_name  = u_data.get("last_name", "")
        user.email      = u_data.get("email", "")
        user.is_staff   = (role == "admin")
        user.save()
        Profil.objects.create(user=user, role=role, organisation=org)
        print(f"✅ Créé : {user.username} [{role}]")
    else:
        # Met à jour le profil si l'utilisateur existe déjà
        profil, _ = Profil.objects.get_or_create(user=user)
        profil.role = role
        profil.organisation = org
        profil.save()
        print(f"🔄 Mis à jour : {user.username} [{role}]")

print("\n✅ Terminé. Utilisateurs disponibles :")
for u in User.objects.select_related('profil').all():
    print(f"   {u.username:25s} → {u.profil.get_role_display()}")
