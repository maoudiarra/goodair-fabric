import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goodair_viz.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Profil

u1, _ = User.objects.get_or_create(username='mdiarra')
u1.set_password('Diarra1997!')
u1.first_name = 'Maou'
u1.last_name = 'DIARRA'
u1.is_staff = True
u1.save()
Profil.objects.update_or_create(user=u1, defaults={'role': 'admin', 'organisation': 'GoodAir'})
print('OK mdiarra admin')

u2, _ = User.objects.get_or_create(username='editeur_goodair')
u2.set_password('GoodAir_Edit_2026!')
u2.save()
Profil.objects.update_or_create(user=u2, defaults={'role': 'editeur', 'organisation': 'GoodAir'})
print('OK editeur_goodair editeur')

u3, _ = User.objects.get_or_create(username='chercheur_goodair')
u3.set_password('GoodAir_View_2026!')
u3.save()
Profil.objects.update_or_create(user=u3, defaults={'role': 'viewer', 'organisation': 'GoodAir'})
print('OK chercheur_goodair viewer')

print('\nUtilisateurs en base :')
for u in User.objects.select_related('profil').all():
    print(f'  {u.username} -> {u.profil.role}')
